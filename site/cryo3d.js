/* CryoLean 3D apparatus viewer (three.js r147, no build step).
   Representative geometry in the same palette and part vocabulary as the Codex frontend scene
   (frontend/src/scene/SceneManager.tsx): steel / white / navy shells, copper and gold cold stages, bolt circles,
   a measurement instrument beside the machine. Shapes are illustrative, not CAD; the sample position is tinted by the
   Lean verdict of the selected pairing. */
(function () {
  const STEEL = 0xa9b7c4, WHITE = 0xd5dee6, NAVY = 0x24324a, COPPER = 0xc89453, GOLD = 0xdeb869, GLASS = 0xbadbdc;
  const VERDICT = { met: 0x2fa35a, fail: 0xd24b4b, info: 0xe0a21f };

  function archetype(c) {
    const f = ((c.family || "") + " " + (c.model || "") + " " + (c.name || "")).toLowerCase();
    const has = (...w) => w.some((x) => f.includes(x));
    if (has("dilution", "bolometer", "cf-1k", "optical_resonator")) return "dilution";
    if (has("probe station", "probe_station")) return "probe_station";
    if (has("frozen sectioning", "microtome")) return "microtome";
    if (has("physical property", "superconducting magnet", "hall_station")) return "magnet";
    if (has("tensile")) return "tensile";
    if (has("cryoablation", "cryoprobe", "nerve")) return "console";
    if (has("microscope", "stage", "calorimeter", "dsc600", "microthermometry")) return "optical_stage";
    if (has("wind_tunnel", "thermal_vacuum", "vacuum_chamber", "facility", "propellant", "guarded", "insulation", "permeation", "srf")) return "chamber";
    if (has("vitrification", "noble_liquid", "neutron", "superconducting_standard", "detector_dewar", "dewar")) return "dewar";
    if (has("freezer", "freeze", "cabinet", "bath", "adsorption", "sorption", "preconcentrator", "mill", "dryer")) return "cabinet";
    return "optical_cryostat";
  }
  const LABEL = { dilution: "Dilution refrigerator", magnet: "Magnet measurement platform", optical_cryostat: "Optical cryostat",
    probe_station: "Cryogenic probe station", optical_stage: "Heating / cooling stage", microtome: "Cryostat microtome",
    chamber: "Cryogenic test chamber", cabinet: "Cryogenic cabinet instrument", dewar: "Liquid-cryogen dewar",
    tensile: "Cryogenic mechanical test frame", console: "Cryoprobe console" };

  let renderer, scene, camera, controls, root, halo, rig, rigPivot, raf = 0, idleT = 0, state = { kind: null, verdict: null, inside: false, id: null, exp: null };
  const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function mat(color, opacity = 1, metal = 0.55, rough = 0.32) {
    return new THREE.MeshStandardMaterial({ color, metalness: metal, roughness: rough, transparent: opacity < 1, opacity,
      side: THREE.DoubleSide, depthWrite: opacity === 1 });
  }
  function add(g, mesh, at) { if (at) mesh.position.set(at[0], at[1], at[2]); mesh.castShadow = mesh.receiveShadow = true; g.add(mesh); return mesh; }
  function cyl(g, at, r, h, color = STEEL, opacity = 1, open = false) {
    return add(g, new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 48, 1, open), mat(color, opacity)), at);
  }
  function box(g, at, s, color = WHITE, opacity = 1, rot) {
    const m = add(g, new THREE.Mesh(new THREE.BoxGeometry(s[0], s[1], s[2]), mat(color, opacity, 0.24, 0.38)), at);
    if (rot) m.rotation.set(rot[0], rot[1], rot[2]);
    return m;
  }
  function ring(g, at, r, color = STEEL, rot = [Math.PI / 2, 0, 0], tube = 0.025) {
    const m = add(g, new THREE.Mesh(new THREE.TorusGeometry(r, tube, 8, 56), mat(color, 1, 0.75, 0.25)), at);
    m.rotation.set(rot[0], rot[1], rot[2]);
    return m;
  }
  function bolts(g, y, r, n = 10) { for (let i = 0; i < n; i++) cyl(g, [Math.cos(i / n * Math.PI * 2) * r, y, Math.sin(i / n * Math.PI * 2) * r], 0.025, 0.04, NAVY); }
  function wire(g, pts, color = COPPER, r = 0.012) {
    const curve = new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(p[0], p[1], p[2])));
    return add(g, new THREE.Mesh(new THREE.TubeGeometry(curve, 48, r, 8, false), mat(color, 1, 0.5, 0.4)));
  }
  function instrument(g, at, color = NAVY) {
    const s = new THREE.Group(); s.position.set(at[0], at[1], at[2]); g.add(s);
    box(s, [0, 0, 0], [0.6, 0.32, 0.44]); box(s, [0, 0, 0.23], [0.5, 0.22, 0.02], color);
    box(s, [-0.08, 0.015, 0.245], [0.22, 0.09, 0.008], 0x8cb4b9); cyl(s, [0.19, -0.02, 0.25], 0.045, 0.03);
    box(s, [0, -0.18, 0], [0.42, 0.04, 0.28], NAVY);
  }
  function sample(g, at, size, verdict) {
    const c = VERDICT[verdict] || GOLD;
    const m = sampleM = add(g, new THREE.Mesh(new THREE.BoxGeometry(size[0], size[1], size[2]),
      new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 0.35, metalness: 0.2, roughness: 0.4 })), at);
    halo = new THREE.Mesh(new THREE.SphereGeometry(Math.max(size[0], size[2]) * 1.4, 24, 16),
      new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: 0.16, depthTest: false }));
    halo.position.copy(m.position); g.add(halo);
    return m;
  }

  const BUILD = {
    magnet(g, inside, v) {
      cyl(g, [0, -0.85, 0], 0.87, 0.16, NAVY); cyl(g, [0, -0.05, 0], 0.77, 1.52, WHITE, inside ? 0.14 : 1, inside);
      cyl(g, [0, 0.76, 0], 0.83, 0.12); bolts(g, 0.84, 0.7); cyl(g, [0, 0.86, 0], 0.22, 0.1, NAVY); cyl(g, [0, 1.03, 0], 0.11, 0.28);
      const h = new THREE.Group(); h.position.set(-0.45, 0.94, -0.1); g.add(h); cyl(h, [0, 0, 0], 0.16, 0.26); box(h, [0, 0.18, 0], [0.25, 0.12, 0.23], NAVY);
      wire(h, [[0, 0.16, 0], [-0.3, 0.3, 0], [-0.7, 0.1, 0], [-0.9, -1.3, -0.1]], 0x647487, 0.03);
      for (let i = 0; i < 16; i++) ring(g, [0, -0.6 + i * 0.045, 0], 0.48, COPPER);
      cyl(g, [0, 0.1, 0], 0.16, 1.28, STEEL, 0.25, true); cyl(g, [0, -0.48, 0], 0.16, 0.1, GOLD);
      sample(g, [0, -0.41, 0], [0.12, 0.03, 0.12], v);
      [-0.55, 0.55].forEach((x) => [-0.45, 0.45].forEach((z) => box(g, [x, -1.04, z], [0.12, 0.3, 0.12], NAVY)));
      instrument(g, [1.3, -0.68, 0.2]); wire(g, [[0.1, 1, 0], [0.8, 1.1, -0.1], [1.4, 0.55, 0], [1.35, -0.6, 0.2]], NAVY, 0.02);
      return [0, -0.41, 0];
    },
    dilution(g, inside, v) {
      cyl(g, [0, 1.1, 0], 0.85, 0.13); bolts(g, 1.19, 0.72);
      cyl(g, [0, -0.05, 0], 0.78, 2.15, WHITE, inside ? 0.12 : 0.97, inside);
      [0.75, 0.25, -0.2, -0.65].forEach((y, i) => { cyl(g, [0, y, 0], 0.69 - i * 0.105, 0.06, i < 2 ? STEEL : COPPER); bolts(g, y + 0.04, 0.58 - i * 0.105, 8); });
      [0, 2.09, 4.19].forEach((a) => { cyl(g, [Math.cos(a) * 0.54, 0.4, Math.sin(a) * 0.54], 0.025, 1.3); cyl(g, [Math.cos(a) * 0.28, -0.42, Math.sin(a) * 0.28], 0.018, 0.5, COPPER); });
      cyl(g, [0, -0.8, 0], 0.18, 0.2, GOLD);
      for (let i = 0; i < 12; i++) { const x = -0.32 + (i % 6) * 0.12, z = i < 6 ? -0.1 : 0.16; wire(g, [[x, 1.17, z], [x, 0.78, z], [x * 0.85, 0.25, z], [x * 0.65, -0.25, z], [x * 0.4, -0.66, z], [x * 0.25, -0.9, z]], i % 3 ? COPPER : 0x9fa9ba, 0.008); }
      cyl(g, [-0.4, 1.35, 0], 0.17, 0.38, NAVY); cyl(g, [0.34, 1.28, 0], 0.12, 0.22);
      sample(g, [0, -0.95, 0], [0.16, 0.05, 0.16], v);
      return [0, -0.95, 0];
    },
    optical_cryostat(g, inside, v) { return cryostat(g, inside, v, false); },
    probe_station(g, inside, v) { return cryostat(g, inside, v, true); },
    optical_stage(g, inside, v) {
      box(g, [0, -0.75, 0], [1.8, 0.18, 1.4], NAVY); box(g, [0, -0.36, 0], [1.15, 0.4, 0.9], STEEL);
      cyl(g, [0, -0.11, 0], 0.51, 0.16, NAVY); cyl(g, [0, 0.03, 0], 0.45, 0.12, STEEL, inside ? 0.25 : 1);
      cyl(g, [0, 0.06, 0], 0.22, 0.13, COPPER); bolts(g, 0.115, 0.36, 8);
      cyl(g, [0, 0.78, 0], 0.13, 0.42, NAVY); cyl(g, [0, 0.51, 0], 0.09, 0.14);
      box(g, [0.65, 0.16, -0.35], [0.17, 1.7, 0.2]); box(g, [0.3, 1.05, -0.18], [0.85, 0.15, 0.4]);
      wire(g, [[-0.5, -0.3, 0], [-0.9, -0.35, 0], [-1, -0.5, -0.5]], 0x8199aa, 0.03); instrument(g, [1.15, -0.55, 0.25]);
      sample(g, [0, 0.15, 0], [0.2, 0.02, 0.14], v);
      return [0, 0.15, 0];
    },
    microtome(g, inside, v) {
      box(g, [0, -0.48, 0], [1.55, 1.28, 1.25]); box(g, [0, -0.4, 0.64], [1.38, 0.9, 0.03], 0xc8d5dc);
      box(g, [0, 0.18, 0], [1.5, 0.1, 1.3], NAVY); box(g, [0, 0.22, 0.1], [1.25, 0.1, 1.02], STEEL);
      box(g, [0, 0.45, -0.44], [1.45, 0.55, 0.16]);
      if (!inside) box(g, [0, 0.48, 0.02], [1.35, 0.04, 1.03], 0xd1e6ef, 0.35, [-0.3, 0, 0]);
      cyl(g, [0.18, 0.31, -0.12], 0.18, 0.16); box(g, [0.18, 0.34, 0.2], [0.53, 0.04, 0.12], STEEL, 1, [0.2, 0, 0]);
      box(g, [-0.4, 0.33, 0.1], [0.2, 0.04, 0.3], 0xe3eee7); ring(g, [0.91, 0, 0], 0.27, NAVY, [0, Math.PI / 2, 0]);
      box(g, [-0.3, 0.8, -0.47], [0.46, 0.27, 0.08], NAVY); box(g, [-0.3, 0.8, -0.42], [0.34, 0.15, 0.01], 0x91b8c4);
      [-0.55, 0.55].forEach((x) => [-0.4, 0.4].forEach((z) => cyl(g, [x, -1.16, z], 0.08, 0.13, NAVY)));
      sample(g, [0.18, 0.43, -0.12], [0.18, 0.1, 0.12], v);
      return [0.18, 0.43, -0.12];
    },
    chamber(g, inside, v) {
      const shell = cyl(g, [0, 0.05, 0], 0.82, 2.3, WHITE, inside ? 0.13 : 1, inside); shell.rotation.z = Math.PI / 2;
      const door = cyl(g, [1.18, 0.05, 0], 0.88, 0.1, NAVY); door.rotation.z = Math.PI / 2;
      const back = cyl(g, [-1.18, 0.05, 0], 0.86, 0.08); back.rotation.z = Math.PI / 2;
      for (let i = 0; i < 9; i++) ring(g, [-0.95 + i * 0.24, 0.05, 0], 0.66, COPPER, [0, Math.PI / 2, 0], 0.018);
      box(g, [0, -0.38, 0], [1.4, 0.05, 0.7], STEEL); cyl(g, [0, -0.25, 0], 0.18, 0.2, COPPER);
      [-0.7, 0.7].forEach((x) => [-0.45, 0.45].forEach((z) => box(g, [x, -0.95, z], [0.12, 0.5, 0.12], NAVY)));
      [-0.4, 0.3].forEach((x) => cyl(g, [x, 0.95, 0], 0.11, 0.25));
      cyl(g, [-0.4, 1.12, 0], 0.15, 0.08, NAVY);
      wire(g, [[0.3, 1.05, 0], [0.9, 1.25, 0.2], [1.5, 0.4, 0.5], [1.55, -0.6, 0.5]], NAVY, 0.022); instrument(g, [1.55, -0.85, 0.55]);
      sample(g, [0, -0.08, 0], [0.22, 0.14, 0.22], v);
      return [0, -0.08, 0];
    },
    cabinet(g, inside, v) {
      box(g, [0, -0.35, 0], [1.5, 1.3, 1.05]); box(g, [0, 0.33, 0], [1.56, 0.08, 1.1], NAVY);
      box(g, [0, -0.3, 0.53], [1.3, 1.0, 0.03], 0xc8d5dc, inside ? 0.25 : 1);
      box(g, [0.45, 0.15, 0.55], [0.36, 0.18, 0.02], NAVY); box(g, [0.45, 0.15, 0.565], [0.26, 0.1, 0.005], 0x91b8c4);
      box(g, [0, -0.3, 0.1], [1.2, 0.9, 0.7], STEEL, inside ? 0.35 : 1);
      [-0.5, -0.15, 0.2].forEach((y) => box(g, [0, y - 0.3, 0.1], [1.1, 0.02, 0.6], STEEL));
      cyl(g, [-1.25, -0.4, -0.1], 0.3, 1.2, WHITE); cyl(g, [-1.25, 0.24, -0.1], 0.12, 0.1, NAVY);
      wire(g, [[-1.25, 0.28, -0.1], [-1.0, 0.5, -0.1], [-0.6, 0.4, -0.2]], STEEL, 0.03);
      [-0.6, 0.6].forEach((x) => [-0.4, 0.4].forEach((z) => cyl(g, [x, -1.05, z], 0.07, 0.1, NAVY)));
      sample(g, [0, -0.35, 0.2], [0.26, 0.12, 0.18], v);
      return [0, -0.35, 0.2];
    },
    dewar(g, inside, v) {
      cyl(g, [0, -0.1, 0], 0.55, 1.9, WHITE, inside ? 0.14 : 1, inside); cyl(g, [0, 0.88, 0], 0.6, 0.1, NAVY); bolts(g, 0.94, 0.5, 8);
      cyl(g, [0, -0.1, 0], 0.42, 1.7, STEEL, inside ? 0.18 : 0.0001, true);
      cyl(g, [0, 0.35, 0], 0.035, 1.6); cyl(g, [0, 1.2, 0], 0.09, 0.2, NAVY);
      cyl(g, [0, -0.62, 0], 0.4, 0.4, 0x9cc3d5, inside ? 0.35 : 0.0001);
      [0, 2.09, 4.19].forEach((a) => box(g, [Math.cos(a) * 0.5, -1.13, Math.sin(a) * 0.5], [0.12, 0.16, 0.12], NAVY));
      wire(g, [[0.05, 1.2, 0], [0.6, 1.3, 0.1], [1.1, 0.4, 0.2], [1.15, -0.65, 0.2]], NAVY, 0.02); instrument(g, [1.15, -0.85, 0.25]);
      sample(g, [0, -0.5, 0], [0.12, 0.08, 0.12], v);
      return [0, -0.5, 0];
    },
    tensile(g, inside, v) {
      box(g, [0, -1.0, 0], [1.6, 0.25, 0.8], NAVY); [-0.55, 0.55].forEach((x) => cyl(g, [x, 0.15, 0], 0.07, 2.1));
      box(g, [0, 1.1, 0], [1.4, 0.2, 0.5], NAVY); box(g, [0, 0.55, 0], [1.25, 0.16, 0.42], STEEL);
      cyl(g, [0, 0.25, 0], 0.06, 0.5); cyl(g, [0, -0.45, 0], 0.06, 0.6);
      cyl(g, [0, -0.15, 0], 0.36, 0.9, WHITE, inside ? 0.15 : 1, inside); cyl(g, [0, 0.31, 0], 0.4, 0.06, NAVY);
      instrument(g, [1.3, -0.7, 0.2]); wire(g, [[0.3, 0.55, 0], [0.9, 0.7, 0.2], [1.3, -0.5, 0.2]], NAVY, 0.02);
      sample(g, [0, -0.15, 0], [0.06, 0.34, 0.06], v);
      return [0, -0.15, 0];
    },
    console(g, inside, v) {
      box(g, [-0.3, -0.45, 0], [0.9, 1.2, 0.7]); box(g, [-0.3, 0.2, 0], [0.95, 0.1, 0.75], NAVY);
      box(g, [-0.3, 0.45, -0.2], [0.6, 0.4, 0.06], NAVY); box(g, [-0.3, 0.45, -0.165], [0.5, 0.3, 0.01], 0x91b8c4);
      cyl(g, [-0.95, -0.4, 0], 0.18, 1.1, STEEL); [-0.6, 0].forEach((x) => [-0.3, 0.3].forEach((z) => cyl(g, [x, -1.1, z], 0.06, 0.08, NAVY)));
      wire(g, [[0.15, -0.1, 0.2], [0.6, 0.1, 0.4], [0.9, 0.3, 0.3], [1.05, 0.25, 0]], 0x8199aa, 0.025);
      const pen = cyl(g, [1.25, 0.15, 0], 0.045, 0.5); pen.rotation.z = Math.PI / 2.6;
      sample(g, [1.47, 0.06, 0], [0.05, 0.05, 0.05], v);
      return [1.47, 0.06, 0];
    },
  };
  function cryostat(g, inside, v, probe) {
    cyl(g, [0, -0.83, 0], probe ? 0.9 : 0.48, 0.16, NAVY);
    cyl(g, [0, -0.05, 0], probe ? 0.78 : 0.42, probe ? 0.72 : 1.4, WHITE, inside ? 0.17 : 1, inside);
    cyl(g, [0, probe ? 0.36 : 0.71, 0], probe ? 0.83 : 0.48, 0.08); bolts(g, probe ? 0.42 : 0.77, probe ? 0.7 : 0.38);
    cyl(g, [0, -0.3, 0], 0.15, 0.65, COPPER); cyl(g, [0, 0.05, 0], 0.23, 0.04, GOLD);
    if (probe) {
      ring(g, [0, 0.44, 0], 0.29, NAVY);
      for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2, s = new THREE.Group(); s.rotation.y = a; g.add(s);
        box(s, [0.55, 0.1, 0], [0.35, 0.12, 0.17], NAVY); wire(s, [[0.45, 0.13, 0], [0.18, 0.15, 0], [0.07, 0.09, 0]], COPPER, 0.01); }
    } else {
      [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2].forEach((a) => { const s = new THREE.Group(); s.rotation.y = a; g.add(s);
        ring(s, [0, 0.1, 0.44], 0.17, NAVY, [0, 0, 0]); box(s, [0, 0.1, 0.45], [0.25, 0.25, 0.008], GLASS, 0.35); });
    }
    cyl(g, [-0.5, -0.3, -0.25], 0.16, 0.9); instrument(g, [1.1, -0.65, 0.25]);
    sample(g, [0, 0.09, 0], [0.14, 0.03, 0.14], v);
    return [0, 0.09, 0];
  }


  // ---------------------------------------------------------------- per-machine variation + detail
  // Every catalog machine gets its own deterministic look (seeded by its id): proportions, trim colours, port count,
  // gauges, valves, feedthrough racks, compressor / pump, hose bundles, nameplate. Still illustrative, not CAD.
  function hash(str) { let h = 2166136261; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rng(seed) { let a = seed || 1; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const TRIMS = [0x24324a, 0x1d4e75, 0x6b2a35, 0x2a5a44, 0x4d3f78, 0x7a4f1c, 0x2b2b2b, 0x135e66, 0x8f3a26, 0x3d5268];
  const SHELLS = [0xd5dee6, 0xe9ecef, 0xc9d3dc, 0xb9c4cc, 0xeee6d8, 0xdfe7e1, 0xd8dbe8];
  function variant(id) {
    const r = rng(hash(id || "x"));
    return { r, trim: TRIMS[Math.floor(r() * TRIMS.length)], shell: SHELLS[Math.floor(r() * SHELLS.length)],
      sx: 0.86 + r() * 0.3, sy: 0.85 + r() * 0.32, ports: 2 + Math.floor(r() * 5), gauges: 1 + Math.floor(r() * 3),
      valves: Math.floor(r() * 4), rack: r() < 0.65, pump: r() < 0.55, compressor: r() < 0.5, hoses: 1 + Math.floor(r() * 3),
      side: r() < 0.5 ? -1 : 1, plate: r() };
  }
  function gauge(g, at, face, trim) {
    const s = new THREE.Group(); s.position.set(at[0], at[1], at[2]); s.rotation.y = face; g.add(s);
    cyl(s, [0, -0.1, 0], 0.015, 0.2, STEEL);
    const d = cyl(s, [0, 0.03, 0], 0.075, 0.035, trim); d.rotation.x = Math.PI / 2;
    const f = cyl(s, [0, 0.03, 0.019], 0.062, 0.004, 0xf4f4ee); f.rotation.x = Math.PI / 2;
    box(s, [0.018, 0.045, 0.024], [0.045, 0.006, 0.003], 0xc0392b, 1, [0, 0, 0.7]);
    for (let i = 0; i < 8; i++) { const a = -2.2 + i * 0.63; box(s, [Math.sin(a) * 0.05, 0.03 + Math.cos(a) * 0.05, 0.022], [0.003, 0.012, 0.002], NAVY, 1, [0, 0, -a]); }
  }
  function valve(g, at, trim) {
    const s = new THREE.Group(); s.position.set(at[0], at[1], at[2]); g.add(s);
    const b = cyl(s, [0, 0, 0], 0.04, 0.16, STEEL); b.rotation.z = Math.PI / 2;
    cyl(s, [0, 0.07, 0], 0.012, 0.1, STEEL); const h = add(s, new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.01, 8, 24), mat(trim, 1, 0.3, 0.5)), [0, 0.13, 0]); h.rotation.x = Math.PI / 2;
    [-0.09, 0.09].forEach((x) => { const f = cyl(s, [x, 0, 0], 0.055, 0.02, STEEL); f.rotation.z = Math.PI / 2; });
  }
  function feedRack(g, at, n, trim) {
    const s = new THREE.Group(); s.position.set(at[0], at[1], at[2]); g.add(s);
    box(s, [0, 0, 0], [0.08 + n * 0.09, 0.07, 0.12], trim);
    for (let i = 0; i < n; i++) { const x = -n * 0.045 + 0.045 + i * 0.09;
      cyl(s, [x, 0.07, 0], 0.03, 0.08, i % 2 ? GOLD : STEEL); cyl(s, [x, 0.12, 0], 0.022, 0.02, NAVY); }
  }
  function compressor(g, at, trim, label) {
    const s = new THREE.Group(); s.position.set(at[0], at[1], at[2]); g.add(s);
    box(s, [0, 0, 0], [0.55, 0.62, 0.45], WHITE); box(s, [0, 0.33, 0], [0.57, 0.04, 0.47], trim);
    for (let i = 0; i < 7; i++) box(s, [0, -0.2 + i * 0.06, 0.226], [0.42, 0.02, 0.005], 0x8795a3);
    box(s, [0.17, 0.2, 0.228], [0.12, 0.07, 0.004], 0x1c2a3a); box(s, [0.17, 0.2, 0.231], [0.09, 0.04, 0.002], label);
    [-0.12, 0.12].forEach((x) => cyl(s, [x, 0.4, 0.1], 0.03, 0.1, GOLD));
    [-0.2, 0.2].forEach((x) => [-0.16, 0.16].forEach((z) => cyl(s, [x, -0.34, z], 0.035, 0.05, NAVY)));
  }
  function pump(g, at, trim) {
    const s = new THREE.Group(); s.position.set(at[0], at[1], at[2]); g.add(s);
    const m = cyl(s, [0, 0, 0], 0.11, 0.38, trim); m.rotation.z = Math.PI / 2;
    for (let i = 0; i < 6; i++) ring(s, [-0.14 + i * 0.056, 0, 0], 0.115, STEEL, [0, Math.PI / 2, 0], 0.008);
    box(s, [0, -0.13, 0], [0.42, 0.04, 0.22], NAVY); cyl(s, [0.05, 0.16, 0], 0.045, 0.12, STEEL); cyl(s, [0.05, 0.23, 0], 0.07, 0.02, STEEL);
  }
  function decorate(g, v, bb) {
    // gauges / valves / feedthroughs stand ON the machine's top plate (inside its footprint); pump + compressor on the floor
    const r = v.r, top = bb.max.y, cx = (bb.min.x + bb.max.x) / 2, cz = (bb.min.z + bb.max.z) / 2;
    const rx = Math.min(0.32, (bb.max.x - bb.min.x) * 0.25), rz = Math.min(0.3, (bb.max.z - bb.min.z) * 0.25), FLOOR = -1.23;
    for (let i = 0; i < v.gauges; i++) gauge(g, [cx + v.side * rx * (0.3 + 0.35 * i), top + 0.1, cz + rz * 0.6], v.side * 0.4, v.trim);
    for (let i = 0; i < v.valves; i++) valve(g, [cx - v.side * rx * (0.2 + 0.4 * i), top + 0.04, cz - rz * 0.7], v.trim);
    if (v.rack) feedRack(g, [cx, top + 0.035, cz - rz * 0.1], Math.min(v.ports, 4), v.trim);
    if (v.compressor) { const px = cx - v.side * ((bb.max.x - bb.min.x) / 2 + 0.45), pz = cz - 0.55;
      compressor(g, [px, FLOOR + 0.31, pz], v.trim, [0x6fe08a, 0x7cc4ff, 0xffd66b][Math.floor(r() * 3)]);
      for (let h = 0; h < v.hoses; h++) wire(g, [[px + (h - 1) * 0.1, FLOOR + 0.72, pz + 0.1], [px * 0.8, top + 0.15 + h * 0.06, pz * 0.6],
        [cx - v.side * rx * 0.5, top + 0.12, cz - rz * 0.3 + h * 0.05], [cx - v.side * rx * 0.3, top + 0.01, cz - rz * 0.3 + h * 0.05]], h % 2 ? 0x9aa7b4 : 0x5d6b78, 0.02); }
    if (v.pump) { const px = cx + v.side * ((bb.max.x - bb.min.x) / 2 + 0.2), pz = cz - 0.6;
      pump(g, [px, FLOOR + 0.15, pz], v.trim); wire(g, [[px, FLOOR + 0.35, pz], [px - v.side * 0.1, (FLOOR + top) / 2, pz * 0.8], [cx + v.side * rx, top - 0.05, cz - rz]], STEEL, 0.025); }
  }

  // ---------------------------------------------------------------- experiment sample rig (spins)
  const RIGS = ["chip", "wafer", "vials", "cassette", "crystal", "coupon", "fiber", "cuvette", "qubit", "foam"];
  function rigKind(ex) {
    const t = ((ex && (ex.id + " " + (ex.name || "") + " " + (ex.sample || ""))) || "").toLowerCase();
    const has = (...w) => w.some((x) => t.includes(x));
    if (has("qubit", "quantum", "transmon", "josephson")) return "qubit";
    if (has("wafer", "semiconductor", "photonic", "led", "solar")) return "wafer";
    if (has("cell", "embryo", "oocyte", "sperm", "vial", "plasma", "serum", "vaccine", "biobank", "blood", "stem")) return "vials";
    if (has("tissue", "section", "biopsy", "histo", "brain", "organ")) return "cassette";
    if (has("crystal", "protein", "diffraction", "x-ray", "xray", "mineral", "ice")) return "crystal";
    if (has("tensile", "fatigue", "fracture", "weld", "alloy", "steel", "composite", "mechanical")) return "coupon";
    if (has("fiber", "fibre", "laser", "optical", "raman", "spectro", "photolum")) return "fiber";
    if (has("liquid", "hydrogen", "methane", "fuel", "propellant", "lng", "solution")) return "cuvette";
    if (has("insulation", "foam", "food", "polymer")) return "foam";
    if (has("resist", "hall", "transport", "superconduct", "magnet", "film")) return "chip";
    return RIGS[hash(t) % RIGS.length];
  }
  function buildRig(kind, c) {
    const g = new THREE.Group(), em = (col, e = 0.25) => new THREE.MeshStandardMaterial({ color: col, emissive: col, emissiveIntensity: e, metalness: 0.3, roughness: 0.35 });
    const m = (geo, material, at, rot) => { const o = new THREE.Mesh(geo, material); if (at) o.position.set(...at); if (rot) o.rotation.set(...rot); g.add(o); return o; };
    if (kind === "chip" || kind === "qubit") {
      m(new THREE.BoxGeometry(0.34, 0.025, 0.34), mat(GOLD, 1, 0.9, 0.2));
      m(new THREE.BoxGeometry(0.16, 0.02, 0.16), em(kind === "qubit" ? 0x5a6cff : 0x2c3e50, 0.15), [0, 0.022, 0]);
      for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2, r1 = 0.15, r0 = 0.085;
        m(new THREE.BoxGeometry(0.02, 0.004, 0.03), mat(GOLD, 1, 0.9, 0.2), [Math.cos(a) * r1, 0.016, Math.sin(a) * r1], [0, -a, 0]);
        const cur = new THREE.QuadraticBezierCurve3(new THREE.Vector3(Math.cos(a) * r0, 0.033, Math.sin(a) * r0), new THREE.Vector3(Math.cos(a) * 0.12, 0.07, Math.sin(a) * 0.12), new THREE.Vector3(Math.cos(a) * r1, 0.02, Math.sin(a) * r1));
        m(new THREE.TubeGeometry(cur, 10, 0.0025, 4), mat(0xe8e8e8, 1, 1, 0.2)); }
      if (kind === "qubit") for (let i = 0; i < 6; i++) m(new THREE.TorusGeometry(0.018, 0.004, 6, 18), em(c, 0.6), [-0.05 + (i % 3) * 0.05, 0.034, -0.025 + Math.floor(i / 3) * 0.05], [Math.PI / 2, 0, 0]);
    } else if (kind === "wafer") {
      m(new THREE.CylinderGeometry(0.2, 0.2, 0.012, 64), mat(0x5c6a80, 1, 0.95, 0.12));
      for (let i = -3; i <= 3; i++) for (let j = -3; j <= 3; j++) if (i * i + j * j < 11) m(new THREE.BoxGeometry(0.042, 0.004, 0.042), em(((i + j) & 1) ? 0x7c5cff : c, 0.3), [i * 0.05, 0.008, j * 0.05]);
    } else if (kind === "vials") {
      m(new THREE.BoxGeometry(0.4, 0.04, 0.3), mat(0x2b5f9e, 1, 0.2, 0.6));
      for (let i = 0; i < 12; i++) { const x = -0.15 + (i % 4) * 0.1, z = -0.1 + Math.floor(i / 4) * 0.1;
        m(new THREE.CylinderGeometry(0.03, 0.03, 0.16, 18), mat(0xe8f4ff, 0.55, 0.1, 0.1), [x, 0.1, z]);
        m(new THREE.CylinderGeometry(0.026, 0.026, 0.08, 18), em(i % 3 ? 0xf2c14e : c, 0.3), [x, 0.06, z]);
        m(new THREE.CylinderGeometry(0.034, 0.034, 0.035, 18), mat([0xd63c3c, 0x3c8dd6, 0x3cd67a][i % 3], 1, 0.1, 0.5), [x, 0.195, z]); }
    } else if (kind === "cassette") {
      m(new THREE.BoxGeometry(0.34, 0.07, 0.26), mat(0x2f9e8f, 1, 0.1, 0.5));
      for (let i = 0; i < 9; i++) m(new THREE.BoxGeometry(0.28, 0.072, 0.01), mat(0x1f6e64, 1, 0.1, 0.5), [0, 0, -0.11 + i * 0.0275]);
      m(new THREE.SphereGeometry(0.07, 24, 16), em(0xd98c8c, 0.2), [0, 0.06, 0]).scale.set(1.4, 0.45, 1);
      m(new THREE.CylinderGeometry(0.01, 0.01, 0.4, 8), mat(STEEL), [0.14, 0.2, 0], [0, 0, 0.9]);
    } else if (kind === "crystal") {
      m(new THREE.CylinderGeometry(0.06, 0.08, 0.06, 6), mat(STEEL));
      m(new THREE.CylinderGeometry(0.008, 0.008, 0.2, 8), mat(STEEL), [0, 0.13, 0]);
      const x = m(new THREE.OctahedronGeometry(0.075, 0), new THREE.MeshPhysicalMaterial({ color: c, transmission: 0.6, roughness: 0.05, metalness: 0, transparent: true, opacity: 0.85, emissive: c, emissiveIntensity: 0.25 }), [0, 0.28, 0]);
      x.scale.set(1, 1.5, 0.8);
      m(new THREE.TorusGeometry(0.04, 0.005, 8, 24), mat(0xb0b0b0), [0, 0.24, 0], [Math.PI / 2, 0, 0]);
    } else if (kind === "coupon") {
      const shape = new THREE.Shape(); shape.moveTo(-0.2, -0.05); shape.lineTo(-0.1, -0.05); shape.quadraticCurveTo(-0.06, -0.02, -0.05, -0.02); shape.lineTo(0.05, -0.02); shape.quadraticCurveTo(0.06, -0.02, 0.1, -0.05); shape.lineTo(0.2, -0.05); shape.lineTo(0.2, 0.05); shape.lineTo(0.1, 0.05); shape.quadraticCurveTo(0.06, 0.02, 0.05, 0.02); shape.lineTo(-0.05, 0.02); shape.quadraticCurveTo(-0.06, 0.02, -0.1, 0.05); shape.lineTo(-0.2, 0.05); shape.closePath();
      m(new THREE.ExtrudeGeometry(shape, { depth: 0.02, bevelEnabled: false }), mat(0xb8c2cc, 1, 0.9, 0.25), [0, 0, -0.01]);
      m(new THREE.BoxGeometry(0.04, 0.02, 0.025), em(c, 0.5), [0, 0, 0.004]);
      [-0.17, 0.17].forEach((x) => m(new THREE.BoxGeometry(0.07, 0.14, 0.06), mat(NAVY), [x, 0, 0]));
    } else if (kind === "fiber") {
      m(new THREE.CylinderGeometry(0.12, 0.12, 0.05, 40), mat(0x30363d, 1, 0.4, 0.5));
      for (let i = 0; i < 5; i++) m(new THREE.TorusGeometry(0.13 + i * 0.006, 0.004, 6, 60), em(i % 2 ? c : 0xff7a3c, 0.5), [0, -0.015 + i * 0.008, 0], [Math.PI / 2, 0, 0]);
      m(new THREE.CylinderGeometry(0.02, 0.02, 0.12, 16), mat(GOLD, 1, 0.9, 0.2), [0, 0.08, 0]);
      m(new THREE.ConeGeometry(0.035, 0.05, 16), em(0xff3c3c, 0.8), [0, 0.16, 0]);
    } else if (kind === "cuvette") {
      m(new THREE.BoxGeometry(0.12, 0.26, 0.12), mat(0xdff3ff, 0.35, 0.05, 0.05), [0, 0.13, 0]);
      m(new THREE.BoxGeometry(0.105, 0.17, 0.105), em(c, 0.35), [0, 0.09, 0]).material.transparent = true;
      for (let i = 0; i < 7; i++) m(new THREE.SphereGeometry(0.01 + (i % 3) * 0.004, 10, 8), mat(0xffffff, 0.7, 0, 0.1), [(i % 3 - 1) * 0.03, 0.05 + i * 0.022, ((i * 7) % 3 - 1) * 0.02]);
      m(new THREE.BoxGeometry(0.14, 0.02, 0.14), mat(NAVY), [0, 0.27, 0]);
    } else {
      const f = m(new THREE.BoxGeometry(0.3, 0.12, 0.22), mat(0xf2e6c9, 1, 0, 0.9)); f.material.color.lerp(new THREE.Color(c), 0.25);
      for (let i = 0; i < 20; i++) m(new THREE.SphereGeometry(0.012, 8, 6), mat(0xd9caa5, 1, 0, 0.9), [(Math.sin(i * 12.9) * 0.13), 0.06, (Math.cos(i * 7.3) * 0.09)]);
      m(new THREE.CylinderGeometry(0.006, 0.006, 0.18, 6), mat(COPPER), [0.1, 0.1, 0], [0, 0, 0.4]);
    }
    return g;
  }

  function init(el) {
    if (!window.THREE || !THREE.OrbitControls) return false;
    try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); } catch (e) { return false; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
    renderer.outputEncoding = THREE.sRGBEncoding; renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);
    scene = new THREE.Scene();
    if (THREE.RoomEnvironment) scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new THREE.RoomEnvironment(), 0.04).texture;
    camera = new THREE.PerspectiveCamera(37, 1, 0.05, 50); camera.position.set(3.35, 1.95, 4.8);
    scene.add(new THREE.AmbientLight(0xffffff, 0.22)); scene.add(new THREE.HemisphereLight(0xe4edfa, 0x8e8a8a, 0.4));
    const key = new THREE.DirectionalLight(0xffffff, 0.85); key.position.set(3, 6, 4); key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0005; Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3 }); scene.add(key);
    const fill = new THREE.DirectionalLight(0xd7d8f5, 0.5); fill.position.set(-4, 2, -1); scene.add(fill);
    const ground = new THREE.Mesh(new THREE.CircleGeometry(4, 64), new THREE.ShadowMaterial({ opacity: 0.12 }));
    ground.rotation.x = -Math.PI / 2; ground.position.y = -1.23; ground.receiveShadow = true; scene.add(ground);
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    Object.assign(controls, { enableDamping: true, minDistance: 1.4, maxDistance: 11, maxPolarAngle: Math.PI * 0.85, autoRotateSpeed: 0.7 });
    controls.autoRotate = !reduced();
    // turntable: the machine keeps spinning; dragging pauses it and it resumes 3 s after the last interaction
    const hold = () => { controls.autoRotate = false; idleT = performance.now(); };
    renderer.domElement.addEventListener("pointerdown", hold); renderer.domElement.addEventListener("wheel", hold, { passive: true });
    new ResizeObserver(() => size(el)).observe(el); size(el);
    const loop = (t) => { raf = requestAnimationFrame(loop); controls.update();
      if (halo && !reduced()) halo.material.opacity = 0.1 + 0.08 * (1 + Math.sin(t / 420));
      if (!reduced()) {
        if (!controls.autoRotate && idleT && t - idleT > 3000) { controls.autoRotate = true; idleT = 0; }
        if (rig) { rig.rotation.y += 0.022; rig.position.y = 0.04 * Math.sin(t / 650); }
      }
      runTick(t);
      renderer.render(scene, camera); };
    raf = requestAnimationFrame(loop);
    return true;
  }
  function size(el) {
    const w = el.clientWidth || 300, h = el.clientHeight || 260;
    renderer.setSize(w, h, false); renderer.domElement.style.width = "100%"; renderer.domElement.style.height = "100%";
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  function build() {
    if (root) { scene.remove(root); root.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); }); }
    root = new THREE.Group(); scene.add(root);
    const target = assemble(root, state.kind, state.inside, state.verdict, state.id);
    rig = null;
    const bb = new THREE.Box3().setFromObject(root), c = bb.getCenter(new THREE.Vector3());
    root.position.x = -c.x; root.position.z = -c.z;
    controls.target.set(0, state.inside ? target[1] * 0.6 : c.y, 0); controls.update();
    if (runState) runStage(runState);   // the rebuilt sample/halo pick up the current stage colours
  }

  function assemble(g, kind, inside, verdict, id) {
    const v = variant(id || kind);
    const inner = new THREE.Group(); g.add(inner);
    const target = BUILD[kind](inner, inside, verdict);
    // recolour shells / trims for this machine (sample + halo keep the verdict colour)
    inner.traverse((o) => { if (!o.isMesh || o === halo || !o.material || !o.material.color) return;
      const hx = o.material.color.getHex();
      if (hx === new THREE.Color(WHITE).convertSRGBToLinear().getHex() || hx === WHITE) o.material.color.setHex(v.shell);
      else if (hx === NAVY) o.material.color.setHex(v.trim); });
    inner.scale.set(v.sx, v.sy, v.sx);
    const t = [target[0] * v.sx, target[1] * v.sy, target[2] * v.sx];
    inner.updateMatrixWorld(true);
    const bb = new THREE.Box3().setFromObject(inner);
    decorate(g, v, bb);
    return t;
  }
  let thumbR, thumbScene, thumbCam;
  function thumb(kind, verdict, id) {
    if (!renderer) return null;
    if (!thumbR) {
      thumbR = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
      thumbR.setPixelRatio(1); thumbR.setSize(240, 180, false); thumbR.outputEncoding = THREE.sRGBEncoding; thumbR.setClearColor(0x000000, 0);
      thumbScene = new THREE.Scene(); thumbScene.environment = scene.environment;
      thumbScene.add(new THREE.AmbientLight(0xffffff, 0.22)); thumbScene.add(new THREE.HemisphereLight(0xe4edfa, 0x8e8a8a, 0.4));
      const k = new THREE.DirectionalLight(0xffffff, 0.85); k.position.set(3, 6, 4); thumbScene.add(k);
      thumbCam = new THREE.PerspectiveCamera(34, 4 / 3, 0.05, 50); thumbCam.position.set(3.1, 1.6, 4.4); thumbCam.lookAt(0, -0.05, 0);
    }
    const keep = halo, g = new THREE.Group(); thumbScene.add(g);
    assemble(g, kind, false, verdict, id);
    // centre and fit every machine in its tile (decorations make footprints differ)
    // bounds from visible parts only (near-transparent shells and the glow halo would skew the centre)
    g.updateMatrixWorld(true);
    const bb = new THREE.Box3();
    g.traverse((o) => { if (o.isMesh && o.material && (o.material.opacity === undefined || o.material.opacity > 0.3) && o.material.depthTest !== false) bb.expandByObject(o); });
    const c = bb.getCenter(new THREE.Vector3()), sz = bb.getSize(new THREE.Vector3());
    g.position.set(-c.x, -c.y, -c.z);
    const r = Math.max(sz.x * 0.85, sz.y, sz.z * 0.85) * 0.5, d = r / Math.tan(THREE.MathUtils.degToRad(34 / 2)) * 1.05;
    thumbCam.position.set(d * 0.55, d * 0.32, d * 0.78); thumbCam.lookAt(0, 0, 0);
    thumbR.render(thumbScene, thumbCam);
    const url = thumbR.domElement.toDataURL("image/png");
    thumbScene.remove(g); g.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); });
    halo = keep;
    return url;
  }

  // ---------------------------------------------------------------- run stages
  // A glowing ring travels down the machine, one level per stage of the run (load, vacuum, cool, magnet, measure,
  // hold). The sample frosts once cool-down passes. The ring stops and pulses at the stage where the run fails.
  const RUNCOL = { run: 0x4f8cff, p: 0x2fa35a, f: 0xd24b4b, u: 0xe0a21f, s: 0xe0a21f };
  let runRing = null, runState = null, sampleM = null;
  function runStage(st) {
    runState = st;
    if (!runRing) {
      runRing = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.022, 12, 72), new THREE.MeshBasicMaterial({ color: RUNCOL.run, transparent: true, opacity: 0.9, depthTest: false }));
      runRing.rotation.x = Math.PI / 2; runRing.renderOrder = 5; scene.add(runRing);
    }
    runRing.visible = !!st;
    if (!st) return;
    runRing.material.color.setHex(RUNCOL[st.status] || RUNCOL.run);
    if (halo) halo.material.color.setHex(RUNCOL[st.status] || RUNCOL.run);
    if (sampleM) { const c = new THREE.Color(st.cold ? 0xbfe6ff : (VERDICT[state.verdict] || GOLD)); sampleM.material.color.copy(c); sampleM.material.emissive.copy(c); }
  }
  function runTick(t) {
    if (!runRing || !runState || !runRing.visible) return;
    const n = Math.max(1, runState.n), y = 0.85 - (runState.i / Math.max(1, n - 1)) * 1.6;
    runRing.position.y += (y - runRing.position.y) * 0.12;
    const stopped = runState.status === "f" || runState.status === "u" || runState.status === "s";
    runRing.material.opacity = stopped ? 0.45 + 0.45 * (1 + Math.sin(t / 180)) / 2 : 0.9;
    const k = stopped ? 1 + 0.06 * Math.sin(t / 180) : 1; runRing.scale.set(k, k, k);
  }

  window.Cryo3D = {
    stage(st) { if (!renderer) return; runStage(st); },
    thumb,
    archetype, label: (k) => LABEL[k] || "Cryogenic apparatus",
    mount(el) { return init(el); },
    rigKind,
    show(kind, verdict, id, exp) { if (!renderer) return; const changed = kind !== state.kind || id !== state.id; Object.assign(state, { kind, verdict, id: id || null, exp: exp || null }); build();
      if (changed) { camera.position.set(3.35, 1.95, 4.8); controls.autoRotate = !reduced(); } },
    setInside(b) { if (!renderer) return; state.inside = b; build(); },
    orbit(d) { if (!renderer) return; const off = camera.position.clone().sub(controls.target); off.applyAxisAngle(new THREE.Vector3(0, 1, 0), d); camera.position.copy(controls.target).add(off); controls.autoRotate = false; },
    reset() { if (!renderer) return; camera.position.set(3.35, 1.95, 4.8); controls.target.set(0, 0, 0); controls.autoRotate = !reduced(); },
  };
})();
