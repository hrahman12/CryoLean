# Oxford Instruments NanoScience (now trading as Quantum Design Oxford) — documented specifications

Accessed: 2026-10-31. Rule applied: only values read on pages/PDFs fetched in this session. Anything not found is marked `UNKNOWN (not found in sources fetched)`.

Important note on sourcing: every `nanoscience.oxinst.com` product and brochure URL tried in this session now returns a 301 redirect to `https://www.qd-oxford.com/`. The manufacturer's current product pages and brochures are hosted on qd-oxford.com ("Oxford NanoScience LTD trading as Quantum Design Oxford"). The only `oxinst.com`-hosted document that still resolved was the 2018 OptistatDry TLEX brochure on andor.oxinst.com.

PDF text was extracted locally with `pdftotext -layout`; in the extracted text some symbols (±, –, ³, ®, µ) rendered as "�". Where a quote below contains such a symbol, the symbol is given as it appeared on the HTML product page, which reproduced the same figure legibly.

---

## 1. TeslatronPT (integrated Cryofree superconducting magnet system)

### Temperature range
- value: 1.5 – 300 K
- applies_to: TeslatronPT (all magnet options), variable temperature insert
- source_url: https://qd-oxford.com/products/teslatronPT.html
- document_title: Quantum Design Oxford - TeslatronPT
- location: "Features" key-specification list
- quote: "Temperature Range:  1.5 - 300 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Corroboration (brochure):
- source_url: https://qd-oxford.com/siteDocs/TeslatronPT_brochure.pdf
- document_title: TeslatronPT — Integrated Cryofree superconducting magnet system (single-page brochure, © 2026)
- location: "Key Specifications" block, row "Temperature Range"
- quote: "1.5 to 300 K"
- Also, "Features / Benefits": "Integrated variable temperature insert with static exchange gas around the sample, providing sample temperatures between 1.5 and 300 K while operating the magnet"

### Temperature stability
- value: ± 50 mK
- applies_to: TeslatronPT, sample temperature in VTI
- source_url: https://qd-oxford.com/products/teslatronPT.html
- document_title: Quantum Design Oxford - TeslatronPT
- location: "Features" key-specification list
- quote: "Temperature Stability:  ± 50 mK"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet field options — 8 T
- value: 8 T
- applies_to: TeslatronPT 8 T option
- source_url: https://qd-oxford.com/products/teslatronPT.html
- document_title: Quantum Design Oxford - TeslatronPT
- location: "Features" key-specification list
- quote: "Magnetic Field Options:  8 T, 12 T, 14 T and 6/1/1 T Vector Rotation"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet field options — 12 T
- value: 12 T
- applies_to: TeslatronPT 12 T option
- source_url: https://qd-oxford.com/siteDocs/TeslatronPT_brochure.pdf
- document_title: TeslatronPT — Integrated Cryofree superconducting magnet system (brochure, © 2026)
- location: "Key Specifications" block, row "Magnetic Field Options"
- quote: "8 T, 12 T, 14 T and 6/1/1 Vector Rotation"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet field options — 14 T
- value: 14 T
- applies_to: TeslatronPT 14 T option (maximum standard field)
- source_url: https://qd-oxford.com/siteDocs/TeslatronPT_brochure.pdf
- document_title: TeslatronPT — Integrated Cryofree superconducting magnet system (brochure, © 2026)
- location: "Features / Benefits" bullet list
- quote: "Wide range of standard magnets with fields up to 14 T with vector magnet geometries available"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet field options — 6/1/1 T vector rotation
- value: 6 T / 1 T / 1 T (vector)
- applies_to: TeslatronPT vector-rotation magnet option
- source_url: https://www.qd-oxford.com/siteDocs/TeslatronPT_Plus_Brochure.pdf
- document_title: TeslatronPT Plus — Made Simple (8-page brochure)
- location: "Cryosystem" page, "Superconducting Magnet" sub-section, row "Magnetic Field Options"
- quote: "8 T, 12 T, 14 T and 6/1/1 T vector rotation"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet conductor / remanence note
- value: fine-filament Nb3Sn (qualitative; no numeric remanent field stated)
- applies_to: TeslatronPT / TeslatronPT Plus magnets
- source_url: https://qd-oxford.com/siteDocs/TeslatronPT_brochure.pdf
- document_title: TeslatronPT brochure (© 2026)
- location: "Features / Benefits"
- quote: "Fine filament Nb3Sn superconducting wire offers the minimum field hysteresis via remnant field, and reduces flux jumping at low fields"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample space bore diameter
- value: 50 mm
- applies_to: TeslatronPT variable temperature insert (VTI) sample space
- source_url: https://qd-oxford.com/products/teslatronPT.html
- document_title: Quantum Design Oxford - TeslatronPT
- location: "Features" key-specification list; also "Why Choose TeslatronPT"
- quote: "Sample Space Diameter:  50 mm" ; "Large 50 mm sample space to accommodate everything from material samples to devices"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cooling power at a stated temperature
- value: UNKNOWN (not found in sources fetched)
- applies_to: TeslatronPT VTI / cryostat
- note: Neither the product page nor the 2026 brochure nor the TeslatronPT Plus brochure states a VTI or cryocooler cooling power. The only cooling-power figure in the fetched material belongs to the optional HelioxVT 3He insert (see "Low-temperature inserts" below).
- accessed: 2026-10-31

### Sample cooldown time
- value: < 2 h (room temperature to < 2 K, basic probe loaded into cold VTI)
- applies_to: TeslatronPT, sample probe exchange into already-cold VTI (NOT full system cooldown from room temperature)
- source_url: https://qd-oxford.com/products/teslatronPT.html
- document_title: Quantum Design Oxford - TeslatronPT
- location: "Features" key-specification list
- quote: "Sample Cooldown:  < 2 hours from room temperature to < 2 K for Basic Probe loaded into cold variable temperature insert (VTI)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Full-system cooldown time (room temperature to 4 K)
- value: UNKNOWN (not found in sources fetched)
- applies_to: TeslatronPT system (magnet + cryostat) from warm
- note: Not stated on the qd-oxford product page, the 2026 TeslatronPT brochure, or the TeslatronPT Plus brochure. The older nanoscience.oxinst.com brochures that may have contained it now redirect to qd-oxford.com and could not be fetched (web.archive.org is blocked for this tool).
- accessed: 2026-10-31

### Cryogen-free pulse tube cryocooler details
- value: UNKNOWN (not found in sources fetched)
- applies_to: TeslatronPT cryocooler (model, stages, compressor)
- note: The product page and both brochures describe the system only as "Cryofree" / "cryogen free"; no cryocooler model, stage count, or compressor is named. (The separate SpectromagPT product page on qd-oxford.com states "Instead, pulse tube refrigerators are used." but that is a different product and is not attributed here to TeslatronPT.)
- accessed: 2026-10-31

### Optical access
- value: UNKNOWN (not found in sources fetched) — no windows specified for TeslatronPT
- applies_to: TeslatronPT
- source_url: https://qd-oxford.com/products/teslatronPT.html
- document_title: Quantum Design Oxford - TeslatronPT
- location: "Options / Accessories" — Universal Measurement Probe
- quote: "configurable DC, RF, optical and driven guard wiring to suit a wide range of experimental requirements"
- note: "optical" here refers to probe wiring (fibre) options, not cryostat windows. Number of windows, diameter, material and NA are not stated.
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Electrical wiring — DC / RF
- value: DC and RF wiring available; shielded twisted pairs with optional driven-guard triax (number of DC lines / coax lines per probe NOT stated)
- applies_to: TeslatronPT sample probes
- source_url: https://qd-oxford.com/siteDocs/TeslatronPT_brochure.pdf
- document_title: TeslatronPT brochure (© 2026)
- location: "Insert features and options"
- quote: "DC and RF wiring to the sample"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Corroboration (TeslatronPT Plus brochure):
- source_url: https://www.qd-oxford.com/siteDocs/TeslatronPT_Plus_Brochure.pdf
- location: "Sample Probes & Holders"
- quote: "Shielded twisted pairs with additional driven-guard triax option" ; "Standard LCC20, LCC40, DIL16 sample holders, parallel or perpendicular to the magnetic field"

### Electrical wiring — breakout-box channel counts (room-temperature side)
- value: IsoSwitch 24 channels (BNC); MultiSwitch 12 channels incl. 6 triax (BNC/Triax); SampleProtect 24 channels incl. 12 twinax (BNC/Twinax)
- applies_to: TeslatronPT Plus breakout boxes (room-temperature signal chain, not the cryogenic probe wiring count)
- source_url: https://www.qd-oxford.com/siteDocs/TeslatronPT_Plus_Brochure.pdf
- document_title: TeslatronPT Plus brochure
- location: "Measurement Hardware" page, breakout-box table
- quote: "Number of Channels  24  12, incl 6 Triax  24, incl 12 Twinax" ; "Cabling  BNC  BNC/Triax  BNC/Twinax" ; "Recommended Frequency Range  DC up to 100 kHz"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Number of DC lines / coax lines to the sample
- value: UNKNOWN (not found in sources fetched)
- applies_to: TeslatronPT Universal Measurement Probe / Basic Probe
- accessed: 2026-10-31

### Low-temperature inserts (related options)
- value: < 300 mK (HelioxVT 3He); < 25 mK (KelvinoxJT dilution refrigerator)
- applies_to: TeslatronPT with optional inserts
- source_url: https://qd-oxford.com/siteDocs/TeslatronPT_brochure.pdf
- document_title: TeslatronPT brochure (© 2026)
- location: "Insert features and options"; "Related Products — HelioxVT"
- quote: "< 300 mK with the HelioxVT ³He refrigerator" ; "< 25 mK with the cryogen free KelvinoxJT dilution refrigerator system" ; HelioxVT: "achieves less than 300 mK for more than 40 hrs or can provide 50 µW of cooling power at 350 mK for over 6 hrs"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 2. OptistatDry (Cryofree optical cryostat) — BLV (bottom-loading, sample-in-vacuum) and TLEX (top-loading, sample-in-exchange-gas)

Primary sources: qd-oxford.com Optistat spectroscopy page (HTML), the Quantum Design Oxford "Optistats" specification matrix PDF (document code "OPTSS 0926 R5", © 2026), and the 2018 Oxford Instruments OptistatDry TLEX brochure (andor.oxinst.com, document no. 4762).

### Temperature range — BLV
- value: < 3 K to 300 K
- applies_to: OptistatDry BLV (minimum temperature with window blanks fitted)
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Models > OptistatDry BLV > Overview; Optistat Model Comparison table
- quote: "< 3 K to 300 K" ; comparison table: "<3 K (blanks fitted)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Corroboration (matrix PDF):
- source_url: https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf
- document_title: Optistats — Automated & Compact Optical Cryostats for Spectroscopy (OPTSS 0926 R5)
- location: p. 10, "Specifications" table, column "OptistatDry BLV", row "Temperature range"
- quote: "< 3 – 300 K" (footnote on p. 3: "** Base temperature with blanked window ports")

### Temperature range — TLEX
- value: < 4 K to 300 K
- applies_to: OptistatDry TLEX (minimum temperature with window blanks fitted)
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Models > OptistatDry TLEX > Overview; Optistat Model Comparison table
- quote: "< 4 K to 300 K" ; comparison table: "<4 K (blanks fitted)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Corroboration (2018 brochure):
- source_url: https://andor.oxinst.com/assets/uploads/products/andor/documents/4762_NS_OptistatDry%20TLEX_Brochure_2018_Web.pdf
- document_title: OptistatDry TLEX — Sample-in-exchange-gas applications (Oxford Instruments Nanotechnology Tools Ltd, 2018)
- location: "Specifications" table, row "Sample temperature range"
- quote: "Sample temperature range  <4 K to 300 K"

### Base temperature with all four windows fitted
- value: 6.5 K
- applies_to: OptistatDry BLV and TLEX, with 4 windows fitted (vs. blanks)
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Optistat Model Comparison table, row "Base temperature"
- quote: "6.5 (4 windows)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature stability
- value: ± 0.1 K (measured over 10 minutes)
- applies_to: OptistatDry BLV and TLEX
- source_url: https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf
- document_title: Optistats specification matrix (OPTSS 0926 R5)
- location: p. 10, "Specifications" table, row "Temperature stability (period)"
- quote: "+/-0.1 K (measured over 10 mins)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample space — BLV
- value: 40 mm diameter × 50 mm tall (vacuum)
- applies_to: OptistatDry BLV
- source_url: https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf
- document_title: Optistats specification matrix (OPTSS 0926 R5)
- location: p. 10, "Specifications" table, row "Maximum sample space", column BLV
- quote: "40 mm dia x 50 mm tall"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration: product page BLV Overview "40 mm x 50 mm vacuum"; comparison chart "Sample holder dims" BLV "20 mm x 50 mm"

### Sample space — TLEX
- value: 20 mm diameter sample tube
- applies_to: OptistatDry TLEX
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Models > OptistatDry TLEX > Overview; comparison chart
- quote: "Sample Tube: 20 mm" ; comparison chart "20 mm Ø" ; sample holder "19 mm x 30 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration: matrix PDF p. 10 row "Maximum sample space", column TLEX: "20 mm diameter"

### Cooling power at a stated temperature — BLV
- value: 0.2 W at 4.2 K (typical)
- applies_to: OptistatDry BLV
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Models > OptistatDry BLV > Overview
- quote: "0.2 W at 4.2 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cooling power at a stated temperature — TLEX
- value: ~0.2 W at 5 K (typical)
- applies_to: OptistatDry TLEX
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Models > OptistatDry TLEX > Overview
- quote: "~ 0.2 W at 5 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cold-head cooling power (mains-frequency dependent)
- value: 0.2 W at 4.2 K (60 Hz); 0.16 W at 4.2 K (50 Hz)
- applies_to: OptistatDry (row spans the TLEX and BLV columns in the PDF layout; column assignment not unambiguous from extracted text)
- source_url: https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf
- document_title: Optistats specification matrix (OPTSS 0926 R5)
- location: p. 10, "Specifications" table, row "Cold head cooling power"
- quote: "0.2 W at 4.2 K (60 Hz)  0.16 W at 4.2 K (50 Hz)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Optical access — BLV
- value: 28 mm diameter clear view, f/1
- applies_to: OptistatDry BLV
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Models > OptistatDry BLV > Overview
- quote: "Optical Access: 28 mm diameter clear view f1"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Optical access — TLEX
- value: 15 mm diameter clear view, f/1
- applies_to: OptistatDry TLEX
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Models > OptistatDry TLEX > Overview
- quote: "Optical Access: 15 mm diameter clear view f1"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (2018 brochure, andor.oxinst.com, bullet list): "Optimised optical access with f1 and a clear view of 15 mm diameter"

### Number of windows and window material (both variants)
- value: 4 radial windows (Spectrosil WF, standard) + 1 axial blank; user-changeable
- applies_to: OptistatDry BLV and TLEX (statement made for every Optistat cryostat)
- source_url: https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf
- document_title: Optistats specification matrix (OPTSS 0926 R5)
- location: p. 11, "Window Options" (OptistatDry ordering page); p. 3 features list
- quote: "Every cryostat is supplied with 4 x Spectrosil WF windows, fitted radially, and 1 x blank fitted axially. All windows are user changeable." ; "Optimised optical access with f/1 in radial directions"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (product page, "Windows for Optistat Cryostats"): "Optistat cryostats are supplied with Spectrosil WF windows as standard, providing good transmission from UV to mid-IR wavelengths."
- optional window materials listed in matrix p. 16-17 table for Dry: Spectrosil B, Sapphire, Crystalline quartz, Calcium fluoride, KRS-5, Zinc selenide, Polythene, Blanks (availability per outer/middle/inner position varies; TLEX has Outer/Middle/Inner window positions, BLV has Outer only)

### Numerical aperture
- value: UNKNOWN (not found in sources fetched) — only f/1 is stated
- applies_to: OptistatDry BLV and TLEX
- accessed: 2026-10-31

### Electrical wiring — BLV (DC lines)
- value: 24 DC wires (24-pin Fischer) standard on X (TLEX) models; 20 DC wires (D-connector) or 12 DC wires (PCB-style puck) on V (BLV) models
- applies_to: OptistatDry BLV = "V models"; TLEX = "X models"
- source_url: https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf
- document_title: Optistats specification matrix (OPTSS 0926 R5)
- location: p. 11, "Creating the Optimum Product for you" ordering code, "Wiring" codes
- quote: "24 DC wires (24 pin Fischer)*  20 DC wires (D-connector)**  12 DC wires (PCB style puck)**   * X models only (standard), ** V models only"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (product page, BLV System Configuration): "Measurement-ready via 12 or 20-pin DC wiring to the sample space" ; comparison chart "Customer wiring" BLV: "20 DC (LX20), 12 DC (DC12)" ; BLV "Unique Sample Exchange and Alignment": "12 sprung PCB connections for dc electrical signals in/out."

### Electrical wiring — TLEX (DC lines)
- value: 10 DC (comparison chart) — note the matrix ordering page instead lists "24 DC wires (24 pin Fischer)" as standard for X (TLEX) models; the two manufacturer documents differ
- applies_to: OptistatDry TLEX
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Optistat Model Comparison table, row "Customer wiring", column TLEX
- quote: "10 DC"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Electrical wiring — coax
- value: UNKNOWN (not found in sources fetched) — the word "coax" does not appear in the OptistatDry sections of the product page; the matrix lists coax options only for the OptistatDN/CF (wet) models
- applies_to: OptistatDry BLV and TLEX
- accessed: 2026-10-31

### Cooldown time — BLV
- value: < 150 min (product page); 2.5 h (code 200 / 20-pin) or 3.0 h (code 12P / 12-pin) ambient to 4.2 K (matrix)
- applies_to: OptistatDry BLV
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Models > OptistatDry BLV > Overview; comparison chart row "Cooldown from room temperature"
- quote: "< 150 mins" ; "<2.5 hrs (LX20), <3 hrs (DC12)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (matrix PDF p. 10, row "Cool down from ambient to 4.2 K", column BLV): "2.5 hrs (200) 3.0 hrs (12P)" ; row "Sample change time", BLV: "4-5 hrs"

### Cooldown time — TLEX
- value: < 6 h ambient to base; sample change 5 min (45 min to base temperature)
- applies_to: OptistatDry TLEX
- source_url: https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf
- document_title: Optistats specification matrix (OPTSS 0926 R5)
- location: p. 10, "Specifications" table, rows "Cool down from ambient to 4.2 K" and "Sample change time", column TLEX
- quote: "6 hrs" ; "5 mins (45 mins to base T)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (product page TLEX Overview): "<6 hrs" ; "< 45 minutes via top-loading probe"
- corroboration (2018 brochure, andor.oxinst.com, "Specifications"): "Cryostat cool down to 10 K  ~360 minutes from ambient" ; "Sample cool down to 10 K with cryostat cold ~45 minutes"

### Vibration
- value: < 10 µm RMS (typical, at sample position, with supplied stand / local vibration mitigation)
- applies_to: OptistatDry BLV and TLEX
- source_url: https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf
- document_title: Optistats specification matrix (OPTSS 0926 R5)
- location: p. 10, "Specifications" table, row "Vibration"; p. 10 features list
- quote: "<10 µm RMS typical" ; "Low vibration when used in conjunction with the supplied stand, typically less than 10 µm RMS"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (product page, both Overviews): "Typical RMS displacement of 10 microns at the sample position"

### Cryogen-free cryocooler details (pulse tube vs GM, model)
- value: UNKNOWN (not found in sources fetched) — cryocooler type/model not named; only "Cryocooler and Compressor" with air- or water-cooled compressor options
- applies_to: OptistatDry BLV and TLEX
- source_url: https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf
- document_title: Optistats specification matrix (OPTSS 0926 R5)
- location: p. 10 features; p. 18 "Power Supply Requirements — Compressors (OptistatDry only)"
- quote: "Water and air-cooled compressors available" ; "No liquid cryogen required" ; compressor: "3.0 kW 15.5 A full load at ~200 V" (50 Hz, 200 V) / "3.4 kW 16.0 A full load at ~220 V" (60 Hz, 220 V)
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (product page, System Configuration): "Compressor: Air- or water-cooled"

### Weight / dimensions
- value: BLV 23 kg, 635-900 (adjustable) × 240 × 290 mm; TLEX 28 kg, 800-880 (adjustable) × 240 × 400 mm
- applies_to: OptistatDry BLV / TLEX
- source_url: https://www.qd-oxford.com/products/optistat_spectroscopy.html
- document_title: Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy
- location: Models > OptistatDry BLV / TLEX > Overview
- quote: BLV "23 kg", "635-900 (adjustable) x 240 x 290 mm"; TLEX "28 kg", "800-880 (adjustable) x 240 x 400 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## Sources fetched (successfully read this session)
- https://qd-oxford.com/products/teslatronPT.html — "Quantum Design Oxford - TeslatronPT" (HTML)
- https://qd-oxford.com/products/teslatronPT_Plus.html — "Quantum Design Oxford - TeslatronPT Plus - An Open-Architecture, Low Temperature Measurement System" (HTML)
- https://qd-oxford.com/siteDocs/TeslatronPT_brochure.pdf — TeslatronPT brochure, 1 page, © 2026 (PDF; text extracted locally with pdftotext)
- https://www.qd-oxford.com/siteDocs/TeslatronPT_Plus_Brochure.pdf — TeslatronPT Plus brochure, 8 pages (PDF; pdftotext)
- https://www.qd-oxford.com/ — Quantum Design Oxford home page (used for navigation)
- https://www.qd-oxford.com/categories.html — product categories (navigation)
- https://www.qd-oxford.com/products/optistat_spectroscopy.html — "Quantum Design Oxford - Optistat - Optical Cryostats for Spectroscopy" (HTML)
- https://www.qd-oxford.com/siteDocs/Optical_Cryostats_matrix_final.pdf — "Optistats — Automated & Compact Optical Cryostats for Spectroscopy", OPTSS 0926 R5, © 2026 (PDF; pdftotext)
- https://andor.oxinst.com/assets/uploads/products/andor/documents/4762_NS_OptistatDry%20TLEX_Brochure_2018_Web.pdf — OptistatDry TLEX brochure, 2018 (PDF; pdftotext)
- https://www.qd-oxford.com/products/spectromagPT.html — SpectromagPT page (checked only for cryocooler wording; not a target product)

## Failed fetches
- https://nanoscience.oxinst.com/products/teslatronpt — 301 redirect to https://www.qd-oxford.com/
- https://nanoscience.oxinst.com/assets/uploads/Oxford_Instruments_TeslatronPT_Brochure.pdf — 301 redirect to https://www.qd-oxford.com/
- https://nanoscience.oxinst.com/assets/uploads/TeslatronPT_Brochure_Feb2018_1%20(2).pdf — 301 redirect to https://www.qd-oxford.com/
- https://nanoscience.oxinst.com/products/optical-cryostats-for-spectroscopy/optistatdry-blv — 301 redirect to https://www.qd-oxford.com/
- https://nanoscience.oxinst.com/products/cryostats-for-spectroscopy/optistatdry-tlex — 301 redirect to https://www.qd-oxford.com/
- https://andor.oxinst.com/products/dry-cryostat-optistatdry — resolved to a generic Andor spectroscopy page with no OptistatDry content
- https://andor.oxinst.com/products/optical-cryostats-for-spectroscopy/optistatdry-blv — HTTP 404
- https://web.archive.org/web/2023/https://nanoscience.oxinst.com/assets/uploads/products/nanoscience/documents/TeslatronPT-the-integrated-cryogen-free-superconducting-magnet-system.pdf — tool cannot fetch web.archive.org
