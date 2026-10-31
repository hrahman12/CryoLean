# Low-temperature experiment library — documented requirements from fetched sources

Compiled 2026-10-31. Every value below was read from a source fetched in this session (full text via Europe PMC XML, arXiv HTML/PDF, or protocols.io PDF). DOIs were checked by fetching `https://doi.org/<doi>`; "resolves" means the DOI server returned a redirect to the publisher landing page. Quantities not stated in the source are written `UNKNOWN (not stated in source)`. The `reported_conditions` are what each paper did, not universal requirements.

---

## cryostat_tissue_sectioning — Frozen-tissue cryosectioning for histology / immunofluorescence
- domain: biology
- source_1: Li, S., You, S., Mao, K. (2025). Protocol for multiplex immunofluorescence imaging of mouse intestinal tumors. STAR Protocols 6(2), 103776. DOI: 10.1016/j.xpro.2025.103776 (resolves) (url: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12224881/fullTextXML ; PMCID PMC12224881)
- source_2: Fan, Y., Steele, C. (2025). Coronal cryosectioning of mouse brains. protocols.io (Caltech; created 2025-01-07, last modified 2025-02-16; CC-BY). DOI: 10.17504/protocols.io.x54v9rkzpv3e/v1 (resolves) (url: https://www.protocols.io/view/coronal-cryosectioning-of-mouse-brains-dxbw7ipe.pdf)
- reported_conditions:
  - temperature: source_1: chamber −20 °C, sample holder −18 °C; tissue equilibrated at −20 °C for 1–2 h before sectioning; blocks stored at −80 °C. source_2: chamber −16 °C to −20 °C, brain holder −20 °C; brains stored at −80 °C before sectioning.
  - magnetic_field: not used
  - sample_dimensions: section thickness 15 µm (source_1); 100 µm free-floating sections (source_2). Tissue block size: UNKNOWN (not stated in source) for both (source_1 embeds in "an embedding mold filled with OCT"; mold size not given).
  - measurement_interface: mechanical sectioning with steel blade; sections collected on charged slides (source_1) or free-floating in PBS (source_2)
  - optical_access: not needed during sectioning (downstream fluorescence microscopy on slides)
  - thermal_load: UNKNOWN (not stated in source)
  - equipment_named: Leica CM1950 cryostat (both sources); Tissue-Tek O.C.T. compound, Sakura Finetek 4583 (source_1); OCT (source_2); charged slides Premiere 9308W (source_1)
  - quotes:
    - source_1, Step 10b: "Set the chamber and sample holder temperatures to −20°C and −18°C, respectively."
    - source_1, Step 10c: "Using a cryostat, cut 15 μm thick sections and collect them on charged slides."
    - source_1, Step 10a: "Prior to sectioning, equilibrate the tissue at −20°C for 1–2 h."
    - source_1, Step 9b: "Freeze the mold on dry ice and store it at −80°C."
    - source_1, Step 10 critical note: "Ambient humidity and temperature are crucial for preserving the sections."
    - source_2, Step 2: "Place brain in cryostat. Set chamber temperature to -16 °C to -20 °C. Set brain holder temperature to -20 °C. Let brain equilibrate to temperature for at least 00:20:00 before sectioning."
    - source_2, Step 6: "Cut 100 micron sections."
    - source_2, Materials: "Leica Biosystems, CM1950cryostat (Leica Biosystems, CM1950)"
  - knife/object temperature: object (specimen) head −18 °C (source_1) / −20 °C (source_2); blade temperature: UNKNOWN (not stated in source)
- physical_necessity_notes: Both sources operate the chamber in the −16 to −20 °C range and name OCT as the embedding medium, but neither states a physical minimum/maximum; the −20 °C setting is this protocol's choice (user must confirm whether a different tissue type needs a different chamber temperature). Section thickness (15 vs 100 µm) is clearly a per-application choice, not intrinsic.
- accessed: 2026-10-31

---

## cryo_em_vitrification_cryo_fluorescence — Plunge-freezing / vitrification and keeping specimens below the devitrification temperature for cryo-EM and cryo-fluorescence
- domain: biology
- source_1: Last, M. G. F., Tuijtel, M. W., Voortman, L. M., Sharp, T. H. (2023). Selecting optimal support grids for super-resolution cryogenic correlated light and electron microscopy. Scientific Reports 13, 8270. DOI: 10.1038/s41598-023-35590-x (resolves) (url: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10203124/fullTextXML ; PMCID PMC10203124)
- source_2: Berkamp, S., Daviran, D., Smeets, M., Caignard, A., Jani, R. A., Sundermeyer, P., Jonker, C., Gerlach, S., Hoffmann, B., Lau, K., Sachse, C. (2023). Correlative Light and Electron Cryo-Microscopy Workflow Combining Micropatterning, Ice Shield, and an In-Chamber Fluorescence Light Microscope. Bio-protocol 13(24), e4901. DOI: 10.21769/BioProtoc.4901 (resolves) (url: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10751236/fullTextXML ; PMCID PMC10751236)
- source_3 (supporting, devitrification physics): Huebinger, J., Bastiaens, P. I. H. (2026). Determination of factors that allow cryogenic nanoscopy with high power illumination without devitrification. PLoS One 21(3), e0344631. DOI: 10.1371/journal.pone.0344631 (resolves) (url: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13038024/fullTextXML)
- reported_conditions:
  - temperature: source_1: plunge into liquid ethane at −183 °C; sample stage held at 77 K (liquid-nitrogen cooled); devitrification threshold stated as ~136 K. source_2: Vitrobot chamber 37 °C / 85 % humidity before plunge; grids stored and handled under liquid nitrogen. source_3: modelled base temperature −196 °C (liquid nitrogen); laser-heated steady-state −108 to −115 °C reached under 300 W/cm² illumination (SMLM case).
  - magnetic_field: not used
  - sample_dimensions: grid diameter UNKNOWN (not stated in source) — grids described by mesh (200/300 mesh) and type (Quantifoil R2/1 gold with SiO2 film, CFlat 2/1 300 mesh Cu, UltrAuFoil 1.2/1.3 300 mesh Au); grid squares ≈ 90 / 58 / 37 µm for 200/300/400 mesh (source_1). Sample volume 3 µL (source_1). Source_3 model: 0.5 µm water layer (up to 5 µm for cells) on 10 nm holey carbon.
  - measurement_interface: optical (cryo-fluorescence through air objective) and electron beam (cryo-EM/FIB); transfer under LN2
  - optical_access: needed (cryo-fluorescence imaging through a cryo-stage window; air objective NA 0.9, source_1; LMPLFLN 50x/0.5 in-chamber objective, source_2)
  - thermal_load: source_1: tolerated illumination power densities 16–254 W/cm² depending on grid film (Table 1), 186.5 W/cm² of 488 nm used; source_3: 300 + 15 W/cm² (SMLM) and 6.7×10^7 W/cm² at 775 nm (STED spot) modelled
  - equipment_named: Leica EM GP plunge freezer; Linkam CMS196v3 cryo-stage; Nikon CFI TU Plan Apo 100x/0.9 NA (source_1). Vitrobot Mark IV (Thermo Fisher); Delmic METEOR in-chamber cryo-FLM; CERES ice shield; Zeiss LSM 800 with Linkam CMS196 (source_2).
  - quotes:
    - source_1, Results ("Light-induced damage…"): "Devitrification occurs when vitrified cryogenic samples are heated to more than approximately 136 K"
    - source_1, Methods (Sample preparation): "grids were plunge-frozen in liquid ethane (− 183 °C) using a Leica EM GP operated at 12 °C and 50% humidity"
    - source_1, Methods: "a commercial cryogenic sample stage (Linkam Scientific, CMS196v3)"
    - source_1, Results: "held at a constant temperature of 77 K by the liquid nitrogen-cooled sample stage"
    - source_1, Methods: "a 0.9 NA air immersion objective lens (Nikon, CFI TU Plan Apo 100x/0.9NA)"
    - source_2, Procedure (Vitrification of mammalian cells): "Turn the vitrobot on and warm the chamber to 37 °C with 85% humidity."
    - source_2, Procedure: "Blot the grids for 8.5 s with 10 blot force and 1 drain time."
    - source_2, Validation (METEOR): "The additional transfer puts the sample in further danger of devitrification."
    - source_2, Troubleshooting: "Always ensure all tools are fully cooled to liquid nitrogen temperatures before use"
    - source_3, Abstract: "If the sample is heated above the glass transition temperature, diffusion and conformational changes perturb the sample and the sample eventually devitrifies."
    - source_3, Results: "a new steady-state temperature between −108 °C and −115 °C, depending on beam shape, with an expected temperature gradient towards the periphery emerged."
  - humidity: 50 % at 12 °C (source_1 Leica EM GP); 85 % at 37 °C (source_2 Vitrobot)
- physical_necessity_notes: Staying below the devitrification temperature is intrinsic: source_1 states devitrification occurs above ~136 K and source_3 states heating above the glass transition devitrifies the sample; both therefore hold specimens at LN2 temperature (77 K / −196 °C) and treat illumination heating as the limiting load. The specific plunge-chamber humidity/temperature, blot time, and grid type are choices of each protocol (user must confirm for their specimen). Grid diameter (commonly 3 mm) is not stated in either source — UNKNOWN here.
- accessed: 2026-10-31

---

## linkam_low_temperature_raman — Low-temperature Raman spectroscopy on a Linkam THMS600 stage
- domain: chemistry
- source_1: Park, H., Wang, A., Kim, J., Pophali, A., Gersappe, D., Kim, T. (2026). Molecular-level freezing and melting dynamics of aqueous lithium chloride solutions using in-situ Raman spectroscopy. Scientific Reports 16, 32309. DOI: 10.1038/s41598-026-61621-4 (resolves) (url: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13668726/fullTextXML ; PMCID PMC13668726)
- source_2: Pamula, K., Pophali, A., Gersappe, D., Kim, T. (2025). In-situ Raman spectroscopic analysis of phase transition temperatures in silica interacting with water and NaCl solutions. Scientific Reports 15, 26449. DOI: 10.1038/s41598-025-12034-2 (resolves) (url: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12280175/fullTextXML ; PMCID PMC12280175)
- reported_conditions:
  - temperature: source_1: room temperature to −140 °C (and back), ramp rates 0.5, 5 and 100 °C/min. source_2: 23 °C to −50 °C freeze/thaw cycles at 1 °C/min with 2 min holds.
  - magnetic_field: not used
  - sample_dimensions: 100 µL liquid in a 15 mm-diameter quartz crucible (source_1); quartz crucible Linkam THMSQ, 15 mm diameter (source_2); samples = aqueous LiCl solutions (source_1), DI water / NaCl solutions / SiO2 paste ~28 wt% (source_2)
  - measurement_interface: optical — Raman backscattering through stage window; laser 532 nm, 5.6 mW (source_1); 532 nm, 10 mW (also 5.6 and 28 mW) (source_2)
  - optical_access: needed. Objective: UNKNOWN (not stated in source_1); long-working-distance Olympus MPlan N 10x/0.25 BD, 6.5 mm WD (source_2). Window material: UNKNOWN (not stated in source) for both.
  - thermal_load: UNKNOWN (not stated in source)
  - equipment_named: HORIBA Xplora Plus Raman microscope; Linkam THMS600-PS cryo-stage; LNP pump; dewar (source_1). HORIBA Xplora; Linkam THMS600-PS; Linkam LNP96 pump; Linkam D2L/80 dewar; Linkam THMSQ quartz crucible (source_2).
  - cooling_medium: liquid nitrogen pumped from a dewar (both)
  - quotes:
    - source_1, Materials and methods (In-situ Raman spectroscopy): "Liquid nitrogen was pumped from a dewar to the THMS600-PS stage to cool the system"
    - source_1, same section: "The liquid sample (100 µl) was tested in a quartz crucible (15 mm diameter) mounted inside the cryo-stage."
    - source_1, same section: "acquisition time of 10 s, accumulation of 5 scans, laser output power of 5.6 mW, and 1200 gr/mm grating."
    - source_1, same section: "Melting experiments were conducted at the same rates as the freezing, reversibly from − 140 °C to room temperature."
    - source_2, Materials and Raman characterization: "The samples were excited by visible laser (wavelength = 532 nm, 10 mW output power)."
    - source_2, same section: "a long working distance objective lens (MPlan N 10x/0.25 BD Olympus, 6.5 mm)"
    - source_2, same section: "pumped from dewar (Linkam D2L/80) to the THMS600-PS cryo-stage to cool the system"
    - source_2, same section: "The freezing and thawing cycles were performed within the temperature range from 23 to -50 ℃."
    - source_2, same section: "The samples were tested in a quartz crucible (Linkam THMSQ, 15 mm diameter) mounted inside the cryo-stage."
- physical_necessity_notes: Optical access through the stage window and a long-working-distance objective are intrinsic to doing Raman inside an enclosed cold stage (source_2 explicitly uses a 6.5 mm WD objective); liquid nitrogen as coolant is what these papers used with the THMS600-PS. The measured temperature ranges (−140 °C or −50 °C) are set by the phase transitions studied, not by the technique. Window material and the stage's specified temperature range are not stated — user must confirm.
- accessed: 2026-10-31

---

## optical_cryostat_pl_absorption — Temperature-dependent photoluminescence / optical spectroscopy in an optical cryostat (4–300 K)
- domain: chemistry
- source_1: Swidinsky, N., Ellingwood, E., Hucker, J., Skensved, P., Di Stefano, P., Mason, J., Boulay, M., Kemp, A., Schuckman, F., Wang, Y. (2024). Temperature-Dependent Photoluminescence of PEDOT:PSS for use as Transparent Electrodes in the DarkSide-20k Time Projection Chamber. arXiv:2407.08075 [physics.ins-det]. DOI: 10.48550/arXiv.2407.08075 (resolves; no journal version listed on arXiv) (url: https://arxiv.org/html/2407.08075v1)
- source_2: Shyam, I., Singh, R., Akkanaboina, M., Sonawane, A. M., Satheeshkumar, M., Majumder, A., Ekta, Khunte, J. J., Khaire, A., Watanabe, K., Taniguchi, T., Rajaraman, G., Dahiwale, S. S., Kumar, A. (2026). Hexagonal Boron Nitride Spin Defects for Quantum Photonics: Annealing-Free Generation by Krypton Ion Implantation. arXiv:2606.23334 [physics.optics]. DOI: 10.48550/arXiv.2606.23334 (resolves; preprint, no journal version listed) (url: https://arxiv.org/html/2606.23334)
- reported_conditions:
  - temperature: source_1: 300 K, 87 K and 4 K (±0.1 K) for spectra; 18 temperatures between 300 K and 4 K for time-resolved data; stability within 0.1 K. source_2: 20 K to 300 K in 20 K steps (15 temperatures).
  - magnetic_field: not used
  - sample_dimensions: source_1: fused-silica substrates 25 × 25 × 2 mm³ (Edmund Optics windows), acrylic 5 mm thick machined to fit the cryochamber. source_2: hBN flakes ~50–250 nm thick (AFM); lateral size UNKNOWN (not stated in source).
  - measurement_interface: optical — excitation 260 nm LED (CW) / 267 nm pulsed LED (source_1); 532 nm laser, 3.83 mW through 100x NA 0.85 objective (source_2). Detection: Horiba spectrometer with Symphony II CCD and Hamamatsu R6095-100 PMT (source_1).
  - optical_access: needed — borosilicate glass windows in the cryostat shrouds (source_1); quartz optical windows on the cryogenic vacuum chamber (source_2)
  - thermal_load: UNKNOWN (not stated in source)
  - vacuum: < 10^-6 mbar (source_1); 10^-5 mbar before cooling, turbomolecular pump (source_2)
  - equipment_named: source_1: cryostat make/model UNKNOWN (not stated in source; cites prior Ellingwood et al. design); gold-plated copper coldfinger; Horiba spectrometer; Horiba Delta Diode 267 nm. source_2: Lakeshore closed-cycle cryostat (model number not given); GE varnish; helium exchange gas.
  - quotes:
    - source_1, Sec. 4.1.1: "Emission spectra were taken with a 10 s exposure at three different temperatures: 300 K, 87 K and 4 K (±0.1 K)."
    - source_1, Sec. 4.1.1: "During measurements, the cryostat temperature is stable within 0.1 K of the desired temperature."
    - source_1, Sec. 4.1.1: "the sample is in a vacuum lower than 10⁻⁶ mbar"
    - source_1, Sec. 4.1.1: "This UV light passes through a 260 nm narrowpass filter before entering the cryostat through borosilicate glass windows in the cryostat shrouds."
    - source_1, Sec. 4.1.1: "The sample is mounted directly onto the gold-plated copper coldfinger of the cryostat."
    - source_1, Sec. 5.1: "Data is taken at 18 temperatures between 300 K and 4 K, including the boiling points for the noble elements."
    - source_2, Sec. IV.6: "PL spectra were collected at 15 temperatures from 20 K to 300 K in steps of 20 K"
    - source_2, Sec. IV.6: "The sample was mounted on the cryostat cold finger using GE Varnish and cooled using Helium exchange gas"
    - source_2, Sec. IV.6: "to achieve high vacuum (10−5 mbar) prior to cooling"
    - source_2, Sec. IV.5: "a 100X objective lens (NA = 0.85)"
- physical_necessity_notes: A transparent window matched to the excitation/emission band is intrinsic (source_1 uses borosilicate windows for 260 nm excitation; source_2 quartz windows and notes a quartz background near 880 nm); cold-finger mounting under vacuum is common to both. The exact base temperature (4 K vs 20 K), step size, and vacuum level are the papers' choices — user must confirm for their material.
- accessed: 2026-10-31

---

## ppms_electrical_transport_magnetoresistance — Electrical transport / magnetoresistance in a Quantum Design PPMS
- domain: materials
- source_1: Nowakowska, P., Pavlosiuk, O., Wiśniewski, P., Kaczorowski, D. (2023). Temperature-dependent Fermi surface probed by Shubnikov–de Haas oscillations in topological semimetal candidates DyBi and HoBi. Scientific Reports 13, 22776. DOI: 10.1038/s41598-023-49941-1 (resolves; PMCID PMC10733278, open access) (url: https://arxiv.org/abs/2401.02294 — arXiv mirror of the published article, full text read from https://arxiv.org/pdf/2401.02294)
- source_2: Rao, K., Allen, K., Gao, Y., Arushi, Mishra, S., Singh, B., Burch, K. S., Deng, L., Saha, S. R., Paglione, J., Lee, M., Zapf, V., Morosan, E. (2026). A Strategy Toward Room Temperature Topological Hall Effect via Local Moment Magnetism. arXiv:2609.03223 [cond-mat.mtrl-sci]. DOI: arXiv DOI 10.48550/arXiv.2609.03223 listed as pending registration on the abstract page — UNVERIFIED (url: https://arxiv.org/html/2609.03223 ; abstract page https://arxiv.org/abs/2609.03223 confirmed)
- reported_conditions:
  - temperature: 2–300 K (both sources)
  - magnetic_field: up to 14 T (both sources); source_2 field along [120]
  - sample_dimensions: source_1: largest single crystals 3 × 3 × 3 mm³ (measured sample size not separately stated). source_2: rod-like crystals, numeric dimensions UNKNOWN (not stated in source).
  - measurement_interface: four-probe ac electrical transport (resistivity, Hall, magnetoresistance); source_1 ac current along [100]; source_2 ac current 1 mA along c axis. Number of contacts: four implied by "four-probe"; contact material UNKNOWN (not stated in source).
  - optical_access: not needed
  - thermal_load: UNKNOWN (not stated in source)
  - equipment_named: Physical Property Measurement System (PPMS, Quantum Design) (source_1; option name not stated — UNKNOWN whether ETO or Resistivity); Quantum Design PPMS DynaCool, "electrical transport option" (source_2)
  - quotes:
    - source_1, Methods (Electrical transport measurements): "Electrical transport properties, including electrical resistivity, Hall effect and magnetoresistance, were measured using a four-probe method employing the Physical Property Measurement System (PPMS, Quantum Design)."
    - source_1, Methods: "Measurements were carried out in the temperature range 2-300 K and in the magnetic fields up to 14 T, with ac electrical current flowing along [100] crystallographic direction."
    - source_1, Methods (Sample synthesis): "The largest among obtained single crystals had a size of 3 × 3 × 3 mm3."
    - source_2, Methods (Electrical transport measurements): "electrical transport option in a Quantum Design (QD) Physical Property Measurement System (PPMS) DynaCool."
    - source_2, Methods: "applied magnetic field of up to 14 T along [120]."
- physical_necessity_notes: Four-probe geometry is the stated method in both papers (intrinsic to low-resistance resistivity measurement as practised here); the 2–300 K and 14 T ranges are what these specific papers used and reflect their PPMS magnet (14 T) — a 9 T PPMS would give a different maximum (user must confirm). Sample dimensions were only given as a crystal-growth maximum in source_1.
- accessed: 2026-10-31

---

## ppms_mpms_magnetometry_heat_capacity — Magnetometry (SQUID MPMS / SQUID-VSM) and heat capacity in a PPMS
- domain: materials
- source_1: Curley, S. P. M., Scatena, R., Williams, R. C., Goddard, P. A., Macchi, P., Hicken, T. J., Lancaster, T., Xiao, F., Blundell, S. J., Zapf, V., Eckert, J. C., Krenkel, E. H., Villa, J. A., Rhodehouse, M. L., Manson, J. L. (2021). Magnetic ground-state of the one-dimensional ferromagnetic chain compounds M(NCS)2(thiourea)2; M = Ni, Co. Physical Review Materials 5, 034401. DOI: 10.1103/PhysRevMaterials.5.034401 (resolves to link.aps.org) (url: https://arxiv.org/abs/2012.00455 ; full text read from https://arxiv.org/pdf/2012.00455 v2)
- source_2: Rao, K. et al. (2026). A Strategy Toward Room Temperature Topological Hall Effect via Local Moment Magnetism. arXiv:2609.03223 (see previous section; DOI pending — UNVERIFIED) (url: https://arxiv.org/html/2609.03223)
- reported_conditions:
  - temperature: source_1: magnetometry 1.8 ≤ T ≤ 300 K; heat capacity: zero-field C(T) and Cmag in fields up to 9 T (temperature range of C(T) not stated numerically). source_2: heat capacity 1.8–300 K; DC magnetization 1.8–400 K.
  - magnetic_field: source_1: field sweeps up to µ0H = 7 T (MPMS-7XL); heat capacity in fields up to 9 T (PPMS). source_2: up to 7 T (MPMS3 SQUID-VSM); up to 65 T pulsed at NHMFL Los Alamos.
  - sample_dimensions: source_1: plate-like single crystals (Co compound) and pressed polycrystalline pellets (Ni compound); mass UNKNOWN (not stated in source). source_2: UNKNOWN (not stated in source).
  - measurement_interface: SQUID magnetometry with sample in gelatin capsule / Teflon holder inside a plastic drinking straw (source_1); relaxation-method calorimetry with Apiezon M grease and addenda correction (source_1); thermal-relaxation heat capacity (source_2); SQUID-VSM (source_2)
  - optical_access: not needed
  - thermal_load: UNKNOWN (not stated in source)
  - equipment_named: Quantum Design PPMS (heat capacity); Quantum Design MPMS-7XL SQUID magnetometer; Apiezon M grease (source_1). Quantum Design PPMS DynaCool (heat capacity); Quantum Design MPMS3 with SQUID-VSM option (source_2).
  - quotes:
    - source_1, Experimental details (Heat capacity): "Heat capacity measurements were made on a Quantum Design PPMS instrument."
    - source_1, same: "The samples were mounted onto the sample stage with a small amount of Apiezon vacuum M-grease to provide good thermal contact between the sample and sample platform."
    - source_1, same: "Addenda measurements were performed to correct for the heat capacity of the sample platform and M-grease."
    - source_1, same: "A small heat pulse is then applied and the time taken for the system to relax back to thermal equilibrium monitored."
    - source_1, Experimental details (Magnetometry): "Magnetometry measurements were performed using a Quantum Design MPMS-7XL SQUID magnetometer."
    - source_1, same: "Both were then placed inside a plastic drinking straw to be measured within the MPMS sample chamber. Temperature sweeps from 1.8 ≤T ≤300 K were completed on both compounds."
    - source_1, same: "Field sweeps up to µ0H = 7 T were completed for Ni(NCS)2(thiourea)2."
    - source_1, Results (Heat capacity): "The behaviour of the Ni-species was investigated further by measuring Cmag in applied magnetic fields up to 9 T as shown in Figure 6."
    - source_2, Methods (Thermodynamic measurements): "Heat capacity measurements between 1.8 K and 300 K were performed using a thermal-relaxation method."
    - source_2, Methods: "a QD magnetic property measurement system (MPMS3)"
- physical_necessity_notes: The relaxation-method heat-capacity measurement with grease mounting and addenda subtraction is the method both papers describe for the PPMS calorimeter option; the 1.8 K base and 7 T / 9 T limits are the instruments' (MPMS-7XL, PPMS 9 T) ranges as used by these authors, not intrinsic requirements. Sample mass was not stated in either source — user must confirm.
- accessed: 2026-10-31

---

## transmon_dilution_refrigerator — Superconducting transmon qubit characterization in a dilution refrigerator
- domain: quantum
- source_1: Tuokkola, M., Sunada, Y., Kivijärvi, H., Albanese, J., Grönberg, L., Kaikkonen, J.-P., Vesterinen, V., Govenius, J., Möttönen, M. (2025). Methods to achieve near-millisecond energy relaxation and dephasing times for a superconducting transmon qubit. Nature Communications 16, 5421. DOI: 10.1038/s41467-025-61126-0 (resolves; PMCID PMC12238396) (url: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12238396/fullTextXML ; arXiv version with component table: https://arxiv.org/html/2407.18778v3)
- source_2: Place, A. P. M., Rodgers, L. V. H., Mundada, P., Smitham, B. M., Fitzpatrick, M., Leng, Z., Premkumar, A., Bryon, J., Vrajitoarea, A., Sussman, S., Cheng, G., Madhavan, T., Babla, H. K., Le, X. H., Gang, Y., Jäck, B., Gyenis, A., Yao, N., Cava, R. J., de Leon, N. P., Houck, A. A. (2021). New material platform for superconducting transmon qubits with coherence times exceeding 0.3 milliseconds. Nature Communications 12, 1779. DOI: 10.1038/s41467-021-22030-5 (resolves; PMCID PMC7979772) (url: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7979772/fullTextXML)
- reported_conditions:
  - temperature: ~10 mK (source_1); base temperature ~9–20 mK (source_2)
  - magnetic_field: not applied; passive shielding only (see below)
  - sample_dimensions: source_1: final chip size UNKNOWN (not stated in source); fabrication coupons 25 mm × 30 mm. source_2: chips diced into 7 × 7 mm squares on 0.53 mm c-plane sapphire.
  - measurement_interface: coaxial microwave lines. source_1: qubits 2.89–4.59 GHz, readout resonators 5.85–6.23 GHz; input coax 0.86 mm SCuNi-CuNi semi-rigid, output MXC→4 K 0.86 mm NbTi-NbTi, 4 K→RT 2.19 mm SCuNi-CuNi (arXiv Table 3); cryogenic 20 dB attenuator (XMA) and 10 dB (Mini-Circuits) named, per-stage totals UNKNOWN (not stated in source); number of coax lines UNKNOWN (not stated in source); TWPA (VTT) + HEMT LNF-LNC4_8F. source_2: transmons 3.1–5.5 GHz, resonators 6.8–7.3 GHz; input attenuated on each plate, dB values UNKNOWN (not stated in main text).
  - optical_access: not needed
  - thermal_load: UNKNOWN (not stated in source)
  - magnetic_shielding: source_1: Amumetal shield inside the OVC, QCage magnetic shielding around holder, tin-plated copper shield at 10 mK, light-tight superconducting aluminium enclosure. source_2: mu-metal can around aluminum cylinder; Eccosorb CR110 filter.
  - equipment_named: Bluefors dilution refrigerator (Nat Commun text; arXiv v3 Table 3 names Bluefors XLD400sl); QDevil QCage.24 holder; Eccosorb IR filter; RLC low-pass F-30-8000-R; VTT TWPA; LNF HEMT (source_1). Dilution refrigerator make UNKNOWN (not stated in source_2).
  - quotes:
    - source_1, Methods (Setup for qubit measurements): "cooled down to approximately 10 mK in a Bluefors dilution refrigerator"
    - source_1, Methods: "The signals then pass through rf attenuators, an Eccosorb infrared filter, and a low-pass filter"
    - source_1, Methods: "an Amumetal magnetic shield just inside the outer vacuum chamber (OVC)"
    - source_1, Methods: "placed inside a light-tight superconducting aluminium enclosure to reject stray microwave and infrared photons"
    - source_1, Methods: "The sample is wire-bonded to the printed circuit board (PCB) of a QCage.24 sample holder"
    - source_1, Results: readout resonators "ranging from 5.85 GHz to 6.23 GHz"
    - source_2, Methods (Device packaging): "The device is mounted in a dilution refrigerator with a base temperature of ~9–20 mK."
    - source_2, Methods (Measurement setup): "The transmon frequencies range from 3.1 to 5.5 GHz" ... "while the resonators range in frequency from 6.8 to 7.3 GHz."
    - source_2, Methods (Device packaging): "This cylinder is enclosed in a mu-metal can to reduce the penetration of ambient magnetic fields into the aluminum during the superconducting transition."
    - source_2, Methods (Measurement setup): "An additional filter made of Eccosorb CR110 epoxy is placed in the aluminum can to attenuate high-frequency radiation."
    - source_2, Methods (Tantalum deposition and lithography): "the chips are diced into 7 × 7-mm squares."
- physical_necessity_notes: Both papers operate at ≈10–20 mK with staged attenuation, infrared (Eccosorb) filtering and high-permeability magnetic shielding (Amumetal / mu-metal) plus a superconducting aluminium enclosure; source_2 states the mu-metal can is to reduce ambient-field penetration during the superconducting transition. Whether 10 mK is strictly required versus merely conventional is not asserted by either source — user must confirm. The 3–7 GHz frequency band is the design choice of these devices.
- accessed: 2026-10-31

---

## mk_vector_magnet_hybrid_device — Josephson-junction / hybrid-nanowire (Majorana-type) measurements at mK with a vector magnet
- domain: quantum
- source_1: van Zanten, D. M. T., Sabonis, D., Suter, J., Väyrynen, J. I., Karzig, T., Pikulin, D. I., O'Farrell, E. C. T., Razmadze, D., Petersson, K. D., Krogstrup, P., Marcus, C. M. (2020). Photon-assisted tunnelling of zero modes in a Majorana wire. Nature Physics (journal reference on arXiv: Nature Physics 2020). DOI: 10.1038/s41567-020-0858-0 (resolves) (url: https://arxiv.org/abs/1902.00797 ; full text read from https://arxiv.org/pdf/1902.00797)
- source_2: Zhou, T., Dartiailh, M. C., Sardashti, K., Han, J. E., Matos-Abiague, A., Shabani, J., Žutić, I. (2022). Fusion of Majorana bound states with mini-gate control in two-dimensional systems. Nature Communications 13, 1738. DOI: 10.1038/s41467-022-29463-6 (resolves) (url: https://arxiv.org/abs/2101.09272 ; full text read from https://arxiv.org/pdf/2101.09272 v3)
- reported_conditions:
  - temperature: base electron temperature T ~ 50 mK (source_1); base temperature 7 mK (source_2)
  - magnetic_field: source_1: 6-1-1 T vector magnet; field B∥ applied along the nanowire, zero-bias feature at B∥ = 0.75 T. source_2: 6-3-1.5 T vector magnet; in-plane field Bx along the junction and out-of-plane field used (Bc = 1.6 T quoted as a model parameter).
  - sample_dimensions: source_1: InAs nanowire with 10 nm epitaxial Al on two facets, on a 525 µm Si chip; Ti/Au leads 5/150 nm; nanowire length/diameter UNKNOWN (not stated in source). source_2: planar InAs/Al Josephson junctions, model geometry L = 5 µm, WS = 0.3 µm, WN = 0.1 µm, 1 µm mini-gates; 4 nm InAs quantum well, Al (111) epitaxial.
  - measurement_interface: source_1: dc lines with ac lock-in (4–10 µV excitation, < 200 Hz) plus rf reflectometry/charge sensing with microwave drive fd = 11.5–14 GHz; 21 dB built-in cryostat attenuation + 15 dB directional coupler below the mixing chamber; Weinreb CITLF3 cryogenic amplifier (~40 dB); Zurich Instruments UHF lock-in. Number of coax lines UNKNOWN (not stated in source). source_2: standard dc and low-frequency lock-in, Iac = 10 nA.
  - optical_access: not needed
  - thermal_load: UNKNOWN (not stated in source)
  - equipment_named: Oxford Instruments Triton-400 dilution refrigerator, 6-1-1 T vector magnet (source_1); Oxford Triton dilution refrigerator, 6-3-1.5 T vector magnet (source_2)
  - quotes:
    - source_1, Methods (Measurement techniques): "Measurements were carried out in an Oxford Instruments Triton-400 dilution refrigerator with a base electron temperature of T ∼50 mK and a 6-1-1 T vector magnet."
    - source_1, Methods: "Differential conductance g = dI/dV was measured using the ac-lockin techniques with an excitation voltage in the range 4-10 µV and excitation frequencies below 200 Hz"
    - source_1, Methods: "The excitation signal coming from the lock-in is first attenuated by 21 dB of built-in cryostat attenuators and then by another 15 dB additionally as it passes though the CPL-to-In port of the directional coupler installed below the mixing chamber."
    - source_1, Methods (Device fabrication): "The InAs nanowire was grown by molecular beam epitaxy with subsequent deposition of epitaxial Al (10 nm) on two of its facets."
    - source_1, Conclusion: "transport data show a clear increase in zero-bias conductance around B|| = 0.75 T."
    - source_2, Methods (Measurements): "The device has been measured in an Oxford Triton dilution refrigerator fitted with a 6-3-1.5 T vector magnet which has a base temperature of 7 mK."
    - source_2, Methods: "All transport measurements are performed using standard dc and lock-in techniques at low frequencies and excitation current Iac = 10 nA."
- physical_necessity_notes: Both experiments need a multi-axis (vector) superconducting magnet with ~6 T along the principal axis so the field can be aligned with the nanowire/junction (source_1 applies B∥ along the wire; source_2 uses in-plane and out-of-plane fields), and mK operation (7–50 mK). Neither source states a minimum field or temperature as a general requirement — the 6 T axis is the magnet these groups had; user must confirm the field needed for their device's topological transition.
- accessed: 2026-10-31

---

## Sources fetched (all confirmed to load in this session)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12224881/fullTextXML — Li et al. 2025, STAR Protocols (DOI 10.1016/j.xpro.2025.103776; doi.org → linkinghub.elsevier.com)
- https://www.protocols.io/view/coronal-cryosectioning-of-mouse-brains-dxbw7ipe.pdf — Fan & Steele 2025, protocols.io (DOI 10.17504/protocols.io.x54v9rkzpv3e/v1; dx.doi.org → protocols.io)
- https://bio-protocol.org/prep2643 — Yan & Wang 2024, Bio-protocol preprint (Leica CM1950, 50 µm, OCT; no DOI; not used as a primary source)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10203124/fullTextXML — Last et al. 2023, Sci Rep (DOI 10.1038/s41598-023-35590-x; doi.org → nature.com)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10751236/fullTextXML — Berkamp et al. 2023, Bio-protocol (DOI 10.21769/BioProtoc.4901; doi.org → bio-protocol.org)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13038024/fullTextXML — Huebinger & Bastiaens 2026, PLoS One (DOI 10.1371/journal.pone.0344631; doi.org → dx.plos.org)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13668726/fullTextXML — Park et al. 2026, Sci Rep (DOI 10.1038/s41598-026-61621-4; doi.org → nature.com)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12280175/fullTextXML — Pamula et al. 2025, Sci Rep (DOI 10.1038/s41598-025-12034-2; doi.org → nature.com)
- https://arxiv.org/abs/2407.08075 and https://arxiv.org/html/2407.08075v1 — Swidinsky et al. 2024 (DOI 10.48550/arXiv.2407.08075; doi.org → arxiv.org)
- https://arxiv.org/abs/2606.23334 and https://arxiv.org/html/2606.23334 — Shyam et al. 2026 (DOI 10.48550/arXiv.2606.23334; doi.org → arxiv.org)
- https://arxiv.org/abs/2401.02294 and https://arxiv.org/pdf/2401.02294 — Nowakowska et al., Sci Rep 2023 (DOI 10.1038/s41598-023-49941-1; doi.org → nature.com; Europe PMC record PMC10733278 confirmed open access)
- https://arxiv.org/abs/2609.03223 and https://arxiv.org/html/2609.03223 — Rao et al. 2026 preprint (arXiv DOI pending registration)
- https://arxiv.org/abs/2012.00455 and https://arxiv.org/pdf/2012.00455 — Curley et al., Phys Rev Materials 2021 (DOI 10.1103/PhysRevMaterials.5.034401; doi.org → link.aps.org)
- https://arxiv.org/abs/2407.18778 and https://arxiv.org/html/2407.18778v3 — Tuokkola et al. preprint; published version https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12238396/fullTextXML (DOI 10.1038/s41467-025-61126-0; doi.org → nature.com)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7979772/fullTextXML — Place et al., Nat Commun 2021 (DOI 10.1038/s41467-021-22030-5; doi.org → nature.com)
- https://arxiv.org/abs/1902.00797 and https://arxiv.org/pdf/1902.00797 — van Zanten et al., Nature Physics 2020 (DOI 10.1038/s41567-020-0858-0; doi.org → nature.com)
- https://arxiv.org/abs/2101.09272 and https://arxiv.org/pdf/2101.09272 — Zhou et al., Nat Commun 2022 (DOI 10.1038/s41467-022-29463-6; doi.org → nature.com)
- Europe PMC search endpoints (REST) used for discovery; https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10733278/fullTextXML (Sci Rep DyBi/HoBi) loaded but Methods were beyond the first 100k characters read, so Methods quotes were taken from the arXiv copy.

## Failed fetches / unverified
- https://bio-protocol.org/e3868 (Harb et al. 2021, Bio-protocol immunostaining of cryostat/vibratome sections) — HTTP 468; not used.
- https://www.renishaw.se/media/pdf/en/c15895a67ae64318ab213e6e96af2bf6.pdf → redirected to renishaw.com → HTTP 404 (Renishaw inVia + Linkam THMS600 KNO3 application note); not used.
- https://www.nature.com/articles/... direct fetches redirected to idp.nature.com (cookie authorisation) and were not followed; DOI resolution was still confirmed via the doi.org 302 redirects listed above, and full texts were read via Europe PMC / arXiv instead.
- https://arxiv.org/pdf/2212.05847 (Bluefors LD-400 attenuation table, second transmon candidate) — exceeded the 10 MB fetch limit; not used.
- https://www.protocols.io/view/coronal-cryosectioning-of-mouse-brains-x54v9rkzpv3e/v1 (HTML view) — returned title only; the PDF export of the same protocol was used instead.
- arXiv:2609.03223 (Rao et al.) — DOI listed as "pending registration"; cited by arXiv ID and confirmed abstract page only.
- Europe PMC record PMC13690583 (Kelly et al. 2026, Nat Electron, hole spin qubit readout) and PMC13672782 (Chu et al. 2026, Nat Commun, moiré excitons) — loaded but Methods sections lay beyond the portion read; not used.
- Tuokkola et al.: refrigerator model "XLD400sl" appears only in Table 3 of the arXiv v3 HTML; the Nat Commun main text read says only "Bluefors dilution refrigerator".
