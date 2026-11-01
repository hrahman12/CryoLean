// Generated vector illustrations, one per kind of machine. Purely decorative: they show what sort of
// instrument is selected, never a capability. Each drawing uses the same light, soft "product shot" style.
import { useId } from "react";

function Defs({ id }) {
  return (
    <defs>
      <linearGradient id={`${id}-metal`} x1="0" x2="1" y1="0" y2="0">
        <stop offset="0" stopColor="#c9ced6" />
        <stop offset="0.35" stopColor="#f4f6f9" />
        <stop offset="0.7" stopColor="#dde1e7" />
        <stop offset="1" stopColor="#aab1bb" />
      </linearGradient>
      <linearGradient id={`${id}-panel`} x1="0" x2="0" y1="0" y2="1">
        <stop offset="0" stopColor="#fbfcfd" />
        <stop offset="1" stopColor="#e3e7ed" />
      </linearGradient>
      <linearGradient id={`${id}-gold`} x1="0" x2="1">
        <stop offset="0" stopColor="#b8862f" />
        <stop offset="0.4" stopColor="#f3d27a" />
        <stop offset="0.75" stopColor="#d9a845" />
        <stop offset="1" stopColor="#9c6f22" />
      </linearGradient>
      <linearGradient id={`${id}-glass`} x1="0" x2="1" y1="0" y2="1">
        <stop offset="0" stopColor="#e8f1ff" />
        <stop offset="1" stopColor="#b9d3f7" />
      </linearGradient>
      <linearGradient id={`${id}-dark`} x1="0" x2="0" y1="0" y2="1">
        <stop offset="0" stopColor="#4a5260" />
        <stop offset="1" stopColor="#2a2f38" />
      </linearGradient>
      <radialGradient id={`${id}-cold`} cx="0.5" cy="0.5" r="0.5">
        <stop offset="0" stopColor="#5aa2ff" stopOpacity="0.9" />
        <stop offset="1" stopColor="#5aa2ff" stopOpacity="0" />
      </radialGradient>
    </defs>
  );
}

const stroke = { stroke: "#8a929e", strokeWidth: 1.5 };

function Shadow({ cx = 160, cy = 296, rx = 110 }) {
  return <ellipse cx={cx} cy={cy} rx={rx} ry={10} fill="#000" opacity="0.08" />;
}

const DRAW = {
  dilution: (id) => (
    <g>
      <Shadow rx={70} />
      <rect x="70" y="22" width="180" height="16" rx="3" fill={`url(#${id}-metal)`} {...stroke} />
      {[0, 1, 2, 3, 4].map((i) => {
        const w = 160 - i * 20;
        const y = 64 + i * 46;
        return (
          <g key={i}>
            {[-1, 1].map((s) => (
              <rect key={s} x={160 + s * (w / 2 - 14) - 3} y={y - 46 + 16 + (i === 0 ? 0 : 6)} width="6" height={i === 0 ? 26 : 40} fill={`url(#${id}-gold)`} />
            ))}
            <rect x={160 - w / 2} y={y} width={w} height="10" rx="2" fill={`url(#${id}-gold)`} stroke="#9c6f22" strokeWidth="1" />
          </g>
        );
      })}
      <path d="M150 38 C 140 120, 175 160, 150 250" stroke="#7d8794" strokeWidth="2" fill="none" />
      <path d="M170 38 C 185 110, 140 170, 172 250" stroke="#9aa3ae" strokeWidth="2" fill="none" />
      <rect x="140" y="258" width="40" height="26" rx="4" fill={`url(#${id}-gold)`} stroke="#9c6f22" />
      <circle cx="160" cy="271" r="22" fill={`url(#${id}-cold)`} />
    </g>
  ),
  magnet: (id) => (
    <g>
      <Shadow />
      <rect x="60" y="160" width="200" height="120" rx="12" fill={`url(#${id}-panel)`} {...stroke} />
      <rect x="80" y="182" width="70" height="40" rx="5" fill={`url(#${id}-dark)`} />
      <path d="M86 210 l12 -10 l12 6 l14 -14 l14 8" stroke="#6fb1ff" strokeWidth="2" fill="none" />
      {[0, 1, 2].map((i) => <circle key={i} cx={180 + i * 22} cy="200" r="6" fill="#c3c9d2" />)}
      <rect x="110" y="40" width="100" height="125" rx="10" fill={`url(#${id}-metal)`} {...stroke} />
      <ellipse cx="160" cy="40" rx="50" ry="10" fill="#eef1f5" {...stroke} />
      <rect x="150" y="12" width="20" height="30" rx="3" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="110" y="96" width="100" height="22" fill="#2f6fde" opacity="0.15" />
      <circle cx="160" cy="107" r="18" fill={`url(#${id}-cold)`} />
    </g>
  ),
  optical: (id) => (
    <g>
      <Shadow rx={95} />
      <rect x="60" y="250" width="200" height="34" rx="6" fill={`url(#${id}-panel)`} {...stroke} />
      <rect x="125" y="36" width="70" height="70" rx="8" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="140" y="20" width="40" height="20" rx="4" fill={`url(#${id}-dark)`} />
      <rect x="95" y="104" width="130" height="146" rx="18" fill={`url(#${id}-metal)`} {...stroke} />
      <circle cx="160" cy="176" r="32" fill={`url(#${id}-glass)`} stroke="#7d8794" strokeWidth="3" />
      <circle cx="160" cy="176" r="14" fill={`url(#${id}-cold)`} />
      <path d="M20 176 H 120" stroke="#ff5d5d" strokeWidth="3" strokeDasharray="6 5" opacity="0.8" />
      <path d="M148 166 l10 -8" stroke="#fff" strokeWidth="3" strokeLinecap="round" opacity="0.8" />
    </g>
  ),
  probe: (id) => (
    <g>
      <Shadow rx={125} />
      <rect x="40" y="200" width="240" height="84" rx="10" fill={`url(#${id}-panel)`} {...stroke} />
      <ellipse cx="160" cy="196" rx="95" ry="28" fill={`url(#${id}-metal)`} {...stroke} />
      <ellipse cx="160" cy="190" rx="60" ry="16" fill={`url(#${id}-glass)`} stroke="#7d8794" />
      <ellipse cx="160" cy="190" rx="22" ry="7" fill={`url(#${id}-cold)`} />
      {[[-1, 0], [1, 0], [-0.6, -1], [0.6, -1]].map(([sx, up], i) => (
        <g key={i}>
          <rect x={160 + sx * 100 - 14} y={170 + up * 20} width="28" height="20" rx="3" fill={`url(#${id}-dark)`} />
          <line x1={160 + sx * 100} y1={180 + up * 20} x2={160 + sx * 30} y2={190} stroke="#5b6472" strokeWidth="2" />
        </g>
      ))}
      <rect x="148" y="60" width="24" height="110" rx="4" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="128" y="40" width="64" height="30" rx="6" fill={`url(#${id}-dark)`} />
      <rect x="140" y="160" width="40" height="14" rx="3" fill="#7d8794" />
    </g>
  ),
  microtome: (id) => (
    <g>
      <Shadow rx={120} />
      <rect x="50" y="110" width="210" height="170" rx="12" fill={`url(#${id}-panel)`} {...stroke} />
      <path d="M60 112 L 90 52 H 240 L 250 112 Z" fill={`url(#${id}-glass)`} stroke="#8a929e" strokeWidth="1.5" opacity="0.9" />
      <rect x="110" y="130" width="90" height="70" rx="6" fill="#eef4ff" stroke="#9fb7d9" />
      <rect x="140" y="140" width="30" height="30" rx="3" fill="#cfd6df" />
      <circle cx="155" cy="185" r="12" fill={`url(#${id}-cold)`} />
      <circle cx="268" cy="170" r="30" fill="none" stroke="#7d8794" strokeWidth="6" />
      <line x1="268" y1="170" x2="290" y2="150" stroke="#7d8794" strokeWidth="6" strokeLinecap="round" />
      <rect x="70" y="220" width="60" height="14" rx="3" fill={`url(#${id}-dark)`} />
    </g>
  ),
  stage: (id) => (
    <g>
      <Shadow rx={100} />
      <rect x="80" y="252" width="160" height="32" rx="8" fill={`url(#${id}-panel)`} {...stroke} />
      <rect x="210" y="70" width="26" height="184" rx="6" fill={`url(#${id}-metal)`} {...stroke} />
      <path d="M236 80 H 150 V 120" stroke="#9aa3ae" strokeWidth="18" fill="none" strokeLinejoin="round" />
      <rect x="138" y="118" width="24" height="34" rx="4" fill={`url(#${id}-dark)`} />
      <ellipse cx="150" cy="190" rx="80" ry="22" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="70" y="190" width="160" height="16" fill="#cfd5dd" />
      <ellipse cx="150" cy="206" rx="80" ry="22" fill="none" {...stroke} />
      <ellipse cx="150" cy="188" rx="22" ry="7" fill={`url(#${id}-glass)`} stroke="#7d8794" />
      <ellipse cx="150" cy="188" rx="12" ry="4" fill={`url(#${id}-cold)`} />
      <path d="M72 200 C 40 210, 40 240, 70 250" stroke="#4f8fe8" strokeWidth="5" fill="none" />
    </g>
  ),
  freezer: (id) => (
    <g>
      <Shadow rx={90} />
      <rect x="85" y="20" width="150" height="266" rx="10" fill={`url(#${id}-panel)`} {...stroke} />
      <rect x="95" y="32" width="130" height="38" rx="4" fill={`url(#${id}-dark)`} />
      <text x="160" y="58" textAnchor="middle" fontSize="18" fontFamily="system-ui" fill="#8cc4ff">−80 °C</text>
      <line x1="95" y1="82" x2="225" y2="82" stroke="#c3c9d2" />
      <rect x="210" y="120" width="8" height="90" rx="4" fill="#9aa3ae" />
      <rect x="85" y="270" width="150" height="16" rx="4" fill="#cfd5dd" />
    </g>
  ),
  dewar: (id) => (
    <g>
      <Shadow rx={85} />
      <path d="M90 90 Q 90 70 110 66 H 210 Q 230 70 230 90 V 270 Q 230 286 210 286 H 110 Q 90 286 90 270 Z" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="135" y="40" width="50" height="30" rx="4" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="128" y="30" width="64" height="14" rx="5" fill={`url(#${id}-dark)`} />
      <path d="M90 110 C 60 110, 60 150, 90 150" stroke="#8a929e" strokeWidth="6" fill="none" />
      <path d="M230 110 C 260 110, 260 150, 230 150" stroke="#8a929e" strokeWidth="6" fill="none" />
      <path d="M150 20 q 8 -10 0 -18 M170 22 q 8 -10 0 -18" stroke="#b9d3f7" strokeWidth="3" fill="none" />
      <rect x="115" y="180" width="90" height="40" rx="6" fill="#ffffff" opacity="0.5" />
    </g>
  ),
  dryer: (id) => (
    <g>
      <Shadow rx={110} />
      <rect x="60" y="180" width="200" height="104" rx="10" fill={`url(#${id}-panel)`} {...stroke} />
      <rect x="80" y="200" width="60" height="26" rx="4" fill={`url(#${id}-dark)`} />
      <rect x="100" y="50" width="120" height="130" rx="14" fill={`url(#${id}-glass)`} stroke="#8a929e" strokeWidth="1.5" opacity="0.9" />
      {[0, 1, 2].map((i) => <rect key={i} x="112" y={80 + i * 32} width="96" height="6" rx="2" fill="#9aa3ae" />)}
      <rect x="96" y="40" width="128" height="14" rx="5" fill={`url(#${id}-metal)`} {...stroke} />
      <circle cx="160" cy="130" r="26" fill={`url(#${id}-cold)`} opacity="0.6" />
    </g>
  ),
  chamber: (id) => (
    <g>
      <Shadow rx={125} />
      <rect x="40" y="40" width="240" height="246" rx="12" fill={`url(#${id}-panel)`} {...stroke} />
      <rect x="58" y="62" width="160" height="200" rx="10" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="88" y="100" width="100" height="90" rx="8" fill={`url(#${id}-glass)`} stroke="#7d8794" />
      <circle cx="138" cy="145" r="22" fill={`url(#${id}-cold)`} />
      <rect x="200" y="140" width="10" height="50" rx="4" fill="#7d8794" />
      <rect x="232" y="70" width="36" height="50" rx="4" fill={`url(#${id}-dark)`} />
      {[0, 1, 2].map((i) => <circle key={i} cx="250" cy={140 + i * 22} r="6" fill="#c3c9d2" />)}
    </g>
  ),
  bath: (id) => (
    <g>
      <Shadow rx={115} />
      <rect x="55" y="120" width="210" height="164" rx="12" fill={`url(#${id}-panel)`} {...stroke} />
      <rect x="70" y="100" width="180" height="36" rx="6" fill={`url(#${id}-metal)`} {...stroke} />
      <path d="M85 118 q 20 -10 40 0 t 40 0 t 40 0 t 40 0" stroke="#4f8fe8" strokeWidth="4" fill="none" />
      <rect x="110" y="40" width="10" height="80" rx="3" fill="#9aa3ae" />
      <rect x="150" y="30" width="8" height="90" rx="3" fill="#c0392b" opacity="0.7" />
      <rect x="85" y="170" width="80" height="34" rx="4" fill={`url(#${id}-dark)`} />
      <text x="125" y="193" textAnchor="middle" fontSize="15" fontFamily="system-ui" fill="#8cc4ff">−40.00</text>
    </g>
  ),
  mill: (id) => (
    <g>
      <Shadow rx={105} />
      <rect x="60" y="90" width="200" height="194" rx="16" fill={`url(#${id}-panel)`} {...stroke} />
      <rect x="85" y="115" width="150" height="90" rx="10" fill={`url(#${id}-glass)`} stroke="#7d8794" />
      <rect x="110" y="140" width="40" height="40" rx="8" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="170" y="140" width="40" height="40" rx="8" fill={`url(#${id}-metal)`} {...stroke} />
      <circle cx="160" cy="160" r="30" fill={`url(#${id}-cold)`} opacity="0.5" />
      <rect x="95" y="225" width="70" height="24" rx="4" fill={`url(#${id}-dark)`} />
      <circle cx="210" cy="237" r="12" fill="#c3c9d2" />
    </g>
  ),
  cooler: (id) => (
    <g>
      <Shadow rx={125} />
      <rect x="180" y="190" width="100" height="94" rx="10" fill={`url(#${id}-panel)`} {...stroke} />
      {[0, 1, 2, 3].map((i) => <line key={i} x1="195" y1={210 + i * 14} x2="265" y2={210 + i * 14} stroke="#c3c9d2" strokeWidth="3" />)}
      <path d="M180 220 C 140 220, 150 120, 120 110" stroke="#5b6472" strokeWidth="6" fill="none" />
      <path d="M180 245 C 130 245, 160 130, 100 116" stroke="#7d8794" strokeWidth="6" fill="none" />
      <rect x="70" y="40" width="80" height="80" rx="10" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="90" y="118" width="40" height="70" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="80" y="186" width="60" height="12" rx="2" fill={`url(#${id}-gold)`} />
      <rect x="98" y="196" width="24" height="60" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="88" y="254" width="44" height="12" rx="2" fill={`url(#${id}-gold)`} />
      <circle cx="110" cy="260" r="20" fill={`url(#${id}-cold)`} />
    </g>
  ),
  plunge: (id) => (
    <g>
      <Shadow rx={90} />
      <rect x="80" y="240" width="160" height="44" rx="8" fill={`url(#${id}-panel)`} {...stroke} />
      <rect x="100" y="40" width="120" height="150" rx="12" fill={`url(#${id}-glass)`} stroke="#8a929e" strokeWidth="1.5" opacity="0.85" />
      <rect x="150" y="20" width="20" height="120" rx="3" fill={`url(#${id}-metal)`} {...stroke} />
      <path d="M156 140 L 160 168 L 164 140" stroke="#5b6472" strokeWidth="2" fill="none" />
      <rect x="120" y="196" width="80" height="44" rx="6" fill={`url(#${id}-metal)`} {...stroke} />
      <ellipse cx="160" cy="198" rx="30" ry="7" fill={`url(#${id}-cold)`} />
    </g>
  ),
  facility: (id) => (
    <g>
      <Shadow rx={140} />
      <rect x="30" y="110" width="230" height="130" rx="65" fill={`url(#${id}-metal)`} {...stroke} />
      <ellipse cx="260" cy="175" rx="30" ry="65" fill={`url(#${id}-panel)`} {...stroke} />
      <ellipse cx="260" cy="175" rx="16" ry="38" fill={`url(#${id}-glass)`} stroke="#7d8794" />
      {[80, 140, 200].map((x) => <rect key={x} x={x - 10} y="240" width="20" height="46" fill="#9aa3ae" />)}
      {[70, 120, 170, 220].map((x) => <line key={x} x1={x} y1="112" x2={x} y2="238" stroke="#b8bec7" strokeWidth="2" />)}
      <rect x="110" y="70" width="50" height="42" rx="4" fill={`url(#${id}-metal)`} {...stroke} />
      <circle cx="260" cy="175" r="22" fill={`url(#${id}-cold)`} />
    </g>
  ),
  cryostat: (id) => (
    <g>
      <Shadow rx={80} />
      <rect x="110" y="20" width="100" height="22" rx="4" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="120" y="40" width="80" height="150" rx="10" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="135" y="188" width="50" height="80" rx="8" fill={`url(#${id}-metal)`} {...stroke} />
      <rect x="140" y="268" width="40" height="18" rx="4" fill={`url(#${id}-dark)`} />
      <circle cx="160" cy="232" r="22" fill={`url(#${id}-cold)`} />
      <circle cx="175" cy="70" r="6" fill="#2f6fde" opacity="0.6" />
    </g>
  ),
};

export default function CryostatArt({ type = "cryostat", size = 320, title }) {
  const raw = useId();
  const id = `a${raw.replace(/[^a-zA-Z0-9]/g, "")}`;
  const draw = DRAW[type] || DRAW.cryostat;
  return (
    <svg viewBox="0 0 320 310" width={size} height={size * (310 / 320)} role="img" aria-label={title || type} className="cryostat-art">
      <Defs id={id} />
      {draw(id)}
    </svg>
  );
}
