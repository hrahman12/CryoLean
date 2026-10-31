# Lake Shore Cryotronics — documented specifications

Accessed: 2026-10-31. Rule applied: only values read on pages/PDFs fetched in this session. Anything not found is marked `UNKNOWN (not found in sources fetched)`.

Sources: lakeshore.com product specification pages (HTML) and the Lake Shore "Probe Stations" catalog PDF (CRX-4K on pp. 42-43, CRX-VF on pp. 44-45), the "CCR vacuum cryostats" datasheet PDF (CCS-100/300/400 series, code "102126"), the "Lake Shore Probe Stations" family flyer PDF, and the Lake Shore cryostat window and feedthrough guides. PDF text was extracted locally with `pdftotext -layout`; in the extracted text "±", "µ" and "Ω" rendered as "�" — where the HTML spec page carried the same row legibly, the HTML version of the quote is used.

---

## 1. CRX-VF cryogenic probe station (cryogen-free, vertical-field superconducting magnet)

### Temperature range
- value: 10 K to 420 K (standard)
- applies_to: CRX-VF, standard configuration
- source_url: http://www.lakeshore.com/products/categories/overview/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (overview page)
- location: body text under product heading
- quote: "It operates over a standard range of 10 K to 420 K."
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature vs. magnetic field table
- value: ±2.5 T at 10 K (up to 6 probe arms installed); ±2 T from 11 K to 400 K; ±1 T from 401 K to 420 K
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Temperature¹" table (columns: Magnetic field | Temperature range | Configuration); footnote 1
- quote: "±2.5 T" | "10 K" | "Up to 6 probe arms installed" ; "±2 T" | "11 K to 400 K" ; "±1 T" | "401 K to 420 K" ; footnote: "Base temperature assumes heat load for probes thermally anchored as listed in the probing section"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- note: the printed catalog (pp. 44) gives the same table as "±2 T  10 K to 400 K" and "±1 T  400 K to 420 K".

### Temperature control stability
- value: ±50 mK at base (no heater control); ±10 mK from 10 K to 420 K
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Control stability" table
- quote: "<10 K": "±50 mK" ; "10 K to 100 K": "±10 mK" ; "101 K to 250 K": "±10 mK" ; "251 K to 350 K": "±10 mK" ; "351 K to 420 K": "±10 mK"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnetic field
- value: ±2.5 T maximum (±25 kOe), vertical, superconducting solenoid
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Magnetic field" section
- quote: "Magnet type: Superconducting solenoid" ; "Field of orientation: Vertical (perpendicular to the sample plane)" ; "Field capability: ±25 kOe (±2.5 T) maximum"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnetic field homogeneity and probe-tip movement in field
- value: 0.5 % over 10 mm diameter; 1.0 % over 25 mm diameter; landed probe tip movement < 5 µm over full field ramp
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Magnetic field" section
- quote: "Field homogeneity: 0.5% over 10 mm diameter; 1.0% over 25 mm diameter" ; "<5 µm full field ramp"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnetic field — customizable maximum
- value: up to 3 T (with specialized probes)
- applies_to: CRX-VF custom configuration
- source_url: http://www.lakeshore.com/products/categories/overview/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (overview page)
- location: feature bullets under product heading
- quote: "Customizable up to 3 T with specialized probes"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample size / sample stage
- value: 51 mm (2 in) diameter maximum sample; included holder SH-1.25-G accepts up to 31.8 mm (1.25 in)
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Sample" section; "Station details"
- quote: "Maximum sample size: 51 mm (2 in) diameter" ; "Removable SH-1.25-G, 31.8 mm (1.25 in) maximum sample size, grounded" ; "Sample backside optical access: Not an option" ; "Sample rotation: Not an option"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Number of probe arms
- value: 6 maximum
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Probing configurations"
- quote: "Maximum probes: 6" ; "All probes can land at single point in a 25.4 mm (1 in) diameter circle"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (Lake Shore Probe Stations family flyer, https://www.lakeshore.com/docs/default-source/product-downloads/literature/probestationfamily.pdf?sfvrsn=3f78b12e_15, table row CRX-VF): "2.5 T vertical field superconducting magnet  6" (Max standard probe arms column)

### Optical access (window)
- value: vacuum-chamber top viewport 63.5 mm (2.50 in) diameter fused quartz, 54.0 mm (2.13 in) viewing area; radiation-shield viewport 50 mm (1.97 in) IR-absorbing window, 50 mm viewing area
- applies_to: CRX-VF (top viewing only; backside optical access not an option)
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Vacuum chamber" and "Radiation shielding" sections
- quote: "Viewport: 63.5 mm (2.50 in) diameter fused quartz" ; "Viewing area: 54.0 mm (2.13 in) diameter" ; "Viewport: 50 mm (1.97 in) diameter IR absorbing window" ; "Viewing area: 50 mm (1.97 in) diameter"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Electrical connections — probe types (DC/RF, microwave, fibre)
- value: DC/RF probes with >100 GΩ isolation; microwave probes DC to 67 GHz; fibre-optic probes available; cooled probe mounts < 50 K
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Probing configurations"
- quote: "Electrical isolation >100 GΩ for low leakage measurements" ; "Frequency range DC up to 67 GHz for RF measurements" ; "Available for electro-optical measurements" ; "Cooled probe mounts: <50 K with sample at base temperature"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- overview page corroboration: "It performs C-V, I-V, microwave, and electro-optical probing" (catalog p. 44) / "C-V, I-V, microwave, and electro-optical probing" (HTML overview)

### Number of DC / RF lines
- value: UNKNOWN (not found in sources fetched) — the pages give the number of probe arms (6) and probe types, not a count of DC or RF lines
- applies_to: CRX-VF
- accessed: 2026-10-31

### Cooling power at a stated temperature
- value: 1 W at 4.2 K (2-stage closed-cycle refrigerator)
- applies_to: CRX-VF cryocooler (cooling source)
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Sample cooling assembly"
- quote: "Type: 3-stage (sample + magnet + radiation shield)" ; "Cooling source: 2-stage closed cycle refrigerator (CCR) with 1 W cooling power at 4.2 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Vibration
- value: < 1 µm at sample
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Vibration at sample" row
- quote: "Vibration at sample: <1 µm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cycle / cooldown time
- value: cycle 8.5 h (pump-down 1.5 h, station cooldown 5 h, warm-up 2 h)
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Cycle time" rows
- quote: "Cycle time: 8.5 h" ; "Pump down: 1.5 h" ; "Station cooldown: 5 h" ; "Station warmup: 2 h"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Vacuum
- value: standard < 1×10⁻⁵ Torr at base; PS-HV-CPX option < 5×10⁻⁷ Torr at base
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Vacuum" table (Standard TPS-FRG / PS-HV-CPX option)
- quote: Standard: "90 min (to reach <1 × 10-3 Torr)", room temperature "<5 × 10-4 Torr", base temperature "<1 × 10-5 Torr"; PS-HV-CPX option: "30 min", "<5 × 10-6 Torr", "<5 × 10-7 Torr"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cryogen consumption / utilities
- value: no cryogens required; CCR 3-phase power 6.6-6.9 kW (50 Hz) / 7.5-7.8 kW (60 Hz)
- applies_to: CRX-VF
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station
- document_title: CRX-VF cryogenic probe station (specifications page)
- location: "Cryogen consumption"; "Utilities"
- quote: "Room to base temperature (total): Not required" ; "Helium at 5 K: Not required" ; "6.6 to 6.9 kW at 50 Hz; 7.5 to 7.8 kW at 60 Hz"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 2. CRX-4K cryogenic probe station (cryogen-free closed-cycle; chosen as the Lake Shore CRX-4K target)

### Temperature range
- value: base 4.5 K; control range 5 K to 350 K (2 probe arms); 5.5 K base / 6 K to 350 K (4 arms); 6.0 K base / 6.5 K to 350 K (6 arms); 20 K to 675 K with PS-HTSTAGE option
- applies_to: CRX-4K, by number of probe arms installed
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K cryogenic probe station — "CRX-4K probe station specifications"
- location: "Temperature" table (Base temperature | Control range | Configuration)
- quote: "4.5 K" | "5 K to 350 K" | "2 probe arms installed" ; "5.5 K" | "6 K to 350 K" | "4 probe arms installed" ; "6.0 K" | "6.5 K to 350 K" | "6 probe arms installed" ; "20 K" | "20 K to 675 K" | "with PS-HTSTAGE option (not compatible with backside biasing of the sample)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Temperature control stability
- value: ±50 mK (<10 K); ±10 mK (10-250 K); ±20 mK (251-350 K); ±50 mK (351-675 K)
- applies_to: CRX-4K
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K probe station specifications
- location: "Control stability" table
- quote: "<10 K": "±50 mK" ; "10 K to 100 K": "±10 mK" ; "101 K to 250 K": "±10 mK" ; "251 K to 350 K": "±20 mK" ; "351 K to 675 K": "±50 mK"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Magnetic field
- value: no built-in magnet; optional ring magnet sample-holder kit "Up to ~0.19 T"
- applies_to: CRX-4K with PS-RING-MAG-KIT option
- source_url: https://www.lakeshore.com/docs/default-source/product-downloads/catalog/probestationcatalog_l.pdf?sfvrsn=c0f0f3c1_68
- document_title: Probe Stations (Lake Shore catalog)
- location: p. 14 "Probe station features by model" table, row CRX-4K, column "Ring magnet sample holder kit"; p. 42 "Magnetic field:" row
- quote: "Up to ~0.19 T" ; "Magnetic field: Ring magnet kit--see page 22"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (HTML spec page "Magnetic field"): "Ring magnet kit" (no field value stated on the HTML page)

### Sample size / sample stage
- value: 51 mm (2 in) diameter maximum sample; included holder SH-1.25-G, 31.8 mm (1.25 in); customizable to 102 mm (4 in) wafer
- applies_to: CRX-4K
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K probe station specifications
- location: "Sample" section; "Station details"
- quote: "51 mm (2 in) diameter" ; "Removable SH-1.25-G, 31.8 mm (1.25 in) maximum sample size, grounded"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration (catalog p. 42): "The CRX4K is designed to accommodate wafers as large as 102 mm (4 in) in diameter, with 51 mm (2 in) diameter probable regions."

### Number of probe arms
- value: 6 maximum
- applies_to: CRX-4K
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K probe station specifications
- location: "Probing configurations"
- quote: "Maximum probes: 6" ; "All probes can land at single point in a 25.4 mm (1 in) diameter circle"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Optical access (window)
- value: chamber viewport 63.5 mm (2.50 in) fused quartz, 54.0 mm (2.13 in) viewing area; radiation shield viewport 50 mm (1.97 in) IR-absorbing window; no backside optical access
- applies_to: CRX-4K
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K probe station specifications
- location: "Vacuum chamber" / "Radiation shielding"; "Sample"
- quote: "63.5 mm (2.50 in) diameter fused quartz" ; "54.0 mm (2.13 in) diameter" ; "50 mm (1.97 in) diameter IR absorbing window" ; "Sample backside optical access: Not an option"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Electrical connections — probe types
- value: DC/RF probes >100 GΩ isolation; microwave probes DC to 67 GHz; fibre-optic probes; cooled probe mounts < 20 K
- applies_to: CRX-4K
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K probe station specifications
- location: "Probing configurations"
- quote: "Electrical isolation >100 GΩ for low leakage measurements" ; "Frequency range DC up to 67 GHz for RF measurements" ; "Available for electro-optical measurements" ; "Cooled probe mounts: <20 K with sample at base temperature"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- Number of DC/RF lines: UNKNOWN (not found in sources fetched)

### Cooling power at a stated temperature
- value: 1 W at 4.2 K (2-stage CCR)
- applies_to: CRX-4K cooling source
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K probe station specifications
- location: "Sample cooling assembly"
- quote: "2-stage closed cycle refrigerator (CCR) with 1 W cooling power at 4.2 K" ; "Type: 2-stage (sample + radiation shield)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Vibration
- value: < 1 µm at sample
- applies_to: CRX-4K
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K probe station specifications
- location: "Vibration at sample"
- quote: "<1 µm"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cycle / cooldown time
- value: cycle 4 h (pump-down 0.5 h, cooldown 2 h, warm-up 1.5 h)
- applies_to: CRX-4K
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K probe station specifications
- location: "Cycle time"
- quote: "Cycle time: 4 h" ; "0.5 h" ; "2 h" ; "1.5 h"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Vacuum
- value: < 1×10⁻⁵ Torr at base and maximum temperature (standard TPS-FRG)
- applies_to: CRX-4K
- source_url: https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station
- document_title: CRX-4K probe station specifications
- location: "Vacuum (Standard TPS-FRG)"
- quote: "30 min (to reach <1 × 10-3 Torr)" ; "<5 × 10-4 Torr" ; "<1 × 10-5 Torr"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## 3. Janis / Lake Shore CCS-series closed-cycle (cryogen-free, sample-in-vacuum) cryostats — CCS-100, CCS-300S/ST, CCS-400/400H

### Temperature range
- value: CCS-100 <4 K to 325 K; CCS-300S <4 K to 325 K; CCS-300ST <4 K to 325 K; CCS-400 <4 K to 500 K; CCS-400H <4 K to 800 K
- applies_to: CCS series (minimum temperature depends on cold-head option; see next entry)
- source_url: http://www.lakeshore.com/products/product-detail/janis/4-k-cryocoolers-sample-in-vacuum-systems
- document_title: Cryogen-free vacuum cryostats
- location: product comparison table (Min temp / Max temp); highlights
- quote: "<4 K to 800 K" ; "Cryogen-free" ; "Sample in vacuum" ; CCS-100 "325 K"; CCS-400 "500 K"; CCS-400H "800 K"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- corroboration: https://www.lakeshore.com/products/product-detail/janis/ccs-100-cryostat "<4 K to 325 K"; https://www.lakeshore.com/products/product-detail/janis/ccs-400-series-cryostats CCS-400 "<4 K to 500 K", CCS-400H "<4 K to 800 K"; https://www.lakeshore.com/products/product-detail/janis/ccs-300-series-cryostats "<4 K to 325 K"

### Minimum temperature by cold-head option
- value: 204 head <9 K (CCS-100) / <10 K (CCS-400) / <12 K (CCS-400H); 204N <7 K / <8 K / <10 K; 101 <5 K (CCS-400, CCS-100 column blank in extraction) / "--" (CCS-400H); 408/415/418 <4 K (CCS-100) / <4 K (CCS-400) / <5 K (CCS-400H)
- applies_to: CCS-100, CCS-400, CCS-400H (CCS-300S/ST columns were blank in the extracted table layout)
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCS-100 Cryogen-free Sample in vacuum cryostats (<4 K to 800 K) — CCR vacuum cryostats datasheet, code 102126
- location: p. 2, "Specifications" table, rows "Minimum temp options" (204 / 204N / 101 / 408 / 415 / 418)
- quote: "Minimum temp options  204 … <9 K … <10 K  <12 K" ; "204N … <7 K … <8 K  <10 K" ; "408 … <4 K" ; CCS-400 column "<5 K" (101), "<4 K" (408)
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- caution: the pdftotext column alignment of this table is imperfect; the row/column mapping above is the best reading of the extracted layout and should be checked against the rendered PDF before use.

### Magnetic field
- value: none (no magnet is offered on the CCS-series pages fetched)
- applies_to: CCS-100 / 300 / 400 series
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCR vacuum cryostats datasheet (102126)
- location: whole document (no magnet row); only the optional Cernox sensor is described as "magnetic field independent"
- quote: "CX-1050-CU-HT-1.4M  Cernox® magnetic field independent, calibrated"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cooling power at a stated temperature (bare cold head)
- value: 204: 7 W at 20 K; 204N: 3 W at 10 K; 101: 0.2 W at 4.2 K; 408: 1 W at 4.2 K; 415: 1.5 W at 4.2 K; 418: 2 W at 4.2 K (bare-head cooling power)
- applies_to: CCS-series cold-head options
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCR vacuum cryostats datasheet (102126)
- location: p. 4, "Configure your cryostat" → "2. Select cryostat configurations" → "Cold head"
- quote: "204  7 W at 20 K bare head cooling power" ; "204N  3 W at 10 K bare head cooling power" ; "101  0.2 W at 4.2 K bare head cooling power" ; "408  1 W at 4.2 K bare head cooling power" ; "415  1.5 W at 4.2 K bare head cooling power" ; "418  2 W at 4.2 K bare head cooling power"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cryocooler type (GM vs pulse tube, model)
- value: "closed-cycle refrigerator"; cold-head numbers 204/204N/101/408/415/418 only — GM vs pulse tube and manufacturer are NOT stated on the fetched pages
- applies_to: CCS series
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCR vacuum cryostats datasheet (102126)
- location: p. 1 "Featured components"; p. 2 "Facility requirements"
- quote: "Choice of cryocooler to match performance and cooling requirements" ; cold-head maintenance interval "13,000 h" / "30,000 h" / "10,000 h" (by head group)
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Cooldown time
- value: CCS-100 1 h to 2 h; CCS-300S/ST 1.5 h to 2.5 h; CCS-400 1.5 h to 3 h; CCS-400H 2 h to 2.5 h (approximate, as read from the extracted table)
- applies_to: CCS series
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCR vacuum cryostats datasheet (102126)
- location: p. 2, "Specifications" table, row "Cooldown time"
- quote: "1 h to 2 h" ; "1.5 h to 2.5 h" ; "1.5 h to 3 h" ; "2 h to 2.5 h"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- caution: column assignment taken from extracted-text layout; verify against rendered PDF.

### Temperature stability
- value: ±50 mK (measured with a temperature controller; may be higher within ~15 K of base)
- applies_to: CCS series
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCR vacuum cryostats datasheet (102126)
- location: p. 2, "Specifications" table, row "Typical temperature stability¹" and footnote 1
- quote: "±50 mK" ; "1 Measured with a temperature controller; may be higher at temperatures within ~15 K of base temperature"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Sample size / sample stage diameter
- value: UNKNOWN (not found in sources fetched) — pages list sample-holder part numbers (SH-BLANK-1.5-STD, SH-OPTICAL-1.5-STD, SH-RESISTIVITY-1.5-STD, SH-BLANK-1.5-800, SH-OPTICAL-1.5-800) but no explicit stage diameter
- applies_to: CCS series
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCR vacuum cryostats datasheet (102126)
- location: p. 4, "Sample holders"
- quote: "SH-BLANK-1.5-STD  Blank" ; "SH-OPTICAL-1.5-STD  Optical" ; "SH-RESISTIVITY-1.5-STD  Resistivity"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

### Optical access (windows)
- value: optical variants (CCS-100, 300S, 400, 400H) have windows; standard fused silica on "1.63 in clear view" Environment-by-Janis ports; window-block size 83-85 mm (3.25-3.75 in) square (CCS-100, CCS-400/400H), 38 mm (1.5 in) square (CCS-300S). Number of windows: UNKNOWN (not found in sources fetched)
- applies_to: CCS-100 / 300S / 400 / 400H (optical); CCS-300ST is non-optical
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCR vacuum cryostats datasheet (102126)
- location: p. 1 "Cryostat models"; p. 2 "Specifications" row "Window block size"
- quote: "CCS-100 optical, vacuum" ; "CCS-300ST subcompact, non-optical, vacuum" ; "83 mm to 85 mm (3.25 in to 3.75 in) square" ; "38 mm (1.5 in) square"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- window material corroboration: https://www.lakeshore.com/docs/default-source/default-document-library/cryostatwindows.pdf?sfvrsn=8ad0a533_13 ("Cryostat Windows", p. 2): "Standard fused silica is an inexpensive choice for general-purpose windows and is the material used on all standard 1.63 in clear view Environment by Janis window ports." ; "Standard optical cryostats have fused silica windows installed"
- CCS-100 page (https://www.lakeshore.com/products/product-detail/janis/ccs-100-cryostat) lists only a "Window options" link; no count stated.

### Electrical connections (feedthroughs / wiring)
- value: standard feedthrough port 1.375 in square; options include 10-pin, 19-pin and 26-pin hermetic feedthroughs; wired option WH-10P = 10-pin with 10 PhBr twisted-pair wires; BNC / SMA coax feedthrough options (e.g. 2, 4 or 6 coaxial cables). Number of DC leads supplied as standard: UNKNOWN (not found in sources fetched)
- applies_to: Lake Shore / Janis cryostats generally (guide is not CCS-specific)
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/cryostatfeedthroughs.pdf?sfvrsn=d6b74e27_7
- document_title: Cryostat Feedthroughs and Wiring
- location: "Hermetic feedthroughs--unwired"; "Hermetic feedthroughs with installed wiring"
- quote: "All options fit a standard 1.375 in square o-ring sealed feedthrough port unless noted." ; "10P-ASSEMBLY  10-pin feedthrough with mating connector" ; "WH-10P  10-pin feedthrough with 10 PhBr twisted-pair wires installed; includes mating connector" ; "WH-SMA-2-G  Double SMA feedthrough with two jack-to-jack SMA feedthroughs and two coaxial cables"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification
- CCS datasheet p. 4 "4. Select cryostat wiring": "We offer a variety of both unwired and wired feedthroughs to complete your measurement setup. Please refer to the cryostat feedthroughs and wiring guide for more information."

### Vibration
- value: UNKNOWN (not found in sources fetched) — the "Vibration" row label exists in the datasheet table but no numeric value was present in the extracted text for any CCS model
- applies_to: CCS series
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCR vacuum cryostats datasheet (102126)
- location: p. 2, "Specifications" table, row "Vibration"
- accessed: 2026-10-31

### Size / weight
- value: CCS-100 height 56-84 cm, 16-29 kg; CCS-300S/ST 71-99 cm, 17-30 kg; CCS-400 61-89 cm, 16-30 kg; CCS-400H 66-94 cm, 16-30 kg (approximate)
- applies_to: CCS series
- source_url: https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24
- document_title: CCR vacuum cryostats datasheet (102126)
- location: p. 2, "Specifications" table, rows "Height (approximate)" and "Weight (approximate)"
- quote: "56 to 84 cm (22 to 33 in)" ; "16 to 29 kg (36 to 64 lb)" ; "71 to 99 cm (28 to 39 in)" ; "17 to 30 kg (37 to 66 lb)"
- accessed: 2026-10-31
- evidence_type: manufacturer_specification

---

## Sources fetched (successfully read this session)
- https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station — "CRX-VF cryogenic probe station" specifications (HTML)
- http://www.lakeshore.com/products/categories/overview/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station — CRX-VF overview (HTML; https → http redirect followed)
- https://www.lakeshore.com/products/categories/downloads/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station — CRX-VF downloads list (HTML)
- https://www.lakeshore.com/products/categories/specification/material-characterization-products/cryogenic-probe-stations/model-crx-4k-cryogenic-probe-station — "CRX-4K probe station specifications" (HTML)
- https://www.lakeshore.com/docs/default-source/product-downloads/catalog/probestationcatalog_l.pdf?sfvrsn=c0f0f3c1_68 — "Probe Stations" catalog, 52 pp. (PDF; text extracted locally with pdftotext; CRX-4K pp. 42-43, CRX-VF pp. 44-45, features table p. 14)
- https://www.lakeshore.com/docs/default-source/product-downloads/literature/probestationfamily.pdf?sfvrsn=3f78b12e_15 — "Lake Shore Probe Stations" family flyer (PDF; pdftotext)
- http://www.lakeshore.com/products/product-detail/janis/4-k-cryocoolers-sample-in-vacuum-systems — "Cryogen-free vacuum cryostats" (HTML; https → http redirect followed)
- https://www.lakeshore.com/products/product-detail/janis/ccs-100-cryostat — "CCS-100 optical cryostat" (HTML)
- https://www.lakeshore.com/products/product-detail/janis/ccs-300-series-cryostats — "CCS-300 Series cryostats" (HTML)
- https://www.lakeshore.com/products/product-detail/janis/ccs-400-series-cryostats — "CCS-400 Series cryostats" (HTML)
- https://www.lakeshore.com/products/categories/downloads/environment-by-janis/cryogen-free-cryostats/ccr-vacuum-cryostats — CCR vacuum cryostats downloads list (HTML)
- https://www.lakeshore.com/docs/default-source/default-document-library/ccr-vacuum.pdf?sfvrsn=aaa472f1_24 — "CCS-100 … Cryogen-free Sample in vacuum cryostats" datasheet, 4 pp., code 102126 (PDF; pdftotext)
- https://www.lakeshore.com/docs/default-source/default-document-library/cryostatwindows.pdf?sfvrsn=8ad0a533_13 — "Cryostat Windows" guide (PDF; pdftotext)
- https://www.lakeshore.com/docs/default-source/default-document-library/cryostatfeedthroughs.pdf?sfvrsn=d6b74e27_7 — "Cryostat Feedthroughs and Wiring" guide (PDF; pdftotext)

## Failed fetches
- https://lakeshore.com/products/categories/overview/material-characterization-products/cryogenic-probe-stations/model-crx-vf-cryogenic-probe-station — 301 redirect (re-fetched successfully at the http://www.lakeshore.com URL above)
- https://lakeshore.com/products/product-detail/janis/4-k-cryocoolers-sample-in-vacuum-systems — 301 redirect (re-fetched successfully at the http://www.lakeshore.com URL above)
- No other Lake Shore fetch failed. Note: WebFetch could not read text from any Lake Shore PDF directly (binary returned); all PDF content above was obtained by extracting the downloaded files locally with pdftotext.
