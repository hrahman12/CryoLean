import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as cryo from "./services/cryolean-client-raw.js";
import { artType, ART_LABEL } from "./lib/art.js";
import CryostatArt from "./components/CryostatArt.jsx";
import ExperimentPicker from "./components/ExperimentPicker.jsx";
import ProfileReview from "./components/ProfileReview.jsx";
import CatalogModal from "./components/CatalogModal.jsx";
import ResultCard from "./components/ResultCard.jsx";
import ChecksDrawer from "./components/ChecksDrawer.jsx";
import FixReview from "./components/FixReview.jsx";
import { saveJson, savePdf } from "./lib/report.js";
import { shortModel } from "./lib/format.js";

const errorText = (e) => (e?.code === "lean_unavailable" ? "Verification is unavailable" : e?.message || String(e));

export default function App() {
  // ---------------------------------------------------------------- catalog (loaded once)
  const [boot, setBoot] = useState({ loading: true, error: null, lean: null, industries: [], equipment: [] });
  const [experimentsByIndustry, setExperimentsByIndustry] = useState({});
  const [industryId, setIndustryId] = useState(null);

  // ---------------------------------------------------------------- the current setup
  const [experiment, setExperiment] = useState(null); // list entry {id, plain_name, name, industry}
  const [profile, setProfile] = useState(null); // get_experiment_requirements
  const [session, setSession] = useState(null); // backend session (experiment kept across machines)
  const [appliedParams, setAppliedParams] = useState({}); // what the user changed, mirrored for display
  const [appliedEdits, setAppliedEdits] = useState([]);
  const [configId, setConfigId] = useState(null);

  // ---------------------------------------------------------------- the check
  const [result, setResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState(null);
  const [appliedFix, setAppliedFix] = useState(null);

  // ---------------------------------------------------------------- overlays & messages
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [checksOpen, setChecksOpen] = useState(false);
  const [fixToReview, setFixToReview] = useState(null);
  const [profileError, setProfileError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);
  const [profileOpen, setProfileOpen] = useState(true);

  const generation = useRef(0); // any change of setup bumps this; late answers for an old setup are dropped
  const experimentToken = useRef(0); // the latest experiment choice wins
  const sessionRef = useRef(null);
  const resultRef = useRef(null);
  sessionRef.current = session;

  // ---------------------------------------------------------------- boot
  useEffect(() => {
    (async () => {
      try {
        const connected = await Promise.race([cryo.ready().then(() => true), new Promise((r) => setTimeout(() => r(false), 15000))]);
        if (!connected) throw new Error("The CryoLean backend is not connected.");
        const [lean, ind, eq] = await Promise.all([
          cryo.getLeanStatus().catch((e) => ({ lean_available: false, error: e.message })),
          cryo.listIndustries(),
          cryo.listEquipment(),
        ]);
        const industries = (ind.industries || []).filter((i) => (i.experiment_ids || []).length > 0);
        setBoot({ loading: false, error: null, lean, industries, equipment: eq.equipment || [] });
        if (industries.length) setIndustryId(industries[0].id);
      } catch (e) {
        setBoot((b) => ({ ...b, loading: false, error: errorText(e) }));
      }
    })();
  }, []);

  useEffect(() => {
    if (!industryId || experimentsByIndustry[industryId]) return;
    cryo.listExperiments(industryId)
      .then((d) => setExperimentsByIndustry((m) => ({ ...m, [industryId]: d.experiments || [] })))
      .catch((e) => setNotice({ tone: "error", text: errorText(e) }));
  }, [industryId, experimentsByIndustry]);

  // configuration id -> {equipment, configuration}
  const configIndex = useMemo(() => {
    const m = {};
    for (const e of boot.equipment) for (const c of e.configurations || []) m[c.id] = { equipment: e, configuration: c };
    return m;
  }, [boot.equipment]);
  const selected = configId ? configIndex[configId] : null;
  const machineName = selected ? `${selected.equipment.manufacturer} ${shortModel(selected.equipment.model)}` : "";

  const clearResult = useCallback(() => {
    generation.current += 1;
    setResult(null);
    setCheckError(null);
    setChecking(false);
    setAppliedFix(null);
    setChecksOpen(false);
  }, []);

  // ---------------------------------------------------------------- the check itself (Lean decides; we display)
  const runCheck = useCallback(async (opts = {}) => {
    const s = opts.session || sessionRef.current;
    const cid = opts.configId;
    if (!s || !(cid || s.configuration_id)) return;
    const gen = ++generation.current;
    setResult(null);
    setCheckError(null);
    setChecksOpen(false);
    setChecking(true);
    try {
      let r;
      try {
        r = await cryo.checkSession(s.id);
      } catch (e) {
        if (e.code !== "stale_result") throw e;
        r = await cryo.checkSession(s.id); // stale: re-check once on the current setup
      }
      if (gen !== generation.current) return; // the setup changed while Lean was working
      setResult(r);
      if (opts.fix) {
        const expected = opts.fix.lean?.lean_input_hash;
        const got = r.verification?.concrete_evaluation?.lean_input_hash;
        setAppliedFix({ fix: opts.fix, sameAsVerified: !!expected && expected === got });
      }
    } catch (e) {
      if (gen !== generation.current) return;
      setCheckError(e);
    } finally {
      if (gen === generation.current) setChecking(false);
    }
  }, []);

  // ---------------------------------------------------------------- choose an experiment
  const chooseExperiment = useCallback(async (exp) => {
    clearResult();
    setProfileError(null);
    setExperiment(exp);
    setProfile(null);
    setSession(null);
    setAppliedParams({});
    setAppliedEdits([]);
    setProfileOpen(true);
    const token = ++experimentToken.current;
    try {
      const [p, s0] = await Promise.all([cryo.getExperimentRequirements(exp.id), cryo.startSession(exp.id)]);
      let s = s0;
      if (configId) s = await cryo.selectEquipment(s.id, configId);
      if (token !== experimentToken.current) return;
      setProfile(p);
      setSession(s);
    } catch (e) {
      if (token === experimentToken.current) setProfileError(errorText(e));
    }
  }, [clearResult, configId]);

  // ---------------------------------------------------------------- switch cryostat (experiment is kept)
  const chooseConfig = useCallback(async (cid, opts = {}) => {
    setCatalogOpen(false);
    clearResult(); // never leave the previous machine's result attached to the new one
    setConfigId(cid);
    const s = sessionRef.current;
    if (!s) return;
    try {
      const s2 = await cryo.selectEquipment(s.id, cid);
      setSession(s2);
      if (s2.confirmed) await runCheck({ session: s2, configId: cid, fix: opts.fix });
    } catch (e) {
      setCheckError(e);
    }
  }, [clearResult, runCheck]);

  // ---------------------------------------------------------------- edits to the profile (reset confirmation)
  const updateSession = useCallback(async (patch) => {
    const s = sessionRef.current;
    if (!s) return null;
    setProfileError(null);
    setBusy(true);
    try {
      const s2 = await cryo.updateSession(s.id, patch);
      clearResult();
      setSession(s2);
      return s2;
    } catch (e) {
      setProfileError(errorText(e));
      return null;
    } finally {
      setBusy(false);
    }
  }, [clearResult]);

  const setParameter = useCallback(async (name, q, { confirmAndCheck = false } = {}) => {
    const s2 = await updateSession({ parameters: { [name]: q }, ...(confirmAndCheck ? { confirmed: true } : {}) });
    if (!s2) return false;
    setAppliedParams((m) => ({ ...m, [name]: q }));
    if (confirmAndCheck && configId) await runCheck({ session: s2 });
    return true;
  }, [updateSession, runCheck, configId]);

  const editRequirement = useCallback(async (key, constraint) => {
    const s2 = await updateSession({ requirementEdits: [{ key, constraint }] });
    if (!s2) return false;
    setAppliedEdits((l) => [...l.filter((e) => e.key !== key), { key, constraint }]);
    return true;
  }, [updateSession]);

  const confirmRequirements = useCallback(async ({ andCheck = false } = {}) => {
    const s2 = await updateSession({ confirmed: true });
    if (s2) setProfileOpen(false);
    if (s2 && andCheck && configId) await runCheck({ session: s2 });
  }, [updateSession, runCheck, configId]);

  // ---------------------------------------------------------------- suggested changes (reviewed first)
  const acceptFix = useCallback(async (fix) => {
    setFixToReview(null);
    if (fix.kind === "alternative_configuration") {
      await chooseConfig(fix.configuration_id, { fix });
      return;
    }
    // parameter change: the user reviewed the exact new value(s) and accepted them as part of the plan
    const s2 = await updateSession({ parameters: fix.parameters, confirmed: true });
    if (!s2) return;
    setAppliedParams((m) => ({ ...m, ...fix.parameters }));
    await runCheck({ session: s2, fix });
  }, [chooseConfig, updateSession, runCheck]);

  // ---------------------------------------------------------------- save report (only a current result)
  const saveReport = useCallback(async (format) => {
    const s = sessionRef.current;
    if (!result || !s) return;
    try {
      await cryo.getSessionResult(s.id); // throws stale_result if anything changed since the check
    } catch (e) {
      if (e.code === "stale_result") {
        clearResult();
        setNotice({ tone: "error", text: "The setup changed since this check, so the result was cleared. Check again before saving." });
        return;
      }
      setNotice({ tone: "error", text: errorText(e) });
      return;
    }
    const ctx = { machineName, parameters: appliedParams, requirementEdits: appliedEdits, verified: cryo.isVerified(result) };
    if (format === "pdf") savePdf(result, ctx);
    else saveJson(result, ctx);
    setNotice({ tone: "ok", text: `Report saved (${format.toUpperCase()}).` });
  }, [result, machineName, appliedParams, appliedEdits, clearResult]);

  // bring a new answer (or error) into view under the button
  useEffect(() => {
    if ((result || checkError) && resultRef.current) resultRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [result, checkError]);

  useEffect(() => {
    if (!notice) return undefined;
    const t = setTimeout(() => setNotice(null), 5000);
    return () => clearTimeout(t);
  }, [notice]);

  // ---------------------------------------------------------------- render
  if (boot.loading) return <Splash text="Opening CryoLean…" />;
  if (boot.error) return <Splash text={boot.error} error />;

  const type = selected ? artType(selected.equipment) : "none";
  const canCheck = !!(session && configId) && !checking && !busy;
  const leanOk = boot.lean?.lean_available;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden>❄</span>
          <span className="wordmark">CryoLean</span>
          <span className="tagline">Cryo, made simple.</span>
        </div>
        <div className={`lean-pill ${leanOk ? "ok" : "bad"}`} title={boot.lean?.version || boot.lean?.error || ""} data-testid="lean-status">
          <span className="dot" /> {leanOk ? "Lean checker ready" : "Verification is unavailable"}
        </div>
      </header>

      <main className="layout">
        <section className="stage-col">
          <div className="stage" data-testid="stage">
            {selected ? (
              <>
                <div className="stage-art" key={configId}>
                  <CryostatArt type={type} size={270} title={ART_LABEL[type]} />
                </div>
                <div className="stage-caption">
                  <div className="kind">{ART_LABEL[type]}</div>
                  <h2 className="machine-name" data-testid="machine-name">{machineName}</h2>
                  <div className="config-name" data-testid="config-name">{selected.configuration.name}</div>
                </div>
              </>
            ) : (
              <div className="stage-empty">
                <CryostatArt type="cryostat" size={220} title="No cryostat selected" />
                <p>Choose a cryostat to see it here.</p>
              </div>
            )}
            <button className="btn secondary change-btn" onClick={() => setCatalogOpen(true)} data-testid="change-cryostat">
              {selected ? "Change cryostat" : "Choose cryostat"}
            </button>
          </div>

          <div className="check-area" ref={resultRef}>
            <button className="btn primary big" disabled={!canCheck} onClick={() => runCheck()} data-testid="check-setup">
              {checking ? "Checking your setup…" : "Check setup"}
            </button>
            {!experiment && <p className="hint">Pick what you would like to do on the right.</p>}
            {experiment && !configId && <p className="hint">Now choose a cryostat.</p>}
            {checking && <div className="checking" data-testid="checking"><span className="spinner" /> Checking your setup…</div>}
            {checkError && (
              <div className={`result-card ${checkError.code === "lean_unavailable" ? "unavailable" : "error"}`} data-testid="check-error">
                <h3>{checkError.code === "lean_unavailable" ? "Verification is unavailable" : "Something went wrong"}</h3>
                <p>{checkError.code === "lean_unavailable" ? "The Lean checker could not run, so there is no result. Nothing has been marked as passing or failing." : checkError.message}</p>
              </div>
            )}
            {result && !checking && (
              <ResultCard
                result={result}
                profile={profile}
                appliedParams={appliedParams}
                appliedFix={appliedFix}
                configIndex={configIndex}
                busy={busy}
                onSeeChecks={() => setChecksOpen(true)}
                onChangeCryostat={() => setCatalogOpen(true)}
                onReviewProfile={() => setProfileOpen(true)}
                onConfirmAndCheck={() => confirmRequirements({ andCheck: true })}
                onAnswerParam={(name, q) => setParameter(name, q, { confirmAndCheck: true })}
                onReviewFix={setFixToReview}
                onSave={saveReport}
              />
            )}
          </div>
        </section>

        <section className="side-col">
          {experiment ? (
            <ProfileReview
              experiment={experiment}
              profile={profile}
              session={session}
              appliedParams={appliedParams}
              appliedEdits={appliedEdits}
              error={profileError}
              busy={busy}
              open={profileOpen}
              onToggle={() => setProfileOpen((o) => !o)}
              onBack={() => { experimentToken.current += 1; clearResult(); setExperiment(null); setProfile(null); setSession(null); setProfileError(null); }}
              onSetParameter={setParameter}
              onEditRequirement={editRequirement}
              onConfirm={() => confirmRequirements()}
            />
          ) : (
            <ExperimentPicker
              industries={boot.industries}
              industryId={industryId}
              onIndustry={setIndustryId}
              experiments={experimentsByIndustry[industryId]}
              onChoose={chooseExperiment}
            />
          )}
        </section>
      </main>

      {catalogOpen && (
        <CatalogModal equipment={boot.equipment} currentId={configId} onChoose={(cid) => chooseConfig(cid)} onClose={() => setCatalogOpen(false)} />
      )}
      {checksOpen && result && (
        <ChecksDrawer result={result} machineName={machineName} onClose={() => setChecksOpen(false)} />
      )}
      {fixToReview && (
        <FixReview fix={fixToReview} result={result} configIndex={configIndex} machineName={machineName} onAccept={() => acceptFix(fixToReview)} onCancel={() => setFixToReview(null)} />
      )}
      {notice && <div className={`toast ${notice.tone}`} role="status" data-testid="toast">{notice.text}</div>}
    </div>
  );
}

function Splash({ text, error }) {
  return (
    <div className="splash">
      <div className="brand big"><span className="logo">❄</span> CryoLean</div>
      <p className={error ? "error-text" : ""}>{text}</p>
      {error && <p className="hint">Start the app with <code>make run</code> so the CryoLean backend is connected.</p>}
    </div>
  );
}
