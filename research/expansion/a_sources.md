# Expansion A — primary-source catalog findings

Research date: 2026-10-31.

This group adds 21 distinct procedure profiles across seven industries and 20 specialized equipment records, reusing the already documented installed DynaCool heat-capacity configuration for the final choice. The manifest selects three experiments and three configurations per industry. These are candidate pairings, not suitability endorsements; Lean must evaluate every pairing.

## Modeling boundaries

Single reported operating points are stored as zero-width intervals. A quoted minimum is stored as cold reach, not a fabricated continuous controlled range. Facility shrouds, optical benches and calorimeter boundary temperatures are distinct quantities. Mandatory apparatus-function flags prevent temperature-only compatibility. Missing roles remain UNKNOWN because an incomplete source is not evidence of absence. The NIST micro-JT prototype's stable integrated THz-detector operation is a mandatory UNKNOWN.

The selected scope checks documented temperatures and essential functions. Cryogenic pressure safety, radiation background, electrothermal load lines, dimensional fit and calibration are not universally formalized. Every profile records its specific limits. Passing the bounded profile must not be described as full engineering qualification.

## Industry coverage

### aerospace_and_space_exploration

Experiments:
- `expa_crm_aerodynamics`: Cryogenic aircraft-model force and pressure testing, 117–302 K
- `expa_hydrogen_lad_transfer`: Liquid-hydrogen screen-channel LAD outflow test at 20.3 K
- `expa_mli_guarded_heat_leak`: Multilayer-insulation heat-leak calorimetry with 20 K / 90 K boundaries

Configuration candidates:
- `expa_nasa_ntf_documented`
- `expa_nasa_smirf_documented`
- `expa_nasa_20_90_calorimeter_documented`

### astronomy_and_astrophysics

Experiments:
- `expa_mid_ir_array_characterization`: Mid-infrared array dark and illuminated characterization on a 16 K bench
- `expa_mirror_cold_figure`: Beryllium-mirror cold surface-figure metrology near 38 K (reported 37.87 K)
- `expa_telescope_cold_alignment`: Integrated telescope artificial-star optical alignment near 37 K

Configuration candidates:
- `expa_mitten_documented`
- `expa_nasa_xrcf_documented`
- `expa_nasa_chamber_a_documented`

### automotive_and_transportation

Experiments:
- `expa_hydrogen_304l_tensile`: Hydrogen-precharged 304L stainless-steel tensile test at 20 K
- `expa_hydrogen_composite_fatigue`: Liquid-hydrogen polymer-composite cyclic fatigue at 20 K
- `expa_cryogenic_membrane_permeation`: Helium permeability of thin cryogenic tank-barrier polymers at 20 K

Configuration candidates:
- `expa_wsu_craft_documented`
- `expa_wsu_ccc_documented`
- `expa_bremen_hb100_documented`

### defense_and_security

Experiments:
- `expa_bib_detector_photometry`: Far-infrared BIB detector dark and illuminated response, 5–20 K
- `expa_thz_microcooler_stability`: 77 K micro-JT cooler stabilization for a terahertz detector
- `expa_ybco_rf_filter`: 77 K microwave insertion-loss measurement of a 4 GHz YBCO filter

Configuration candidates:
- `expa_drs_janis_bib_documented`
- `expa_nist_micro_jt_documented`
- `expa_nasa_ybco_fixture_documented`

Shortfall: Three real specialized research configurations are documented, but two are historical paper setups without a commercial cryostat model. The NIST micro-JT prototype is not validated for stable integrated THz operation; its corresponding mandatory check intentionally remains UNKNOWN. No three commercially purchasable complete defense instruments are claimed.

### nuclear_engineering_and_fusion

Experiments:
- `expa_iter_coil_cold_test`: Full superconducting fusion-magnet cold qualification at 4 K
- `expa_cicc_critical_current`: Fusion cable-in-conduit critical-current characterization at 4.5 K and 10.8 T
- `expa_torus_cryopump_gas_test`: Fusion torus cryopump gas-injection test near 5 K

Configuration candidates:
- `expa_iter_magnet_facility_documented`
- `expa_epfl_sultan_documented`
- `expa_iter_cryopump_test_documented`

### physics_and_particle_accelerators

Experiments:
- `expa_srf_2k_resonance`: 2 K, 2.6 GHz superconducting RF-cavity resonance characterization
- `expa_argon_charge_scintillation`: Two-phase liquid-argon ionization and scintillation detection at 87 K
- `expa_teo2_bolometer`: TeO2 crystal bolometer particle-energy calorimetry near 10 mK

Configuration candidates:
- `expa_fnal_vts_documented`
- `expa_warp_2l3_documented`
- `expa_cuore_documented`

### scientific_research

Experiments:
- `expa_magnetic_powder_neutrons`: Magnetic powder neutron diffraction of GaV4S8 at 1.5 K
- `expa_nitrogen_bet_adsorption`: Nitrogen adsorption isotherm and BET surface-area analysis at 77 K
- `expa_relaxation_heat_capacity`: Zero-field heat-pulse relaxation calorimetry, 2–300 K

Configuration candidates:
- `expa_nist_bt1_oc50_documented`
- `expa_tristar_3030_documented`
- `qd_dynacool_14T_eto_vsm_hc`

## Inspected primary sources

### `expa_ntf`

[NASA National Transonic Facility virtual tour](https://www.nasa.gov/langley/virtual-tour/ntf/)

NTF is a nitrogen/air closed-circuit cryogenic aerodynamic wind tunnel; current tour lists Mach 0.2–1.2 and -250–130 F. Temperature bounds below are conservatively rounded inward to 117–327 K.

Source location: Quick Facts. Evidence type: `experimental_observation`.

### `expa_crm`

[NASA Common Research Model: Experimental Approach](https://www.nasa.gov/common_research_model/high-speed-crm/experimental-approach/)

The documented CRM aerodynamic campaign varied tunnel temperature between 117 and 302 K to reach Reynolds numbers 5, 19.8 and 30 million. This is a source-specific aircraft model test, not a generic cryostat experiment.

Source location: Experimental approach, NTF test conditions. Evidence type: `experimental_observation`.

### `expa_smirf`

[NASA Small Multi-Purpose Research Facility](https://www.nasa.gov/setmo/facilities/smirf/)

SMiRF has conducted liquid-hydrogen liquid-acquisition-device tests and supports tank chilldown/transfer. Reported minimum -424 F is about 19.817 K; 20 K is a conservatively rounded cold-reach requirement. Source gives 20–80 psi tank pressure but this catalog does not infer a specimen pressure rating from it.

Source location: Facility description, liquid acquisition devices. Evidence type: `experimental_observation`.

### `expa_lad_operating_point`

[Hartwig et al., Screen Channel Liquid Acquisition Device Outflow Tests in Liquid Hydrogen](https://ntrs.nasa.gov/api/citations/20140010818/downloads/20140010818.pdf)

The reported SMiRF experiment used fixed liquid saturation temperatures 20.3, 21.4, 22.9 and 24.2 K. The selected catalog fixture represents only the demonstrated 20.3 K point, not a continuous controllable interval. Section 5.4 identifies the actual SMiRF tank, LAD channels, heaters, outflow controls and thermometry; this was inverted 1-g vertical outflow, not microgravity.

Source location: Sections 5.4 and 6.1 / Table 3, apparatus and fixed fluid temperatures. Evidence type: `experimental_observation`.

### `expa_creek`

[NASA Creek Road Cryogenics Complex](https://www.nasa.gov/centers-and-facilities/glenn/creek-road-cryogenics-complex/)

The 20–90 K calorimeter uses separate warm/cold boundary temperatures and a vacuum vessel. SMiRF thermal shroud temperature is a background boundary, not the liquid-hydrogen sample temperature. Calorimeter vacuum capability is 1e-7 Torr or better.

Source location: 20 K to 90 K Calorimeter section. Evidence type: `experimental_observation`.

### `expa_mli`

[Chato et al., Design and Operation of a Calorimeter for Advanced Multilayer Insulation Testing](https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20170003927.pdf)

NASA's guarded calorimeter was designed for insulation heat-leak tests with nominal 20 K inner and 90 K outer boundaries and a calibrated rod measuring conducted heat flow. These are two simultaneous boundaries, not a uniform 20–90 K sample range.

Source location: Title and calorimeter design description. Evidence type: `experimental_observation`.

### `expa_mitten`

[Bowens et al., The Michigan Infrared Test Thermal ELT N-band (MITTEN) Cryostat](https://arxiv.org/abs/2012.06620)

MITTEN characterizes 8–13 um mid-IR detectors; interior below 40 K, optical bench 16 K, internal source and Offner relay. The paper says filter/aperture mechanisms will be added, so they are not labeled installed. Bench temperature is not asserted to be the detector setpoint.

Source location: Abstract. Evidence type: `experimental_observation`.

### `expa_xrcf`

[NASA Marshall Optics and X-Ray and Cryogenic Facility](https://www.nasa.gov/marshall/optics/)

XRCF evaluates large optical mirrors/structures down to 20 K; this is a cryogenic optical metrology facility, not an arbitrary microscope cryostat.

Source location: X-Ray and Cryogenic Facility description. Evidence type: `experimental_observation`.

### `expa_sbmd_operating_point`

[UAH, Subscale Beryllium Mirror Demonstrator Testing Support, Final Report 521134-FR](https://ntrs.nasa.gov/api/citations/20010070993/downloads/20010070993.pdf)

The September 2000 SBMD-3 optical test at XRCF measured a 0.532 m beryllium mirror in vacuum near 38 K; Table 4 reports mean temperature 37.87 K. This is an actual mirror measurement point, distinct from the generic facility's cold-reach figure. The procedure requires thermal drift below 2 K/hour and no gradients above 3 K; those bounds are not a universal facility guarantee.

Source location: Pages 2–4 procedure; page 9 / Table 4, actual cold optical test. Evidence type: `experimental_observation`.

### `expa_xrcf_interferometry`

[NASA Marshall Optical Systems Capabilities](https://www.nasa.gov/wp-content/uploads/2015/04/opticalsystems.pdf?emrc=602655)

NASA describes XRCF's two interferometers measuring structural distortions in cryogenic mirrors, vacuum typically below 1e-6 Torr. This supports the mirror-interferometry function, not a universal nanometer-accuracy guarantee.

Source location: X-Ray and Cryogenic Facility optical metrology description. Evidence type: `experimental_observation`.

### `expa_chamber_a`

[NASA Apollo-Era Test Chamber Now James Webb Space Telescope Ready](https://www.nasa.gov/universe/nasas-apollo-era-test-chamber-now-james-webb-space-telescope-ready/)

Chamber A's helium shroud is approximately 11 K and supports Webb testing near its 37 K operating temperature and 20 K survival condition. The 11 K shroud is not labeled a specimen-temperature capability.

Source location: Cryogenic shroud and telescope operating temperatures. Evidence type: `experimental_observation`.

### `expa_webb_optics`

[NASA Science, Webb's Mirrors](https://science.nasa.gov/mission/webb/webbs-mirrors/)

Webb's integrated telescope underwent cryogenic optical tests in Chamber A using artificial stars to assess optical alignment. This is distinct from testing one mirror's surface figure.

Source location: Cryogenic telescope mirror and optical alignment testing. Evidence type: `experimental_observation`.

### `expa_304l`

[PNNL, Effect of Hydrogen on Tensile Properties of 304L Stainless Steel at Cryogenic Temperatures](https://www.pnnl.gov/publications/effect-hydrogen-tensile-properties-304l-stainless-steel-cryogenic-temperatures)

PNNL reports 304L specimens thermally precharged with internal hydrogen and tensile tested at 20, 77 and 113 K. This is not a 700 bar in-situ hydrogen-pressure experiment.

Source location: Publication abstract, tensile testing temperatures. Evidence type: `experimental_observation`.

### `expa_craft`

[Washington State University HYPER, CRyogenic Accelerated Fatigue Testing](https://hydrogen.wsu.edu/craft/)

Operational CRAFT uses an MTS Acumen 12 frame with a custom cryogenic cell for tensile/compression/fatigue testing of polymer composites in 20 K liquid hydrogen or 77 K liquid nitrogen. Cryocooler theoretical 4 K minimum is not transcribed as demonstrated 4 K fatigue testing. Frequency maximum 100 Hz; 0.57 L cell.

Source location: CRAFT overview and System and Test Specifications. Evidence type: `experimental_observation`.

### `expa_ccc`

[Washington State University HYPER, Cubic Cryo Chamber](https://hydrogen.wsu.edu/ccc/)

CCC's actual thin-polymer helium-permeation apparatus modulates the test cell and ongoing permeation test between 20 and 200 K with a PT415 cryocooler and PID-controlled heaters. The separate general specification reports about 5 K cold reach for another MLI/thermal-resistor configuration; it is not used as proof of 5 K permeation. Disc specimens are 4.73 inch diameter and 0.001–0.05 inch thick.

Source location: 2016–2020 Kjell Westra: Helium Permeation Through Thin Polymer Films; controlled test-cell temperature. Evidence type: `experimental_observation`.

### `expa_bremen`

[University of Bremen MAPEX, ZwickRoell HB 100 cryogenic testing machine](https://www.uni-bremen.de/en/mapex-cf/instrument-database/show/76?cHash=e27ad4f95c225e8b3c8b2d5476ebf893)

University owner describes actual ZwickRoell HB 100 installed for static/dynamic tensile, compression, bending and fracture testing with a liquid-helium continuous-flow cryostat reaching 10 K. The model name is not used to infer an unquoted load rating.

Source location: Instrument capabilities / cryogenic continuous-flow insert. Evidence type: `experimental_observation`.

### `expa_drs`

[DRS, Far-Infrared Blocked Impurity Band Detector Development](https://ntrs.nasa.gov/api/citations/20070030828/downloads/20070030828.pdf?attachment=true)

DRS used a custom Janis liquid-helium dewar with a liquid-nitrogen intermediate shield, optical port, gravity-operated cold shutter and controlled 5–20 K detector stage. For far-IR tests, filters were not installed and silicon replaced the KRS5 window.

Source location: Page 4, custom Janis dewar / detector characterization apparatus. Evidence type: `experimental_observation`.

### `expa_nist_jt`

[NIST, Microcryocooler for Terahertz Detectors](https://www.nist.gov/programs-projects/microcryocooler-terahertz-detectors)

The NIST/Colorado DARPA prototype achieved 77 K but exhibited temperature oscillations below about 140 K. The source motivates THz weapons screening and IR detection, but does not establish stable operation or a completed characterized THz detector instrument.

Source location: Phase II prototype status. Evidence type: `experimental_observation`.

### `expa_ybco_filter`

[Sabataitis et al., YBCO High-Temperature Superconducting Filters on M-Plane Sapphire Substrates](https://ntrs.nasa.gov/citations/19970019925)

NASA/CWRU reported measured insertion loss of 4.0 GHz YBCO hairpin/edge-coupled filters at 77 K. The abstract establishes a cryogenic microwave transmission test fixture; cryostat manufacturer/model and calibration chain are not identified.

Source location: Abstract, fabrication and measured 77 K insertion loss. Evidence type: `experimental_observation`.

### `expa_iter_magnet`

[ITER, World's largest superconducting magnet test facility now operational](https://www.iter.org/worlds-largest-superconducting-magnet-test-facility-now-operational-iter)

The 2026 ITER magnet cold-test facility is operational with the first coil cooled to 4 K. ITER explicitly says it cannot reproduce every in-machine condition; no full reactor-environment equivalence is claimed.

Source location: First coil cold test / facility operating regime. Evidence type: `experimental_observation`.

### `expa_sultan`

[EPFL Swiss Plasma Center, SULTAN Test Facility](https://www.epfl.ch/research/domains/swiss-plasma-center/sultan-test-facility/)

SULTAN's present owner lists 10.8 T background field, 4.5–50 K sample temperature and sample current up to 100 kA for conductor/joint DC/AC testing. The 94 x 144 mm well and about 300 mm uniform region constrain sample layout. Separate maxima are not proven simultaneously feasible by scalar checks.

Source location: Facility technical specifications. Evidence type: `experimental_observation`.

### `expa_iter_pump`

[ITER, Let there be cold](https://www.iter.org/node/20687/let-there-be-cold)

ITER reports the pre-production torus cryopump cooled to approximately 5 K on 1 August 2025, followed by gas injection to test pumping. This is commissioning with test gases; tritium pumping is not asserted.

Source location: Cryopump test-facility commissioning, 2025. Evidence type: `experimental_observation`.

### `expa_fnal_vts`

[Fermilab, SRF Technology and Materials](https://technology.fnal.gov/capabilities/srf-technology-and-materials/)

Fermilab VTS has three liquid-helium test dewars for bare SRF cavities, high-power RF over several frequencies, and helium bath temperatures as low as 1.4 K, with diagnostic thermometry/second sound.

Source location: Vertical Test Stand capability. Evidence type: `experimental_observation`.

### `expa_fnal_2k`

[PI Loop Resonance Control for the Dark Photon Experiment at 2 K Using a 2.6 GHz SRF Cavity](https://arxiv.org/abs/2307.10433)

The authors report 2.6 GHz SRF cavities operated at 2 K in the Fermilab vertical test facility. This supplies an actual operating point and RF measurement context, rather than extrapolating from a cooler's base temperature.

Source location: Title and abstract. Evidence type: `experimental_observation`.

### `expa_warp`

[Benetti et al., First results from a Dark Matter search with liquid Argon at 87 K](https://arxiv.org/abs/astro-ph/0701286)

The WARP collaboration reports a 2.3 litre natural-liquid-argon chamber at 87 K with simultaneous VUV scintillation and electron signals extracted through the liquid-gas boundary. Abstract source does not establish gas purity, HV margin or full calibration.

Source location: Abstract. Evidence type: `experimental_observation`.

### `expa_cuore`

[INFN Laboratori Nazionali del Gran Sasso, CUORE](https://www.lngs.infn.it/it/cuore?cookie_08fa49e35a0857da952fcd871a3a3923=accepted)

CUORE operates 988 TeO2 crystals arranged in 19 towers as cryogenic bolometers at approximately 10 mK. Energy deposition is inferred from thermal pulses; radiopurity and shielding are essential to rare-event sensitivity but no sensitivity is promised here.

Source location: CUORE bolometer and cryostat description. Evidence type: `experimental_observation`.

### `expa_orange`

[NIST NCNR, Orange Cryostats](https://www.nist.gov/ncnr/neutron-instruments/sample-environment/equipment/liquid-helium-cryostats/orange-cryostats)

NIST OC50 is a top-loading helium exchange-gas cryostat with 50 mm sample well, 1.5–300 K range, and compatibility with instruments other than HFBS, including BT-1. It is an actual neutron sample environment, not an optical dewar.

Source location: OC50 specifications and instrument compatibility. Evidence type: `experimental_observation`.

### `expa_bt1`

[NIST NCNR, BT-1 high-resolution neutron powder diffractometer specifications](https://ncnr.nist.gov/instruments/bt1/bt1_spec.html)

BT-1 provides high-resolution neutron powder diffraction with cryogenic sample environments. The equipment entry is explicitly the integrated BT-1 + OC50 configuration; the bare Orange cryostat alone does not perform diffraction.

Source location: Instrument title and sample environment specifications. Evidence type: `experimental_observation`.

### `expa_gav4s8`

[Investigation of the magnetic ground state of GaV4S8 using powder neutron diffraction](https://arxiv.org/abs/2104.09912)

The authors use powder neutron diffraction at 1.5 K to investigate the magnetic ground state of GaV4S8. NIST BT-1 + OC50 is presented as a candidate apparatus with relevant capabilities, not falsely identified as the paper's reported machine.

Source location: Abstract and low-temperature magnetic structure discussion. Evidence type: `experimental_observation`.

### `expa_tristar`

[Micromeritics, Minimum Surface Area Measurements with Physisorption Analyzers](https://micromeritics.com.cn/en/resources/minimum-surface-area-measurements-with-micromeritics-physisorption-analyzers/)

The manufacturer documents nitrogen adsorption at 77 K on TriStar II / TriStar II Plus physisorption analyzers. The selected configuration is TriStar II Plus 3030 with liquid-nitrogen bath, not an invented cryostat modification.

Source location: Nitrogen measurement protocol / instrument comparison. Evidence type: `manufacturer_specification`.

### `expa_bet`

[RSC supplementary information c9cc00626e: gas sorption methods](https://www.rsc.org/suppdata/c9/cc/c9cc00626e/c9cc00626e1.pdf)

The authors report nitrogen adsorption at 77 K on a Micromeritics TriStar II Plus with BET analysis after sample activation. The procedure is physisorption of activated porous solids, not cold imaging or calorimetry.

Source location: Gas sorption experimental methods. Evidence type: `experimental_observation`.

### `expa_qd_hc`

[Quantum Design Heat Capacity Option, 1084-500 Rev. J0](https://www.qdusa.com/siteDocs/productBrochures/1084-500_PPMS_Heat_Capacity.pdf)

Manufacturer describes high-vacuum thermal-pulse relaxation calorimetry on a puck. Nominal operational range 1.8–400 K, 3 x 3 mm maximum footprint. Accuracy specification is for zero field over 2–300 K; performance is not generalized to all fields/materials.

Source location: Heat Capacity Specifications and method. Evidence type: `manufacturer_specification`.

## Final temperature semantic audit

The tensile and fatigue procedures require an actual 20 K operating point, not a base-temperature inequality. CRAFT records its reported 20 K bath; Bremen's 10 K minimum remains a cold-reach capability with an explicitly UNKNOWN operating interval. LAD outflow uses the directly documented SMiRF 20.3 K fixed fluid point from Hartwig et al. Table 3. CCC permeation uses its explicitly controlled 20–200 K specimen interval, selecting 20 K; its separate approximately 5 K hardware minimum is not a claimed permeation test condition. Mirror metrology uses the reported SBMD-3 mean mirror temperature of 37.87 K, with the published maximum 3 K specimen-gradient requirement remaining mandatory UNKNOWN until qualified. No observed operating point is labeled as a manufacturer specification.

## Reproduction

Run `python research/expansion/build_a.py` to regenerate only this group's new files. The integration owner must merge `vocabulary_proposals` from `a_manifest.json` before building the shared SQLite catalog and evaluating the 63 pairings in this group's seven 3×3 grids. No outcome is hardcoded by the generator.
