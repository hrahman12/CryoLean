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

  let renderer, scene, camera, controls, root, halo, raf = 0, state = { kind: null, verdict: null, inside: false };
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
    const m = add(g, new THREE.Mesh(new THREE.BoxGeometry(size[0], size[1], size[2]),
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
    renderer.domElement.addEventListener("pointerdown", () => { controls.autoRotate = false; });
    new ResizeObserver(() => size(el)).observe(el); size(el);
    const loop = (t) => { raf = requestAnimationFrame(loop); controls.update();
      if (halo && !reduced()) halo.material.opacity = 0.1 + 0.08 * (1 + Math.sin(t / 420));
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
    const target = BUILD[state.kind](root, state.inside, state.verdict);
    controls.target.set(0, state.inside ? target[1] * 0.6 : 0, 0); controls.update();
  }

  let thumbR, thumbScene, thumbCam;
  function thumb(kind, verdict) {
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
    BUILD[kind](g, false, verdict); thumbR.render(thumbScene, thumbCam);
    const url = thumbR.domElement.toDataURL("image/png");
    thumbScene.remove(g); g.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); });
    halo = keep;
    return url;
  }

  window.Cryo3D = {
    thumb,
    archetype, label: (k) => LABEL[k] || "Cryogenic apparatus",
    mount(el) { return init(el); },
    show(kind, verdict) { if (!renderer) return; const changed = kind !== state.kind; Object.assign(state, { kind, verdict }); build();
      if (changed) { camera.position.set(3.35, 1.95, 4.8); controls.autoRotate = !reduced(); } },
    setInside(b) { if (!renderer) return; state.inside = b; build(); },
    orbit(d) { if (!renderer) return; const off = camera.position.clone().sub(controls.target); off.applyAxisAngle(new THREE.Vector3(0, 1, 0), d); camera.position.copy(controls.target).add(off); controls.autoRotate = false; },
    reset() { if (!renderer) return; camera.position.set(3.35, 1.95, 4.8); controls.target.set(0, 0, 0); controls.autoRotate = !reduced(); },
  };
})();
