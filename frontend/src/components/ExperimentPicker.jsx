import { industryShortName } from "../lib/format.js";

export default function ExperimentPicker({ industries, industryId, onIndustry, experiments, onChoose }) {
  return (
    <div className="picker" data-testid="picker">
      <h1 className="picker-title">What would you like to do?</h1>
      <div className="tabs" role="tablist" aria-label="Field">
        {industries.map((i) => (
          <button
            key={i.id}
            role="tab"
            aria-selected={i.id === industryId}
            className={`tab ${i.id === industryId ? "active" : ""}`}
            onClick={() => onIndustry(i.id)}
            data-testid={`tab-${i.id}`}
          >
            {industryShortName(i.name)}
          </button>
        ))}
      </div>
      <ul className="experiment-list" role="tabpanel">
        {!experiments && <li className="muted">Loading…</li>}
        {experiments?.length === 0 && <li className="muted">No prepared experiments yet.</li>}
        {experiments?.map((e) => (
          <li key={e.id}>
            <button className="experiment" onClick={() => onChoose(e)} data-testid={`exp-${e.id}`}>
              <span className="exp-plain">{e.plain_name || e.name}</span>
              {e.plain_name && e.plain_name !== e.name && <span className="exp-tech">{e.name}</span>}
              <span className="chev" aria-hidden>›</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
