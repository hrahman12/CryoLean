# Linkam Scientific THMS600 heating/freezing microscope stage — documented specifications

Compiled 2026-10-31. Rule applied: every value below was read on a page/PDF fetched in this session. Values not found are marked `UNKNOWN (not found in sources fetched)`. Where Linkam's own documents disagree with each other (older vs. newer revisions), each version is recorded separately with its source.

Note on sources: Linkam's current web pages and the current brochure PDF (v1.54, 2026) are primary. Two older Linkam-authored documents were fetched from third-party hosts (a Polish university and the US distributor McCrone); they are Linkam documents but older revisions (LNP95/T95 era) and are labelled as such. Distributor-only figures (McCrone product page) are labelled `distributor_listing`, not `manufacturer_specification`.

---

## 1. Temperature range

### Temperature range with LNP96 cooling (full range)
- value: < -195 °C to 600 °C
- applies_to: THMS600 with LNP96-S liquid nitrogen pump and T96-S controller
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications", first bullet
- quote: "Temperature range < -195°C to 600°C (cooling option required)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature range (brochure statement)
- value: < -195 °C to 600 °C
- applies_to: THMS600 with optional LNP96-S
- source_url: https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download (linked from https://www.linkam.co.uk/thms600-brochure)
- document_title: THMS600 Versatile Heating and Cooling Stage (Linkam brochure, "v1.54 2026")
- location: page 3, "Technical Specification" table, row "Temperature Range"
- quote: "< -195°C (with the addition of an optional LNP96-S) up to 600°C"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature range without LNP (heating only)
- value: UNKNOWN as an explicit lower bound. Linkam only states that cooling below ambient requires the LNP96-S; the heating-only range is therefore ambient to 600 °C by implication, but no page states a numeric lower limit for the pump-less configuration.
- applies_to: THMS600 with T96-S only (no LNP96)
- source_url: https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: THMS600 Versatile Heating and Cooling Stage (Linkam brochure v1.54 2026)
- location: page 2, "Introducing the THMS600" paragraph 4
- quote: "For cooling below ambient temperatures, an optional LNP96-S liquid nitrogen pump is also available."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature range (older Linkam datasheet, LNP95 era)
- value: -196 °C to 600 °C
- applies_to: THMS600 with LNP95 (older configuration)
- source_url: https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf
- document_title: THMS600 Heating and Freezing Stage (Linkam Scientific Instruments, PDF metadata title "THMS600_systems_v1.1")
- location: page 3, "Specifications", first bullet
- quote: "Temperature range -196°C to 600°C (LNP95 required)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification (older revision, third-party hosted)

---

## 2. Heating/cooling rates and stability/accuracy

### Maximum heating rate
- value: 150 °C/min
- applies_to: THMS600 with T96-S
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications", second bullet
- quote: "Up to 150°C/min heating, 100°C/min cooling (using LNP96)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Maximum cooling rate
- value: 100 °C/min
- applies_to: THMS600 with LNP96
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications", second bullet
- quote: "Up to 150°C/min heating, 100°C/min cooling (using LNP96)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cooling rate range (LNP96 page)
- value: 0.01 °C/min to 100 °C/min (linear)
- applies_to: LNP96 cooling option with T96 controller
- source_url: https://www.linkam.co.uk/lnp96
- document_title: LNP96 Features — Linkam Scientific
- location: section "LNP96 Cooling Option"
- quote: "linear cooling rates as fast as 100°C/min or as slow as 0.01°C/min"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Heating/cooling rate range (brochure)
- value: 0.01 °C/min to 150 °C/min
- applies_to: THMS600 with T96-S (and LNP96-S for cooling)
- source_url: https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: THMS600 Versatile Heating and Cooling Stage (Linkam brochure v1.54 2026)
- location: page 3, "Technical Specification", row "Heating/Cooling Rates"
- quote: "Heating/Cooling Rates 0.01°C to 150°C/min"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Controller maximum ramp (T96)
- value: up to 200 °C/min (stage dependent)
- applies_to: T96 controller (generic; THMS600 is limited to 150 °C/min per its own spec)
- source_url: https://www.linkam.co.uk/t96
- document_title: T96 Features — Linkam Scientific
- location: section "High Speed Temperature Ramps"
- quote: "Temperature ramps of up to 200°C/min (dependent on stage attached)."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature stability (current spec page)
- value: < 0.01 °C
- applies_to: THMS600 with T96-S
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications", third bullet
- quote: "Temperature stability <0.01°C"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature stability (brochure)
- value: < 0.01 °C
- applies_to: THMS600 with T96-S
- source_url: https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: THMS600 Versatile Heating and Cooling Stage (Linkam brochure v1.54 2026)
- location: page 3, "Technical Specification", row "Temperature Stability"
- quote: "Temperature Stability < 0.01°C"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Accuracy and stability (product page wording)
- value: 0.01 °C "accuracy and stability"
- applies_to: THMS600
- source_url: https://www.linkam.co.uk/thms600
- document_title: Linkam THMS600 - Temperature Control Stage for Microscopy and Spectroscopy — Linkam Scientific
- location: product description text
- quote: "0.01°C accuracy and stability"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature stability (older Linkam datasheet and electrical variant — note discrepancy)
- value: < 0.1 °C
- applies_to: THMS600 (older v1.1 datasheet, T95 era) and THMSEL600 (current spec page)
- source_url: https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf ; https://www.linkam.co.uk/thmsel600-specifications
- document_title: THMS600 Heating and Freezing Stage (THMS600_systems_v1.1) ; THMSEL600 Specifications — Linkam Scientific
- location: v1.1 PDF page 3 "Specifications" bullet 3 ; THMSEL600 spec list bullet 3
- quote: "Temperature stability <0.1°C" (both documents)
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature sensor
- value: 100 Ω platinum resistor (Pt100), 1/10th DIN Class B
- applies_to: THMS600
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications"
- quote: "100 Ω platinum resistor sensor. 1/10th Din Class B"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Controller temperature resolution
- value: better than 0.01 °C
- applies_to: T96 controller
- source_url: https://www.linkam.co.uk/t96
- document_title: T96 Features — Linkam Scientific
- location: section "High Temperature Resolution"
- quote: "Temperature measurement using a PT100 platinum sensor with better than 0.01°C resolution."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 3. Sample size, heating block, aperture

### Sample area (diameter)
- value: 22 mm diameter
- applies_to: THMS600
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications"
- quote: "Sample area 22 mm diameter"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample size (brochure)
- value: 22 mm diameter
- applies_to: THMS600
- source_url: https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: THMS600 Versatile Heating and Cooling Stage (Linkam brochure v1.54 2026)
- location: page 3, "Technical Specification", row "Sample Size"
- quote: "Sample Size 22mm diameter"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample carrier / cover slip
- value: samples loaded on 0.17 mm thick cover slip; spare glass windows/sample discs supplied as 22 × 0.17 mm, 16 × 0.17 mm, 22 × 0.3 mm
- applies_to: THMS600 (older v1.1 datasheet)
- source_url: https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf
- document_title: THMS600 Heating and Freezing Stage (THMS600_systems_v1.1)
- location: page 1 "Features and Benefits"; page 6 "Suggested Spares", part ACCE
- quote: "Samples loaded onto a 0.17mm thick cover slip are placed on a highly polished pure silver heating element" ; "Box of Glass for Windows / Sample: 22x0.17mm (x50); 16x0.17mm (x50); 22x0.3mm (x10)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification (older revision, third-party hosted)

### Maximum sample thickness
- value: 3 mm (distributor listing only; not found on any Linkam page)
- applies_to: THMS600
- source_url: https://www.mccrone.com/product/linkam-thms600-thermal-stage/
- document_title: Linkam THMS600 Thermal Stage (McCrone Microscopes & Accessories)
- location: specifications list
- quote: "Maximum Sample Thickness: 3mm"
- accessed: 2026-10-31
- evidence_type: distributor_listing (not verified on linkam.co.uk)

### Silver heating block
- value: pure silver heating block; coolant injected directly into block. Block dimensions: UNKNOWN (not found in sources fetched)
- applies_to: THMS600
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications"
- quote: "Silver heating block for high thermal conductivity" ; "Direct injection of the coolant into the silver block"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Light aperture (transmitted-light hole through block) — current spec
- value: 2.0 mm diameter
- applies_to: THMS600 (current)
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications"
- quote: "Light aperture - 2.0mm Ø"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Light aperture — older Linkam datasheet (note discrepancy)
- value: 2.4 mm diameter
- applies_to: THMS600 (older v1.1 datasheet); also McCrone listing "Light Aperture Opening: 2.4mm"
- source_url: https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf
- document_title: THMS600 Heating and Freezing Stage (THMS600_systems_v1.1)
- location: page 3, "Specifications"
- quote: "Light aperture: 2.4mm diameter"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification (older revision, third-party hosted)

### XY sample manipulation
- value: 16 mm (spec page) / 15 mm (brochure) in X and Y
- applies_to: THMS600
- source_url: https://www.linkam.co.uk/thms600-specifications ; https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: THMS600 Specifications — Linkam Scientific ; THMS600 brochure v1.54 2026
- location: spec page bullet 4 ; brochure page 3 row "XY Manipulation"
- quote: "16 mm XY sample manipulation" ; "XY Manipulation 15mm in X and Y"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample loading
- value: side loading without removing lid
- applies_to: THMS600
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications", last bullet
- quote: "Sample side loading without removing the stage lid"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 4. Optical access

### Lid window thickness (current spec)
- value: 0.5 mm single lid window; material UNKNOWN (not stated on current THMS600 pages)
- applies_to: THMS600 (current)
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications"
- quote: "Single ultra thin lid window - 0.5mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Lid window thickness (older Linkam datasheet — note discrepancy)
- value: 0.17 mm
- applies_to: THMS600 (older v1.1 datasheet)
- source_url: https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf
- document_title: THMS600 Heating and Freezing Stage (THMS600_systems_v1.1)
- location: page 3, "Specifications"
- quote: "Single ultra thin lid window: 0.17mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification (older revision, third-party hosted)

### Window material options
- value: spectroscopy-grade quartz windows in a range of thicknesses (stated for the THMSEL600 electrical variant); sapphire sample window 7 mm Ø × 0.3 mm in the "Precision Temperature Kit" (older datasheet); ZnSe and BaF2 offered for the FTIR600 variant
- applies_to: THMSEL600 / THMS600 accessory kit / FTIR600 variant respectively
- source_url: https://www.linkam.co.uk/thmsel600-specifications ; https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf ; https://www.linkam.co.uk/ftir600
- document_title: THMSEL600 Specifications — Linkam Scientific ; THMS600_systems_v1.1 ; FTIR600 — Linkam Scientific
- location: THMSEL600 spec page text ; v1.1 PDF page 7, part W7S ; FTIR600 page text
- quote: "A range of different thickness spectroscopy grade quartz windows are available." ; "7mm diameter Sapphire Sample Window (0.3mm thick) x10" ; "Alternative window materials such as Zinc Selenide (ZnSe) and Barium Fluoride (BaF2) are also available."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Objective lens working distance (current)
- value: 4.8 mm
- applies_to: THMS600 (current)
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications"
- quote: "Objective lens working distance 4.8mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Objective lens working distance (older datasheet) and condenser working distance
- value: objective 4.5 mm; condenser minimum 12.5 mm
- applies_to: THMS600 (older v1.1 datasheet)
- source_url: https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf
- document_title: THMS600 Heating and Freezing Stage (THMS600_systems_v1.1)
- location: page 2 "Optical Specifications" and page 3 "Specifications"
- quote: "We recommend that you use an objective lens with at least 4.5mm working distance." ; "Condenser lens minimum working distance: 12.5mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification (older revision, third-party hosted)

### Condenser extension lenses
- value: range available (no numeric spec on current page)
- applies_to: THMS600 transmitted-light use
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications"
- quote: "Range of condenser extension lenses available"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Microscope orientation / compatibility
- value: designed for upright microscopes (objective above sample); reflected and transmitted light
- applies_to: THMS600
- source_url: https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf ; https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: THMS600_systems_v1.1 ; THMS600 brochure v1.54 2026
- location: v1.1 page 2 "Optical Specifications" ; brochure page 3 row "Compatibility"
- quote: "The THMS600 is designed to be used with an upright microscope, where the objective lens is above the sample." ; "Reflected and transmitted light microscopes, confocal, Raman Spectroscopy, X-ray and more."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 5. Electrical connections

### Electrical variant availability
- value: electrical connectors can be added (variant THMSEL600, previously THMSE600 / "THMS600E")
- applies_to: THMS600 options
- source_url: https://www.linkam.co.uk/thms600-options
- document_title: THMS600 Options — Linkam Scientific
- location: section "Stage Modifications", "Electrical Connections"
- quote: "Electrical connectors can be added to the THMS600 stage to enable electrical sample measurements."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### THMSEL600 range and specs
- value: < -195 °C to 600 °C (with LNP96); up to 150 °C/min; stability <0.1 °C; sample area 22 mm Ø; light aperture 2 mm Ø
- applies_to: THMSEL600 (electrical variant) with T96-S
- source_url: https://www.linkam.co.uk/thmsel600-specifications
- document_title: THMSEL600 Specifications — Linkam Scientific
- location: specifications bullet list
- quote: "Temperature range < -195°C to 600°C (with use of an LNP96)" ; "Sample area 22 mm Ø" ; "Light aperture - 2mm Ø"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Number of electrical contacts
- value: UNKNOWN for THMSEL600 specifically (not found in sources fetched). Linkam's electrical-stages brochure states "up to 16 point electrical measurements" for the electrical stage family generally and "Lemo connections available" for the THMS600E.
- applies_to: Linkam electrical stage family / THMS600E
- source_url: https://www.mccrone.com/wp-content/uploads/2020/02/Linkam-Microelectronics-Semiconductor-Materials.pdf
- document_title: Electrical Stages — Analysis of Microelectronics and Semiconductor Materials (Linkam, "V1.01 2018")
- location: page 1 cover panel; page 3 "Technical Specification*" table, column THMS600E
- quote: "Probes/Spring Clip Connectors Enabling up to 16 point electrical measurements" ; "THMS600E ... Lemo connections available" ; "Objective Lens Working Distance ... 4.8mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification (2018 brochure, distributor hosted)

### Probe/connector types (family level)
- value: gold-tipped tungsten needle probes or spring-clip posts
- applies_to: Linkam electrical stages generally
- source_url: https://www.mccrone.com/wp-content/uploads/2020/02/Linkam-Microelectronics-Semiconductor-Materials.pdf
- document_title: Electrical Stages — Analysis of Microelectronics and Semiconductor Materials (Linkam V1.01 2018)
- location: page 2, introduction paragraph
- quote: "stages can be fitted with gold tipped tungsten needle probes or spring clip posts which can be coupled to various output connectors."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 6. Gas purging / vacuum

### Gas purging
- value: quick-release gas valves / gas ports for atmospheric control
- applies_to: THMS600
- source_url: https://www.linkam.co.uk/thms600-specifications ; https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: THMS600 Specifications — Linkam Scientific ; THMS600 brochure v1.54 2026
- location: spec page bullet ; brochure page 2 "QUICK-RELEASE GAS PORTS"
- quote: "Quick-release gas valves for atmospheric control" ; "Simple and easy stage purging to allow atmospheric composition control."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Dry-nitrogen purge from LN2 pump exhaust (anti-condensation)
- value: recycled dry nitrogen exhaust from the pump purges chamber and lid window
- applies_to: THMS600 with LNP95 (older documentation; LNP96 pages fetched do not restate this)
- source_url: http://www.mccrone.com/wp-content/uploads/2018/11/cooling_20systems_v1.1.pdf
- document_title: Cooling Systems — Features and Benefits (Linkam Scientific Instruments, LNP95)
- location: page 1, paragraph 4
- quote: "warmed recycled dry nitrogen gas is used to purge the sample chamber and clear the upper lid window surface of condensation."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification (LNP95 era)

### Vacuum capability
- value: standard THMS600: no vacuum spec stated. Vacuum version is a separate stage, THMS350V: 10^-3 mbar, < -195 °C to 350 °C, light aperture 1.3 mm Ø, heating/cooling max 30 °C/min
- applies_to: THMS350V (vacuum variant linked from THMS600 page as "Vacuum version")
- source_url: https://www.linkam.co.uk/thms350v-specifications ; https://www.linkam.co.uk/thms350v
- document_title: THMS350V Specifications — Linkam Scientific ; THMS350V Features — Linkam Scientific
- location: specification bullets 1, 5, 13, 16 ; features text
- quote: "Maximum vacuum tested to 10-3mbar (tested onsite under full vacuum load)" ; "Temperature range < -195°C* to 350°C (*with LNP96)" ; "Light aperture 1.3mm Ø"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Pressure variant (for completeness)
- value: THMS600-PS: up to 14 bar; -100 °C to 500 °C at high pressure; < -192 °C to 600 °C at atmospheric pressure
- applies_to: THMS600-PS
- source_url: https://www.linkam.co.uk/thms600-ps
- document_title: THMS600-PS Features — Linkam Scientific
- location: features text
- quote: "pressurising the sample chamber up to 14bar" ; "-100°C to 500°C at high pressure"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Water cooling of stage body
- value: water cooling pump for work above 300 °C
- applies_to: THMS600
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications"
- quote: "The stage body can be cooled with a water cooling pump for high temperature work (>300°C)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 7. Liquid nitrogen pump (LNP96) and dewar

### LNP96 requirement
- value: LNP96-S required for sub-ambient operation; automatically controlled by T96
- applies_to: THMS600 with LNP96-S
- source_url: https://www.linkam.co.uk/lnp96 ; https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: LNP96 Features — Linkam Scientific ; THMS600 brochure v1.54 2026
- location: LNP96 page section "LNP96 Cooling Option" ; brochure page 2
- quote: "automatically controlled by the T96 controller" ; "cooling down to < -195°C" ; "A cooling system consists of the control unit housing the pumps and a Dewar."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### LNP96 dewar size
- value: UNKNOWN (not found in sources fetched) for LNP96. The predecessor LNP95 is documented with a 2 litre dewar (supplied) and an optional 25 L dewar.
- applies_to: LNP95 (older model) — NOT confirmed for LNP96
- source_url: http://www.mccrone.com/wp-content/uploads/2018/11/cooling_20systems_v1.1.pdf ; https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf
- document_title: Cooling Systems — Features and Benefits (Linkam, LNP95) ; THMS600_systems_v1.1
- location: Cooling Systems page 1 paragraphs 2–3 and "Options" ; v1.1 PDF page 1 "Cooling" and page 5
- quote: "a day of cooling experiments can be achieved using just a 2L dewar." ; "A 25L dewar with extra long siphon can be supplied for ultra long cooling experiments." ; "LNP95 (includes tubing, 2L Dewar and siphon)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification (LNP95 era)

### LNP96 dimensions / weight / LN2 consumption
- value: UNKNOWN (not found in sources fetched)
- applies_to: LNP96
- source_url: https://www.linkam.co.uk/lnp96 (checked; not stated) ; https://www.linkam.co.uk/lnp96-specifications (404)
- document_title: LNP96 Features — Linkam Scientific
- location: n/a
- quote: n/a
- accessed: 2026-10-31
- evidence_type: n/a

### Required controller
- value: T96-S controller (supports THMS family); NEXUS software or LinkPad touch screen
- applies_to: THMS600 system
- source_url: https://www.linkam.co.uk/t96 ; https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: T96 Features — Linkam Scientific ; THMS600 brochure v1.54 2026
- location: T96 page "Universal Voltage Controller" ; brochure page 2 paragraph 4
- quote: "T96-S model supports the Linkam THMS, HFS, LTS420, TS, BCS, FTIR, MFS, MDS, DSC, CSS, HS and CCR families of our stages." ; "A system requires both the THMS600 stage and a T96-S temperature controller"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 8. Stage dimensions and weight

### Stage body dimensions
- value: UNKNOWN on linkam.co.uk (not found in sources fetched). Distributor listing gives 138 mm × 92 mm × 22 mm.
- applies_to: THMS600
- source_url: https://www.mccrone.com/product/linkam-thms600-thermal-stage/
- document_title: Linkam THMS600 Thermal Stage (McCrone Microscopes & Accessories)
- location: specifications list
- quote: "Stage Body Size: 138mm x 92mm x 22mm"
- accessed: 2026-10-31
- evidence_type: distributor_listing (not verified on linkam.co.uk). For comparison, Linkam's own THMS350V spec page gives "Stage body size 160mm x 80mm x 24mm" for the vacuum variant.

### Stage weight
- value: UNKNOWN (not found in sources fetched)
- applies_to: THMS600
- source_url: n/a (Linkam THMS600 features, specifications, options pages and brochure v1.54 checked; none states weight)
- document_title: n/a
- location: n/a
- quote: n/a
- accessed: 2026-10-31
- evidence_type: n/a

---

## 9. Stated applications

### Raman / confocal / X-ray compatibility (spec page)
- value: suitable for confocal, laser Raman, X-ray
- applies_to: THMS600
- source_url: https://www.linkam.co.uk/thms600-specifications
- document_title: THMS600 Specifications — Linkam Scientific
- location: section "THMS600 Specifications"
- quote: "Suitable for confocal, Laser Raman and X-ray" ; "Can be used with all microscope techniques"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Optical techniques (brochure)
- value: Raman spectroscopy, confocal microscopy, X-ray diffraction, light microscopy
- applies_to: THMS600
- source_url: https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: THMS600 Versatile Heating and Cooling Stage (Linkam brochure v1.54 2026)
- location: page 1 cover panel "Optical Techniques"; page 2 "VARIOUS OPTICAL TECHNIQUES"
- quote: "Supports confocal, Raman, Light Microscopy, X-ray and more" ; "Add environmental control to Raman spectroscopy, confocal microscopy, X-ray diffraction, and most other experimental setups."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### FTIR
- value: vertical sample holders for FTIR spectrometers; dedicated FTIR600 variant (< -195 °C to 600 °C, tapered hole in silver block, ZnSe/BaF2 windows)
- applies_to: THMS600 (FTIR holders) / FTIR600 variant
- source_url: https://www.linkam.co.uk/thms600 ; https://www.linkam.co.uk/ftir600
- document_title: Linkam THMS600 — Linkam Scientific ; FTIR600 - Temperature control from -195°C to 600°C, optimised for Infrared and FTIR systems — Linkam Scientific
- location: THMS600 page text ; FTIR600 page text
- quote: "The silver block has a tapered hole to allow maximum transmittance of IR without interference."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Linkam case study: Raman with THMS600 (polar ice)
- value: Raman spectroscopy combined with THMS600 and FDCS196 (KOPRI)
- applies_to: THMS600
- source_url: https://linkam.co.uk/notes-and-articles/temperature-controlled-microscopy-enhances-research-of-chemical-processes-in-polar-ice
- document_title: Researchers use Linkam stages to investigate how temperature-controlled microscopy enhances research of chemical processes in polar ice (19 November 2020)
- location: article body; tags
- quote: "The Korean Polar Research Institute (KOPRI) used Raman spectroscopy in combination with Linkam's THMS600"
- accessed: 2026-10-31
- evidence_type: manufacturer_case_study

### Linkam webinar: Raman with temperature-controlled stages
- value: temperature-controlled confocal Raman microscopy talks (cultural heritage; Martian compounds)
- applies_to: THMS600 / TS1500 (tagged)
- source_url: https://linkam.co.uk/notes-and-articles/webinar-from-ancient-relics-to-life-on-mars-temperature-controlled-experiments-for-materials-characterisation
- document_title: Webinar: From Ancient Relics to Life on Mars: Temperature-Controlled Experiments for Materials Characterisation (17 February 2021)
- location: talk titles
- quote: "The Importance of Using Temperature Controlled Confocal Raman Microscopy to Study Phase Transitions in Martian Compounds"
- accessed: 2026-10-31
- evidence_type: manufacturer_webinar_listing

### Third-party Raman application note using THMS600 (Edinburgh Instruments, not Renishaw/Horiba)
- value: THMS600 on an RM5 confocal Raman microscope, 50X 0.5 NA long-working-distance objective, 532 nm; spectra 173–473 K; stage range quoted as 78–873 K
- applies_to: THMS600 on Edinburgh Instruments RM5
- source_url: https://www.edinst.com/wp-content/uploads/2025/03/AN_R33_Si-Temperature-Raman.pdf
- document_title: Application Note AN_R33 — Raman Thermometry of a Silicon Semiconductor Chip (Edinburgh Instruments, 2025)
- location: page 1, "Materials and Methods"
- quote: "The chip was placed in a Linkam THMS600 Heating and Cooling Stage, which allows for temperature control in a range between 78 K and 873 K."
- accessed: 2026-10-31
- evidence_type: third_party_application_note

### Renishaw / Horiba Raman application notes
- value: UNKNOWN (not found in sources fetched). No Linkam, Renishaw or Horiba application note specific to THMS600 + Raman was located; https://www.linkam.co.uk/raman returned 404. The Linkam THMS600 application-notes page lists no Renishaw/Horiba items.
- applies_to: n/a
- source_url: https://www.linkam.co.uk/thms600-applications
- document_title: THMS600 Application Notes — Linkam Scientific
- location: list of nine notes/case studies
- quote: n/a
- accessed: 2026-10-31
- evidence_type: n/a

### Other stated application areas (brochure)
- value: Earth sciences/geology (fluid inclusions, geo-fluids), semiconductor/electrical (photovoltaics, 2D materials, liquid crystals), materials/metallurgy (melting point, grain analysis, oxidation)
- applies_to: THMS600
- source_url: https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download
- document_title: THMS600 Versatile Heating and Cooling Stage (Linkam brochure v1.54 2026)
- location: page 3, "Application Examples"
- quote: "The device adds precise atmospheric control in combination with many microscopy and spectroscopic characterisation techniques."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## Sources fetched (successfully read in this session)

Linkam (manufacturer) web pages:
1. https://www.linkam.co.uk/thms600 — "Linkam THMS600 - Temperature Control Stage for Microscopy and Spectroscopy — Linkam Scientific"
2. https://www.linkam.co.uk/thms600-specifications — "THMS600 Specifications — Linkam Scientific"
3. https://www.linkam.co.uk/thms600-brochure — "THMS600 Brochure — Linkam Scientific" (link page only)
4. https://www.linkam.co.uk/thms600-applications — "THMS600 Application Notes — Linkam Scientific"
5. https://www.linkam.co.uk/thms600-options — "THMS600 Options — Linkam Scientific"
6. https://www.linkam.co.uk/thms600-ps — "THMS600-PS Features — Linkam Scientific"
7. https://www.linkam.co.uk/thmsel600 — "THMSEL600 Features — Linkam Scientific"
8. https://www.linkam.co.uk/thmsel600-specifications — "THMSEL600 Specifications — Linkam Scientific"
9. https://www.linkam.co.uk/thms350v — "THMS350V Features — Linkam Scientific"
10. https://www.linkam.co.uk/thms350v-specifications — "THMS350V Specifications — Linkam Scientific"
11. https://www.linkam.co.uk/lnp96 — "LNP96 Features — Linkam Scientific"
12. https://www.linkam.co.uk/t96 — "T96 Features — Linkam Scientific"
13. https://www.linkam.co.uk/ftir600 — "FTIR600 ... — Linkam Scientific"
14. https://linkam.co.uk/notes-and-articles/temperature-controlled-microscopy-enhances-research-of-chemical-processes-in-polar-ice
15. https://linkam.co.uk/notes-and-articles/webinar-from-ancient-relics-to-life-on-mars-temperature-controlled-experiments-for-materials-characterisation
16. https://linkam.co.uk/notes-and-articles/2026/5/11/investigating-fluid-inclusions-to-understand-ore-forming-processes-and-for-sequestion-of-carbon-dioxide-using-linkams-thms600-and-ts1400xy

Linkam (manufacturer) PDFs:
17. https://drive.usercontent.google.com/download?id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U&export=download — THMS600 brochure, 4 pages, "v1.54 2026" (linked from linkam.co.uk/thms600-brochure)
18. https://phavi.umcs.pl/at/attachments/2016/0622/081208-thms600-linkam.pdf — Linkam "THMS600 Heating and Freezing Stage" datasheet, 7 pages, PDF title "THMS600_systems_v1.1" (older, T95/LNP95 era; third-party host)
19. http://www.mccrone.com/wp-content/uploads/2018/11/cooling_20systems_v1.1.pdf — Linkam "Cooling Systems — Features and Benefits" (LNP95), 1 page (distributor host)
20. https://www.mccrone.com/wp-content/uploads/2020/02/Linkam-Microelectronics-Semiconductor-Materials.pdf — Linkam "Electrical Stages — Analysis of Microelectronics and Semiconductor Materials", V1.01 2018, 4 pages (distributor host)

Distributor / third-party pages:
21. https://www.mccrone.com/product/linkam-thms600-thermal-stage/ — "Linkam THMS600 Thermal Stage" (McCrone)
22. https://www.mccrone.com/product/linkam-lnp96-liquid-nitrogen-pump/ — "Linkam LNP96 Liquid Nitrogen Pump" (McCrone)
23. https://www.mccrone.com/wp-content/uploads/2020/06/20200609_Linkam_ThermalStages_4-pg-letter.pdf — "Linkam Thermal Stages" (McCrone brochure; states -196 °C to +600 °C, 0.01 °C accuracy, 150 °C/min, 16 mm XY)
24. https://www.mccrone.com/mm/a-focus-on-linkam-thermal-stages-for-electrical-measurements/ — "A Focus on Linkam Thermal Stages for Electrical Measurements" (McCrone)
25. https://www.pharmaceutical-tech.com/products/linkam-scientific-instruments/lnp96-cooling-option — "LNP96 COOLING OPTION"
26. https://www.edinst.com/wp-content/uploads/2025/03/AN_R33_Si-Temperature-Raman.pdf — Edinburgh Instruments AN_R33 (page 1 read; pages 2–3 not extracted due to a text-encoding error, page 1 contained the method details)

## Failed fetches
- https://admin.jhtechnologies.com/sites/default/files/THMS600_systems_v1.4_0.pdf — TLS certificate hostname mismatch (WebFetch); Tavily extract failed; curl with certificate check disabled was not permitted
- https://www.mmk.su.se/polopoly_fs/1.207276.1413535355!/menu/standard/file/THMS600_T95_manual.pdf (and https://mmk.su.se/... variant) — TLS certificate hostname mismatch; Tavily extract failed (this Linkam THMS600/720 user guide likely contains stage dimensions/weight)
- https://www.linkam.co.uk/condenser-extension-lenses — HTTP 404
- https://www.linkam.co.uk/lnp96-specifications — HTTP 404
- https://www.linkam.co.uk/t96-specifications — HTTP 404
- https://www.linkam.co.uk/raman — HTTP 404
- https://cp.yiqi.com/items/40663069ba.html — WebFetch failed with no output; Tavily extract failed
- https://www.jhtechnologies.com/products/linkam-thms600 — HTTP 403
- https://drive.google.com/uc?export=download&id=1I2MLqNJAnsX4AtrlPzK3h0iBu2Dv9O3U — 303 redirect only (followed successfully to drive.usercontent.google.com, listed above)
