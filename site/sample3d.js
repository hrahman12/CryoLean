/* CryoLean step-1 sample viewer: a detailed 3D model of the physical sample/specimen for each experiment, spinning on a
   brass stage. Geometry is illustrative (built from the experiment's documented sample), not CAD. */
(function () {
  if (!window.THREE) return;
  const T = THREE;
  const C = { brass: 0xc99437, cu: 0xc0784a, au: 0xe2b85a, steel: 0xaab4bd, al: 0xc9cfd4, dark: 0x1e2530, navy: 0x24324a,
    white: 0xf2f4f5, glass: 0xdff2ff, si: 0x55606e, ptfe: 0xf7f7f2, black: 0x151515, red: 0xa5141c, kapton: 0xd98b1c };

  // ------------------------------------------------------------------ materials + primitives
  const M = {
    metal: (c, r = 0.3) => new T.MeshStandardMaterial({ color: c, metalness: 0.92, roughness: r }),
    plastic: (c, r = 0.45) => new T.MeshStandardMaterial({ color: c, metalness: 0.05, roughness: r }),
    glass: (c = C.glass, o = 0.35) => new T.MeshPhysicalMaterial({ color: c, metalness: 0, roughness: 0.05, transmission: 0.9, transparent: true, opacity: o, side: T.DoubleSide, depthWrite: false }),
    glow: (c, e = 0.4) => new T.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: e, roughness: 0.4 }),
    liquid: (c, o = 0.8) => new T.MeshPhysicalMaterial({ color: c, roughness: 0.15, transparent: true, opacity: o, transmission: 0.3 }),
    tex: (tx, r = 0.5, m = 0.1) => new T.MeshStandardMaterial({ map: tx, roughness: r, metalness: m }),
  };
  let G;   // current group
  function put(geo, mat, p = [0, 0, 0], r = [0, 0, 0], parent) {
    const o = new T.Mesh(geo, mat); o.position.set(p[0], p[1], p[2]); o.rotation.set(r[0], r[1], r[2]);
    o.castShadow = o.receiveShadow = true; (parent || G).add(o); return o;
  }
  const box = (s, mat, p, r, pa) => put(new T.BoxGeometry(s[0], s[1], s[2]), mat, p, r, pa);
  const cyl = (rt, rb, h, mat, p, r, seg = 40, pa) => put(new T.CylinderGeometry(rt, rb, h, seg), mat, p, r, pa);
  const sph = (rad, mat, p, pa) => put(new T.SphereGeometry(rad, 24, 16), mat, p, [0, 0, 0], pa);
  const tor = (R, t, mat, p, r = [Math.PI / 2, 0, 0], pa) => put(new T.TorusGeometry(R, t, 12, 48), mat, p, r, pa);
  const tube = (pts, rad, mat, pa) => put(new T.TubeGeometry(new T.CatmullRomCurve3(pts.map((q) => new T.Vector3(...q))), 64, rad, 8), mat, [0, 0, 0], [0, 0, 0], pa);
  const rbox = (w, h, d, rad, mat, p, r) => {   // rounded rectangle slab
    const s = new T.Shape(), x = -w / 2, y = -d / 2;
    s.moveTo(x + rad, y); s.lineTo(x + w - rad, y); s.quadraticCurveTo(x + w, y, x + w, y + rad); s.lineTo(x + w, y + d - rad);
    s.quadraticCurveTo(x + w, y + d, x + w - rad, y + d); s.lineTo(x + rad, y + d); s.quadraticCurveTo(x, y + d, x, y + d - rad);
    s.lineTo(x, y + rad); s.quadraticCurveTo(x, y, x + rad, y);
    const g = new T.ExtrudeGeometry(s, { depth: h, bevelEnabled: true, bevelSize: rad * 0.3, bevelThickness: rad * 0.3, bevelSegments: 3 });
    g.rotateX(-Math.PI / 2); g.translate(0, -h / 2, 0);
    return put(g, mat, p, r);
  };
  function canvasTex(w, h, draw) {
    const c = document.createElement("canvas"); c.width = w; c.height = h; draw(c.getContext("2d"), w, h);
    const t = new T.CanvasTexture(c); t.encoding = T.sRGBEncoding; t.anisotropy = 4; return t;
  }
  const label = (text, bg = "#fff", fg = "#1b2430", w = 256, h = 96, sub) => canvasTex(w, h, (g) => {
    g.fillStyle = bg; g.fillRect(0, 0, w, h); g.fillStyle = fg; g.font = "bold 30px sans-serif"; g.fillText(text, 12, 40);
    if (sub) { g.font = "18px sans-serif"; g.fillText(sub, 12, 70); }
    g.fillStyle = fg; for (let i = 0; i < 26; i++) g.fillRect(w - 110 + i * 4, h - 28, (i * 7) % 3 + 1, 20);   // barcode
  });
  const screws = (n, R, y, mat = M.metal(C.steel)) => { for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2;
    cyl(0.018, 0.018, 0.02, mat, [Math.cos(a) * R, y, Math.sin(a) * R]); box([0.026, 0.004, 0.005], M.plastic(C.dark), [Math.cos(a) * R, y + 0.011, Math.sin(a) * R], [0, a, 0]); } };
  const wires = (n, from, to, mat, rad = 0.004) => { for (let i = 0; i < n; i++) { const f = from(i), t = to(i);
    tube([f, [(f[0] + t[0]) / 2, Math.max(f[1], t[1]) + 0.06, (f[2] + t[2]) / 2], t], rad, mat); } };
  const holder = (r = 0.42) => { cyl(r, r, 0.05, M.metal(C.cu, 0.25), [0, 0.025, 0]); screws(6, r - 0.05, 0.06); };

  // ------------------------------------------------------------------ the sample models
  const B = {
    dilatometer() {   // capacitance cell: thin crystal plate clamped between guard-ring electrodes
      cyl(0.36, 0.36, 0.12, M.metal(C.cu, 0.22), [0, 0.06, 0]); cyl(0.3, 0.3, 0.02, M.plastic(C.ptfe), [0, 0.13, 0]);
      box([0.26, 0.012, 0.18], M.glass(0x9fd8ff, 0.8), [0, 0.15, 0]);
      cyl(0.22, 0.22, 0.03, M.metal(C.au, 0.2), [0, 0.172, 0]); tor(0.25, 0.008, M.metal(C.au), [0, 0.172, 0]);
      cyl(0.36, 0.36, 0.1, M.metal(C.cu, 0.22), [0, 0.24, 0]); screws(3, 0.31, 0.3);
      [0, 2.1, 4.2].forEach((a) => cyl(0.012, 0.012, 0.3, M.metal(C.steel), [Math.cos(a) * 0.31, 0.15, Math.sin(a) * 0.31]));
      [-1, 1].forEach((s) => tube([[s * 0.36, 0.2, 0], [s * 0.5, 0.25, 0.1], [s * 0.55, 0.4, 0.2]], 0.01, M.metal(C.steel)));
    },
    hallbar() {   // chip carrier with a graphene Hall bar and gold bond wires
      box([0.62, 0.05, 0.62], M.plastic(0xc9b38b, 0.6), [0, 0.025, 0]);
      for (let i = 0; i < 24; i++) { const side = Math.floor(i / 6), k = i % 6 - 2.5, a = side * Math.PI / 2;
        const x = Math.cos(a) * 0.27 - Math.sin(a) * k * 0.07, z = Math.sin(a) * 0.27 + Math.cos(a) * k * 0.07;
        box([0.04, 0.006, 0.05], M.metal(C.au, 0.2), [x, 0.053, z], [0, -a, 0]); }
      box([0.28, 0.03, 0.28], M.metal(0x4a3d6e, 0.15), [0, 0.065, 0]);
      box([0.2, 0.004, 0.04], M.glow(0x2a2a2a, 0.05), [0, 0.082, 0]);
      for (let i = 0; i < 6; i++) box([0.012, 0.004, 0.11], M.glow(0x2a2a2a, 0.05), [-0.08 + i * 0.032, 0.082, 0]);
      for (let i = 0; i < 8; i++) { const x = -0.1 + (i % 4) * 0.066, z = i < 4 ? -0.1 : 0.1; box([0.04, 0.004, 0.04], M.metal(C.au), [x, 0.083, z]); }
      wires(8, (i) => [-0.1 + (i % 4) * 0.066, 0.085, i < 4 ? -0.1 : 0.1], (i) => [-0.1 + (i % 4) * 0.066, 0.055, i < 4 ? -0.27 : 0.27], M.metal(C.au), 0.003);
    },
    arpes() {   // Omicron-style sample plate with a gold film, tantalum clips
      box([0.5, 0.02, 0.5], M.metal(0x9aa0a6, 0.35), [0, 0.01, 0]); box([0.08, 0.06, 0.5], M.metal(0x9aa0a6), [0.26, 0.03, 0]);
      cyl(0.16, 0.16, 0.02, M.metal(C.au, 0.08), [0, 0.03, 0]);
      [-1, 1].forEach((s) => { box([0.14, 0.006, 0.04], M.metal(0x777f88, 0.25), [s * 0.17, 0.042, 0]); cyl(0.015, 0.015, 0.02, M.metal(C.steel), [s * 0.22, 0.045, 0]); });
      box([0.05, 0.03, 0.05], M.plastic(0xf1f1ec), [0, 0.035, 0.22]); tube([[0, 0.05, 0.22], [0.1, 0.2, 0.3], [0.3, 0.3, 0.2]], 0.006, M.metal(C.cu));
    },
    bloodbag(opt = {}) {   // PVC blood bag with ports, tubing segments and label
      const col = opt.color || 0xf3c35a;
      rbox(0.6, 0.06, 0.4, 0.06, M.glass(0xfafcff, 0.5), [0, 0.06, 0]);
      rbox(0.55, 0.045, 0.34, 0.05, M.liquid(col, opt.frozen ? 0.95 : 0.75), [0, 0.06, 0]);
      box([0.24, 0.002, 0.14], M.tex(label(opt.label || "FFP", "#fff", "#c0101a", 256, 96, opt.sub || "ABO/Rh  Exp")), [-0.1, 0.095, 0.02]);
      [-0.08, 0.08].forEach((x) => { cyl(0.02, 0.02, 0.07, M.plastic(0xe8e8e8), [x, 0.06, -0.24], [Math.PI / 2, 0, 0]); });
      tube([[0, 0.06, -0.22], [0.05, 0.08, -0.4], [0.3, 0.07, -0.42], [0.4, 0.06, -0.2], [0.42, 0.06, 0.1]], 0.012, M.liquid(col, 0.8));
      if (opt.cassette) { box([0.7, 0.02, 0.5], M.metal(C.al, 0.4), [0, 0.0, 0]); box([0.7, 0.02, 0.5], M.metal(C.al, 0.4), [0, 0.13, 0]).material = M.glass(0xccd6dd, 0.25);
        [-0.34, 0.34].forEach((x) => box([0.02, 0.14, 0.5], M.metal(C.al), [x, 0.065, 0])); }
      if (opt.canister) { cyl(0.4, 0.4, 0.04, M.metal(C.al), [0, -0.02, 0]); tor(0.4, 0.012, M.metal(C.al), [0, 0.12, 0]); }
    },
    cryobox(opt = {}) {   // 9x9 cryobox with screw-cap cryovials
      const n = opt.n || 9, s = 0.075;
      box([n * s + 0.04, 0.08, n * s + 0.04], M.plastic(opt.box || 0x2f6db5, 0.5), [0, 0.04, 0]);
      const caps = opt.caps || [0xd22d2d, 0xf3c018, 0x2d9b4d, 0x2d6dd2, 0xf4f4f4, 0x8a3fc7];
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
        if ((i * 7 + j * 3) % 11 === 0) continue;
        const x = (i - (n - 1) / 2) * s, z = (j - (n - 1) / 2) * s;
        cyl(0.026, 0.026, 0.12, M.glass(0xf5fbff, 0.6), [x, 0.12, z], [0, 0, 0], 16);
        cyl(0.022, 0.022, 0.05, M.liquid(opt.fluid || 0xf2e3b5, 0.8), [x, 0.09, z], [0, 0, 0], 16);
        cyl(0.03, 0.03, 0.04, M.plastic(caps[(i + j) % caps.length], 0.35), [x, 0.2, z], [0, 0, 0], 16);
      }
    },
    afs() {   // freeze-substitution carousel with flow-through capsules
      cyl(0.4, 0.4, 0.06, M.metal(C.al, 0.3), [0, 0.03, 0]);
      for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2;
        cyl(0.055, 0.055, 0.14, M.plastic(0xf6f2e8, 0.3), [Math.cos(a) * 0.28, 0.12, Math.sin(a) * 0.28]);
        cyl(0.045, 0.045, 0.1, M.liquid(0x9bc7e6, 0.6), [Math.cos(a) * 0.28, 0.13, Math.sin(a) * 0.28]);
        cyl(0.06, 0.06, 0.015, M.plastic([0x2d6dd2, 0xd22d2d, 0x2d9b4d][i % 3]), [Math.cos(a) * 0.28, 0.2, Math.sin(a) * 0.28]); }
      cyl(0.08, 0.08, 0.2, M.metal(C.steel), [0, 0.12, 0]); cyl(0.12, 0.12, 0.02, M.plastic(C.dark), [0, 0.22, 0]);
    },
    mxloop() {   // magnetic SPINE base + pin + nylon loop holding a protein crystal
      cyl(0.13, 0.13, 0.1, M.metal(C.steel, 0.2), [0, 0.05, 0]); cyl(0.14, 0.14, 0.02, M.metal(C.steel), [0, 0.11, 0]);
      cyl(0.03, 0.03, 0.06, M.plastic(0x2d6dd2), [0, 0.15, 0]); cyl(0.008, 0.008, 0.45, M.metal(C.steel, 0.15), [0, 0.4, 0]);
      tor(0.06, 0.004, M.glass(0xffffff, 0.8), [0, 0.68, 0], [0, 0, 0]);
      put(new T.CircleGeometry(0.058, 32), M.glass(0xcfe8ff, 0.3), [0, 0.68, 0]);
      const x = put(new T.OctahedronGeometry(0.03, 0), new T.MeshPhysicalMaterial({ color: 0x7fd4c8, transmission: 0.7, roughness: 0.05, transparent: true, opacity: 0.9 }), [0, 0.68, 0.005]); x.scale.set(1.3, 1, 0.5);
      tube([[0, 0.9, 0.35], [0, 0.75, 0.15], [0, 0.69, 0.03]], 0.01, M.glass(0xbfe4ff, 0.4));   // cold stream
    },
    crucible() {   // quartz crucible with freezing aqueous solution
      cyl(0.22, 0.18, 0.22, M.glass(0xeef8ff, 0.4), [0, 0.11, 0]);
      cyl(0.205, 0.17, 0.14, M.liquid(0xbfe6ff, 0.55), [0, 0.08, 0]);
      for (let i = 0; i < 18; i++) { const a = i * 2.4, r = 0.04 + (i % 6) * 0.025; const n = put(new T.ConeGeometry(0.012, 0.08, 4), M.glass(0xffffff, 0.85), [Math.cos(a) * r, 0.16, Math.sin(a) * r], [Math.PI / 2, a, 0]); n.scale.set(1, 1.6, 0.3); }
      holder(0.32);
    },
    waxslide() {   // glass slide + coverslip over a wax film with branching crystal domains
      const tx = canvasTex(512, 256, (g, w, h) => { g.fillStyle = "#e9dcb8"; g.fillRect(0, 0, w, h);
        for (let i = 0; i < 70; i++) { g.strokeStyle = `hsla(${30 + i * 4},60%,${45 + (i % 5) * 6}%,0.8)`; g.lineWidth = 1 + (i % 3);
          let x = Math.random() * w, y = Math.random() * h; g.beginPath(); g.moveTo(x, y);
          for (let k = 0; k < 6; k++) { x += (Math.random() - 0.5) * 60; y += (Math.random() - 0.5) * 60; g.lineTo(x, y); } g.stroke(); } });
      box([0.76, 0.02, 0.26], M.glass(0xe8f6ff, 0.5), [0, 0.06, 0]); box([0.26, 0.004, 0.2], M.tex(tx, 0.3), [0, 0.072, 0]);
      box([0.24, 0.003, 0.22], M.glass(0xffffff, 0.3), [0, 0.076, 0]); box([0.18, 0.003, 0.24], M.plastic(0xffffff), [-0.28, 0.072, 0]);
      cyl(0.42, 0.42, 0.04, M.metal(C.steel, 0.25), [0, 0.02, 0]); cyl(0.08, 0.08, 0.042, M.glass(0xffffff, 0.2), [0, 0.022, 0]);
    },
    filmsubstrate() {   // 25x25 mm fused silica with a thin PEDOT film, spring clips
      box([0.5, 0.04, 0.5], M.glass(0xf4fbff, 0.5), [0, 0.07, 0]); box([0.46, 0.004, 0.46], M.liquid(0x2c4f9a, 0.75), [0, 0.092, 0]);
      holder(0.42); [-1, 1].forEach((s) => box([0.06, 0.01, 0.2], M.metal(0xd6c48b), [s * 0.25, 0.1, 0]));
    },
    temgrid() {   // 3 mm copper TEM grid with nanoflakes, in a cryo-holder tip
      box([0.9, 0.06, 0.22], M.metal(C.steel, 0.25), [-0.15, 0.04, 0]); cyl(0.16, 0.16, 0.065, M.metal(C.steel), [0.2, 0.04, 0]);
      cyl(0.12, 0.12, 0.01, M.metal(C.cu, 0.3), [0.2, 0.077, 0]);
      for (let i = -5; i <= 5; i++) { box([0.24, 0.004, 0.006], M.metal(C.cu), [0.2, 0.084, i * 0.02]); box([0.006, 0.004, 0.24], M.metal(C.cu), [0.2 + i * 0.02, 0.084, 0]); }
      for (let i = 0; i < 6; i++) box([0.03, 0.002, 0.02], M.glow(0x6e5aa8, 0.3), [0.17 + (i % 3) * 0.03, 0.088, -0.02 + Math.floor(i / 3) * 0.04], [0, i, 0]);
      tor(0.13, 0.008, M.metal(0xd8d8d8), [0.2, 0.08, 0]);
    },
    monolayer() {   // SiO2/Si chip with a WSe2 monolayer flake + gold markers
      box([0.4, 0.04, 0.4], M.metal(0x6a5aa3, 0.12), [0, 0.07, 0]);
      const s = new T.Shape([[-0.08, -0.05], [0.06, -0.08], [0.1, 0.02], [0.02, 0.08], [-0.09, 0.04]].map((p) => new T.Vector2(...p)));
      put(new T.ShapeGeometry(s), M.glow(0x4fb6a4, 0.3), [0, 0.0915, 0], [-Math.PI / 2, 0, 0]);
      for (let i = 0; i < 16; i++) box([0.012, 0.002, 0.012], M.metal(C.au), [-0.16 + (i % 4) * 0.107, 0.091, -0.16 + Math.floor(i / 4) * 0.107]);
      holder(0.34);
    },
    xrdpowder() {   // TTK flat sample holder with a powder well
      cyl(0.36, 0.36, 0.06, M.metal(C.cu, 0.3), [0, 0.03, 0]); cyl(0.18, 0.18, 0.02, M.plastic(0xe6e0d0, 0.95), [0, 0.065, 0]);
      for (let i = 0; i < 120; i++) { const a = i * 2.39996, r = Math.sqrt(i / 120) * 0.17; sph(0.008, M.plastic(0xd7ccb2, 0.95), [Math.cos(a) * r, 0.078, Math.sin(a) * r]); }
      box([0.06, 0.06, 0.12], M.metal(C.steel), [0.36, 0.03, 0]); cyl(0.015, 0.015, 0.3, M.metal(C.steel), [0.5, 0.03, 0], [0, 0, Math.PI / 2]);
    },
    pigtail(opt = {}) {   // butterfly package with fibre pigtail (single-photon source / QD)
      box([0.44, 0.1, 0.24], M.metal(opt.c || 0xb9a46a, 0.3), [0, 0.05, 0]); box([0.4, 0.01, 0.2], M.metal(0xd7d7d7, 0.2), [0, 0.105, 0]);
      for (let i = 0; i < 7; i++) [-1, 1].forEach((s) => box([0.02, 0.006, 0.12], M.metal(C.au), [-0.15 + i * 0.05, 0.04, s * 0.17]));
      cyl(0.025, 0.025, 0.14, M.metal(C.steel), [0.29, 0.05, 0], [0, 0, Math.PI / 2]);
      tube([[0.36, 0.05, 0], [0.55, 0.06, 0.1], [0.6, 0.1, 0.4], [0.3, 0.12, 0.5], [-0.1, 0.1, 0.45]], 0.008, M.plastic(0xf0c419));
      cyl(0.03, 0.03, 0.07, M.plastic(0x2a9df4), [-0.15, 0.1, 0.45], [0, 0, Math.PI / 2]);
    },
    photonchip() {   // superconducting-nanowire / photonic chip with a fibre V-groove array
      box([0.5, 0.04, 0.34], M.metal(C.cu, 0.25), [0, 0.02, 0]); box([0.22, 0.02, 0.18], M.metal(0x3d3f63, 0.15), [0.02, 0.05, 0]);
      for (let i = 0; i < 8; i++) box([0.18, 0.002, 0.004], M.glow(0x7ad1ff, 0.6), [0.02, 0.062, -0.07 + i * 0.02]);
      box([0.12, 0.04, 0.16], M.glass(0xeef8ff, 0.7), [-0.17, 0.06, 0]);
      for (let i = 0; i < 4; i++) tube([[-0.22, 0.06, -0.045 + i * 0.03], [-0.45, 0.08, -0.06 + i * 0.04], [-0.6, 0.15, -0.1 + i * 0.07]], 0.006, M.plastic([0xf0c419, 0x2a9df4, 0xe94b3c, 0x29b36b][i]));
      wires(6, (i) => [0.1, 0.062, -0.06 + i * 0.024], (i) => [0.22, 0.042, -0.08 + i * 0.032], M.metal(C.au), 0.002);
    },
    wafer300() {   // 300 mm silicon wafer with die grid and notch
      const g = new T.CylinderGeometry(0.46, 0.46, 0.012, 96); put(g, M.metal(0x6c7484, 0.08), [0, 0.06, 0]);
      for (let i = -8; i <= 8; i++) for (let j = -8; j <= 8; j++) { const x = i * 0.05, z = j * 0.05; if (x * x + z * z > 0.42 * 0.42) continue;
        box([0.044, 0.003, 0.044], M.metal((i + j) & 1 ? 0x7a6cc0 : 0x5e8bc4, 0.15), [x, 0.068, z]); }
      cyl(0.47, 0.47, 0.03, M.plastic(0x2b2b2b, 0.6), [0, 0.035, 0], [0, 0, 0], 96);
      box([0.04, 0.03, 0.03], M.plastic(0x2b2b2b), [0, 0.06, 0.47]);
    },
    nbsheet() {   // niobium RRR strip with four-terminal voltage/current leads
      box([0.7, 0.02, 0.1], M.metal(0x8f9aa8, 0.35), [0, 0.07, 0]);
      [-0.3, -0.1, 0.1, 0.3].forEach((x, i) => { box([0.03, 0.03, 0.12], M.metal(C.cu), [x, 0.085, 0]); cyl(0.01, 0.01, 0.03, M.metal(C.steel), [x, 0.11, 0]);
        tube([[x, 0.1, 0.05], [x, 0.2, 0.2], [x * 1.2, 0.25, 0.4]], 0.006, M.plastic(i % 3 ? 0xe94b3c : 0x2a9df4)); });
      box([0.8, 0.04, 0.2], M.plastic(0xf1ecdc, 0.7), [0, 0.03, 0]);
    },
    bolometer() {   // TeO2 crystal towers in copper frames with PTFE holders and NTD sensors
      for (let t = 0; t < 3; t++) { const x0 = (t - 1) * 0.28;
        for (let f = 0; f < 4; f++) { const y = 0.08 + f * 0.17;
          box([0.22, 0.02, 0.22], M.metal(C.cu, 0.25), [x0, y - 0.075, 0]);
          box([0.13, 0.13, 0.13], new T.MeshPhysicalMaterial({ color: 0xf6f0e0, transmission: 0.6, roughness: 0.05, transparent: true, opacity: 0.85 }), [x0, y, 0]);
          box([0.025, 0.004, 0.025], M.plastic(C.black), [x0, y + 0.067, 0.03]);
          [[-1, -1], [1, 1]].forEach(([a, b]) => box([0.02, 0.025, 0.02], M.plastic(C.ptfe), [x0 + a * 0.075, y - 0.05, b * 0.075])); }
        [-1, 1].forEach((a) => [-1, 1].forEach((b) => cyl(0.008, 0.008, 0.72, M.metal(C.cu), [x0 + a * 0.1, 0.33, b * 0.1]))); }
    },
    sipm() {   // SiPM tile: 4x4 array on a PCB with a connector
      box([0.5, 0.03, 0.5], M.plastic(0x1f6b3a, 0.55), [0, 0.06, 0]);
      for (let i = 0; i < 16; i++) { const x = -0.165 + (i % 4) * 0.11, z = -0.165 + Math.floor(i / 4) * 0.11;
        box([0.1, 0.012, 0.1], M.metal(0x2d2f5c, 0.12), [x, 0.081, z]); box([0.09, 0.002, 0.09], M.glass(0xb6c8ff, 0.5), [x, 0.088, z]); }
      box([0.14, 0.04, 0.04], M.plastic(C.white), [0, 0.06, 0.28]); holder(0.4);
    },
    prt() {   // platinum resistance thermometer: ceramic body, 4-wire PTFE lead, flight connector
      cyl(0.03, 0.03, 0.4, M.plastic(0xf4f1e8, 0.3), [0, 0.07, 0], [0, 0, Math.PI / 2]);
      cyl(0.033, 0.033, 0.06, M.metal(C.steel), [0.22, 0.07, 0], [0, 0, Math.PI / 2]);
      tube([[0.25, 0.07, 0], [0.45, 0.08, 0.1], [0.4, 0.1, 0.4], [0, 0.1, 0.45], [-0.3, 0.08, 0.3]], 0.014, M.plastic(0xffffff, 0.3));
      cyl(0.06, 0.06, 0.12, M.metal(0x7c8a96, 0.3), [-0.36, 0.08, 0.28], [0, 0, Math.PI / 2]);
      box([0.6, 0.02, 0.2], M.metal(C.al, 0.4), [0, 0.03, 0]); box([0.1, 0.03, 0.06], M.plastic(C.kapton, 0.4), [0, 0.06, 0]);
    },
    avionics(opt = {}) {   // flight electronics unit: machined box, fins, mil connectors, mounting feet, label
      const c = opt.c || 0x6b7480;
      box([0.6, 0.26, 0.42], M.metal(c, 0.45), [0, 0.15, 0]);
      for (let i = 0; i < 9; i++) box([0.6, 0.02, 0.012], M.metal(c, 0.45), [0, 0.29, -0.18 + i * 0.045]);
      [-0.18, 0, 0.18].forEach((x) => { cyl(0.05, 0.05, 0.05, M.metal(0x4d5560), [x, 0.15, 0.235], [Math.PI / 2, 0, 0]); cyl(0.035, 0.035, 0.03, M.plastic(C.dark), [x, 0.15, 0.27], [Math.PI / 2, 0, 0]); });
      [-1, 1].forEach((a) => [-1, 1].forEach((b) => box([0.08, 0.02, 0.06], M.metal(c), [a * 0.33, 0.03, b * 0.18])));
      box([0.2, 0.001, 0.09], M.tex(label(opt.label || "UNIT", "#e7e2d2", "#222", 256, 96, opt.sub)), [0.1, 0.302, 0.12]);
    },
    detchip(opt = {}) {   // IR/CCD focal-plane array in a gold-plated package with flex cable
      box([0.5, 0.06, 0.5], M.metal(opt.pkg || 0x8a6a3a, 0.3), [0, 0.05, 0]); box([0.4, 0.02, 0.4], M.metal(C.au, 0.15), [0, 0.09, 0]);
      const tx = canvasTex(256, 256, (g) => { const grd = g.createLinearGradient(0, 0, 256, 256); grd.addColorStop(0, opt.c1 || "#2b2560"); grd.addColorStop(0.5, opt.c2 || "#6d3fa0"); grd.addColorStop(1, opt.c1 || "#2b2560");
        g.fillStyle = grd; g.fillRect(0, 0, 256, 256); g.strokeStyle = "rgba(255,255,255,0.08)"; for (let i = 0; i < 256; i += 4) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 256); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(256, i); g.stroke(); } });
      box([0.32, 0.01, 0.32], M.tex(tx, 0.1, 0.6), [0, 0.105, 0]);
      box([0.3, 0.004, 0.3], M.plastic(C.kapton, 0.4), [0, 0.03, 0.4]); box([0.14, 0.03, 0.06], M.plastic(C.dark), [0, 0.04, 0.56]);
      screws(4, 0.31, 0.09);
    },
    tesarray() {   // TES bolometer array wafer with horn feeds above
      cyl(0.4, 0.4, 0.015, M.metal(0x5d6676, 0.1), [0, 0.06, 0], [0, 0, 0], 6);
      for (let i = 0; i < 61; i++) { const r = Math.floor(Math.sqrt(i / 3)), a = i * 2.39996, rr = Math.sqrt(i / 61) * 0.34;
        cyl(0.025, 0.012, 0.08, M.metal(C.au, 0.2), [Math.cos(a) * rr, 0.11, Math.sin(a) * rr]); }
      cyl(0.42, 0.42, 0.04, M.metal(C.cu, 0.25), [0, 0.03, 0], [0, 0, 0], 6);
    },
    icboard(opt = {}) {   // qualification board with packaged ICs in sockets
      box([0.7, 0.03, 0.5], M.plastic(0x1f6b3a, 0.5), [0, 0.04, 0]);
      for (let i = 0; i < 6; i++) { const x = -0.22 + (i % 3) * 0.22, z = -0.12 + Math.floor(i / 3) * 0.24;
        box([0.15, 0.03, 0.15], M.plastic(0x2a2a2a), [x, 0.07, z]); box([0.11, 0.02, 0.11], M.plastic(opt.ceramic ? 0xd9d4c3 : 0x1a1a1a, 0.4), [x, 0.095, z]);
        if (opt.ceramic) box([0.06, 0.004, 0.06], M.metal(C.au), [x, 0.107, z]);
        for (let k = 0; k < 8; k++) [-1, 1].forEach((s) => box([0.008, 0.006, 0.03], M.metal(0xcfcfcf), [x - 0.042 + k * 0.012, 0.087, z + s * 0.065])); }
      box([0.06, 0.04, 0.5], M.plastic(C.dark), [0.37, 0.06, 0]);
    },
    probecard() {   // cryo probe card: ring PCB with tungsten needles landing on a die
      tor(0.36, 0.06, M.plastic(0x1f6b3a, 0.5), [0, 0.25, 0]); box([0.25, 0.02, 0.25], M.metal(0x4b4f7a, 0.12), [0, 0.06, 0]);
      for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2; tube([[Math.cos(a) * 0.32, 0.25, Math.sin(a) * 0.32], [Math.cos(a) * 0.15, 0.17, Math.sin(a) * 0.15], [Math.cos(a) * 0.06, 0.075, Math.sin(a) * 0.06]], 0.003, M.metal(0xb0b0b8)); }
      box([0.5, 0.02, 0.5], M.metal(C.au, 0.2), [0, 0.04, 0]);
    },
    linbo3() {   // Er:LiNbO3 crystal on a copper mount, fibre-coupled
      box([0.36, 0.06, 0.14], new T.MeshPhysicalMaterial({ color: 0xf9d7e4, transmission: 0.7, roughness: 0.04, transparent: true, opacity: 0.85 }), [0, 0.1, 0]);
      box([0.5, 0.06, 0.24], M.metal(C.cu, 0.25), [0, 0.04, 0]);
      [-1, 1].forEach((s) => { cyl(0.025, 0.025, 0.1, M.metal(C.steel), [s * 0.26, 0.1, 0], [0, 0, Math.PI / 2]);
        tube([[s * 0.31, 0.1, 0], [s * 0.5, 0.12, 0.1], [s * 0.55, 0.2, 0.3]], 0.006, M.plastic(0xf0c419)); });
      box([0.34, 0.004, 0.02], M.glow(0xff3060, 0.7), [0, 0.13, 0]);
    },
    dogbone(opt = {}) {   // tensile specimen in wedge grips with an extensometer
      const s = new T.Shape(); s.moveTo(-0.4, -0.08); s.lineTo(-0.2, -0.08); s.bezierCurveTo(-0.15, -0.08, -0.12, -0.04, -0.1, -0.04); s.lineTo(0.1, -0.04);
      s.bezierCurveTo(0.12, -0.04, 0.15, -0.08, 0.2, -0.08); s.lineTo(0.4, -0.08); s.lineTo(0.4, 0.08); s.lineTo(0.2, 0.08); s.bezierCurveTo(0.15, 0.08, 0.12, 0.04, 0.1, 0.04);
      s.lineTo(-0.1, 0.04); s.bezierCurveTo(-0.12, 0.04, -0.15, 0.08, -0.2, 0.08); s.lineTo(-0.4, 0.08); s.closePath();
      const sp = put(new T.ExtrudeGeometry(s, { depth: 0.03, bevelEnabled: false }), M.metal(opt.c || 0xb8c2cc, 0.3), [0, 0.32, -0.015], [0, 0, Math.PI / 2]);
      [-1, 1].forEach((d) => { box([0.22, 0.18, 0.14], M.metal(0x4f5862, 0.4), [0, 0.32 + d * 0.33, 0]); cyl(0.05, 0.05, 0.12, M.metal(C.steel), [0, 0.32 + d * 0.47, 0]); });
      box([0.04, 0.12, 0.05], M.metal(0x2c3440), [0.08, 0.32, 0.03]); [-1, 1].forEach((d) => box([0.06, 0.008, 0.02], M.metal(C.steel), [0.04, 0.32 + d * 0.05, 0.03]));
    },
    rebco() {   // REBCO coated-conductor tape soldered on a bending beam with voltage taps
      box([0.8, 0.06, 0.16], M.metal(0x9a7b4f, 0.3), [0, 0.06, 0]); box([0.78, 0.006, 0.06], M.metal(0xc0c4c8, 0.15), [0, 0.094, 0]);
      for (let i = 0; i < 5; i++) { const x = -0.3 + i * 0.15; cyl(0.006, 0.006, 0.02, M.metal(C.au), [x, 0.105, 0.02]); tube([[x, 0.11, 0.02], [x, 0.2, 0.1], [x + 0.05, 0.25, 0.3]], 0.004, M.plastic(i % 2 ? 0xe94b3c : 0x2a9df4)); }
      [-1, 1].forEach((s) => box([0.1, 0.12, 0.2], M.metal(C.cu), [s * 0.42, 0.08, 0]));
    },
    mli() {   // tank-wall section wrapped in crinkled multilayer insulation
      const g = new T.CylinderGeometry(0.4, 0.4, 0.5, 64, 12, true, 0, Math.PI * 1.2); const p = g.attributes.position;
      for (let i = 0; i < p.count; i++) { const n = Math.sin(p.getY(i) * 60 + p.getX(i) * 40) * 0.008; p.setX(i, p.getX(i) * (1 + n)); p.setZ(i, p.getZ(i) * (1 + n)); }
      g.computeVertexNormals(); put(g, M.metal(0xd8c48a, 0.2), [0, 0.3, 0]);
      for (let i = 0; i < 5; i++) put(new T.CylinderGeometry(0.4 - i * 0.012, 0.4 - i * 0.012, 0.5, 64, 1, true, 0, Math.PI * 1.2), M.metal(i % 2 ? 0xe6e8ea : 0xd8c48a, 0.25), [0, 0.3, 0]);
      put(new T.CylinderGeometry(0.33, 0.33, 0.5, 64, 1, true, 0, Math.PI * 1.2), M.metal(C.steel, 0.35), [0, 0.3, 0]);
      for (let i = 0; i < 4; i++) box([0.04, 0.5, 0.004], M.plastic(0xf2f2f2), [Math.cos(i * 0.9) * 0.41, 0.3, Math.sin(i * 0.9) * 0.41], [0, -i * 0.9, 0]);
    },
    cutarget() {   // copper target with laser-grating spots, thermocouple and clamp
      box([0.4, 0.04, 0.4], M.metal(C.cu, 0.2), [0, 0.08, 0]);
      for (let i = 0; i < 3; i++) cyl(0.04, 0.04, 0.002, M.glow([0xff3355, 0x33ff88, 0x5599ff][i], 0.9), [-0.1 + i * 0.1, 0.101, 0]);
      box([0.5, 0.06, 0.06], M.metal(C.steel), [0, 0.13, -0.17]); holder(0.38);
      tube([[0.2, 0.1, 0.2], [0.3, 0.2, 0.35], [0.45, 0.2, 0.4]], 0.006, M.plastic(0xe9c11b));
    },
    pellet() {   // pellet injector barrel with a frozen deuterium pellet
      cyl(0.05, 0.05, 0.9, M.metal(C.steel, 0.25), [0, 0.12, 0], [0, 0, Math.PI / 2]); cyl(0.12, 0.12, 0.2, M.metal(C.cu, 0.3), [-0.2, 0.12, 0], [0, 0, Math.PI / 2]);
      for (let i = 0; i < 6; i++) tor(0.125, 0.01, M.metal(C.cu), [-0.28 + i * 0.03, 0.12, 0], [0, Math.PI / 2, 0]);
      cyl(0.035, 0.035, 0.07, M.glass(0xeaf6ff, 0.85), [0.35, 0.12, 0], [0, 0, Math.PI / 2]);
      cyl(0.02, 0.02, 0.05, M.glow(0xd9f1ff, 0.5), [0.35, 0.12, 0], [0, 0, Math.PI / 2]);
      [-1, 1].forEach((s) => box([0.08, 0.08, 0.12], M.metal(0x4f5862), [s * 0.4, 0.04, 0]));
    },
    cicc() {   // CICC: two conduit legs joined by a bottom joint, petal strands visible at cut end
      [-0.14, 0.14].forEach((x) => { cyl(0.08, 0.08, 0.7, M.metal(0x9aa4ae, 0.35), [x, 0.45, 0]);
        for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; cyl(0.025, 0.025, 0.02, M.metal(C.cu), [x + Math.cos(a) * 0.045, 0.81, Math.sin(a) * 0.045]); }
        cyl(0.018, 0.018, 0.02, M.metal(C.steel), [x, 0.81, 0]); });
      box([0.48, 0.14, 0.2], M.metal(C.cu, 0.3), [0, 0.08, 0]); box([0.5, 0.02, 0.22], M.metal(C.steel), [0, 0.16, 0]);
    },
    tyre() {   // passenger-car tyre with tread blocks, frosted from LN2
      tor(0.34, 0.13, M.plastic(0x1b1b1b, 0.85), [0, 0.15, 0]);
      for (let i = 0; i < 40; i++) { const a = i / 40 * Math.PI * 2; box([0.06, 0.05, 0.2], M.plastic(0x222222, 0.9), [Math.cos(a) * 0.47, 0.15, Math.sin(a) * 0.47], [0, -a, 0]); }
      for (let i = 0; i < 40; i++) { const a = i * 0.71; sph(0.012, M.plastic(0xffffff, 0.3), [Math.cos(a) * 0.4, 0.28, Math.sin(a) * 0.4]); }
    },
    charpy() {   // Charpy V-notch specimen (55 x 10 x 10 mm) with weld bead, on anvils
      box([0.66, 0.12, 0.12], M.metal(0xa9b2bb, 0.35), [0, 0.18, 0]);
      put(new T.CylinderGeometry(0.03, 0.001, 0.12, 3), M.plastic(0x222222), [0, 0.25, 0], [Math.PI / 2, 0, 0]);
      box([0.08, 0.121, 0.121], M.metal(0x8b7a62, 0.6), [0, 0.18, 0]);
      [-1, 1].forEach((s) => box([0.1, 0.12, 0.2], M.metal(0x4f5862), [s * 0.28, 0.06, 0]));
    },
    dscpan() {   // aluminium DSC pan with lid and the black SBR disc, beside reference pan
      [-0.15, 0.15].forEach((x, k) => { cyl(0.11, 0.1, 0.05, M.metal(C.al, 0.25), [x, 0.08, 0]); cyl(0.095, 0.095, 0.002, M.metal(0xb7bdc2, 0.2), [x, 0.106, 0]);
        if (!k) cyl(0.06, 0.06, 0.02, M.plastic(C.black, 0.8), [x, 0.08, 0]); });
      cyl(0.4, 0.4, 0.05, M.metal(0xd8b55e, 0.25), [0, 0.03, 0]);
    },
    pouchcell() {   // EV pouch cell with tabs, sensors taped on
      rbox(0.5, 0.06, 0.66, 0.03, M.metal(0xb8bfc6, 0.35), [0, 0.06, 0]);
      [-0.12, 0.12].forEach((x, i) => box([0.1, 0.006, 0.12], M.metal(i ? C.cu : C.al, 0.25), [x, 0.07, -0.38]));
      box([0.07, 0.002, 0.07], M.plastic(C.kapton), [0, 0.096, 0.1]); tube([[0, 0.1, 0.1], [0.2, 0.15, 0.2], [0.4, 0.2, 0.3]], 0.005, M.plastic(0xe9c11b));
      box([0.3, 0.001, 0.12], M.tex(label("Li-ion NMC", "#203040", "#fff", 256, 96, "3.7 V 60 Ah")), [0, 0.096, -0.12]);
    },
    ecu(opt = {}) { B.avionics({ c: opt.c || 0x2a2d31, label: opt.label || "ECU", sub: "12 V  ISO 16750" }); },
    tuna() {   // block of sashimi-grade tuna, deep red with fat lines and frost, on a tray
      const tx = canvasTex(256, 256, (g) => { g.fillStyle = "#9b1a24"; g.fillRect(0, 0, 256, 256); g.strokeStyle = "rgba(255,210,210,0.45)"; g.lineWidth = 3;
        for (let i = 0; i < 12; i++) { g.beginPath(); g.moveTo(0, i * 22); g.bezierCurveTo(80, i * 22 + 18, 170, i * 22 - 18, 256, i * 22 + 4); g.stroke(); } });
      rbox(0.5, 0.18, 0.3, 0.04, M.tex(tx, 0.45), [0, 0.13, 0]);
      box([0.62, 0.02, 0.42], M.plastic(0xffffff, 0.3), [0, 0.03, 0]);
      for (let i = 0; i < 30; i++) sph(0.006, M.plastic(0xffffff, 0.2), [(i % 6 - 2.5) * 0.08, 0.225, (Math.floor(i / 6) - 2) * 0.05]);
    },
    blueberries() {   // tray of frozen blueberries with bloom
      box([0.7, 0.04, 0.5], M.metal(C.steel, 0.3), [0, 0.02, 0]);
      for (let i = 0; i < 70; i++) { const x = ((i * 37) % 13 - 6) * 0.048, z = ((i * 17) % 9 - 4) * 0.048;
        const b = sph(0.03, new T.MeshStandardMaterial({ color: 0x2b3576, roughness: 0.55 }), [x, 0.07 + (i % 3) * 0.02, z]); b.scale.set(1, 0.85, 1);
        sph(0.008, M.plastic(0x1c1c2c), [x, 0.1 + (i % 3) * 0.02, z]); }
    },
    straws() {   // 0.25 mL French straws on a freezing rack above LN2 vapour
      box([0.7, 0.02, 0.4], M.metal(C.steel, 0.3), [0, 0.16, 0]);
      for (let i = 0; i < 16; i++) { const z = -0.17 + i * 0.023; cyl(0.008, 0.008, 0.62, M.plastic([0xe94b3c, 0x2a9df4, 0xf0c419, 0x29b36b][i % 4], 0.3), [0, 0.18, z], [0, 0, Math.PI / 2]); }
      cyl(0.5, 0.5, 0.1, M.glass(0xcfe8ff, 0.3), [0, 0.05, 0]); cyl(0.48, 0.48, 0.04, M.liquid(0xc8e6ff, 0.5), [0, 0.03, 0]);
    },
    jars() {   // environmental specimen archive: labelled PFA jars in a rack
      box([0.7, 0.03, 0.46], M.metal(C.steel, 0.35), [0, 0.02, 0]);
      for (let i = 0; i < 6; i++) { const x = -0.22 + (i % 3) * 0.22, z = -0.11 + Math.floor(i / 3) * 0.22;
        cyl(0.08, 0.08, 0.22, M.glass(0xf2f8fa, 0.55), [x, 0.15, z]); cyl(0.07, 0.07, 0.12, M.liquid([0x7a5a2a, 0x3c6b3a, 0x9e9a8a, 0x5a4a3a, 0xa38b5c, 0x4a6a7a][i], 0.9), [x, 0.1, z]);
        cyl(0.085, 0.085, 0.04, M.plastic(0xf1f1f1), [x, 0.28, z]); box([0.1, 0.06, 0.001], M.tex(label("ESB-" + (100 + i))), [x, 0.17, z + 0.081]); }
    },
    wellplate() {   // 96-well PCR plate with droplets
      box([0.76, 0.05, 0.5], M.plastic(0xf2f2f2, 0.4), [0, 0.04, 0]);
      for (let i = 0; i < 12; i++) for (let j = 0; j < 8; j++) { const x = -0.33 + i * 0.06, z = -0.21 + j * 0.06;
        cyl(0.022, 0.015, 0.05, M.glass(0xffffff, 0.5), [x, 0.08, z], [0, 0, 0], 12); cyl(0.015, 0.012, 0.02, M.liquid((i + j) % 5 ? 0xbfe6ff : 0xffffff, 0.85), [x, 0.07, z], [0, 0, 0], 12); }
    },
    grindjar() {   // stainless grinding jar with soil and steel ball, lid off
      cyl(0.2, 0.2, 0.5, M.metal(C.steel, 0.2), [0, 0.12, 0], [0, 0, Math.PI / 2]).material.side = T.DoubleSide;
      put(new T.CylinderGeometry(0.19, 0.19, 0.48, 40, 1, true), M.metal(0x9aa4ae, 0.4), [0, 0.12, 0], [0, 0, Math.PI / 2]);
      for (let i = 0; i < 60; i++) sph(0.018 + (i % 3) * 0.006, M.plastic([0x6b4a2b, 0x8a6a3a, 0x4a3420][i % 3], 0.95), [((i * 13) % 20 - 10) * 0.02, -0.0 + (i % 4) * 0.02, ((i * 7) % 10 - 5) * 0.02]);
      sph(0.06, M.metal(C.steel, 0.1), [0.1, 0.06, 0]); cyl(0.21, 0.21, 0.05, M.metal(C.steel, 0.2), [0.42, 0.12, 0], [0, 0, Math.PI / 2]);
    },
    icecolumn() {   // sea-ice column: acrylic tube with layered ice and microplastics
      cyl(0.16, 0.16, 0.8, M.glass(0xeaf6ff, 0.35), [0, 0.42, 0]);
      for (let i = 0; i < 6; i++) cyl(0.15, 0.15, 0.1, M.liquid(i < 4 ? 0xf2f9ff : 0x8cc6e8, i < 4 ? 0.85 : 0.6), [0, 0.1 + i * 0.11, 0]);
      for (let i = 0; i < 40; i++) sph(0.008, M.glow([0xff4f7a, 0x4fd1ff, 0xffd84f][i % 3], 0.4), [Math.cos(i) * 0.1 * ((i % 5) / 5), 0.08 + (i % 13) * 0.05, Math.sin(i) * 0.1 * ((i % 5) / 5)]);
      cyl(0.2, 0.2, 0.04, M.plastic(0x2a2a2a), [0, 0.02, 0]);
    },
    bottles() {   // HDPE seawater nutrient bottles, frozen, with caps and labels
      for (let i = 0; i < 5; i++) { const a = i / 5 * Math.PI * 2, x = Math.cos(a) * 0.24, z = Math.sin(a) * 0.24;
        cyl(0.07, 0.07, 0.26, M.plastic(0xf4f6f7, 0.5), [x, 0.15, z]); cyl(0.065, 0.065, 0.16, M.liquid(0xcde7f5, 0.9), [x, 0.1, z]);
        cyl(0.035, 0.05, 0.04, M.plastic(0xf4f6f7), [x, 0.3, z]); cyl(0.04, 0.04, 0.04, M.plastic([0x2a9df4, 0xe94b3c][i % 2]), [x, 0.34, z]); }
      holder(0.4);
    },
    cryotrap() {   // stainless cryogenic trap: coiled tube with VCR fittings and valves
      for (let i = 0; i < 6; i++) tor(0.22, 0.02, M.metal(C.steel, 0.25), [0, 0.12 + i * 0.06, 0]);
      cyl(0.12, 0.12, 0.38, M.metal(C.cu, 0.3), [0, 0.27, 0]);
      [-1, 1].forEach((s) => { tube([[s * 0.22, 0.45, 0], [s * 0.3, 0.6, 0], [s * 0.35, 0.65, 0]], 0.02, M.metal(C.steel)); B._valve([s * 0.4, 0.66, 0]); });
    },
    _valve(p) { cyl(0.04, 0.04, 0.12, M.metal(C.steel), p, [0, 0, Math.PI / 2]); cyl(0.012, 0.012, 0.08, M.metal(C.steel), [p[0], p[1] + 0.06, p[2]]); tor(0.04, 0.008, M.plastic(0x1a1a1a), [p[0], p[1] + 0.1, p[2]]); },
    tpcell() {   // sealed argon triple-point cell with SPRT inserted
      cyl(0.16, 0.16, 0.6, M.metal(C.steel, 0.2), [0, 0.32, 0]); cyl(0.17, 0.17, 0.04, M.metal(C.steel), [0, 0.63, 0]);
      cyl(0.02, 0.02, 0.6, M.glass(0xf6fbff, 0.7), [0, 0.8, 0]); cyl(0.015, 0.015, 0.06, M.plastic(0x2a2a2a), [0, 1.1, 0]);
      tube([[0, 1.12, 0], [0.1, 1.2, 0], [0.4, 1.1, 0.1]], 0.008, M.plastic(0x2a2a2a)); B._valve([0.2, 0.55, 0]);
    },
    gasbulb(opt = {}) {   // gas-thermometer bulb (copper) with capillary and pressure gauge
      sph(0.2, M.metal(C.cu, 0.25), [0, 0.25, 0]); cyl(0.05, 0.05, 0.1, M.metal(C.cu), [0, 0.47, 0]);
      tube([[0, 0.52, 0], [0.05, 0.7, 0], [0.3, 0.75, 0.1], [0.4, 0.5, 0.2]], 0.006, M.metal(C.steel));
      const g = cyl(0.1, 0.1, 0.04, M.metal(C.steel), [0.42, 0.44, 0.2], [Math.PI / 2, 0, 0]); cyl(0.088, 0.088, 0.002, M.plastic(0xffffff), [0.42, 0.44, 0.222], [Math.PI / 2, 0, 0]);
      if (opt.he) sph(0.16, M.glass(0xd6ecff, 0.35), [0, 0.25, 0]);
      for (let i = 0; i < 4; i++) cyl(0.008, 0.008, 0.08, M.plastic(C.dark), [Math.cos(i * 1.57) * 0.15, 0.12, Math.sin(i * 1.57) * 0.15]);
    },
    radio() {   // rugged military radio: olive housing, knobs, antenna, handle
      box([0.4, 0.5, 0.2], M.plastic(0x4b5320, 0.75), [0, 0.27, 0]); box([0.3, 0.12, 0.002], M.plastic(0x101810, 0.2), [0, 0.38, 0.101]);
      [-0.1, 0.1].forEach((x) => cyl(0.04, 0.04, 0.06, M.plastic(C.black), [x, 0.55, 0])); cyl(0.012, 0.006, 0.6, M.plastic(C.black), [0.14, 0.82, 0]);
      for (let i = 0; i < 12; i++) box([0.04, 0.03, 0.01], M.plastic(0x2c2f20), [-0.12 + (i % 4) * 0.08, 0.2 - Math.floor(i / 4) * 0.05, 0.105]);
      tube([[-0.2, 0.45, 0], [-0.28, 0.3, 0], [-0.2, 0.1, 0]], 0.02, M.plastic(C.black));
    },
    munitions() {   // munition rounds in a wooden crate (inert illustration)
      box([0.7, 0.06, 0.45], M.plastic(0x8a6a3a, 0.8), [0, 0.03, 0]); [-1, 1].forEach((s) => box([0.7, 0.2, 0.03], M.plastic(0x8a6a3a, 0.8), [0, 0.12, s * 0.22]));
      for (let i = 0; i < 4; i++) { const z = -0.15 + i * 0.1; cyl(0.04, 0.04, 0.42, M.metal(0xb08d57, 0.3), [-0.05, 0.11, z], [0, 0, Math.PI / 2]);
        put(new T.ConeGeometry(0.04, 0.16, 24), M.metal(0x4b5320, 0.5), [0.24, 0.11, z], [0, 0, -Math.PI / 2]); tor(0.042, 0.006, M.metal(C.cu), [0.14, 0.11, z], [0, Math.PI / 2, 0]); }
    },
    idca() {   // integrated detector-dewar-cooler assembly: dewar, window, Stirling cooler
      cyl(0.13, 0.13, 0.32, M.metal(0x8a929a, 0.3), [0, 0.35, 0]); cyl(0.09, 0.09, 0.01, M.glass(0x6a4a8a, 0.75), [0, 0.515, 0]);
      cyl(0.12, 0.12, 0.38, M.metal(0x3a3f45, 0.4), [0.26, 0.15, 0], [0, 0, Math.PI / 2]);
      for (let i = 0; i < 8; i++) tor(0.125, 0.012, M.metal(0x6a7078), [0.14 + i * 0.035, 0.15, 0], [0, Math.PI / 2, 0]);
      box([0.2, 0.04, 0.2], M.metal(0x8a929a), [0, 0.17, 0]); box([0.1, 0.03, 0.04], M.plastic(C.dark), [-0.15, 0.3, 0]);
    },
    generic() { holder(); box([0.2, 0.06, 0.2], M.plastic(0x2c3440), [0, 0.08, 0]); },
  };

  // ------------------------------------------------------------------ experiment -> model
  const MAP = {
    sci_thin_crystal_dilatometry: ["dilatometer"], sci_graphene_yig_quantum_hall: ["hallbar"], sci_arpes_gold_fermi_edge: ["arpes"],
    med_ffp_contact_shock_freezing: ["bloodbag", { label: "FFP", sub: "Plasma  O Rh+", frozen: true }],
    med_glycerolized_rbc_frozen_storage: ["bloodbag", { color: 0x8e1018, label: "RBC", sub: "Glycerolized  Rare", cassette: true }],
    med_cord_blood_unit_ln2_banking: ["bloodbag", { color: 0x9e1a22, label: "CORD", sub: "HPC  25 mL", canister: true }],
    bio_bacterial_glycerol_stock_minus80: ["cryobox", { fluid: 0xefe6c6 }], bio_freeze_substitution_afs2: ["afs"], bio_mx_cryocrystallography_100k: ["mxloop"],
    chem_low_temperature_raman: ["crucible"], chem_phase_transition_pom: ["waxslide"], chem_temperature_dependent_photoluminescence: ["filmsubstrate"],
    mat_cryo_tem_cdw_nanoflakes: ["temgrid"], mat_monolayer_wse2_lowtemp_photoluminescence: ["monolayer"], mat_lowtemp_xrd_phase_transitions_ttk600: ["xrdpowder"],
    quantum_fibre_pigtailed_photon_source: ["pigtail"], quantum_heralded_qubit_amplifier: ["photonchip"], quantum_spin_qubit_wafer_cryoprobing: ["wafer300"],
    phys_niobium_rrr: ["nbsheet"], expa_teo2_bolometer: ["bolometer"], phys_lar_sipm_ln2_qualification: ["sipm"],
    aero_mars_prt_thermal_cycling: ["prt"], aero_ecss_equipment_tvac: ["avionics", { c: 0x8f969c, label: "ESA UNIT", sub: "ECSS-E-ST-10-03" }],
    aero_gevs_unit_tvac: ["avionics", { c: 0x2f3a46, label: "GSFC", sub: "GEVS-SE  TVAC" }],
    astro_ge_ccd_nir_95k: ["detchip", { c1: "#1f2d3a", c2: "#5a7a8a" }], astro_h2rg_ir_array_35k: ["detchip", { pkg: 0x3a3f45, c1: "#2a1d4a", c2: "#8a4fc0" }], astro_qubic_tes_array_320mk: ["tesarray"],
    semi_aecq100_grade0_tc_ptc: ["icboard"], semi_mil883_tc_condition_c: ["icboard", { ceramic: true }], semi_finfet_5nm_cryo_probe: ["probecard"],
    photon_fibre_pigtailed_qd_source: ["pigtail", { c: 0x8f969c }], photon_mosi_heralded_qubit_amplifier: ["photonchip"], photon_er_linbo3_afc_memory: ["linbo3"],
    expc_energy_tensile_20k: ["dogbone"], energy_rebco_ic_axial_strain_77k: ["rebco"], expc_energy_insulation_boiloff: ["mli"],
    nuc_cryo_ion_irradiation_tgs: ["cutarget"], nuc_ipi_d2_pellet_high_speed: ["pellet"], expa_cicc_critical_current: ["cicc"],
    mfg_waste_tyre_ln2_impact_crumbing: ["tyre"], mfg_lng_austenitic_weld_charpy_minus196c: ["charpy"], expansion_b_manufacturing_sbr_rubber_dsc: ["dscpan"],
    auto_iec62660_low_temp_capacity: ["pouchcell"], auto_iso16750_constant_temperature: ["ecu", { c: 0x2a2d31, label: "ECU" }],
    auto_iso16750_temperature_cycling: ["ecu", { c: 0x5a6068, label: "BCM" }],
    food_tuna_ultralow_frozen_storage: ["tuna"], food_blueberry_ln2_quick_freezing: ["blueberries"], food_bull_semen_ln2_vapour_box_freezing: ["straws"],
    env_specimen_bank_ln2_vapour_archive: ["jars"], env_fresh_inp_plate_freezing: ["wellplate"], expansion_b_env_soil_cryogenic_preparation: ["grindjar"],
    geo_sea_ice_column_contaminant_uptake: ["icecolumn"], geo_seawater_nutrient_frozen_storage: ["bottles"], geo_noble_gas_he_ne_cryotrap: ["cryotrap"],
    metro_argon_triple_point_sprt: ["tpcell"], metro_icvgt_3k_to_neon: ["gasbulb"], metro_helium_vapour_pressure_scale: ["gasbulb", { he: true }],
    def_mil810_502_cold_operation_c2: ["radio"], def_mil810_502_munitions_storage_c3: ["munitions"], def_hot_mwir_idca_120k: ["idca"],
  };
  const KEYS = [["qubit|photon", "photonchip"], ["wafer", "wafer300"], ["crystal", "dilatometer"], ["blood|plasma", "bloodbag"], ["cell|bacteria|vial", "cryobox"],
    ["tensile", "dogbone"], ["chip|ic|semi", "icboard"], ["detector|camera|ir", "detchip"], ["food", "blueberries"], ["soil", "grindjar"], ["battery", "pouchcell"]];
  function pick(ex) {
    if (MAP[ex.id]) return MAP[ex.id];
    const t = (ex.id + " " + (ex.name || "") + " " + (ex.sample || "")).toLowerCase();
    for (const [re, k] of KEYS) if (new RegExp(re).test(t)) return [k];
    return ["generic"];
  }

  // ------------------------------------------------------------------ viewer
  let R, S, Cam, Ctl, stage, cur, idle = 0;
  const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function mount(el) {
    if (!T.OrbitControls) return false;
    try { R = new T.WebGLRenderer({ antialias: true, alpha: true }); } catch (e) { return false; }
    R.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2)); R.outputEncoding = T.sRGBEncoding; R.toneMapping = T.ACESFilmicToneMapping; R.toneMappingExposure = 1.05;
    R.shadowMap.enabled = true; R.shadowMap.type = T.PCFSoftShadowMap; R.setClearColor(0, 0);
    R.domElement.style.cssText = "position:absolute;inset:0;width:100%;height:100%;cursor:grab"; el.appendChild(R.domElement);
    S = new T.Scene();
    if (T.RoomEnvironment) S.environment = new T.PMREMGenerator(R).fromScene(new T.RoomEnvironment(), 0.04).texture;
    Cam = new T.PerspectiveCamera(30, 1, 0.02, 30); Cam.position.set(1.35, 1.05, 1.6);
    S.add(new T.HemisphereLight(0xeaf2ff, 0x8a7a66, 0.45));
    const k = new T.DirectionalLight(0xffffff, 1.0); k.position.set(2, 4, 3); k.castShadow = true; k.shadow.mapSize.set(1024, 1024);
    Object.assign(k.shadow.camera, { left: -1.2, right: 1.2, top: 1.2, bottom: -1.2 }); k.shadow.bias = -0.0004; S.add(k);
    const rim = new T.DirectionalLight(0xbcd4ff, 0.6); rim.position.set(-3, 2, -2); S.add(rim);
    // brass turntable
    stage = new T.Group(); S.add(stage);
    const base = new T.Group(); S.add(base);
    const bm = new T.MeshStandardMaterial({ color: 0xc99437, metalness: 0.95, roughness: 0.28 });
    const b1 = new T.Mesh(new T.CylinderGeometry(0.75, 0.8, 0.08, 96), bm); b1.position.y = -0.04; b1.receiveShadow = true; base.add(b1);
    const b2 = new T.Mesh(new T.TorusGeometry(0.77, 0.012, 8, 96), new T.MeshStandardMaterial({ color: 0x8f5f1f, metalness: 0.9, roughness: 0.3 })); b2.rotation.x = Math.PI / 2; base.add(b2);
    for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2, s = new T.Mesh(new T.CylinderGeometry(0.02, 0.02, 0.012, 16), new T.MeshStandardMaterial({ color: 0x2a3038, metalness: 0.8, roughness: 0.3 })); s.position.set(Math.cos(a) * 0.68, 0.005, Math.sin(a) * 0.68); base.add(s); }
    const shadow = new T.Mesh(new T.CircleGeometry(0.74, 64), new T.ShadowMaterial({ opacity: 0.25 })); shadow.rotation.x = -Math.PI / 2; shadow.position.y = 0.001; shadow.receiveShadow = true; base.add(shadow);
    Ctl = new T.OrbitControls(Cam, R.domElement);
    Object.assign(Ctl, { enableDamping: true, enablePan: false, minDistance: 0.9, maxDistance: 4, maxPolarAngle: Math.PI * 0.49, autoRotate: !reduced(), autoRotateSpeed: 2.2 });
    Ctl.target.set(0, 0.18, 0);
    const hold = () => { Ctl.autoRotate = false; idle = performance.now(); };
    R.domElement.addEventListener("pointerdown", hold); R.domElement.addEventListener("wheel", hold, { passive: true });
    const size = () => { const w = el.clientWidth || 360, h = el.clientHeight || 236; R.setSize(w, h, false); Cam.aspect = w / h; Cam.updateProjectionMatrix(); };
    new ResizeObserver(size).observe(el); size();
    const loop = (t) => { requestAnimationFrame(loop);
      if (!Ctl.autoRotate && idle && t - idle > 2500 && !reduced()) { Ctl.autoRotate = true; idle = 0; }
      Ctl.update(); R.render(S, Cam); };
    requestAnimationFrame(loop);
    return true;
  }
  function show(ex) {
    if (!R || !ex || cur === ex.id) return; cur = ex.id;
    stage.children.slice().forEach((c) => { stage.remove(c); c.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } }); });
    G = new T.Group(); const [k, opt] = pick(ex); B[k](opt || {});
    // fit to the turntable
    const bb = new T.Box3().setFromObject(G), sz = bb.getSize(new T.Vector3()), s = Math.min(1.15 / Math.max(sz.x, sz.z, 0.01), 0.9 / Math.max(sz.y, 0.01), 1.6);
    G.scale.setScalar(s); const bb2 = new T.Box3().setFromObject(G), c = bb2.getCenter(new T.Vector3());
    G.position.set(-c.x, -bb2.min.y, -c.z); stage.add(G);
    const hgt = bb2.max.y - bb2.min.y; Ctl.target.set(0, hgt * 0.35, 0);
    const d = 2.35 + hgt * 0.6; Cam.position.set(d * 0.62, 0.95 + hgt * 0.5, d * 0.78); Ctl.update();
  }
  window.Sample3D = { mount, show, pick, kinds: Object.keys(B).filter((k) => k[0] !== "_") };
})();
