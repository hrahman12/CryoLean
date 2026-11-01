import { paramLabel, shortModel } from "../lib/format.js";

/** The user reviews a suggested change before anything is applied. */
export default function FixReview({ fix, result, configIndex, machineName, onAccept, onCancel }) {
  const alt = fix.kind === "alternative_configuration";
  const target = configIndex[fix.configuration_id];
  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onCancel()}>
      <div className="modal fix" role="dialog" aria-modal="true" aria-label="Review suggested change" data-testid="fix-review">
        <div className="modal-head">
          <h2>Review the suggested change</h2>
          <button className="icon-btn" onClick={onCancel} aria-label="Close">✕</button>
        </div>
        <table className="diff">
          <thead><tr><th /><th>Now</th><th>Suggested</th></tr></thead>
          <tbody>
            {alt ? (
              <tr>
                <td>Cryostat</td>
                <td>{machineName}<div className="muted small">{result?.equipment?.configuration_name}</div></td>
                <td className="new">{target ? `${target.equipment.manufacturer} ${shortModel(target.equipment.model)}` : fix.name}<div className="muted small">{target?.configuration.name || fix.name}</div></td>
              </tr>
            ) : (
              (fix.changes || []).map((c) => (
                <tr key={c.parameter}>
                  <td>{paramLabel(c.parameter)}</td>
                  <td>{c.from}</td>
                  <td className="new">{c.to}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <ul className="plain-list fix-facts">
          <li>{alt ? "Your experiment and its requirements stay exactly the same." : "This changes a value in your plan. Your requirements stay the same."}</li>
          <li>Suggested by {fix.proposed_by === "lanyon" ? "Lanyon AI" : "the Z3 solver"}; the Lean checker already confirmed this exact setup meets the requirements.</li>
          <li>Accepting it runs a fresh Lean check on the new setup.</li>
        </ul>
        <div className="row end">
          <button className="btn secondary" onClick={onCancel}>Keep current setup</button>
          <button className="btn primary" onClick={onAccept} data-testid="accept-fix">Accept and check</button>
        </div>
      </div>
    </div>
  );
}
