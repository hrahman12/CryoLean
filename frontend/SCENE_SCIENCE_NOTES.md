# Scene science notes

All geometry is authored procedurally with Three.js/React Three Fiber. No
manufacturer CAD, copied product photos, external textures or proprietary model
assets are used. There is no claim of exact scale or manufacturer approval.
Relative size, line thickness and clearances are exaggerated for legibility.

## Sources and installation boundary

Scene selection uses explicit repository equipment and experiment IDs in
`src/scene/registry.ts`. Sources are the configuration capabilities and experiment
profiles returned by `CryoLeanAPI`; the read-only browser snapshot is generated
from the same API. The evidence panels show the actual document titles, page or
section, quotations and URLs. The canonical scientific data remain the JSON
seeds under `data/cryostats`, `data/experiments`, `data/evidence` and `data/physics`.

The **machine views** show a representative family enclosure and its interfaces.
Optional modules, magnetic coils, wiring and optical windows are enabled only
when the configuration supplies a documented installed capability. The **Experiment
view** is an enlarged schematic of the required measurement, not a claim that
the selected machine already contains that apparatus. It is explicitly labeled.

| Family | Physical elements | Key limits |
|---|---|---|
| Leica CM1950 class | Insulated cabinet, chamber, chuck, blade, collection surface, handwheel | No exact knife geometry, tissue mechanics or section-thickness simulation |
| Linkam THMS600 class | Compact stage, sample support, lid, objective, control unit | External microscope is representative; no exact working-distance or optical NA claim |
| PPMS / Teslatron class | Dewar/chamber, flange, sample access, cold stage, documented magnet and connections | Family geometry is schematic; classic PPMS and Teslatron do not claim exact DynaCool internals |
| Optical cryostat | Cold finger, sample platform, chamber, documented optical access | Number/shape of depicted windows is representative, not an exact CAD reconstruction |
| CRX probe station | Broad chamber, sample platform, top optical access, documented probe count | Probe manipulators are simplified; no inferred RF bandwidth or contact geometry |
| Bluefors LD class | Nested stage structure, support rods, mixing chamber, documented wiring | Representative cable paths/counts; no magnet or optical option is invented |

## Experiment archetypes

- Frozen tissue: an irregular pink specimen on a chuck, blade and collection
  slide. Motion advances the specimen conceptually. No biological image,
  measured slice thickness, diagnostic result or living-tissue model is shown.
- Four-probe transport: mounted bar specimen and four separate contacts.
  Outer contacts carry current; inner contacts sense voltage. Colored moving
  markers indicate conceptual signal flow, with no generated I/V/R reading.
- Millikelvin transport uses that transport mechanism as a schematic; it is not
  a reconstruction of a specific nanodevice's lithography or exact wiring.
- Cryo-fluorescence: cooled specimen support and objective with illustrative
  illumination/collection. There is no invented microscope image or Raman
  spectrum; fluorescence has its own archetype.
- Raman: incident excitation and a collection path to the spectrometer. The
  displayed colors distinguish paths; they do not assert a wavelength or a
  material's Raman shift.
- Photoluminescence: excitation followed by emission collection to a detector.
  It is a distinct process label from Raman; no emission energy is predicted.
- Phase-transition microscopy: stage, specimen, illumination, objective and
  crossed polarizers. The illustration is conceptual and provides no measured
  phase boundary or transition temperature.
- VSM: oscillating sample rod, fixed pickup coils and external electronics.
  Motion is exaggerated and produces no simulated magnetization signal.
- Wiring heat budget: stages, representative cables and thermal anchors. No
  qubit chip is inferred from a profile that only checks wiring. Load/cooling
  values appear only when returned by a real coupled check.
- Transmon characterization: adds an explicitly illustrative chip inset and
  microwave connections. No frequency, layout, coherence time or measurement
  performance is claimed.

## Interaction and explanation

Outside, Inside and Experiment views share one WebGL canvas. Camera presets,
unrestricted azimuthal orbit, zoom, reset, fullscreen, component labels and
keyboard alternatives are provided. Component facts always display their actual
installation state and evidence; missing dimensions never become a fit overlay.
Failure highlights are local. Unknown highlights use dashed styling and a
neutral color. The entire machine is never recolored as certified compatible.

Animation is optional, pausable, reduced-motion aware and labeled illustrative.
Storyboards remain available as explicit steps. GPU failure/context loss and an
explicit “Use text diagram” control preserve the experiment explanation and the
verification controls without WebGL.

Known fidelity limits: these are schematic teaching models, not collision,
thermal, optical, electrical-field or real-time acquisition simulations.
Current expansion: cryolean/visuals.py provides source-guided descriptors for all 204 profiles and 220 configurations. ScientificModels.tsx renders 39 instrument families and 41 measurement mechanisms; 60 configurations include researched internal construction. Source outer aspect and stage descriptions guide appearance without filling unknown checker specifications. Both sample and machine viewers have explicit Spin controls, unrestricted azimuth orbit and zoom.
