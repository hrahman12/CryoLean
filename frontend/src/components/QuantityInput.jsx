import { useState } from "react";
import { isExactDecimal, unitSymbol } from "../lib/format.js";

/** Value + unit entry. Sends {value: "<exact decimal>", unit} exactly as typed; the backend converts and checks. */
export default function QuantityInput({ initialValue = "", initialUnit, units, onSubmit, submitLabel = "Save", busy, integer = false, testId }) {
  const [value, setValue] = useState(initialValue == null ? "" : String(initialValue));
  const [unit, setUnit] = useState(initialUnit || units[0]);
  const trimmed = value.trim();
  const valid = integer ? /^\d+$/.test(trimmed) : isExactDecimal(trimmed);
  return (
    <form
      className="qty"
      onSubmit={(e) => {
        e.preventDefault();
        if (valid && !busy) onSubmit(integer ? Number(trimmed) : { value: trimmed, unit });
      }}
    >
      <input
        className={`qty-value ${trimmed && !valid ? "invalid" : ""}`}
        inputMode="decimal"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        aria-label="Value"
        placeholder="Value"
        data-testid={testId ? `${testId}-value` : undefined}
      />
      {!integer && units.length > 1 && (
        <select className="qty-unit" value={unit} onChange={(e) => setUnit(e.target.value)} aria-label="Unit">
          {units.map((u) => <option key={u} value={u}>{unitSymbol(u) || u}</option>)}
        </select>
      )}
      {!integer && units.length === 1 && unitSymbol(units[0]) && <span className="qty-fixed-unit">{unitSymbol(units[0])}</span>}
      <button className="btn primary small" type="submit" disabled={!valid || busy} data-testid={testId ? `${testId}-submit` : undefined}>
        {submitLabel}
      </button>
      {trimmed && !valid && <span className="qty-hint">Use a plain number{integer ? "" : " like 12 or 0.5"}.</span>}
    </form>
  );
}
