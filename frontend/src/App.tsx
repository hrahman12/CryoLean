import { lazy, Suspense, useCallback, useEffect, useReducer, useRef, useState } from 'react';
import { ArrowRight, ArrowUpRight, Snowflake, FlaskConical, Monitor, BookOpen, ChevronDown, CircleHelp, Check, LoaderCircle } from 'lucide-react';
import * as client from './services/cryolean-client';
import snapshotData from './data/catalog.json';
import { initialSetup, setupReducer } from './features/verification/setup-state';
import { RequirementReview } from './features/verification/RequirementReview';
import { VerificationPanel } from './features/verification/VerificationPanel';
import { SuggestedFixes } from './features/verification/SuggestedFixes';
import { DEMO_SCENARIOS, type DemoScenario } from './features/demo/demo-scenarios';
import { Dialog } from './components/Dialog';
import { ConfiguratorCards } from './components/ConfiguratorCards';
import { RecordedDemos } from './features/demo/RecordedDemos';
import { CoverageMatrix } from './components/CoverageMatrix';
import { ResearchEvidence } from './components/ResearchEvidence';
import { Evidence } from './components/Evidence';
import { VerificationIngredients } from './components/VerificationIngredients';
import { humanize, safeUrl } from './services/format';
import { getComponentForCheck } from './scene/mappings/constraint-to-component';
import { getSceneDefinition } from './scene/registry';
import { EXPERIMENT_PRESENTATION, startingConfiguration } from './features/catalog/experiment-presentation';
import type { Industry, ExperimentProfile, EquipmentItem, ExperimentRequirements, ConfigurationDetails,
  LeanStatus, EvidenceRecord, AlternativeCandidate, VerificationResult, Quantity, VerifiedFix, VerifiedRepairSearch } from './types/backend';
import type { SceneViewMode } from './scene/core/LabCanvas';

const Viewer = lazy(() => import('./scene/core/LabCanvas'));
interface CatalogSnapshot {
  provenance: { source: string; seed_sha256: string; note: string };
  industries: Industry[]; experiments: ExperimentProfile[]; equipment: EquipmentItem[];
  profiles: Record<string, ExperimentRequirements>; configurations: Record<string, ConfigurationDetails>;
}
const snapshot = snapshotData as unknown as CatalogSnapshot;
const errorMessage = (e: unknown) => e instanceof Error ? e.message : 'The backend request failed. Please retry.';

export function App() {
  const [setup, dispatch] = useReducer(setupReducer, initialSetup);
  const [mode,setMode]=useState<'live'|'recorded'>('live');
  const setupRef = useRef(setup); setupRef.current = setup;
  const busy = useRef<number | null>(null);
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(true);
  const [catalog, setCatalog] = useState({ industries: snapshot.industries, experiments: snapshot.experiments, equipment: snapshot.equipment });
  const [catalogError, setCatalogError] = useState('');
  const [leanStatus, setLeanStatus] = useState<LeanStatus | null>(null);
  const [industry, setIndustry] = useState('materials_and_nanotechnology');
  const [profile, setProfile] = useState<ExperimentRequirements | null>(null);
  const [configuration, setConfiguration] = useState<ConfigurationDetails | null>(null);
  const [loadError, setLoadError] = useState('');
  const [reconnect, setReconnect] = useState(0);
  const [query, setQuery] = useState('');
  const [matcherConsent, setMatcherConsent] = useState(false);
  const [matches, setMatches] = useState<Awaited<ReturnType<typeof client.matchExperiment>>['matches']>([]);
  const [matching, setMatching] = useState(false);
  const [matchError, setMatchError] = useState('');
  const [demo, setDemo] = useState<DemoScenario | null>(null);
  const [dialog, setDialog] = useState<'demo' | 'research' | 'how' | 'evidence' | 'proof' | 'alternatives' | 'equipment' | 'review' | 'why' | 'coverage' | 'choose' | null>(null);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [searching, setSearching] = useState(false);
  const [alternatives, setAlternatives] = useState<AlternativeCandidate[]>([]);
  const [searchError, setSearchError] = useState('');
  const [compareId, setCompareId] = useState('');
  const [comparisons, setComparisons] = useState<VerificationResult[]>([]);
  const [viewMode, setViewMode] = useState<SceneViewMode>('inside');
  const [animating, setAnimating] = useState(false);
  const [highlight, setHighlight] = useState<{id: string; outcome: 'pass' | 'fail' | 'unknown' | null} | null>(null);
  const [proofLoading, setProofLoading] = useState(false);
  const [repairSearch,setRepairSearch]=useState<VerifiedRepairSearch|null>(null);
  const [repairPending,setRepairPending]=useState(false);
  const [repairError,setRepairError]=useState('');
  const [applyingFix,setApplyingFix]=useState<string|null>(null);
  const [repairRetry,setRepairRetry]=useState(0);
  const [repairHistory,setRepairHistory]=useState<{resultId:string;original:VerificationResult}|null>(null);

  useEffect(()=>{
    let current=true;
    setRepairSearch(null);setRepairError('');setRepairPending(false);setApplyingFix(null);
    const result=setup.result;
    if(!connected||!result||result.verdict==='REQUIREMENTS_MET')return;
    setRepairPending(true);
    void client.getVerifiedRepairs(result.result_id).then(r=>{if(current)setRepairSearch(r);})
      .catch(e=>{if(current)setRepairError(errorMessage(e));}).finally(()=>{if(current)setRepairPending(false);});
    return()=>{current=false;};
  },[setup.result?.result_id,setup.revision,connected,repairRetry]);

  async function applyFix(fix:VerifiedFix){
    const captured=setupRef.current;
    if(!captured.result||applyingFix||fix.verified!==true||fix.lean_verdict!=='REQUIREMENTS_MET')return;
    setApplyingFix(fix.id);setRepairError('');
    try{
      const result=await client.applyVerifiedRepair(captured.result.result_id,fix.id);
      if(setupRef.current.revision!==captured.revision||setupRef.current.result?.result_id!==captured.result.result_id)return;
      if(result.verdict!=='REQUIREMENTS_MET'||result.verification.concrete_evaluation.lean_input_hash!==fix.verification.concrete_evaluation.lean_input_hash)
        throw new Error('The verified candidate did not reproduce. Run a fresh check; no passing result was applied.');
      setRepairHistory({resultId:result.result_id,original:captured.result});
      dispatch({type:'apply-fix',originalResultId:captured.result.result_id,configurationId:fix.configuration_id,parameters:fix.parameters,result});
    }catch(e){if(setupRef.current.revision===captured.revision)setRepairError(errorMessage(e));}
    finally{setApplyingFix(null);}
  }

  // Late injection and manual retry both recover from preview without reloading.
  useEffect(() => {
    let current = true;
    async function connect() {
      setConnecting(true); setCatalogError('');
      const available = await client.checkBridgeConnection();
      if (!current) return;
      setConnected(available);
      if (available) {
        try {
          const [industries, experiments, equipment] = await Promise.all([client.listIndustries(), client.listExperiments(), client.listEquipment()]);
          if (!current) return;
          setCatalog({ industries: industries.industries, experiments: experiments.experiments, equipment: equipment.equipment });
        } catch (e) { if (current) setCatalogError(errorMessage(e)); }
        try { const status = await client.getLeanStatus(); if (current) setLeanStatus(status); }
        catch { if (current) setLeanStatus(null); }
      } else if (current) setLeanStatus(null);
      if (current) setConnecting(false);
    }
    void connect();
    const onReady = () => setReconnect(x => x + 1);
    window.addEventListener('pywebviewready', onReady);
    return () => { current = false; window.removeEventListener('pywebviewready', onReady); };
  }, [reconnect]);

  useEffect(() => {
    let current = true; setProfile(null); setLoadError('');
    if (!setup.experimentId) return;
    if (!connected) { setProfile(snapshot.profiles[setup.experimentId] ?? null); return; }
    void client.getExperimentRequirements(setup.experimentId).then(r => { if (current) setProfile(r); })
      .catch(e => { if (current) setLoadError(errorMessage(e)); });
    return () => { current = false; };
  }, [setup.experimentId, connected, reconnect]);
  useEffect(() => {
    let current = true; setConfiguration(null);
    if (!setup.configurationId) return;
    if (!connected) { setConfiguration(snapshot.configurations[setup.configurationId] ?? null); return; }
    void client.getEquipmentDetails(setup.configurationId).then(r => {
      if (current) setConfiguration(r.configurations.find(c => c.id === setup.configurationId) ?? null);
    }).catch(e => { if (current) setLoadError(errorMessage(e)); });
    return () => { current = false; };
  }, [setup.configurationId, connected, reconnect]);
  useEffect(() => { setHighlight(null); setAlternatives([]); setComparisons([]); setSearchError(''); setSearching(false); }, [setup.revision]);
  useEffect(() => {
    if (!connected || !setup.result) return;
    const revision = setup.revision;
    const resultId = setup.result.result_id;
    const refresh = async () => {
      if (document.visibilityState === 'hidden') return;
      try { await client.getVerificationDetails(resultId); }
      catch (e) {
        if (setupRef.current.revision !== revision || setupRef.current.result?.result_id !== resultId) return;
        dispatch({type:'start',revision});
        dispatch({type:'error',revision,message:errorMessage(e)});
      }
    };
    window.addEventListener('focus',refresh);document.addEventListener('visibilitychange',refresh);
    return()=>{window.removeEventListener('focus',refresh);document.removeEventListener('visibilitychange',refresh);};
  },[connected,setup.result,setup.revision]);

  const activeProfile = profile?.id === setup.experimentId ? profile : null;
  const activeConfig = configuration?.id === setup.configurationId ? configuration : null;
  const experiment = catalog.experiments.find(e => e.id === setup.experimentId);
  const equipmentItem = catalog.equipment.find(e => e.configurations.some(c => c.id === setup.configurationId));
  const scene = getSceneDefinition(setup.experimentId, equipmentItem?.id ?? '',experiment?.visualization,activeConfig?.visualization??equipmentItem?.visualization);
  const filteredExperiments = catalog.experiments.filter(e => query.trim()
    ? `${e.plain_name} ${e.name} ${e.description ?? ''}`.toLowerCase().includes(query.trim().toLowerCase())
    : !industry || e.industry === industry||e.industries?.includes(industry));

  function selectExperiment(id: string) {
    const exp = catalog.experiments.find(e => e.id === id);
    if (exp && !exp.industries?.includes(industry) && exp.industry!==industry) setIndustry(exp.industry);
    dispatch({ type: 'experiment', id, configurationId: startingConfiguration(id,catalog.equipment,exp) });
    setViewMode('inside'); setAnimating(false); setMatches([]); setDemo(null);
  }
  function selectIndustry(id:string) {
    const next=catalog.experiments.find(e=>!id||e.industry===id||e.industries?.includes(id));
    setIndustry(id);setQuery('');setDemo(null);setAnimating(false);setViewMode('inside');
    dispatch({type:'experiment',id:next?.id??'',configurationId:next?startingConfiguration(next.id,catalog.equipment,next):''});
  }
  function selectEquipment(id: string) { dispatch({ type: 'equipment', id }); setViewMode('inside'); setAnimating(false); }
  function selectDemo(scenario: DemoScenario) {
    const exp = catalog.experiments.find(e => e.id === scenario.experimentId);
    if (exp) setIndustry(exp.industry);
    dispatch({ type: 'experiment', id: scenario.experimentId, configurationId: scenario.configurationId, parameters: scenario.parameters });
    setDemo(scenario); setQuery(''); setViewMode('inside'); setAnimating(false); setDialog(null);
  }
  const showEvidence = useCallback((records: EvidenceRecord[]) => { setEvidence(records); setDialog('evidence'); }, []);
  const highlightCheck = useCallback((id: string, outcome: 'pass' | 'fail' | 'unknown' | null) => {
    setHighlight({ id, outcome }); setViewMode('inside');
  }, []);
  async function verify() {
    const state = setupRef.current;
    if (!state.confirmed || busy.current === state.revision || !activeProfile || !activeConfig) return;
    busy.current = state.revision;
    dispatch({ type: 'start', revision: state.revision });
    try {
      const result = await client.checkCompatibility(state.experimentId, state.configurationId, {
        confirmed: true, parameters: state.parameters, requirementEdits: state.edits, suggestions: false,
      });
      dispatch({ type: 'success', revision: state.revision, result });
      if (setupRef.current.revision === state.revision) {
        const check = [...result.checks, ...result.coupled_checks].find(c => c.outcome === 'fail')
          ?? [...result.checks, ...result.coupled_checks].find(c => ['unknown', 'unsupported'].includes(c.outcome));
        const component = check && getComponentForCheck(check);
        if (component && check) highlightCheck(component.componentId, check.outcome === 'fail' ? 'fail' : 'unknown');
      }
    } catch (e) { dispatch({ type: 'error', revision: state.revision, message: errorMessage(e) }); }
    finally { if (busy.current === state.revision) busy.current = null; }
  }
  async function searchAlternatives() {
    const state = setupRef.current;
    if (!state.confirmed) return;
    setDialog('alternatives'); setSearching(true); setSearchError(''); setComparisons([]);
    try {
      const found = await client.findCompatibleEquipment(state.experimentId, { confirmed: true, parameters: state.parameters, requirementEdits: state.edits });
      if (setupRef.current.revision === state.revision) setAlternatives(found.candidates.filter(c=>c.verified===true&&c.lean_verdict==='REQUIREMENTS_MET'&&!c.hypothetical));
    } catch (e) { if (setupRef.current.revision === state.revision) setSearchError(errorMessage(e)); }
    finally { if (setupRef.current.revision === state.revision) setSearching(false); }
  }
  async function compare() {
    const state = setupRef.current;
    if (!state.confirmed || !compareId || compareId === state.configurationId) return;
    setSearching(true); setSearchError('');
    try {
      const result = await client.compareEquipment(state.experimentId, [state.configurationId, compareId], { confirmed: true, parameters: state.parameters, requirementEdits: state.edits });
      if (setupRef.current.revision === state.revision) setComparisons(result.results);
    } catch (e) { if (setupRef.current.revision === state.revision) setSearchError(errorMessage(e)); }
    finally { if (setupRef.current.revision === state.revision) setSearching(false); }
  }
  async function showProof() {
    if (!setup.result) return;
    const state = setupRef.current; setProofLoading(true);
    try {
      const fresh = await client.getVerificationDetails(setup.result.result_id);
      if (setupRef.current.revision === state.revision && fresh.fingerprint === state.result?.fingerprint) setDialog('proof');
    } catch (e) {
      if (setupRef.current.revision === state.revision) {
        dispatch({ type: 'start', revision: state.revision });
        dispatch({ type: 'error', revision: state.revision, message: errorMessage(e) });
      }
    } finally { setProofLoading(false); }
  }
  async function match() {
    if (!matcherConsent || !connected || !query.trim()) return;
    const capturedQuery = query;
    setMatching(true); setMatchError('');
    try { const found = await client.matchExperiment(query.trim()); if (capturedQuery === query) setMatches(found.matches); }
    catch (e) { setMatchError(errorMessage(e)); } finally { setMatching(false); }
  }
  const parameterDefaults = Object.fromEntries((activeProfile?.params ?? []).filter(p => p.value && typeof p.value === 'object')
    .map(p => [p.name, p.value as Quantity]));
  const title = dialog === 'demo' ? 'Try a guided demo' : dialog === 'research' ? 'The science behind the answer'
    : dialog === 'how' ? 'From your experiment to an answer' : dialog === 'evidence' ? 'Source evidence'
    : dialog === 'review' ? 'Review your experiment requirements' : dialog === 'why' ? 'Why this result?' : dialog === 'coverage' ? 'Industry coverage matrix' : dialog === 'choose' ? 'Describe your experiment' : dialog === 'proof' ? 'Mathematical verification' : dialog === 'equipment' ? 'Documented configuration' : 'Find another machine';

  return <div className="app-shell">
    <a href="#workspace" className="skip-link">Skip to experiment</a>
    <header className="site-header"><a className="brand" href="#" aria-label="CryoLean home"><span className="brand-mark"><Snowflake size={24} strokeWidth={1.5} /></span>CryoLean<span className="brand-caption">A little colder. A lot clearer.</span></a>
      <nav aria-label="Main navigation"><a href="#workspace" className="nav-explore">Explore</a><button onClick={() => setDialog('how')}>How it works</button>
        <button onClick={() => setDialog('coverage')}>Industry coverage</button><a href="https://github.com/hrahman12/CryoLean" target="_blank" rel="noreferrer">GitHub <ArrowUpRight size={13} /></a></nav>
      <div className="mode-tabs" role="tablist" aria-label="CryoLean mode"><button role="tab" aria-selected={mode==='live'} onClick={()=>setMode('live')}>Live checker</button><button role="tab" aria-selected={mode==='recorded'} onClick={()=>setMode('recorded')}>Demos · recorded runs</button></div>
    </header>
    <div className="hero configurator-hero reference-hero"><h1 className="reference-logo">CryoLean</h1>
      <h2>Can this cryostat do my experiment?</h2>
    </div>
    {demo && <div className="guided-banner" data-testid="guided"><FlaskConical size={18} /><div><strong>Guided example · {demo.title}</strong><span>{demo.learningGoal}</span></div>
      <button onClick={() => setDemo(null)}>Return to normal mode <ArrowRight size={15} /></button></div>}
    {(catalogError || loadError) && <div className="global-error" role="alert">Catalog unavailable: {catalogError || loadError}<button onClick={() => { dispatch({type:'invalidate'}); setReconnect(x => x + 1); }}>Retry loading</button></div>}
    <div className={`backend-state ${connected?'':'disconnected'}`} role="status">{mode==='recorded'?'Recorded demo playback · historical Lean evaluations':connecting?'Connecting to the verification engine…':connected&&leanStatus?.lean_available?'Live backend connected · Lean 4 + Z3':'Live backend unavailable'} {!connected&&<button className="text-button" onClick={()=>setReconnect(x=>x+1)}>Reconnect</button>}</div>
    {mode==='recorded'?<RecordedDemos catalog={catalog} configurations={snapshot.configurations} onUseLive={(eid,cid,parameters)=>{setMode('live');const e=catalog.experiments.find(e=>e.id===eid);if(e)setIndustry(e.industry);dispatch({type:'experiment',id:eid,configurationId:cid,parameters});setViewMode('inside');}}/>:<ConfiguratorCards industries={catalog.industries} experiments={catalog.experiments} equipment={catalog.equipment} industry={industry}
      backendAvailable={connected&&Boolean(leanStatus?.lean_available)}
      experiment={experiment} profile={activeProfile} configuration={activeConfig} equipmentItem={equipmentItem} setup={setup} scene={scene}
      viewMode={viewMode} animating={animating} highlight={highlight} onIndustry={selectIndustry} onExperiment={selectExperiment} onEquipment={selectEquipment}
      onViewMode={setViewMode} onAnimating={setAnimating} onHighlight={highlightCheck} onEvidence={showEvidence}
      onConfirm={value=>dispatch({type:'confirm',value})} onParameter={(name,quantity)=>dispatch({type:'parameter',name,quantity})} onEdit={edit=>dispatch({type:'edit',edit})}
      onReview={()=>{if(setup.confirmed)void verify();else setDialog('review');}} onWhy={()=>setDialog('why')}
      onSearch={searchAlternatives} onSpecs={()=>setDialog('equipment')} onCoverage={()=>setDialog('coverage')} onDescribe={()=>setDialog('choose')}
      repairs={setup.result&&<SuggestedFixes result={setup.result} search={repairSearch} pending={repairPending} error={repairError} applying={applyingFix}
        onApply={applyFix} onRetry={()=>setRepairRetry(x=>x+1)} previous={repairHistory?.resultId===setup.result.result_id?repairHistory.original:null}/>}/>}

    {mode==='live'&&<VerificationIngredients result={setup.result} experiment={experiment} configuration={activeConfig} onProof={()=>{if(setup.result)void showProof();}}/>}

    <ResearchEvidence/>

    <p className="reference-slogan">Switch the cryostat. Keep the experiment. Check again.</p><footer className="site-footer"><span><Snowflake size={13} /> CryoLean · Cryo, made simple.</span><span className="featured-stamp">180 featured pairings · 113 met (63%) · decided by the Lean 4 checker</span><span className="full-catalog-stamp">Full catalog: 44,880 pairs · 3,118 met (6.9%)</span><button onClick={()=>setDialog('coverage')}>Coverage matrix</button><button onClick={()=>setDialog('how')}>How it works</button><button onClick={() => setDialog('research')}><CircleHelp size={14} /> What is verified?</button></footer>
    <Dialog open={dialog !== null} title={title} onClose={() => setDialog(null)}>
      {dialog==='coverage'&&<CoverageMatrix/>}
      {dialog==='review'&&<RequirementReview profile={activeProfile} setup={setup} connected={connected} onConfirm={value=>dispatch({type:'confirm',value})}
        onVerify={()=>{setDialog(null);void verify();}} onParameter={(name,quantity)=>dispatch({type:'parameter',name,quantity})} onEdit={edit=>dispatch({type:'edit',edit})}
        onEvidence={showEvidence} onHighlight={key=>{const c=getComponentForCheck({keys:[key]});if(c)highlightCheck(c.componentId,null);}}/>}
      {dialog==='why'&&setup.result&&<VerificationPanel result={setup.result} onHighlight={highlightCheck} onEvidence={showEvidence} onProof={showProof}
        onReview={()=>{dispatch({type:'invalidate'});setDialog('review');}} onSearch={searchAlternatives} searching={searching}
        onParameter={(name,quantity)=>{dispatch({type:'parameter',name,quantity});setDialog('review');}} profileParameters={parameterDefaults}/>}
      {dialog==='choose'&&<><p>Search the documented procedures, or ask the configured matcher for a suggested profile.</p>
        <label className="field-label" htmlFor="experiment-search">What would you like to do?</label><input id="experiment-search" className="search-input" value={query} onChange={e=>{setQuery(e.target.value);setMatches([]);}} placeholder="Describe the experiment"/>
        <div className="experiment-list">{filteredExperiments.map(e=><button className="experiment-choice" key={e.id} onClick={()=>{selectExperiment(e.id);setDialog(null);}}><strong>{EXPERIMENT_PRESENTATION[e.id]?.title??e.name}</strong></button>)}</div>
        {connected&&<><label className="confirmation"><input type="checkbox" checked={matcherConsent} onChange={e=>setMatcherConsent(e.target.checked)}/><span>I agree to send this description to the configured matcher, which may use an external AI provider.</span></label><button className="secondary-button" onClick={match} disabled={!matcherConsent||matching||!query.trim()}>{matching?'Finding profiles…':'Suggest a researched profile'}</button></>}
        {matchError&&<p role="alert" className="error-text">{matchError}</p>}{matches.map(m=><button className="match-choice" key={m.experiment_id} onClick={()=>{selectExperiment(m.experiment_id);setDialog(null);}}>{m.name}<small>{m.reason} · Review and confirm before checking.</small></button>)}</>}
      {dialog === 'evidence' && <Evidence records={evidence} />}
      {dialog === 'equipment' && activeConfig && <><p>{activeConfig.name}</p><p className="muted">Only this configuration’s documented installed capabilities are represented as installed. Proposed modifications are listed separately.</p>
        {activeConfig.modifications?.map((m,index) => <div className="scope-note" key={index}><strong>{humanize(m.status)}</strong><p>{m.description}</p><pre>{JSON.stringify(m.changes, null, 2)}</pre></div>)}
        {activeConfig.capabilities.map(c => <details className="capability-row" key={c.key}><summary><span>{humanize(c.key)}<small>{c.display}</small></span><span className="tag">{humanize(c.install)}</span></summary><p>Evidence status: {humanize(c.evidence_status)}</p><Evidence records={c.evidence} /></details>)}</>}
      {dialog === 'proof' && setup.result && <><p className="dialog-intro">The checker’s record for this exact setup.</p><div className="featured-context"><strong>Featured coverage: 180 pairings · 113 met · 1 needs information · 66 not met</strong><small>Full catalog: 44,880 pairs · 3,118 met (6.9%).</small></div><p>{setup.result.verdict_card?.reason}</p><dl className="proof-metadata"><dt>Verdict</dt><dd>{setup.result.verdict}</dd><dt>Source hash</dt><dd>{setup.result.verdict_card?.source_hash ?? 'Not supplied'}</dd><dt>Exact input hash</dt><dd>{setup.result.verification.concrete_evaluation.lean_input_hash}</dd><dt>Catalog fingerprint</dt><dd>{setup.result.fingerprint}</dd><dt>Axiom audit</dt><dd>{setup.result.verdict_card?.axiom_audit ?? 'Not supplied'} · {setup.result.verdict_card?.axioms_standard_only ? 'Standard axioms only' : 'Audit not established'}</dd><dt>Checker</dt><dd>{setup.result.verification.concrete_evaluation.engine}</dd></dl>
        <h3>Audited theorems</h3>{setup.result.verdict_card?.theorems?.map(t => <div className="theorem" key={t}><code>{t}</code><small>{setup.result?.verdict_card?.axioms?.[t]?.join(', ') ?? 'Audit entry unavailable'}</small></div>)}
        <p>{setup.result.verdict_card?.z3_role}</p><details><summary>Exact evaluated input</summary><pre>{JSON.stringify(setup.result.lean_input, null, 2)}</pre></details><details><summary>Full backend record</summary><pre>{JSON.stringify(setup.result, null, 2)}</pre></details>
        <h3>References</h3>{setup.result.references?.map((r,index) => <p key={index}>{(r as any).document_title ?? r.citation} {safeUrl((r as any).url) && <a href={safeUrl((r as any).url)} target="_blank" rel="noreferrer">Source ↗</a>}</p>)}</>}
      {dialog === 'alternatives' && <><p className="dialog-intro">Z3 searches. Lean checks.</p><p>Every candidate has its own Lean result. Switching machines keeps the experiment and clears its previous result.</p>
        {searching && <p role="status"><LoaderCircle size={16} className="spin" /> Checking catalog candidates…</p>}{searchError && <p role="alert" className="error-text">{searchError}</p>}
        {!searching && !alternatives.length && !searchError && <p>No verified solution found</p>}
        {alternatives.map(c => <article className="alternative" key={c.configuration_id}><h3>{c.name ?? c.configuration_id}</h3><span className={`outcome ${c.verified && c.lean_verdict === 'REQUIREMENTS_MET' ? 'pass' : 'unknown'}`}>{c.verified && c.lean_verdict === 'REQUIREMENTS_MET' ? 'Lean checked: requirements met' : client.HEADLINE[c.lean_verdict] ?? 'Not established'}</span>
          <p>{c.lean_summary}</p>{c.hypothetical && <p className="edited-note">Proposed options · not installed: {c.added_options.join(', ')}</p>}
          {!c.hypothetical && catalog.equipment.some(e => e.configurations.some(x => x.id === c.configuration_id)) && <button className="secondary-button" onClick={() => {selectEquipment(c.configuration_id);setDialog(null);}}>Select & check this machine <ArrowRight size={14} /></button>}</article>)}
        <h3>Compare two configurations</h3><label className="field-label" htmlFor="compare">Compare the current machine with</label><select id="compare" value={compareId} onChange={e => setCompareId(e.target.value)}><option value="">Choose a configuration</option>{catalog.equipment.flatMap(e => e.configurations).filter(c => c.id !== setup.configurationId).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select><button className="secondary-button" disabled={!compareId || searching} onClick={compare}>Run comparison</button>
        {!!comparisons.length && <div className="comparison-table"><table><thead><tr><th>Configuration</th><th>Lean verdict</th><th>Reason</th></tr></thead><tbody>{comparisons.map(r => <tr key={r.result_id}><td>{r.equipment.configuration_id}</td><td>{r.headline}</td><td>{r.user_message}</td></tr>)}</tbody></table></div>}</>}
      {dialog === 'how' && <><p className="dialog-intro">Explore the machine. Check the conditions.</p><ol className="how-steps"><li><h3>Start with your experiment</h3><p>Choose a researched procedure, then review its requirements and sources. Edit the inputs to match your own sample and confirm them.</p></li><li><h3>Choose the actual configuration</h3><p>A family of machines can have different magnets, wiring and installed options. CryoLean checks the configuration you selected.</p></li><li><h3>Let the backend check</h3><p>Python prepares exact quantities. The Lean 4 checker evaluates the modeled requirements. Z3 then searches for conflicts and alternatives, and Lean checks those candidates.</p></li><li><h3>Follow the reason back to the apparatus</h3><p>Open a check to highlight the relevant component. Inspect its requirement, documented capability, source and model assumptions.</p></li></ol><button className="primary-button" onClick={() => {setDialog(null);setMode('recorded');}}>Explore a guided example <ArrowRight size={16} /></button></>}
      {dialog === 'research' && <><p className="dialog-intro">An answer with an inspectable boundary.</p><p>CryoLean checks whether the encoded experiment requirements follow from the documented equipment capabilities and applicable models. The backend provides the result; the 3D scene explains the physical components.</p>
        <div className="trust-flow"><span>Documented inputs</span><ArrowRight size={18} /><span>Lean 4 evaluation</span><ArrowRight size={18} /><span>Verdict & evidence</span></div>
        <h3>What the mathematical check establishes</h3><p>A positive verdict means the checker accepted the exact encoded inputs. Missing mandatory facts stay unknown. A documented violation produces a rejection. Z3 and AI suggestions cannot override the acceptance checker.</p>
        <h3>What it does not establish</h3><p>Formal proofs do not prove manufacturer data true, validate an unmodeled physical effect, or certify all real-world laboratory safety. The apparatus models are representative procedural geometry, with exaggerated details for visibility.</p>
        <p>Confirm actual hardware details and safety procedures with the manufacturer and your lab personnel.</p><h3>Research materials</h3><p>Source documents, model assumptions and theorem metadata are available with each real result. Paper and benchmark content can be linked here when independently prepared and reviewed.</p>
        <div className="inline-actions"><a href="https://github.com/hrahman12/CryoLean/blob/main/VERIFICATION_SCOPE.md" target="_blank" rel="noreferrer">Verification scope ↗</a><a href="https://github.com/hrahman12/CryoLean/blob/main/RESEARCH_SOURCES.md" target="_blank" rel="noreferrer">Research sources ↗</a></div></>}
    </Dialog>
  </div>;
}
