# Group B — primary-source catalog expansion

Accessed 2026-10-31. The implementation adds **16 experiment profiles and 13 real instrument configurations**. With the five existing biology/chemistry profiles, the seven assigned industries each have three different primary profiles and three equipment candidates: 63 requested cross-pairings. Equipment membership does not assert suitability. Actual matrix outcomes must be produced by the existing Lean engine after merging the proposed vocabulary in `b_manifest.json`.

All new files use the `expansion_b_` prefix. `build_b_catalog.py` reproduces them without editing shared vocabulary or existing profiles. Source quantities use exact strings; Celsius is converted to Kelvin before entering the checker. Each of the 21 profiles has a distinct specimen description and three procedural scene steps in the manifest. These describe illustrations, never synthetic measurements.

## Biological research

The existing tissue-sectioning and cryogenic-fluorescence profiles remain separate. The added PBMC profile follows Angel et al.'s **+4 to −80 °C, 1 °C/min** initial freezing program for 1 mL aliquots. The paper used Mr. Frosty containers; Planer is a documented alternative thermal implementation, not an asserted biological-equivalence result. Subsequent nitrogen-vapor storage is explicitly outside this initial-freeze profile. [Primary article](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5180082/fullTextXML)

The Planer Kryo 560-16 specification gives **+30 to −180 °C and system cooling 0.01–50 °C/min**. The controller's larger programmable rate is not substituted for actual freezer performance. Its basket/dewar geometry differs from a microtome and optical grid stage. [Manufacturer specification](https://planer.com/docs/freezers/K560_V2_0.pdf)

## Chemistry and pharmaceuticals

The three existing researched procedures remain Raman freezing/melting of an aqueous sample, polarized microscopy of synthetic-wax crystallization, and photoluminescence of a PEDOT:PSS film on fused silica. The existing Linkam THMS600, Oxford OptistatDry and Janis CCS-100 configurations provide three real, distinct candidates. Requirements and evidence of the existing profiles are not rewritten. New scene descriptors use a quartz crucible, crystalline wax specimen and square film substrate respectively.

## Healthcare

Three primary profiles have different apparatus and purposes:

- **Intercostal nerve cryoneurolysis:** Graves et al.'s randomized trial reports cryoprobe use at **−60 °C for 2 minutes**, under thoracoscopic visualization. This is distinct from a bath experiment on cultured cells. [Primary trial](https://escholarship.org/content/qt9qv3x483/qt9qv3x483_noSplash_14462970dec59270c3a1dc7d725b12cd.pdf)
- **Oocyte vitrification:** Kitazato specifies **at most four oocytes per Cryotop**, direct liquid-nitrogen plunge within one second, submerged capping, and dedicated carrier/container materials. No fictitious temperature-controlled chamber or guaranteed cooling rate is assigned. [Manufacturer protocol](https://www.kitazato.co.jp/en/pdf/vitrification/Protocol-EN-Vitrification_for_Oocytes_Embryos.pdf)
- **Cancer-cell freeze–thaw injury:** Snyder et al. use **8-well strips, 75 µL/well and a −25 °C/5-minute selected arm**, with a refrigerated circulating bath, aluminum contact blocks and independent sample thermometry. This is an in-vitro research protocol; no clinical tumor-ablation outcome follows from its equipment verdict. [Primary article](https://journals.sagepub.com/doi/pdf/10.1177/1178223420972363)

AtriCure's cryoSPHERE IFU establishes a real peripheral-nerve cryoprobe/BOX system, a typical probe range **−50 to −70 °C**, and a **120-second default**. The conservative duration interval records only that supported setting. Probe temperatures are separate from tissue temperatures and room operating conditions. The candidate's thoracoscopic chain is UNKNOWN. [Official IFU](https://asia.atricure.com/sites/default/files/devices-ifu/IFU-0036.C.pdf)

The candidate Neslab RTE740 has **−40 to +200 °C process-fluid capability**. The source study does not identify its exact Neslab model, so RTE740 is presented as a real candidate. The custom block and logger remain UNKNOWN. Its stability specification is qualified at 20 °C water conditions and is not generalized to −25 °C samples. [Manufacturer manual hosted by NIST](https://www.nist.gov/system/files/documents/ncnr/Circulating-Bath_Thermo-Scientific_NESLAB-RTE-7.pdf)

## Food and agriculture

RETSCH's primary application table documents gummy confectionery in the MM400/CryoKit with **50 mL steel jars, 30 Hz and 1 minute**. The MM400 has two jars and separate precooling, unlike the single continuously cooled CryoMill. A constant −196 °C sample temperature is deliberately not assigned to MM400. [Primary application report](https://www.retsch.com/files/15592/white-paper-cryogenic-preparation-of-sample-materials.pdf), [MM400 specification](https://www.retsch.com/products/milling/ball-mills/mixer-mill-mm-400/)

Donhowe and Hartel observe ice-cream recrystallization by cold-stage microscopy at mean temperatures **−20 to −5 °C**, with the constant-temperature arm controlled within **±0.01 °C**. [Primary publisher abstract](https://www.sciencedirect.com/science/article/abs/pii/S0958694696000295)

The strawberry paper specifies **−40 °C prefreezing for 4 hours**, then **−67 °C condenser and 0.055 mbar vacuum**. Condenser temperature is a dedicated key, never a sample-temperature range. The documented −50 °C candidate fails the collector requirement; the missing pump/system-pressure specification remains UNKNOWN. No compatible machine is invented. [Primary paper PDF](https://mdpi-res.com/d_attachment/processes/processes-13-02065/article_deploy/processes-13-02065.pdf)

The LTS120 candidate explicitly includes the manufacturer's optional water chiller, necessary below −25 °C to obtain its **−40 to +120 °C** range. It offers optical access and **<0.01 °C** stability. Gas valves do not prove an installed dewpoint-control system. [Manufacturer specification](https://www.linkam.co.uk/lts120-specifications)

## Environmental science

Cryogenic soil homogenization is explicitly a **manufacturer-documented sample-preparation method**, not a matrix-specific pollutant-recovery study. Soil is a named CryoMill material; the primary white paper describes LN2 cooling and preservation of volatile constituents. There is no invented feed mass, extraction recovery or detection limit. [Manufacturer application/specification](https://www.retsch.com/products/milling/ball-mills/mixer-mill-cryomill/)

The marine-aerosol droplet study uses **2 µL drops, +5 to −40 °C, 1 °C/min cooling**, and approximately **−39 °C dewpoint**, with separate humidified/dry nitrogen mixing and a hygrometer. Its published stage is LTS350; LTS120 is a different candidate. Its complete environmental-control chain and a guaranteed cold-end ramp are UNKNOWN. [Primary final article](https://acp.copernicus.org/articles/23/12707/2023/)

EPA SOP5188 identifies an actual **Entech7200A/Agilent8890/5977B** installation. The Appendix B screenshot on printed page57 (PDF index58) was visually inspected: **Module3 precool −180 °C, transfer −160 °C and injection +80 °C**. Separate trap-setting keys avoid inferring a continuous sample-temperature range or confusing the later 7200A+ specification with the installed 7200A. EPA identifies this as an internal research SOP, not an officially approved EPA method. [Primary EPA SOP](https://www.epa.gov/system/files/documents/2023-12/sop-5188-entech-7200a-agilent-5977b_508-compliant.pdf)

## Geology and oceanography

Zhou et al. use doubly polished **approximately 0.2 mm** mineral wafers and a THMSG600, with the low-temperature leg calibrated over **−56.6 to 0 °C**. The profile explicitly covers that leg, not the entire paper's high-temperature work. [Primary paper](https://mdpi-res.com/d_attachment/minerals/minerals-13-00365/article_deploy/minerals-13-00365.pdf)

The THMSG600 manufacturer documents a geology-specific optical stage, a **7 mm quartz cover slip**, **<−195 to 600 °C** range, and LNP96 cooling. The data conservatively use −195 °C as the lower endpoint. [Manufacturer description](https://www.linkam.co.uk/thmsg600)

Wu et al.'s Arctic-soil study induces freeze–thaw with **+4 and −20 °C environments** and records complex resistivity. The ESPEC EGNX12-4NWL is a real **380 L, −70 to +180 °C** chamber candidate; its electrical measurement chain is UNKNOWN. The PDF's model-specific table was visually checked, preventing confusion with the −35 °C models beneath it. [Primary author-institution abstract](https://www.ornl.gov/publication/remote-sensing-freeze-thaw-transitions-arctic-soils-using-complex-resistivity-method), [manufacturer table, page7](https://espec.com/images/uploads/files/e_globaln-A4.pdf)

Minnesota CSD documents an actual **FreeZone6 L/−50 °C** sediment freeze-dryer with three shelves and six ports. Samples are frozen separately and dried for multiple days. The selected −50 °C collector requirement reproduces this facility method; it is not a universal sediment eutectic limit. No drying time, sample temperature or mass-specific throughput is invented. [Facility's primary method](https://cse.umn.edu/csd/subsample-preparation-and-analysis)

Labconco's manufacturer brochure independently confirms −50 °C and −84 °C collector variants and separately required pumps/accessories. A required vacuum-pump ultimate pressure is not misrepresented as an achieved loaded system pressure. [Manufacturer specification](https://documents.thermofisher.com/TFS-Assets/ANZ/brochures/labconco-console-freeze-dryers.pdf)

## Manufacturing

Messer documents a real industrial cabinet and typical steel-treatment conditions **−160 to −185 °C for 24–72 hours**. The selected procedure uses −160 °C/24h. The brochure rounds Fahrenheit/Celsius limits inconsistently; the catalog uses a conservative interior envelope of **89.15–900 K** rather than claiming −300 °F is exactly −185 °C. Loaded maximum hold capability remains UNKNOWN. [Manufacturer process and equipment brochure](https://www.messer-us.com/hubfs/Messer%20US%20Website_2019/Resources/MESS-3145%20Metal%20Cryogenic%20Treatment%20Brochure.pdf)

The rubber cryomilling profile reproduces RETSCH's **4 g, 50 mL steel jar, 25 mm ball, 2 min/30 Hz** caoutchouc application. Its published fineness is an observation, not a guarantee for every elastomer. [Primary application table](https://www.retsch.com/files/15592/white-paper-cryogenic-preparation-of-sample-materials.pdf)

NETZSCH's primary SBR application heats **15.41 mg from −100 to +220 °C at 10 K/min**, twice, under dynamic nitrogen. Linkam DSC600 is a different real candidate, with **0.1–130 °C/min heating**, but its installed dynamic-N2 purge remains UNKNOWN. Actual sample/reference calorimetry is required, preventing a temperature-only PASS. [Primary rubber measurement](https://analyzing-testing.netzsch.com/_Resources/Persistent/1/1/3/a/113a82aa25c66d466843e79a134e449ecb15ac00/DSC_214_Polyma_en_web.pdf), [Linkam specification](https://www.linkam.co.uk/dsc600-specifications)

The DSC600 configuration explicitly includes optional **LNP96**, which the manufacturer requires for the low-temperature range. [Manufacturer system description](https://www.linkam.co.uk/dsc600)

## Integration and scope

Per-function flags use the existing present constraint. An undocumented function is UNKNOWN, not a false closed-set exclusion; no documented absence has been invented. Mandatory measurement-chain flags prevent ordinary cold chambers from passing merely because their temperatures overlap a specialized protocol. No new acceptance semantics, physical-law kernel or proof was introduced.

Every new profile is author-reviewed but still requires the product's normal user confirmation before verification. Changing either selection must invalidate stale results. Illustrations show procedural geometry, with unverified ancillary components identified as such; they are not manufacturer CAD or assertions that hypothetical hardware is installed.

The final source/schema audit reports **zero errors and zero warnings** for all 16 additions, 13 configurations and 26 evidence records, with 21 distinct primary profiles and 21 scene descriptors. The parent task is responsible for importing the merged vocabulary and reporting all 63 actual Lean outcomes together with the other industry groups.
