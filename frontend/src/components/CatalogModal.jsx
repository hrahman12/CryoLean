import { useEffect, useMemo, useRef, useState } from "react";
import CryostatArt from "./CryostatArt.jsx";
import { artType, ART_LABEL } from "../lib/art.js";
import { shortModel } from "../lib/format.js";

export default function CatalogModal({ equipment, currentId, onChoose, onClose }) {
  const [q, setQ] = useState("");
  const input = useRef(null);
  useEffect(() => {
    input.current?.focus();
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const list = useMemo(() => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    return [...equipment]
      .sort((a, b) => `${a.manufacturer} ${a.model}`.localeCompare(`${b.manufacturer} ${b.model}`))
      .map((e) => ({ e, type: artType(e) }))
      .filter(({ e, type }) => {
        if (!words.length) return true;
        const hay = `${e.manufacturer} ${e.model} ${e.family} ${ART_LABEL[type]} ${(e.configurations || []).map((c) => c.name).join(" ")}`.toLowerCase();
        return words.every((w) => hay.includes(w));
      });
  }, [equipment, q]);

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal catalog" role="dialog" aria-modal="true" aria-label="Change cryostat" data-testid="catalog">
        <div className="modal-head">
          <h2>Change cryostat</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <input
          ref={input}
          className="search"
          placeholder="Search by name, maker or type (e.g. Bluefors, freezer, 9 T)"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          data-testid="catalog-search"
        />
        <p className="muted small">{list.length} machines · each configuration is checked separately</p>
        <ul className="catalog-list">
          {list.map(({ e, type }) => (
            <li key={e.id} className="cat-item">
              <div className="cat-thumb"><CryostatArt type={type} size={84} title={ART_LABEL[type]} /></div>
              <div className="cat-body">
                <div className="cat-maker">{e.manufacturer}</div>
                <div className="cat-model">{shortModel(e.model)}</div>
                <div className="cat-kind">{ART_LABEL[type]}</div>
                <div className="cat-configs">
                  {(e.configurations || []).map((c) => (
                    <button
                      key={c.id}
                      className={`config-btn ${c.id === currentId ? "current" : ""}`}
                      onClick={() => onChoose(c.id)}
                      data-testid={`config-${c.id}`}
                    >
                      <span>{c.name}</span>
                      {c.id === currentId ? <span className="tag">Selected</span> : <span className="chev">›</span>}
                    </button>
                  ))}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
