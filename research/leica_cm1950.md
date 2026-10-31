# Leica Biosystems CM1950 cryostat — documented manufacturer specifications

Compiled 2026-10-31. Every value below was read on a page/PDF fetched in this session. Nothing is filled in from memory. Where a value was not found in a fetched source it is marked `UNKNOWN (not found in sources fetched)`.

## Important: two instrument generations are documented by Leica

Leica currently documents two CM1950 generations and the numbers differ between them. Each fact below states which one it applies to.

- **Gen A — "legacy" CM1950 (serial numbers below 20000, refrigerant R-452A).** Documented in the Instructions for Use V3.0 Rev ZA (05.2024) and the brochure 95.7826 Rev F (05/2023). Leica's flyer says "Comparative claims refer to Leica CM1950 cryostat without DualEcoTec cooling technology (serial number below 20000)".
- **Gen B — CM1950 with DualEcoTec cooling system (refrigerant R290), launched globally 11 Feb 2026.** Documented on the current product page and the flyer 250760 Rev A (12/2025). No IFU for this generation was found on leicabiosystems.com in this session.

Note on PDF text extraction: the IFU PDF was downloaded from leicabiosystems.com and converted to text locally (pdftotext / PyMuPDF). Printed page numbers below are the numbers printed on the IFU pages (PDF page index + 1).

---

## 1. Temperature ranges

### Cryochamber temperature range (Gen B, DualEcoTec)
- value: -5 °C to -35 °C, adjustable in 1 K increments
- applies_to: CM1950 with DualEcoTec cooling system (all configurations)
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat ("Leica CM1950 – The Cryostat with DualEcoTec cooling system")
- location: Specifications tab > Cooling > "Chamber temperature range"
- quote: "Chamber temperature range: -5°C to -35°C (adjustable in 1 k increments)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cryochamber temperature range (Gen A, legacy)
- value: 0 °C to -35 °C ±5 K, adjustable in 1 K increments, at 20 °C ambient
- applies_to: CM1950 legacy (R-452A), model numbers 14047742464/-465/-466/-467, 14047743909 (120 V/60 Hz)
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat, Instructions for Use, English, Order No. 14 0477 8U101 - Revision ZA, Version 3.0, Revision ZA - 05.2024
- location: Chapter 3 "Technical Data", printed page 22, table "Refrigeration system > Cryochamber > Temperature range"
- quote: "Temperature range 0 °C to -35 °C ±5 K, adjustable in 1 K increments, at ambient temperature of 20 °C"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cryochamber cool-down time (both generations, for context)
- value: Gen B: < 2 h from ambient (230 V/50 Hz and 120 V/60 Hz); Gen A: approx. 5 h to -25 °C, approx. 8 h to -35 °C
- applies_to: Gen B product page; Gen A IFU
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/ and https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 | Clinical Cryostat; Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Product page Specifications > Cooling; IFU Chapter 3, printed page 22
- quote: "Chamber cool down time from ambient: < 2 h (230V/50Hz and 120V/60Hz versions)" / "Cool down time to -25 °C at starting point and ambient temperature of 20 °C approx. 5 h"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Object head (specimen) temperature range (Gen B)
- value: -10 °C to -50 °C
- applies_to: CM1950 with DualEcoTec; "Specimen cooling" is listed in all three configurations (STANDARD, VACUUM, VACUUM/MOTOR)
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Cooling > "Specimen head temperature range"
- quote: "Specimen head temperature range: -10°C to -50°C"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Object head (specimen) temperature range (Gen A)
- value: -10 to -50 °C ± 3 K
- applies_to: CM1950 legacy with object head cooling (IFU: "Optional feature included in model number ... 14047742464, 14047742465, 14047742466, 14047742467"); brochure lists object head cooling under "Options"
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 23, "Refrigeration system > Object head cooling > Temperature range"
- quote: "Optional feature included in model number At 120 V/60 Hz: 14047742464, 14047742465, 14047742466, 14047742467 Temperature range -10 to -50 °C ± 3 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Corroboration (Gen A brochure, official FR PDF): "Options Dispositif de refroidissement de la tête de l'objet Fonctionne avec un compresseur séparé Plage de température -10 à -50 °C ±3 K" — https://www.leicabiosystems.com/sites/default/files/media_product-download/2023-08/Brochure_Leica_CM1950_Cryostat_FR_95.7826_Rev_F.pdf, "PLATEFORME LEICA CM1950", p. 7 "CARACTÉRISTIQUES TECHNIQUES".

---

## 2. Peltier element / quick-freeze stations

### Peltier element — documented extra cooling vs. quick-freeze shelf (Gen A)
- value: 17 K max. temperature difference to quick-freeze shelf, at chamber temperature -35 °C (+5 K); 2 Peltier stations
- applies_to: CM1950 legacy, all configurations (Peltier element is part of the freeze shelf, not listed as optional)
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 23, "Peltier element"
- quote: "Peltier element Max. difference in temperature to quick-freez shelf 17 K, at chamber temperature of -35 °C +5 K Number of freezing stations 2"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Quick-freeze shelf lowest temperature (Gen A)
- value: -42 °C (±5 K) at chamber temp. -35 °C (+5 K); 15+2 freezing stations; manual hot gas defrost
- applies_to: CM1950 legacy
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 23, "Quick-freeze shelf"
- quote: "Quick-freeze shelf Lowest temperature -42 °C (±5 K), at chamber temp. -35 °C (+5 K) Number of freezing stations 15+2 Defrosting Manual hot gas defrost"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Freezing shelf and quick-freeze (Peltier) station temperatures (Gen B)
- value: freezing shelf -42 °C; quick-freeze stations -59 °C (both at chamber temp. -35 °C); 15 + 2 quick freeze stations
- applies_to: CM1950 with DualEcoTec
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Cooling
- quote: "Freezing shelf lowest Temperature: -42°C (at chamber temp. -35°C) Quickfreeze stations temperature: -59°C (at chamber temp. -35°C) Number of freezing stations: 15 + 2 quick freeze stations"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Product page feature text (same URL, "Fast Freezing of Histology Specimens"): "The two integrated Peltier freeze stations ensure an efficient workflow and speed up freezing by reducing the temperature even more with just one touch."

### Peltier element operating-time limit (Gen A)
- value: automatically switched off after 10 minutes of use
- applies_to: CM1950 legacy (platform page FAQ)
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950-platform/leica-cm1950
- document_title: Leica CM1950 | Clinical Cryostat ("Leica CM1950 - The cryostat for laboratories with numerous specimens and varying specimen types")
- location: Knowledge Hub > FAQs > "Why is the operating time of the Peltier element limited to 10 minutes only?"
- quote: "To avoid "weakening" the freezing rate by a warming Peltier element, it is automatically switched off after 10 minutes of use."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

IFU corroboration (printed page ~41, control panel description): "The Peltier element provides additional cooling for the freezing stations." and "The specimen head and Peltier do not switch on until the chamber temperature reaches -5 °C".

---

## 3. Section thickness and trimming

### Section thickness range
- value: 1 to 100 µm
- applies_to: both generations (product page Gen B; IFU Gen A)
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Sectioning
- quote: "Section thickness range: 1 to 100 µm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

IFU corroboration: "Section thickness range 2 1 to 100 μm" — IFU V3.0 Rev ZA, Chapter 3, printed page 23 (footnote 2: "for additional details, see (→ p. 45 – Setting section/trim thickness)").

### Trimming thickness range
- value: 10 to 40 µm (clinical mode); 1 to 600 µm (research mode)
- applies_to: both generations
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Sectioning
- quote: "Trimming thickness range: 10 to 40 µm (clinical mode) 1 to 600 µm (research mode)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

IFU corroboration (printed page 23): "Trimming thickness range 2 Clinical: 10 to 40 μm Research: 1 to 600 μm". IFU printed page ~54 explains switching: "To switch from a trimming section thickness for research applications (1 - 600 μm) to a thickness for clinical applications (10, 20, 30 or 40 μm), press and hold down the TRIM/SECT button ... while switching on the instrument."

### Electronic coarse feed
- value: Single step 20 µm; slow 300 µm/s; fast 900 µm/s
- applies_to: both generations
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Sectioning
- quote: "Electronic coarse feed: Single : 20 µm Slow: 300 µm/s Fast: 900 µm/s"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 4. Specimen size, stroke, feed

### Maximum specimen size (Gen B product page)
- value: 80 x 50 x 25 mm (W x H x D)
- applies_to: CM1950 with DualEcoTec
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Sectioning
- quote: "Maximum specimen size (WxHxD): 80 x 50 x 25 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Maximum specimen size (Gen A IFU / brochure)
- value: 50 x 80 mm
- applies_to: CM1950 legacy
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 23, "Microtome"
- quote: "Maximum specimen size 50 x 80 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Horizontal specimen feed (total feed)
- value: 25 mm + 1 mm
- applies_to: CM1950 legacy (IFU); Gen B product page does not list horizontal feed
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 23, "Microtome"
- quote: "Horizontal specimen feed 25 mm + 1 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Vertical specimen stroke
- value: 59 mm (IFU: 59 mm ± 0.5 mm)
- applies_to: both generations
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Sectioning
- quote: "Vertical stroke: 59 mm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

IFU corroboration (printed page 23): "Vertical specimen stroke 59 mm ± 0.5 mm".

### Specimen retraction
- value: 20 µm (can be switched off / deactivated)
- applies_to: both generations
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Sectioning
- quote: "Specimen retraction: 20 µm (can be switched off)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sectioning speed (motorized configuration)
- value: Slow 0 to 50 (+35) strokes/min; Fast 0 to 85 (+35) strokes/min; Vmax 85 to 90 (+35) strokes/min
- applies_to: CM1950 legacy with optional motorized sectioning
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 23, "Microtome > Sectioning speed"
- quote: "Sectioning speed Slow: 0 to 50 (+35) strokes/min Fast: 0 to 85 (+35) strokes/min Vmax speed: 85 to 90 (+35) strokes/min"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 5. Specimen orientation

### Specimen orientation range
- value: ±8° (x-, y-axis)
- applies_to: CM1950 legacy (IFU + brochure); Gen B product page does not state orientation (UNKNOWN for Gen B from sources fetched)
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 23, "Microtome"
- quote: "Specimen orientation ±8 ° (x-, y-axis)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Brochure corroboration (official FR PDF, p. 7): "Orientation de l'objet ±8 ° (axe x, y)". EN brochure mirror (ISN Medical copy of 95.7826 Rev F): "Specimen orientation ±8 ° (x-, y-axis)".

---

## 6. Optional vs. standard features and accessories

### Configurations offered (Gen B, DualEcoTec) — what is standard vs. optional
- value: STANDARD (1491950STUS / STEU / STJP): Chamber cooling, Specimen cooling, UV-C light, Premium blade holder. VACUUM (1491950VCUS / VCEU / VCJP): adds Vacuum extraction system. VACUUM/MOTOR (1491950VMUS / VMEU / VMJP): adds Vacuum extraction system + Motorized sectioning.
- applies_to: CM1950 with DualEcoTec, US/EU/JP configuration codes
- source_url: https://www.leicabiosystems.com/histology-equipment/cryostats/leica-cm1950
- document_title: Leica CM1950 | Clinical Cryostat (global site)
- location: "Configurations" section
- quote: "STANDARD: 1491950STUS Chamber cooling Specimen cooling UV-C light Premium blade holder ... VACUUM/MOTOR: 1491950VMUS Chamber cooling Specimen cooling UV-C light Vacuum extraction system Motorized sectioning Premium blade holder"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Same table on the US page (https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/), "Configurations": codes 1491950STUS, 1491950VCUS, 1491950VMUS with rows Chamber cooling / Specimen cooling / UV-C light / Premium blade holder / Vacuum extraction system / Motorized sectioning. Conclusion from the table: in Gen B, specimen (Peltier-independent object head) cooling and UV-C are standard; vacuum extraction and motorized sectioning are optional configurations.

### Standard vs. optional (Gen A brochure 95.7826 Rev F)
- value: Standard: UVC disinfection, AgProtect coating, CryoZone, encapsulated microtome with specimen orientation. Optional: actively cooled object head (dual compressor), motorized sectioning drive, vacuum section waste removal system.
- applies_to: CM1950 legacy
- source_url: https://isnmedical.com/wp-content/uploads/2025/07/Brochure-Leica-CM1950-EN-95.7826-Rev-F.pdf (third-party mirror of Leica brochure 95.7826 Rev F 05/2023; official EN PDF URL not resolvable, see Failed fetches; official FR/DE PDFs on leicabiosystems.com carry the same table)
- document_title: LEICA CM 1950 PLATFORM — The cryostat for large numbers of specimen and varying specimen types (95.7826 Rev F • 05/2023)
- location: p. 7 "TECHNICAL SPECIFICATIONS", intro paragraph
- quote: "The Leica CM1950 basic instrument is equipped with UVC Disinfection, AgProtect™ antimicrobial nanosilver coating, CryoZone™ technology, and encapsulated microtome with specimen orientation."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Second quote, same location: "The instrument can be ordered with various options including actively cooled object head (dual compressor,) motorized sectioning drive, vacuum section waste removal system, and a wide range of accessories."

### Vacuum extraction system (optional)
- value: Optional; includes extraction nozzle for cleaning and suction nozzle for section flattening
- applies_to: CM1950 legacy (brochure); Gen B VACUUM and VACUUM/MOTOR configurations
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2023-08/Brochure_Leica_CM1950_Cryostat_FR_95.7826_Rev_F.pdf
- document_title: PLATEFORME LEICA CM1950 (95.7826 Rév. F • 05/2023)
- location: p. 7 "CARACTÉRISTIQUES TECHNIQUES" > "Dispositif d'aspiration sous vide"
- quote: "Dispositif d'aspiration sous vide En option, comprend une buse d'extraction pour le nettoyage et une buse d'aspiration pour l'aplanissement de la coupe"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

EN mirror wording (ISN Medical copy, p. 7): "Vacuum extraction system Optional, includes extraction nozzle for cleaning and suction nozzle for section flattening". IFU V3.0 Rev ZA, Chapter 4 "Standard Delivery", printed page 25: "Basic instrument WITHOUT motor and WITH extraction ... Standard scope of delivery as above, additionally: 1 Accessory kit (extraction) 14 0477 43300".

### UVC disinfection
- value: 30 or 180 minutes, user selectable; manual start yes, automatic start no, manual abort yes
- applies_to: both generations (standard; Gen B configurations list "UV-C light" in all three)
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 24, "UVC lamp"
- quote: "UVC lamp Manual start Yes Automatic start No Manual abort Yes Duration cycle Short cycle: 30 min Long cycle: 180 min"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Brochure corroboration (FR official PDF p. 7): "Désinfection par UVC 30 ou 180 minutes, sélectionnable par l'utilisateur". IFU V2.7 Rev X (search snippet from leicabiosystems.com-hosted PDF, not fully fetched): "This type of disinfection reduces the number of germs by at least 99.99 %."

### Motorized sectioning (optional)
- value: Optional; cannot be retrofitted
- applies_to: both generations
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950-platform/leica-cm1950
- document_title: Leica CM1950 | Clinical Cryostat (platform page)
- location: Features > Efficiency; Knowledge Hub > FAQs
- quote: "the Leica CM1950 cryostat can be ordered with a motor drive for fast and efficient sectioning of large numbers of specimen." / "No, it is not possible to retrofit a second compressor or motor drive."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

IFU 1.4 Intended purpose (printed page 10): "The Leica CM1950 is a semi-motorized (motorized specimen feeding), high-performance cryostat with an option for motorized sectioning."

### Blade holder / knife holder types
- value: CE blade holder (high- and low-profile disposable blades, lateral movement) — standard ("Premium blade holder" in Gen B configurations). CN and CNZ knife holders for reusable steel / tungsten carbide knives — optional accessories.
- applies_to: both generations
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Features > "Reproducible Frozen Section Quality"
- quote: "The CE blade holder accommodates both high- and low-profile disposable blades and can be moved laterally to utilize the entire blade length. ... The optional CNZ knife holders support various reusable knives, especially for hard objects."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

IFU V3.0 Rev ZA, Chapter 11.1 "Ordering information" (printed page 65) lists as optional accessories: "Blade holder CE-BB, assembly", "Knife holder attachment CN, assembly", "Knife holder attachment CN-Z, assembly", "Anti-roll plate 70-50 µm / 70-100 µm / 70-150 µm assembly", "Heat and cold extractor, assembly", "Storage system, assembly". Brochure (EN mirror p. 3): "1. Knife holder CN for steel knives (optional accessory) 2. Knife holder CNZ for steel or tungsten carbide knives (optional accessory)".

### Specimen cooling (object head cooling) — optional vs standard
- value: Gen A: option ("Operated with separate compressor", second compressor cannot be retrofitted). Gen B: listed as "Specimen cooling" in all three configurations (standard).
- applies_to: see above
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950-platform/leica-cm1950
- document_title: Leica CM1950 | Clinical Cryostat (platform page)
- location: Knowledge Hub > FAQs
- quote: "After turning on the cryostat, the compressor for the cabinet cooling will cool the cabinet down to -5 °C before the second compressor, for object cooling, can be activated."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 7. Electrical, dimensions, weight

### Nominal voltage / frequency (Gen A, US variant)
- value: 120 VAC (±10 %), 60 Hz
- applies_to: CM1950 legacy, US/Canada IFU variant (model numbers 14047742464, 14047742465, 14047742466, 14047742467, 14047743909)
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA (US English)
- location: Chapter 3 "Technical Data", printed page 21, top table
- quote: "Nominal voltage (±10 %) 120 VAC Nominal frequency 60 Hz"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Power consumption (Gen A, US variant)
- value: 1500 VA with object head cooling / 1300 VA without; max. start-up current 35 A eff. for 5 sec; power supply connector IEC 60320 C20; mains input fuse T15A T1
- applies_to: CM1950 legacy, 120 V/60 Hz
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA (US English)
- location: Chapter 3 "Technical Data", printed page 21
- quote: "Power consumption (with/ without object head cooling) 1500/1300 VA Max. start-up current for 5 sec. 35 A eff."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Same page: "Heat emission (max., with / without object head cooling) 1500/1300 J/s"; "A-weighted noise level, measured at 1 m distance < 70 dB (A)"; "Operating temperature +18 °C to +35 °C"; "Relative humidity (operation) 20 to 60 % RH non-condensing".

### Electrical requirements (Gen B, DualEcoTec)
- value: UNKNOWN (not found in sources fetched) — only "230V/50Hz and 120V/60Hz versions" and a relative claim "up to 50% reduction in power consumption" are stated; no VA/W figure found.
- applies_to: CM1950 with DualEcoTec
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications > Cooling; Features > "Reduce Environmental Impact"
- quote: "The instrument is engineered to improve energy usage, resulting in up to 50% reduction in power consumption when compared to previous Leica CM1950 cryostats models."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Flyer 250760 Rev A (https://www.leicabiosystems.com/sites/default/files/media_product-download/2026-02/Flyer-250760-Rev-A-CM1950-DualEcoTec.pdf, "LEICA CM1950 With DualEcoTec Cooling System", comparison table): "Regular refrigerant and power use | Up to 50% lower power consumption"; "Comparative claims refer to Leica CM1950 cryostat without DualEcoTec cooling technology (serial number below 20000)".

### Refrigerant
- value: Gen B: R290 (IPCC6 GWP 0,02). Gen A: 320 g R-452A (chamber); 147 g R-452A (object head, 120 V/60 Hz)
- applies_to: as stated
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/ ; https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 | Clinical Cryostat; IFU V3.0 Rev ZA
- location: Product page Specifications > Cooling; IFU Chapter 3 printed pages 22–23
- quote: "Refrigerant type: R290 (IPCC6 GWP: 0,02)" / "Refrigerant* 320 g, refrigerant R-452A" / "Refrigerant and quantity At 120 V/60 Hz: 147 g, refrigerant R-452A*"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Dimensions
- value: 700 x 850 x 1215 mm (W x D x H) without handwheel; 835 x 850 x 1215 mm with handwheel; working height 1025 mm (armrest), 900 mm (handwheel)
- applies_to: both generations (identical figures on Gen B page and Gen A IFU)
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Dimensions and Weight
- quote: "Overall size of device (Width x Depth x Height): 700 x 850 x 1215 (without handwheel) 835 x 850 x 1215 (with handwheel) Working height: 1025 mm (armrest) 900 mm (handwheel)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

IFU corroboration (printed page 21): "Overall size of device, without handwheel (width x depth x height) 700 x 850 x 1215 mm"; "Overall size of packging (width x depth x height) 960 x 820 x 1420 mm".

### Weight (Gen B)
- value: max. 172 kg with accessories
- applies_to: CM1950 with DualEcoTec
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Specifications tab > Dimensions and Weight
- quote: "Weight: Max. 172 kg with accessories"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Weight (Gen A)
- value: 145–193 kg empty weight without accessories, depending on configuration; 193 kg with motor and suction (platform page)
- applies_to: CM1950 legacy
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 21, "Dimensions and weights"
- quote: "Empty weight (without accessories) 145‑193 kg depending on configuration"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Platform page corroboration (https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950-platform/leica-cm1950, Specifications > General): "Weight (w/ motor and suct.): 193 kg"; "Operating temperature range: 18°C to 35°C".

---

## 8. Defrost cycle

### Cryochamber defrost (Gen A)
- value: Hot gas defrost; manual defrost yes; automatic defrost programmable with selectable time; 1 defrost in 24 h or manual; defrost time 12 minutes; automatic shut-off at chamber temperature above -5 °C
- applies_to: CM1950 legacy (all configurations)
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 22, "Refrigeration system > Cryochamber > Defrosting"
- quote: "Defrosting Hot gas defrosting Manual defrosting Yes Automatic defrosting Programmable Yes (hot gas defrost), selectable time Defrosting intervals 1 defrost in 24 h or manual hot gas defrost Defrost time 12 minutes Automatic shutoff defrost At chamber temperature of more than -5 °C"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Brochure corroboration (FR official PDF p. 7): "Dégivrage par gaz chaud, automatique ou à activation manuelle, 1 cycle de dégivrage automatique/24 heures, minuté (durée 12 min.)".

### Object head (specimen) cooling defrost (Gen A)
- value: Electrical heater; automatic defrost no; manual defrost yes; duration 15 min; defrost temperature 45 °C ±2 K
- applies_to: CM1950 legacy with object head cooling
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 3 "Technical Data", printed page 23, "Defrosting object head cooling"
- quote: "Defrosting Electrical heater Automatic defrosting No Manual defrosting Yes Defrost duration 15 min. Defrost temperature 45 °C ±2 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Specimen head behaviour during chamber defrost (Gen A)
- value: during automatic/manual chamber defrost the specimen head goes to -10 °C to -5 °C and specimen cooling turns off; after automatic defrost it re-enables after 4 hours once chamber is within 5 K of target
- applies_to: CM1950 legacy
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Chapter 8 "Working with the Instrument", printed page ~52–53, "Programming the defrost cycle"
- quote: "When the automatic defrost cycle begins, the specimen head temperature adjusts to a temperature between -10 °C and -5 °C (reduction of ice formation). The specimen head cooling turns off."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Same section: "The specimen cooling (controlled to set value) automatically turns back on after 4 hours, once the chamber temperature varies by less than 5 K from the target temperature." and "The manual defrost takes 12 min."

### Defrost cycle (Gen B)
- value: UNKNOWN (not found in sources fetched) — the DualEcoTec product page and flyer do not mention defrost.
- applies_to: CM1950 with DualEcoTec
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: n/a
- quote: n/a
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 9. Intended use and sample type

### Intended purpose (IFU)
- value: semi-motorized high-performance cryostat; freezes and sections varying human specimen material quickly for histological medical diagnosis by a pathologist (e.g. cancer diagnosis); suitable for in-vitro diagnostic applications
- applies_to: CM1950 legacy (IFU V3.0 Rev ZA); product pages for both generations state "For In Vitro Diagnostic Use."
- source_url: https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf
- document_title: Leica CM1950 Cryostat Instructions for Use V3.0 Rev ZA
- location: Section 1.4 "Intended purpose", printed page 10
- quote: "It is used to freeze and section varying human specimen material quickly. These sections are used for histological medical diagnosis by a pathologist, e.g. for cancer diagnosis. The Leica CM1950 is suitable for in-vitro diagnostic applications."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Also (same section): "Any other use of this instrument is considered as improper operation." Section 1.3: "The Leica CM1950 may be operated by trained laboratory personnel only. The instrument is intended for professional use only."

### IVD statement (product page, Gen B)
- value: For In Vitro Diagnostic Use
- applies_to: CM1950 with DualEcoTec
- source_url: https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/
- document_title: Leica CM1950 | Clinical Cryostat
- location: Overview section
- quote: "For In Vitro Diagnostic Use."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Clinical positioning / sample types (brochure)
- value: positioned for in-surgery (intra-operative) cancer diagnostics; multiple tissue types "from brain biopsies to lymph nodes"; optional object head cooling for "difficult samples such as brain or fatty tissue"
- applies_to: CM1950 legacy brochure 95.7826 Rev F
- source_url: https://isnmedical.com/wp-content/uploads/2025/07/Brochure-Leica-CM1950-EN-95.7826-Rev-F.pdf (third-party mirror; official FR version at https://www.leicabiosystems.com/sites/default/files/media_product-download/2023-08/Brochure_Leica_CM1950_Cryostat_FR_95.7826_Rev_F.pdf says the same)
- document_title: LEICA CM 1950 PLATFORM (95.7826 Rev F • 05/2023)
- location: p. 2 "DELIVER DIAGNOSTIC CONFIDENCE" / "ACCURATE ALIGNMENT"
- quote: "In-surgery cancer diagnostics relies on reproducible section quality within minutes. ... varying tissue types from brain biopsies to lymph nodes."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

Research use: the only "research" reference found is the trimming "research mode" (1 to 600 µm) on the product page and in the IFU ("trimming section thickness for research applications (1 - 600 μm)"). No explicit "research cryostat" intended-use statement was found in the sources fetched.

---

## Additional Gen B comparison data (flyer)

Leica flyer 250760 Rev A, "CM1950 Upgrade Comparison: Standard vs. DualEcoTec Cooling System" (https://www.leicabiosystems.com/sites/default/files/media_product-download/2026-02/Flyer-250760-Rev-A-CM1950-DualEcoTec.pdf):
- Chamber cooling: "Adjustable from 0°C to -35°C" (existing) vs "Adjustable from -5°C to -35°C" (DualEcoTec); "Less than 5 hours from ambient to -25°C" vs "Less than 2 hours from ambient to -25°C".
- Specimen cooling: "Adjustable –10°C to -50°C" for both; "3× faster cool-down and 33% greater temperature stability".
- Freezing: "Two integrated Peltier freeze stations for faster specimen freezing" (both).
- Sustainability: "Medium Global Warming Potential refrigerant" vs "Zero Global Warming Potential refrigerant"; "50% noise reduction"; "Cuts heat by 33%".

Third-party mirror of Leica flyer 250384 Rev A (07/2025), EN (https://www.triolab.no/media/optk4e1e/flyer-cm1950-dualecotec_en-250384-rev-a.pdf, "LEICA CM1950 LESS IS MORE"), technical table: "CRYOCHAMBER Temperature range -5 °C to -35 °C ±3 K, adjustable in 1 K increments, at ambient temperature of 20 °C Cooling time to -25 °C <2h (230V and 120V) and <3 h (100V)"; "OBJECT HEAD COOLING Temperature range -10 °C to -50 °C ± 3 K"; "15 + 2 quick freeze positions with minimun temperature of -59°C (17 K colder that freeze shelf)"; "15% lighter"; "up to 50% less power draw"; "11 dB (A) quieter". (Not an official leicabiosystems.com URL; the official EN flyer link on the product page is gated.)

---

## Sources fetched (successfully read in this session)

1. https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950/ — "Leica CM1950 | Clinical Cryostat" (DualEcoTec product page, US). Fetched via WebFetch and Tavily extract.
2. https://www.leicabiosystems.com/histology-equipment/cryostats/leica-cm1950 — same product page, global site (configurations table with EU/US/JP codes). Tavily extract.
3. https://www.leicabiosystems.com/us/histology-equipment/cryostats/leica-cm1950-platform/leica-cm1950 — "Leica CM1950 - The cryostat for laboratories with numerous specimens and varying specimen types" (legacy platform page with FAQs). WebFetch + Tavily extract.
4. https://www.leicabiosystems.com/sites/default/files/media_product-download/2024-06/Leica_CM1950_IFU_3v0ZA_US_en.pdf — Leica CM1950 Cryostat Instructions for Use, English, Version 3.0 Rev ZA, 05.2024 (94 pages). Downloaded via WebFetch (binary saved) and text-extracted locally; also Tavily extract passages.
5. https://www.leicabiosystems.com/sites/default/files/media_product-download/2023-08/Brochure_Leica_CM1950_Cryostat_FR_95.7826_Rev_F.pdf — "PLATEFORME LEICA CM1950", 95.7826 Rév. F 05/2023 (official FR brochure). Tavily extract, full text.
6. https://www.leicabiosystems.com/sites/default/files/media_product-download/2026-02/Flyer-250760-Rev-A-CM1950-DualEcoTec.pdf — "LEICA CM1950 With DualEcoTec Cooling System" flyer, 250760 Rev A 12/2025. Tavily extract, full text.
7. https://isnmedical.com/wp-content/uploads/2025/07/Brochure-Leica-CM1950-EN-95.7826-Rev-F.pdf — third-party (distributor) mirror of the English brochure 95.7826 Rev F 05/2023. Tavily extract, full text.
8. https://www.triolab.no/media/optk4e1e/flyer-cm1950-dualecotec_en-250384-rev-a.pdf — third-party (distributor) mirror of the English DualEcoTec flyer 250384 Rev A 07/2025. Tavily extract, full text.
9. https://files.leicabiosystems.com/US/en?keycode=CM1950 — IFU/SDS portal linked from the product page; fetched but the page contained no document links (only a "Request a document" form).

Search-result snippets only (not fully fetched; used only for corroboration notes above): https://www.leicabiosystems.com/sites/default/files/media_product-download/2023-08/Brochure_Leica_CM1950_Cryostat_DE_95.7826_Rev_F.pdf (DE brochure, snippet showed "Peltier-Element Max. Temperaturdifferenz -17 °C"); https://www.leicabiosystems.com/sites/default/files/media_product-download/2022-05/Leica_CM1950_IFU_2v6W_US_en.pdf and ..._IFU_2v7X_en.pdf (older IFU revisions).

## Failed fetches

1. https://www.leicabiosystems.com/sites/default/files/media_product-download/2023-08/Brochure_Leica_CM1950_Cryostat_EN_95.7826_Rev_F.pdf — URL inferred from the DE/FR file-name pattern; returned "Sorry, we could not find that page" (404). The official EN brochure download on the product page is a gated link ("#"), so no direct official EN URL was obtained.
2. "Brochure - Leica CM1950 Cryostat US - EN (211322 Rev A)" — listed on the US product page as a gated download; no direct URL found by search; not fetched.
3. "Flyer - Leica CM1950 DualEcotec - EN (250385 Rev A)" — listed on the product page as gated; not fetched (the 250760 Rev A flyer, which is directly hosted, was fetched instead).
4. WebFetch text-extraction of the IFU PDF (item 4 above) failed ("Flate-compressed binary"), but the binary was saved and converted locally with pdftotext/PyMuPDF, so the document itself counts as fetched.
5. No Instructions for Use for the DualEcoTec (R290) generation was found on leicabiosystems.com.
