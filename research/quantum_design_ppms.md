# Quantum Design PPMS DynaCool — Documented Manufacturer Specifications

Compiled 2026-10-31. Every value below was read on a page/PDF fetched in this session. Values not found are marked `UNKNOWN (not found in sources fetched)`. PDFs were fetched from qdusa.com (and one QD user manual mirrored by KTH) and text-extracted with PyMuPDF; "PDF page N" refers to the physical page index in the file, and "printed page" to the number printed on the page where present.

Document key (titles as shown in the documents):
- **[A]** `https://qdusa.com/products/dynacool.html` — "Quantum Design North America - Products - Quantum Design PPMS DynaCool is a Physical Property Measurement System for Low Temperature and High Magnetic Field Materials Characterization."
- **[B]** `https://qdusa.com/siteDocs/productBrochures/1307-010.pdf` — "Product Description / Cryogen-Free Physical Property Measurement System / PPMS DynaCool" (footer: "1307-010 Rev. G0"; PDF metadata title "1307-010 revG0 WORK.ai"), 4 pages.
- **[C]** `https://qdusa.com/siteDocs/productBrochures/1084-500.pdf` — "PPMS Family Measurement Options" (footer: "1084-500 Rev. J0"), 31 PDF pages.
- **[D]** `https://qdusa.com/siteDocs/productBrochures/1070-002.pdf` — "PPMS Physical Measurement Property System Product Description" (footer: "1070-002 Rev. C1"), 2 pages. Classic (legacy, liquid-helium) PPMS.
- **[E]** `https://qdusa.com/products/ppms.html` — "Quantum Design North America - Products - Physical Property Measurement System (PPMS) obsolescence notice."
- **[F]** `https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_AC_Resistance_ETO.pdf` — single-page ETO sheet "Electrical Transport / AC Resistance (ETO) / PPMS DynaCool (D605) / PPMS VersaLab (V605)" (identical text to [C] PDF page 4).
- **[G]** `https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_Heat_Capacity.pdf` — single-page "Thermal Measurements / Heat Capacity / PPMS DynaCool (D650) / PPMS VersaLab (V650)" (identical to [C] PDF page 16).
- **[H]** `https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_TTO.pdf` — 2-page "Thermal Measurements / Thermal Transport (TTO) / PPMS DynaCool (D670) / PPMS VersaLab (V670)" (identical to [C] PDF pages 17-18).
- **[I]** `https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_LBCS_VSM.pdf` — single-page "Magnetometry / Large Bore Coil Set (VSM) / PPMS DynaCool (D529) / PPMS VersaLab (V529)" (identical to [C] PDF page 10).
- **[J]** `https://qdusa.com/siteDocs/productBrochures/PPMS_Options_Compatibility_Table.pdf` — single-page "Compatibility Table / Sub-Kelvin Compatibility Kits" (identical to [C] PDF page 30).
- **[K]** `https://www.nanophys.kth.se/nanolab/ppms/4307-004%20Dynacool%20Digital%20User%20Manual%20Set/02%201307-110%20Rev%20D1%20Dynacool%20User's%20Manual.pdf` — "Physical Property Measurement System / DynaCool User's Manual / Part Number 1307-110, D1", "Fifth edition of manual completed November 2017", Quantum Design, Inc. (institutional mirror of the QD manual; not hosted on qdusa.com), 127 pages.

---

## 1. Temperature range (base system)

### Temperature range — DynaCool base system
- value: 1.8 to 400 K (60 Hz line frequency); 1.85 to 400 K (50 Hz)
- applies_to: PPMS DynaCool base system (all magnet options)
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description, Cryogen-Free Physical Property Measurement System, PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications" table, row "Temperature Control / Range"
- quote: "1.8 to 400 K @ 60Hz; 1.85 to 400 K @ 50Hz (Continuous Low Temperature Control and Temperature Sweep modes)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature range — DynaCool (corroboration, options brochure)
- value: 1.8 to 400 K
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 3 (printed page 1), "Specifications / PPMS DynaCool", row "Temperature Range*" and footnote
- quote: "1.8 to 400 K" ... "*Stated 1.8 K is for 60 Hz line frequency; 50 Hz line frequency has a base of 1.85 K."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature range — DynaCool (product web page)
- value: 1.8 K – 400 K
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/products/dynacool.html
- document_title: Quantum Design North America - Products - Quantum Design PPMS DynaCool is a Physical Property Measurement System for Low Temperature and High Magnetic Field Materials Characterization.
- location: Main product page, feature list
- quote: "Temperature range of 1.8 K – 400 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Extended temperature range with sub-Kelvin options (not base system)
- value: 0.05 K (Dilution Refrigerator option) up to 1000 K (VSM Oven option)
- applies_to: PPMS DynaCool with optional D850 Dilution Refrigerator / D527 VSM Oven
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 3 (printed page 1), introductory paragraph "PPMS Family"
- quote: "These systems provide sample environments from 0.05 K to 1000 K and fields up to 14 T."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 2. Magnet options

### Magnet options — 9 T, 12 T, 14 T are mutually exclusive choices ("either ... or")
- value: 9 T, 12 T or 14 T (one installed per system)
- applies_to: PPMS DynaCool
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description, Cryogen-Free Physical Property Measurement System, PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 1, section "Magnet Control"
- quote: "The PPMS DynaCool comes equipped with either a 9 T, 12 T or 14 T conduction-cooled superconducting switch-less magnet system."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet options — field range and orientation (spec table)
- value: Longitudinal: ±9 T, ±12 T, ±14 T
- applies_to: PPMS DynaCool 9 T / 12 T / 14 T magnet options
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description, Cryogen-Free Physical Property Measurement System, PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications" table, row "Magnet Options / Range and Orientation"
- quote: "Longitudinal: ±9 T, ±12 T, ±14 T"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet options — 9 T (web page confirmation)
- value: 9 T
- applies_to: PPMS DynaCool 9 T magnet option
- source_url: https://qdusa.com/products/dynacool.html
- document_title: Quantum Design North America - Products - Quantum Design PPMS DynaCool ...
- location: Main product page, feature list
- quote: "9 T, 12 T and 14 T magnets available"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet options — 12 T (confirmation, options brochure)
- value: ±12 T
- applies_to: PPMS DynaCool 12 T magnet option
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 3 (printed page 1), "Specifications / PPMS DynaCool", row "Field Range"
- quote: "± 9 T, ± 12 T, ± 14 T"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet options — 14 T (confirmation, DynaCool; ≥10 T configuration)
- value: ±14 T
- applies_to: PPMS DynaCool 14 T magnet option
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description, Cryogen-Free Physical Property Measurement System, PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications" table, rows "Field Uniformity" and "Power Supply"
- quote: "14 T: ±0.1% over 5.5 cm on axis; magnet center located 4 cm above puck surface" ... "9 T: 60 A; 12 T: 120 A; 14 T: 120 A"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet options — platform summary on PPMS page
- value: DynaCool 9 T, 12 T or 14 T; VersaLab 3 T; classic PPMS up to ±16 T
- applies_to: PPMS family
- source_url: https://qdusa.com/products/ppms.html
- document_title: Quantum Design North America - Products - Physical Property Measurement System (PPMS) obsolescence notice.
- location: Main page text (platform comparison)
- quote: "Sample environment controls included magnetic fields up to ±16 T" (classic PPMS); DynaCool listed as 9 T, 12 T, or 14 T; VersaLab 3 T (per page summary)
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet options — 9 T magnetic shield
- value: 5 gauss line "very near to the surface of the cryostat cabinet" (9 T only)
- applies_to: PPMS DynaCool 9 T magnet option
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 1, section "Magnet Control"
- quote: "The PPMS DynaCool-9T now includes an integrated magnetic shield capable of maintaining the 5 gauss line very near to the surface of the cryostat cabinet"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 3. Field uniformity and ramp rate

### Field uniformity — 9 T
- value: ±0.01% over 3 cm on axis
- applies_to: PPMS DynaCool 9 T magnet option
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Field Uniformity"
- quote: "9 T: ±0.01% over 3 cm on axis; magnet center located 4 cm above puck surface"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Field uniformity — 12 T
- value: ±0.1% over 5.5 cm on axis
- applies_to: PPMS DynaCool 12 T magnet option
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Field Uniformity"
- quote: "12 T: ±0.1% over 5.5 cm on axis; magnetic center located 4 cm above puck surface"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Field uniformity — 14 T
- value: ±0.1% over 5.5 cm on axis
- applies_to: PPMS DynaCool 14 T magnet option
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Field Uniformity"
- quote: "14 T: ±0.1% over 5.5 cm on axis; magnet center located 4 cm above puck surface"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Field uniformity — reference point (corroboration)
- value: uniform region centered 4.05 cm above puck surface
- applies_to: PPMS DynaCool (all magnets)
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 3 (printed page 1), footnote "**" to "Field Uniformity"
- quote: "**Uniformity range is centered 4.05 cm above the surface of a standard transport puck; this point represents the center of an installed VSM coilset."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Max field charging rate (per magnet)
- value: 9 T: 200 Oe/s; 12 T: 100 Oe/s; 14 T: 100 Oe/s
- applies_to: PPMS DynaCool 9 T / 12 T / 14 T magnet options
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 3 (printed page 1), "Specifications / PPMS DynaCool", row "Max Field Charging Rate"
- quote: "9 T: 200 Oe/s; 12 T: 100 Oe/s; 14 T: 100 Oe/s"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Min field charging rate (per magnet)
- value: 9 T: 0.1 Oe/s; 12 T: 0.2 Oe/s; 14 T: 0.2 Oe/s (typical)
- applies_to: PPMS DynaCool 9 T / 12 T / 14 T magnet options
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 3 (printed page 1), "Specifications / PPMS DynaCool", row "Min Field Charging Rate"
- quote: "9 T: 0.1 Oe/s; 12 T: 0.2 Oe/s; 14 T: 0.2 Oe/s; (typical)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Minimum time to full field (per magnet)
- value: 9 T: < 8 min; 12 T: < 25 min; 14 T: < 40 min (typical)
- applies_to: PPMS DynaCool 9 T / 12 T / 14 T magnet options
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Min Time to Full Field"
- quote: "9 T: less than 8 min (typical) 12 T: less than 25 min (typical) 14 T: less than 40 min (typical)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Field control modes
- value: Driven mode: Linear, Oscillating, No Overshoot
- applies_to: PPMS DynaCool (all magnets)
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Control Modes"
- quote: "Driven Mode: Linear, Oscillating, No Overshoot"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnet power supply current
- value: 9 T: 60 A; 12 T: 120 A; 14 T: 120 A
- applies_to: PPMS DynaCool 9 T / 12 T / 14 T magnet options
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Power Supply"
- quote: "9 T: 60 A; 12 T: 120 A; 14 T: 120 A"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 4. Sample chamber bore, puck and per-option sample-size limits

### Sample chamber clear bore diameter
- value: 2.5 cm (1 inch) clear bore
- applies_to: PPMS DynaCool base system (all magnets)
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "General System Details / Sample Space Size"
- quote: "Clear bore 2.5 cm (1 inch) diameter"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample chamber diameter — classic PPMS (for comparison)
- value: 2.6 cm diameter
- applies_to: classic (legacy) PPMS
- source_url: https://qdusa.com/siteDocs/productBrochures/1070-002.pdf
- document_title: PPMS Physical Measurement Property System Product Description (1070-002 Rev. C1)
- location: PDF page 1, "Features" bullet list
- quote: "Sample chamber has 2.6 cm diameter to accommodate custom probes"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample puck diameter
- value: 2.3 cm (0.91 inch) diameter disk
- applies_to: PPMS DynaCool standard sample puck
- source_url: https://www.nanophys.kth.se/nanolab/ppms/4307-004%20Dynacool%20Digital%20User%20Manual%20Set/02%201307-110%20Rev%20D1%20Dynacool%20User's%20Manual.pdf
- document_title: DynaCool User's Manual, Part Number 1307-110, D1 (Quantum Design; fifth edition November 2017) — mirrored by KTH
- location: PDF page 35, Chapter 2, text below "Figure 2-10. Top and bottom views of a sample puck"
- quote: "The puck is a 2.3 cm (0.91 inch) diameter disk constructed of high conductivity copper for maintaining high thermal uniformity."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample puck electrical interface
- value: 12-pin puck connector
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 2, section "Sample Mounting"
- quote: "providing at the bottom of the sample chamber a 12-pin connector pre-wired to the system electronics. This connector allows you to plug in a removable sample insert (or "puck")"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### VSM (standard bore) coil set bore diameter — sample size limit
- value: Bore diameter 6.3 mm; coil separation 9 mm
- applies_to: PPMS DynaCool VSM option D525 (standard bore coil set)
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 9 (printed page 7), "Vibrating Sample Magnetometer Specifications", "Coil Set Dimensions"
- quote: "Bore Diameter: ... 6.3 mm" ; "Coil Separation: ... 9 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### VSM accuracy reference sample dimensions
- value: ±0.5% accuracy using 2.8 mm dia. × 4 mm tall cylinder
- applies_to: PPMS DynaCool VSM option D525
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 9 (printed page 7), "Vibrating Sample Magnetometer Specifications", "Accuracy"
- quote: "± 0.5%, using 2.8 mm dia. × 4 mm tall cylinder (shape of included Pd reference)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### VSM Large Bore Coil Set bore diameter — larger sample limit
- value: Bore diameter 12 mm; coil separation 12.2 mm
- applies_to: PPMS DynaCool VSM Large Bore Coil Set option D529
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_LBCS_VSM.pdf
- document_title: Magnetometry / Large Bore Coil Set (VSM) / PPMS DynaCool (D529) / PPMS VersaLab (V529) (1084-500 Rev. J0)
- location: PDF page 1, "Large Bore Coil Set (VSM) Specifications", "Coil Set Dimensions"
- quote: "Bore Diameter: ... 12 mm" ; "Coil Separation: ... 12.2 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Heat capacity calorimeter platform area (max sample footprint)
- value: 3 mm × 3 mm
- applies_to: PPMS DynaCool Heat Capacity option D650
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_Heat_Capacity.pdf
- document_title: Thermal Measurements / Heat Capacity / PPMS DynaCool (D650) / PPMS VersaLab (V650) (1084-500 Rev. J0)
- location: PDF page 1, "Heat Capacity Specifications (for Zero Field)", "Calorimeter Platform Area (maximum sample footprint)"
- quote: "Calorimeter Platform Area (maximum sample footprint): ... 3 mm × 3 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### ACMS II coil set bore diameter
- value: 8 mm
- applies_to: PPMS DynaCool AC Susceptibility option ACMS II (D505)
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 15 (printed page 13), "AC Measurement System (ACMS II) Specifications (for zero-field)", "Coil Set Dimensions / Bore Diameter"
- quote: "Bore Diameter: ... 8 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Resistivity (DC Resistance / ETO) puck sample area
- value: UNKNOWN (not found in sources fetched) — only puck diameter (2.3 cm, above) and part number "Resistivity Puck (QD part number: 8084-109)" stated
- applies_to: PPMS DynaCool DC Resistance option D400 / ETO D605
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 5 (printed page 3), figure caption
- quote: "Resistivity Puck (QD part number: 8084-109)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### TTO sample size limits
- value: UNKNOWN (not found in sources fetched) — only a footnote that range depends on sample aspect ratio
- applies_to: PPMS DynaCool Thermal Transport option D670
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_TTO.pdf
- document_title: Thermal Measurements / Thermal Transport (TTO) / PPMS DynaCool (D670) / PPMS VersaLab (V670) (1084-500 Rev. J0)
- location: PDF page 2, footnote "*" to specifications table
- quote: "*Range estimates can depend significantly on an individual sample's aspect ratio and heat capacity."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Torque magnetometer sample volume / weight (option)
- value: available sample volume 1.5 mm × 1.5 mm × 1.5 mm; max sample weight 10 mg; chip 6 mm × 6 mm × 1 mm
- applies_to: PPMS DynaCool Torque Magnetometer option D550
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 8 (printed page 6), "Torque Magnetometer Specifications", "Physical Parameters"
- quote: "Chip Size: ... 6 mm × 6 mm × 1 mm" ; "Available Sample Volume: ... 1.5 mm × 1.5 mm × 1.5 mm" ; "Maximum Sample Weight: ... 10 mg"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Dilatometer ideal sample size (option)
- value: 2 ± 0.05 mm × 2.5 mm × 3 mm
- applies_to: PPMS DynaCool Dilatometer option D680
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 19 (printed page 17), "Dilatometer Specifications", "Ideal Sample Size*"
- quote: "Ideal Sample Size*: ... 2 ± 0.05 mm × 2.5 mm × 3 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Dilution refrigerator user-experiment space (option)
- value: 0.88" (22 mm) diameter × 1.4" (35 mm) long cylinder
- applies_to: PPMS DynaCool Dilution Refrigerator option D850
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 22 (printed page 20), "Dilution Refrigerator Specifications", "Space for User Experiments"
- quote: "0.88" (22 mm) diameter by 1.4" (35 mm) long cylindrical volume"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 5. Cooling

### Cryocooler type
- value: single two-stage pulse tube cryocooler; cryogen-free
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 1, introductory paragraph
- quote: "The system uses a single, two-stage pulse tube cryocooler for both the superconducting magnet and the temperature control system"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Pulse tube stage temperatures
- value: 1st stage ~45 K; 2nd stage ~4.2 K
- applies_to: PPMS DynaCool base system
- source_url: https://www.nanophys.kth.se/nanolab/ppms/4307-004%20Dynacool%20Digital%20User%20Manual%20Set/02%201307-110%20Rev%20D1%20Dynacool%20User's%20Manual.pdf
- document_title: DynaCool User's Manual, Part Number 1307-110, D1 (Quantum Design) — KTH mirror
- location: PDF page 64, Section 4.2.1 "Pulse Tube Cryocooler"
- quote: "The pulse tube cryocooler has two cooling stages. The first stage typically runs at ~ 45 K, while the second stage typically runs at ~ 4.2 K."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cooling power (base system, in watts)
- value: UNKNOWN (not found in sources fetched) — no numeric cryocooler cooling-power figure appears in [A], [B], [C], or [K]. Only option-level sample-stage cooling powers are stated (He-3 and DR, below).
- applies_to: PPMS DynaCool base system
- source_url: n/a
- document_title: n/a
- location: n/a
- quote: n/a
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cooling power — Helium-3 refrigerator option (sample stage)
- value: 6 μW at 0.5 K; 80 μW at 1.0 K
- applies_to: PPMS DynaCool Helium-3 Refrigerator option D825A/V
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 21 (printed page 19), "Helium-3 Refrigerator Specifications", "Cooling Power"
- quote: "6 μW at sample stage at 0.5 K 80 μW at sample stage at 1.0 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cooling power — Dilution refrigerator option (sample stage)
- value: 0.25 μW at 100 mK
- applies_to: PPMS DynaCool Dilution Refrigerator option D850
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 22 (printed page 20), "Dilution Refrigerator Specifications", "Cooling Power"
- quote: "0.25 μW at sample stage at 100 mK"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample cooldown time (300 K to 1.9 K)
- value: 40 minutes (typical), 300 K to stable 1.9 K
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Sample Cool Down Time"
- quote: "300 to 1.9 K (stable) in 40 minutes (typical)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### System startup (initial cooldown from room temperature) time, per magnet
- value: 9 T: 16 hours; 12 T: 30 hours; 14 T: 40 hours (typical)
- applies_to: PPMS DynaCool 9 T / 12 T / 14 T magnet options
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "System Startup Time"
- quote: "9 T: 16 hours (typical); 12 T: 30 hours (typical); 14 T: 40 hours (typical)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### System startup time (corroboration, user manual)
- value: about 16 hours (9 T)
- applies_to: PPMS DynaCool 9 T
- source_url: https://www.nanophys.kth.se/nanolab/ppms/4307-004%20Dynacool%20Digital%20User%20Manual%20Set/02%201307-110%20Rev%20D1%20Dynacool%20User's%20Manual.pdf
- document_title: DynaCool User's Manual, Part Number 1307-110, D1 (Quantum Design) — KTH mirror
- location: PDF page 17, Chapter 1 "Quick Start: System Startup and Cool Down", "Wait for Cool Down"
- quote: "A typical cool down time for a 9 T DynaCool is about 16 hours."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Helium gas consumption (bottled gas, no liquid cryogens)
- value: ~500 liters STP per cooldown to charge circulation loop; < 10 liters per purge/vent
- applies_to: PPMS DynaCool base system
- source_url: https://www.nanophys.kth.se/nanolab/ppms/4307-004%20Dynacool%20Digital%20User%20Manual%20Set/02%201307-110%20Rev%20D1%20Dynacool%20User's%20Manual.pdf
- document_title: DynaCool User's Manual, Part Number 1307-110, D1 (Quantum Design) — KTH mirror
- location: PDF page 34, Chapter 2 (helium gas supply)
- quote: "A cool down will require approximately 500 liters STP of helium to charge the circulation loop. A typical purge or vent operation will use less than 10 liters."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Integrated cryopump / high vacuum
- value: < 10^-4 Torr in under 10 minutes; spec table "< 0.1 mTorr"
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 1, section "Integrated High-Vacuum"
- quote: "the cryo-pump evacuates the sample chamber to less than 10-4 Torr in under 10 minutes."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Maintenance intervals
- value: ~2 years compressor adsorber; ~4 years pulse tube (40,000–60,000 h); ~6 months scroll pump tip seal
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Maintenance Interval"
- quote: "~2 years for the Cryocooler compressor ... ~4 years for the Pulse Tube cryocooler (designed for maintenance every 40,000 to 60,000 hours ... ) ~6 months scroll pump tip-seal replacement"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Power requirements
- value: System cabinet 200-230 V, 50/60 Hz, 30 A single phase; compressor 3-phase
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Power Requirements*"
- quote: "System Cabinet: 200-230 V, 50/60 Hz, 30 A, single phase Compressor: 3 Phase."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Dimensions and weights (per magnet)
- value: Cabinet 67×70×100 cm, ~70 kg; Cryostat & Can Rack 9 T: 92×123×127 cm, ~271 kg; 12 T: 94×132×127 cm, ~318 kg; 14 T: 94×132×127 cm, ~328 kg; Compressor 69×50×62 cm, ~134 kg
- applies_to: PPMS DynaCool 9 T / 12 T / 14 T
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "System Dimensions and Weights*"
- quote: "Cryostat & Can Rack 9 T: 92 cm x 123 cm x 127 cm; ~271 kg Cryostat & Can Rack 12 T: 94 cm x 132 cm x 127 cm; ~318 kg Cryostat & Can Rack 14 T: 94 cm x 132 cm x 127 cm; ~328 kg"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 6. Electrical: channels, leads, excitation ranges

### Base system sample leads
- value: 12 electrical leads via 12-pin puck interface
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 1, section "Temperature Control"
- quote: "while maintaining the robust 12-pin sample puck interface from the original PPMS."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### ETO (AC Resistance, D605) — channel count
- value: up to 2 channels simultaneously
- applies_to: PPMS DynaCool ETO option D605
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_AC_Resistance_ETO.pdf
- document_title: Electrical Transport / AC Resistance (ETO) / PPMS DynaCool (D605) / PPMS VersaLab (V605) (1084-500 Rev. J0)
- location: PDF page 1, "Key Features"
- quote: "Simultaneous measurement of resistance on up to two channels with phase angle and quadrature voltage reported for diagnostics"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### ETO — resistance range
- value: 10 μΩ to 10 MΩ (4-probe); 2 MΩ to 5 GΩ (high-impedance 2-probe)
- applies_to: PPMS DynaCool ETO option D605
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_AC_Resistance_ETO.pdf
- document_title: Electrical Transport / AC Resistance (ETO) ... (1084-500 Rev. J0)
- location: PDF page 1, "Electrical Transport (ETO) Specifications (for zero-field)", "Resistance / Range"
- quote: "10 μΩ to 10 MΩ 2 MΩ to 5 GΩ (high-impedance 2-probe)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### ETO — excitation current, frequency, voltage ranges, sensitivity
- value: current 10 nA to 100 mA; frequency 0.1 to 200 Hz; voltage 10 mV to 10 V (2-probe); sensitivity 10 nΩ RMS typical
- applies_to: PPMS DynaCool ETO option D605
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_AC_Resistance_ETO.pdf
- document_title: Electrical Transport / AC Resistance (ETO) ... (1084-500 Rev. J0)
- location: PDF page 1, "Drive Parameters"
- quote: "Frequency Range: 0.1 to 200 Hz (nominal) Current Amplitude Range**: 10 nA to 100 mA ... Voltage Amplitude Range: 10 mV to 10 V (high-impedance 2-probe)" ; "Sensitivity: 10 nΩ RMS typical"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### ETO — operational range
- value: 1.8 to 400 K; 0 to 16 T
- applies_to: PPMS DynaCool ETO option D605
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_AC_Resistance_ETO.pdf
- document_title: Electrical Transport / AC Resistance (ETO) ... (1084-500 Rev. J0)
- location: PDF page 1, "Operational Range"
- quote: "1.8 to 400 K; 0 to 16 T"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### DC Resistance (Resistivity, D400) — channels
- value: 3 multiplexed 4-probe channels on one puck; optional 4th channel
- applies_to: PPMS DynaCool DC Resistance option D400
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 5 (printed page 3), "Electrical Transport / DC Resistance", "Key Features"
- quote: "Three multiplexed four-probe measurement channels accessible on a single puck" ; "Optional fourth channel for customized measurements"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### DC Resistance — range, current, sensitivity
- value: 10 μΩ to 5 MΩ; current 10 nA to 8 mA; compliance 4 V max; sensitivity 15 nV RMS typical
- applies_to: PPMS DynaCool DC Resistance option D400
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 5 (printed page 3), "DC Resistivity Specifications (for zero-field)"
- quote: "Range: 10 μΩ to 5 MΩ Sensitivity: 15 nV RMS typical* ... Current Range: 10 nA to 8 mA Compliance Voltage: 4 V, maximum Waveform: Low frequency square wave"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### van der Pauw–Hall (D542) — current range
- value: 2 nA to 8 mA; 10 μΩ to 5 MΩ (uses DC Resistance hardware)
- applies_to: PPMS DynaCool van der Pauw-Hall option D542
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 6 (printed page 4), "van der Pauw − Hall Transport Specifications*"
- quote: "Current Range: 2 nA to 8 mA" ; "*The vdP-H Option uses the DC Resistance hardware for measurements and thus shares its specifications."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Horizontal Rotator (D310) — channels
- value: 2 channels per sample board, each 4-probe; -10° to 370°; 0.0011°/step
- applies_to: PPMS DynaCool Horizontal Rotator option D310
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 7 (printed page 5), "Horizontal Rotator", "Key Features" and specifications
- quote: "Two channels per sample board, each channel provides 4-probe electrical contacts" ; "-10° to 370° 0.0011°/step"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### VSM (D525) — sensitivity / noise and moment range
- value: noise floor < 6.0×10^-7 emu @ 300 K; m_max [emu] = 40 / peak amplitude [mm]; 0.1–5 mm amplitude; 10–60 Hz
- applies_to: PPMS DynaCool VSM option D525
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 9 (printed page 7), "Vibrating Sample Magnetometer Specifications"
- quote: "Noise Floor*: < 6.0∙10-7 emu @ 300 K" ; "mmax [emu]= 40/Peak Amplitude [mm]" ; "0.1 to 5 mm peak, 2 mm (typical) 10 to 60 Hz, 40 Hz (typical)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### ACMS II (D505) — sensitivity, excitation, frequency
- value: AC sensitivity 1×10^-8 emu @ 10 kHz; DC moment sensitivity 5×10^-6 emu; drive 0.05 to 15 Oe peak; 10 Hz to 10 kHz
- applies_to: PPMS DynaCool ACMS II option D505
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 15 (printed page 13), "AC Measurement System (ACMS II) Specifications (for zero-field)"
- quote: "1∙10-8 emu @ 10 kHz ± 0.5° 5∙10-6 emu ± 1% 0.05 to 15 Oe (peak) 10 Hz to 10 kHz 8 mm 1.8 to 400 K; 0 to 16 T"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Heat Capacity (D650) — accuracy, resolution, addenda
- value: accuracy ±5% for 2–300 K (< ±2% typical); resolution 10 nJ/K @ 2 K; addenda 0.2 μJ/K @ 2 K, 15 mJ/K @ 400 K
- applies_to: PPMS DynaCool Heat Capacity option D650
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_Heat_Capacity.pdf
- document_title: Thermal Measurements / Heat Capacity / PPMS DynaCool (D650) / PPMS VersaLab (V650) (1084-500 Rev. J0)
- location: PDF page 1, "Heat Capacity Specifications (for Zero Field)"
- quote: "± 5% for 2 K to 300 K; ± < 2% typical 10 nJ/K @ 2 K 3 mm × 3 mm 0.2 μJ/K @ 2 K; 15 mJ/K @ 400 K 1.8 to 400 K; 0 to 16 T"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### TTO (D670) — ranges
- value: thermal conductivity 0.1 to 250 W/m·K @ 300 K; Seebeck 1 μV/K to 1 V/K; resistivity 10 μΩ to 5 MΩ; ZT accuracy ±15%
- applies_to: PPMS DynaCool Thermal Transport option D670
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_TTO.pdf
- document_title: Thermal Measurements / Thermal Transport (TTO) / PPMS DynaCool (D670) / PPMS VersaLab (V670) (1084-500 Rev. J0)
- location: PDF page 2, "Thermal Transport (TTO) Specifications (for zero-field)"
- quote: "0.1 to 250 W/m∙K @ T = 300 K" ; "1 μV/K to 1 V/K" ; "10 μΩ to 5 MΩ" ; "± 15 %"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### TTO — two-/four-probe mounting
- value: two- or four-probe configuration
- applies_to: PPMS DynaCool Thermal Transport option D670
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_TTO.pdf
- document_title: Thermal Measurements / Thermal Transport (TTO) ... (1084-500 Rev. J0)
- location: PDF page 1, "Key Features"
- quote: "Mounting hardware included for two- or four-probe configuration to best suit a particular sample's geometry"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 7. Temperature sweep rates and stability

### Temperature stability — DynaCool
- value: ±0.1% for T < 20 K; ±0.02% for T > 20 K (typical)
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4, "PPMS DynaCool Specifications", row "Temperature Control / Stability"
- quote: "+/-0.1% for T < 20 K (typical) +/-0.02% for T > 20 K (typical)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature accuracy — DynaCool
- value: ±1%
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 3 (printed page 1), "Specifications / PPMS DynaCool", row "Temperature Accuracy"
- quote: "± 1%"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature sweep rate — DynaCool base system (numeric spec)
- value: UNKNOWN (not found in sources fetched) — neither [B] nor [C] lists a numeric sweep-rate specification for DynaCool. Related documented statements: product page lists "Controlled temperature Sweep Mode" ([A]); user manual uses 20 K/min as an example set rate and describes ramping down at "> 5-10 K/minute" ([K], below); classic PPMS lists 6 K/min cooling / 10 K/min warming ([D], below).
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 4 spec table (no sweep-rate row present)
- quote: "Temperature Control Range: ... Stability: ... Sample Cool Down Time: ... System Startup Time:" (no sweep rate row)
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature ramp behaviour — user manual statements
- value: fast ramp-down "> 5-10 K/minute"; example set-point rate 20 K/min
- applies_to: PPMS DynaCool base system
- source_url: https://www.nanophys.kth.se/nanolab/ppms/4307-004%20Dynacool%20Digital%20User%20Manual%20Set/02%201307-110%20Rev%20D1%20Dynacool%20User's%20Manual.pdf
- document_title: DynaCool User's Manual, Part Number 1307-110, D1 (Quantum Design) — KTH mirror
- location: PDF page 68, Section 4.3.2 (chamber flow control); PDF page 17/19 Quick Start examples
- quote: "When the chamber temperature is ramping down quickly (> 5-10 K/minute), the main flow is typically set to its maximum value of 5000 sccm" ; "enter 298 K, 20 K/min"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature sweep rate — classic PPMS (for comparison)
- value: 6 K/min cooling, 10 K/min warming (typical)
- applies_to: classic (legacy) PPMS
- source_url: https://qdusa.com/siteDocs/productBrochures/1070-002.pdf
- document_title: PPMS Physical Measurement Property System Product Description (1070-002 Rev. C1)
- location: PDF page 2, "Specifications", row "Temperature Sweep Rate"
- quote: "6 K/min. cooling, 10 K/min. warming; (typical)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature slew rate — TTO option (measurement while ramping)
- value: ±0.5 K/min for T > 20 K; ±0.2 K/min for T < 20 K
- applies_to: PPMS DynaCool Thermal Transport option D670
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_TTO.pdf
- document_title: Thermal Measurements / Thermal Transport (TTO) ... (1084-500 Rev. J0)
- location: PDF page 2, "Speed of Acquisition / Typical Temperature Slew Rates"
- quote: "± 0.5 K/min, T > 20 K ± 0.2 K/min, T < 20 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Low-temperature noise improvement claim
- value: > 2× improved noise below 20 K vs previous PPMS
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 1, section "Temperature Control"
- quote: "the PPMS DynaCool offers better than 2X improved noise performance at temperatures below 20K than previous PPMS models."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 8. Optical access

### Optical access — base system
- value: UNKNOWN (not found in sources fetched) — no statement of optical windows or optical access on the base cryostat appears in [A], [B], [C] or [K]. Optical access is documented only via add-on probes (OMFP, FOSH, Photoconductivity MFP, light sources), below.
- applies_to: PPMS DynaCool base system
- source_url: n/a
- document_title: n/a
- location: n/a
- quote: n/a
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Optical access — Optical Multi-Function Probe option (D725A/B)
- value: axial free-beam optical port (SM1, 1" diameter) at top of probe; coatings 350–700 nm and 650–1050 nm; 350 to 5 K on DynaCool; 0 to 16 T
- applies_to: PPMS DynaCool Optical Multi-Function Probe option D725A/B
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 27 (printed page 25), "Optical Multi-Function Probe (OMFP)" text and specifications
- quote: "a wired access port (WAP) features an axial optical port window for free-beam experiments in the cryostat." ; "350 to 5 K (DynaCool)" ; "SM1 (1" diameter)" ; "350 to 700 nm, and 650 to 1050 nm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Optical access — VSM Fiber Optic Sample Holder option (D320)
- value: fiber-delivered light; sample max 1.6 mm length × 1.6 mm diameter; transmittance > 60% (325–900 nm UV holder; 375–2250 nm IR holder)
- applies_to: PPMS DynaCool FOSH option D320 (requires D525 VSM)
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 13 (printed page 11), "FOSH Specifications (VSM) (for zero-field)"
- quote: "Maximum Length: 1.6 mm Maximum Diameter: 1.6 mm Transmittance: > 60% of 325 nm to 900 nm; UV holder > 60% of 375 nm to 2250 nm; IR holder"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 9. Measurement options list (standard vs optional)

### Standard with base system
- value: integrated cryopump + vacuum gauge; 12-pin puck interface; MultiVu software; magnet controller; one magnet (9/12/14 T)
- applies_to: PPMS DynaCool base system
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 1, "Integrated High-Vacuum"; PDF page 2 "Sample Mounting", "MultiVu Software"
- quote: "The PPMS DynaCool comes with an integrated cryopump and vacuum gauge for controlling the sample environment."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Optional measurement options (brochure list)
- value: VSM; Heat Capacity; AC & DC Electrical Transport; He3 Refrigerator (to 0.5 K); Dilution Refrigerator (4 K to 50 mK); Thermal Transport; AC Susceptibility; Horizontal Rotator; Torque Magnetometry; Multi-Function Probe; Magneto-Optic (light source + FOSH); VSM Oven (to 1000 K)
- applies_to: PPMS DynaCool (all are separately ordered options)
- source_url: https://qdusa.com/siteDocs/productBrochures/1307-010.pdf
- document_title: Product Description ... PPMS DynaCool (1307-010 Rev. G0)
- location: PDF page 3, "Measurement Options" list
- quote: "• Vibrating Sample Magnetometer • Heat capacity • AC & DC Electrical Transport • He3-Refrigerator – continuous operation down to 0.5 K • Dilution Refrigerator – continuous operation from 4 K down to 50 mK • Thermal Transport • AC Susceptibility • Horizontal Rotator • Torque Magnetometry • Multi-Function Probe"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Optional measurement options — DynaCool model numbers and dependencies
- value: ETO D605; DC Resistance D400A [Incl. D415]; Rotator D310A/B [Incl. D415]; VSM D525; VSM Large Bore D529; VSM Oven D527 [Req. D525]; FORC D181 [Req. D525]; FOSH D320 UV/IR [Req. D525]; Pressure Cell (Magnetometry) D421 [Req. D525]; Torque Magnetometer D550 [Req. D310]; ACMS II D505A [Req. D525]; Thermal Transport D670; Heat Capacity D650; Dilatometer D680; ADR D810 [Req. D605 or D400A]; Helium-3 D825A/AV; Dilution Refrigerator D850A; MFP D450A/G/M [Req. D415], D450B/C; MFP Photoconductivity D790A/B; MFP CryoFMR D886B; Optical MFP D725A/B [Req. D415]; CryoFMR D882A/D880A/D885A/D887A; Cryo ST-FMR D888A/D889A
- applies_to: PPMS DynaCool
- source_url: https://qdusa.com/siteDocs/productBrochures/PPMS_Options_Compatibility_Table.pdf
- document_title: Compatibility Table / Sub-Kelvin Compatibility Kits (1084-500 Rev. J0)
- location: PDF page 1, column "PPMS DynaCool"
- quote: "AC Resistance (ETO) D605 ... DC Resistance D400A [Incl. D415] ... VSM D525 ... VSM Oven D527 [Req. D525] ... ACMS II D505A [Req. D525] ... Thermal Transport D670 ... Heat Capacity D650 ... Dilatometer D680"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sub-Kelvin option ranges and compatible measurements
- value: ADR 300 K – 0.1 K (ETO, Resistivity compatible; 0 T only); 3He 350 K – 0.4 K (ETO, Resistivity, Heat Capacity); DR 4 K – 0.05 K (ETO, Resistivity, Heat Capacity, AC Susceptibility; 0 to 14 T)
- applies_to: PPMS DynaCool with D810 / D825 / D850 options
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: PDF page 30 (printed page 28), "Sub-Kelvin Compatibility Kits" table; PDF page 20 ADR "0.1 to 2 K; 0 T"; PDF page 22 DR "0.05 to 4 K; 0 to 14 T"
- quote: "ADR 300 K – 0.1 K Compatible Compatible n/a ... 3He 350 K – 0.4 K Compatible Compatible ... DR 4 K – 0.05 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Options compatibility with 14 T magnet (fields "0 to 16 T" quoted for most options)
- value: ETO, DC Resistance, vdP-Hall, Rotator, Tq-Mag, VSM, LBCS, ACMS II, Heat Capacity, TTO, Dilatometer, MFPs each list operational range "0 to 16 T"; DR "0 to 14 T"; AC DR "0 to 12 T"; ADR "0 T"
- applies_to: PPMS DynaCool options (operational range statements)
- source_url: https://qdusa.com/siteDocs/productBrochures/1084-500.pdf
- document_title: PPMS Family Measurement Options (1084-500 Rev. J0)
- location: "Operational Range" rows on PDF pages 4–19, 22, 24, 25
- quote: "1.8 to 400 K; 0 to 16 T" (ETO, DC Resistance, VSM, ACMS II, Heat Capacity, Dilatometer); "0.05 to 4 K; 0 to 14 T" (DR); "0.05 to 4 K; 0 to 12 T" (AC DR)
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 10. Classic PPMS (non-DynaCool) 14 T / 16 T configuration

### Classic PPMS magnet configurations — 9 T, 14 T, 16 T
- value: 9 T, 14 T or 16 T longitudinal solenoid (select one; or no magnet)
- applies_to: classic (legacy) PPMS
- source_url: https://qdusa.com/siteDocs/productBrochures/1070-002.pdf
- document_title: PPMS Physical Measurement Property System Product Description (1070-002 Rev. C1)
- location: PDF page 2, "Magnet Configurations"
- quote: "Select from 9 T, 14 T, or 16 T longitudinal solenoid magnet configurations" ; "Systems may also be ordered without any installed magnet"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Classic PPMS — field range
- value: ±9 T, ±14 T, ±16 T
- applies_to: classic (legacy) PPMS
- source_url: https://qdusa.com/siteDocs/productBrochures/1070-002.pdf
- document_title: PPMS Physical Measurement Property System Product Description (1070-002 Rev. C1)
- location: PDF page 2, "Specifications", row "Field Range"
- quote: "± 9 T, ± 14 T, ± 16 T"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Classic PPMS — field uniformity per magnet
- value: 9 T: ±0.01% over 5.5 cm; 14 T: ±0.1% over 5.5 cm; 16 T: ±0.1% over 1.0 cm (on-axis)
- applies_to: classic (legacy) PPMS 9 T / 14 T / 16 T
- source_url: https://qdusa.com/siteDocs/productBrochures/1070-002.pdf
- document_title: PPMS Physical Measurement Property System Product Description (1070-002 Rev. C1)
- location: PDF page 2, "Specifications", row "Field Uniformity*"
- quote: "9 T: ± 0.01% over 5.5 cm on-axis 14 T: ± 0.1% over 5.5 cm on-axis 16 T: ± 0.1% over 1.0 cm on-axis"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Classic PPMS — max/min field charging rate per magnet
- value: 9 T: 190 Oe/s; 14 T: 100 Oe/s; 16 T: 160 Oe/s; min 0.1 Oe/s
- applies_to: classic (legacy) PPMS 9 T / 14 T / 16 T
- source_url: https://qdusa.com/siteDocs/productBrochures/1070-002.pdf
- document_title: PPMS Physical Measurement Property System Product Description (1070-002 Rev. C1)
- location: PDF page 2, "Specifications", rows "Max Field Charging Rate" and "Min Field Charging Rate"
- quote: "9 T: 190 Oe/s (> 1 T/min.) 14 T: 100 Oe/s (≈1 T/min.) 16 T: 160 Oe/s (≈1 T/min.)" ; "0.1 Oe/s"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Classic PPMS — temperature range, stability, accuracy, cooldown
- value: 1.9 to 400 K; stability ±0.2% (T<20 K), ±0.02% (T>20 K); accuracy ±1%; cooldown 40 min to stable 1.9 K from 300 K
- applies_to: classic (legacy) PPMS
- source_url: https://qdusa.com/siteDocs/productBrochures/1070-002.pdf
- document_title: PPMS Physical Measurement Property System Product Description (1070-002 Rev. C1)
- location: PDF page 2, "Specifications"
- quote: "1.9 to 400 K ± 0.2% (T < 20 K), ± 0.02% (T > 20 K); (typical) ± 1% 6 K/min. cooling, 10 K/min. warming; (typical) 40 minutes (typical time to stable 1.9 K from 300 K)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Classic PPMS — discontinued status
- value: discontinued; service continues (per page) until end of 2028
- applies_to: classic (legacy) PPMS
- source_url: https://qdusa.com/products/ppms.html
- document_title: Quantum Design North America - Products - Physical Property Measurement System (PPMS) obsolescence notice.
- location: Main page
- quote: "The original PPMS product has been discontinued."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Classic PPMS — electrical leads
- value: 12 electrical leads in cryostat insert
- applies_to: classic (legacy) PPMS
- source_url: https://qdusa.com/siteDocs/productBrochures/1070-002.pdf
- document_title: PPMS Physical Measurement Property System Product Description (1070-002 Rev. C1)
- location: PDF page 1, "Features"
- quote: "Versatile sample mounts couple easily to the 12 electrical leads built into the cryostat insert for consistently reliable electrical access"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## Notes / caveats
- 9 T field uniformity differs between the DynaCool brochure ("±0.01% over 3 cm on axis", [B]/[C]) and the classic PPMS ("±0.01% over 5.5 cm on-axis", [D]). Both are quoted as printed.
- Base-system cooling power (W), base-system numeric temperature sweep rate, base-system optical access, resistivity-puck sample area, and TTO sample dimensions were NOT found in any fetched source.
- The DynaCool User's Manual [K] is a Quantum Design document (Part Number 1307-110, D1, Nov 2017) but was fetched from an institutional mirror (KTH), not qdusa.com. qdusa.com itself does not expose the manual publicly in the pages fetched.
- Individual option PDFs [F]-[J] carry identical text to the corresponding pages of the master brochure [C]; both URLs are listed as sources.

## Sources fetched (successfully read)
1. https://qdusa.com/products/dynacool.html (HTML)
2. https://qdusa.com/siteDocs/productBrochures/1307-010.pdf (PDF, 4 pages; text-extracted)
3. https://qdusa.com/siteDocs/productBrochures/1084-500.pdf (PDF, 31 pages; text-extracted)
4. https://qdusa.com/siteDocs/productBrochures/1070-002.pdf (PDF, 2 pages; text-extracted)
5. https://qdusa.com/products/ppms.html (HTML)
6. https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_AC_Resistance_ETO.pdf (PDF, 1 page)
7. https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_Heat_Capacity.pdf (PDF, 1 page)
8. https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_TTO.pdf (PDF, 2 pages)
9. https://qdusa.com/siteDocs/productBrochures/1084-500_PPMS_LBCS_VSM.pdf (PDF, 1 page)
10. https://qdusa.com/siteDocs/productBrochures/PPMS_Options_Compatibility_Table.pdf (PDF, 1 page)
11. https://www.nanophys.kth.se/nanolab/ppms/4307-004%20Dynacool%20Digital%20User%20Manual%20Set/02%201307-110%20Rev%20D1%20Dynacool%20User's%20Manual.pdf (PDF, 127 pages; QD manual 1307-110 Rev. D1, institutional mirror)

## Failed fetches
- None failed outright. Note: WebFetch's built-in summarizer could not read any of the PDFs (returned raw binary); all PDF content above was obtained by downloading the file via WebFetch and extracting text locally with PyMuPDF. The Read tool's PDF rendering was unavailable (pdftoppm not installed).
- Not attempted / not found on qdusa.com: a DynaCool user manual hosted on qdusa.com; a standalone 14 T or 16 T magnet datasheet (the 14 T/16 T specs come from the 1070-002 and 1307-010/1084-500 brochures instead).
