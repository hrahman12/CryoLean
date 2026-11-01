import { useMemo, useState } from "react";
import {
  compatibleUnits, conditionText, constraintText, editableFields, fmtQuantity, isExactDecimal, keysLabel, paramLabel, unitSymbol, unitsForDim,
} from "../lib/format.js";
import QuantityInput from "./QuantityInput.jsx";

const ORIGIN = {
  experimental_observation: "From a published procedure",
  manufacturer_specification: "From a manufacturer specification",
  reference_data: "Reference data",
  user_entered: "Entered by you",
};

/** Parameter dimension, from the coupled models of the profile. */
export function paramDims(profile) {
  const m = {};
  for (const cm of profile?.coupled_models || []) for (const [k, v] of Object.entries(cm.parameters || {})) m[k] = v.unit_dim;
  return m;
}

export function effectiveParams(profile, appliedParams) {
  return (profile?.params || []).map((p) => (p.name in appliedParams ? { ...p, value: appliedParams[p.name], origin: "user_entered" } : p));
}

export default function ProfileReview({ experiment, profile, session, appliedParams, appliedEdits, error, busy, open, onToggle, onBack, onSetParameter, onEditRequirement, onConfirm }) {
  const confirmed = !!session?.confirmed;
  const dims = useMemo(() => paramDims(profile), [profile]);
  const requirements = useMemo(() => {
    const edits = Object.fromEntries((appliedEdits || []).map((e) => [e.key, e.constraint]));
    return (profile?.requirements || []).map((r) => {
      const id = (r.keys || [r.key]).join("|");
      const c = edits[id] ?? edits[r.key];
      return c ? { ...r, constraint: c, origin: "user_entered", edited: true } : r;
    });
  }, [profile, appliedEdits]);
  const params = useMemo(() => effectiveParams(profile, appliedParams || {}), [profile, appliedParams]);
  const missingParams = params.filter((p) => p.value == null);
  const required = requirements.filter((r) => r.mandatory);
  const optional = requirements.filter((r) => !r.mandatory);
  const modelName = (id) => profile?.coupled_models?.find((m) => m.id === id)?.name || id.replace(/_/g, " ");

  return (
    <div className="profile" data-testid="profile">
      <button className="link back" onClick={onBack} data-testid="back-to-experiments">‹ All experiments</button>
      <h1 className="profile-title">{experiment.plain_name || experiment.name}</h1>
      <p className="profile-tech">{experiment.name}</p>

      <div className={`confirm-state ${confirmed ? "ok" : "todo"}`} data-testid="confirm-state">
        {confirmed ? "✓ Requirements confirmed" : "Review the requirements below, then confirm them."}
        {confirmed && <button className="link" onClick={onToggle}>{open ? "Hide" : "Review"}</button>}
      </div>

      {error && <div className="inline-error" role="alert" data-testid="profile-error">{error}</div>}
      {!profile && !error && <p className="muted">Loading the prepared profile…</p>}

      {profile && (open || !confirmed) && (
        <div className="profile-body">
          {profile.description && <p className="profile-desc">{profile.description}</p>}

          {missingParams.length > 0 && (
            <section className="block questions">
              <h3>A few questions first</h3>
              {missingParams.map((p) => (
                <div className="question" key={p.name} data-testid={`param-question-${p.name}`}>
                  <p>{p.description ? cleanDesc(p.description) : paramLabel(p.name)}</p>
                  <p className="hint">Needed for the check. The app won’t guess it.</p>
                  <QuantityInput
                    units={unitsForDim(dims[p.name])}
                    integer={dims[p.name] === "1"}
                    busy={busy}
                    submitLabel="Save"
                    testId={`param-${p.name}`}
                    onSubmit={(v) => onSetParameter(p.name, typeof v === "number" ? { value: String(v), unit: "count" } : v)}
                  />
                </div>
              ))}
            </section>
          )}

          <section className="block">
            <h3>What this experiment needs</h3>
            <ul className="req-list">
              {required.map((r, i) => <Requirement key={`m${i}`} r={r} busy={busy} onEdit={onEditRequirement} />)}
              {(profile.coupled || []).filter((c) => c.mandatory).map((c) => (
                <li className="req" key={c.model}>
                  <div className="req-main">
                    <span className="req-label">{modelName(c.model)}</span>
                    <span className="req-value">must stay within budget</span>
                  </div>
                  {c.rationale && <p className="req-why">{c.rationale}</p>}
                </li>
              ))}
            </ul>
            {optional.length > 0 && (
              <>
                <h4 className="sub">Nice to have (does not block the result)</h4>
                <ul className="req-list optional">
                  {optional.map((r, i) => <Requirement key={`o${i}`} r={r} busy={busy} onEdit={onEditRequirement} />)}
                </ul>
              </>
            )}
          </section>

          {params.some((p) => p.value != null) && (
            <section className="block">
              <h3>Values used in the check</h3>
              <ul className="req-list">
                {params.filter((p) => p.value != null).map((p) => <Param key={p.name} p={p} dim={dims[p.name]} busy={busy} onSet={onSetParameter} />)}
              </ul>
            </section>
          )}

          {(profile.missing_information || []).length > 0 && (
            <section className="block">
              <h3>Not covered by this profile</h3>
              <ul className="plain-list">{profile.missing_information.map((m) => <li key={m}>{m}</li>)}</ul>
            </section>
          )}

          {(profile.sources || []).length > 0 && (
            <section className="block sources">
              <h3>Based on</h3>
              <ul className="plain-list">
                {profile.sources.map((s) => (
                  <li key={s.id}>
                    {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.citation}</a> : s.citation}
                    {s.doi && <span className="muted"> · doi:{s.doi}</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {!confirmed && (
            <div className="confirm-bar">
              <p className="hint">Nothing is checked as “met” until you confirm. Missing details stay open; the app won’t guess them.</p>
              <button className="btn primary" disabled={busy || !session} onClick={onConfirm} data-testid="confirm-requirements">
                These requirements are right
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function cleanDesc(s) {
  const t = s.replace(/\s*\((?:not stated|not given)[^)]*\)\s*/gi, " ").trim();
  return t.charAt(0).toUpperCase() + t.slice(1);
}

function Requirement({ r, busy, onEdit }) {
  const [editing, setEditing] = useState(false);
  // any-of requirements (several keys) are not editable through the bridge: the edit rules need one vocabulary key
  const fields = (r.keys?.length || 1) > 1 ? [] : editableFields(r.constraint);
  const key = (r.keys || [r.key]).join("|");
  return (
    <li className={`req ${r.edited ? "edited" : ""}`} data-testid={`req-${key}`}>
      <div className="req-main">
        <span className="req-label">{keysLabel(r.keys || [r.key])}</span>
        <span className="req-value">{constraintText(r.constraint)}</span>
        {fields.length > 0 && !editing && <button className="link small" onClick={() => setEditing(true)} disabled={busy} data-testid={`edit-${key}`}>Edit</button>}
      </div>
      {(r.conditions || []).length > 0 && <p className="req-cond">Only {r.conditions.map(conditionText).join(" and ")}</p>}
      <p className="req-why">
        <span className="origin">{ORIGIN[r.origin] || r.origin}</span>
        {r.rationale && <> · {r.rationale}</>}
      </p>
      {editing && (
        <ConstraintEditor
          constraint={r.constraint}
          fields={fields}
          busy={busy}
          testId={`edit-form-${key}`}
          onCancel={() => setEditing(false)}
          onSave={async (c) => { if (await onEdit(r.key || r.keys[0], c)) setEditing(false); }}
        />
      )}
    </li>
  );
}

function ConstraintEditor({ constraint, fields, busy, onSave, onCancel, testId }) {
  const [vals, setVals] = useState(() => Object.fromEntries(fields.map(([f]) => [f, f === "n" ? String(constraint.n ?? "") : String(constraint[f]?.value ?? "")])));
  const [units, setUnits] = useState(() => Object.fromEntries(fields.map(([f]) => [f, constraint[f]?.unit])));
  const valid = fields.every(([f]) => (f === "n" ? /^\d+$/.test(vals[f].trim()) : isExactDecimal(vals[f])));
  const submit = (e) => {
    e.preventDefault();
    if (!valid) return;
    const c = { ...constraint };
    for (const [f] of fields) c[f] = f === "n" ? Number(vals[f].trim()) : { value: vals[f].trim(), unit: units[f] };
    onSave(c);
  };
  return (
    <form className="constraint-editor" onSubmit={submit} data-testid={testId}>
      {fields.map(([f, label]) => (
        <label key={f} className="ce-field">
          <span>{label}</span>
          <input value={vals[f]} onChange={(e) => setVals((v) => ({ ...v, [f]: e.target.value }))} inputMode="decimal" data-testid={`${testId}-${f}`} />
          {f !== "n" && (
            <select value={units[f]} onChange={(e) => setUnits((u) => ({ ...u, [f]: e.target.value }))}>
              {compatibleUnits(constraint[f]?.unit).map((u) => <option key={u} value={u}>{unitSymbol(u) || u}</option>)}
            </select>
          )}
        </label>
      ))}
      <p className="hint">Changing a requirement marks it “entered by you” and asks you to confirm again. Required items can’t be removed.</p>
      <div className="row">
        <button className="btn primary small" type="submit" disabled={!valid || busy} data-testid={`${testId}-save`}>Save change</button>
        <button className="btn secondary small" type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}

function Param({ p, dim, busy, onSet }) {
  const [editing, setEditing] = useState(false);
  const isQty = p.value && typeof p.value === "object";
  const integer = dim === "1" || p.value?.unit === "count";
  return (
    <li className="req" data-testid={`param-${p.name}`}>
      <div className="req-main">
        <span className="req-label">{p.description || paramLabel(p.name)}</span>
        <span className="req-value">{isQty ? fmtQuantity(p.value) : String(p.value).replace(/^material:/, "material: ")}</span>
        {isQty && !editing && <button className="link small" disabled={busy} onClick={() => setEditing(true)} data-testid={`edit-param-${p.name}`}>Edit</button>}
      </div>
      <p className="req-why"><span className="origin">{ORIGIN[p.origin] || p.origin}</span></p>
      {editing && (
        <div className="row">
          <QuantityInput
            initialValue={p.value.value}
            initialUnit={p.value.unit}
            units={integer ? ["count"] : compatibleUnits(p.value.unit)}
            integer={integer}
            busy={busy}
            testId={`edit-param-${p.name}-form`}
            onSubmit={async (v) => { if (await onSet(p.name, typeof v === "number" ? { value: String(v), unit: "count" } : v)) setEditing(false); }}
          />
          <button className="btn secondary small" onClick={() => setEditing(false)}>Cancel</button>
        </div>
      )}
    </li>
  );
}
