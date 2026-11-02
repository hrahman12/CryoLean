# CryoLean industry coverage matrix

Actual Lean evaluations: **180** of the 180-pair minimum target.
Recorded 2026-11-01T08:03:35.142939+00:00. Checker source/binary SHA-256: `a1b460f33516d78c570e478e938dd6a99992b3c4f123e5505ce1184b99390f2e`.

PASS = REQUIREMENTS_MET; FAIL = DOES_NOT_MEET_REQUIREMENTS; UNKNOWN = NEED_MORE_INFORMATION.
These are evaluations of the prepared requirements as authored. Grouping equipment under an industry does not establish suitability.

## Aerospace and space exploration

1. **Frontier 18 in DIA x 24 in L LN2 thermal cycling system with shrouds and D-sub feedthroughs (X-1P33958, up to 6U CubeSat)** (`laco_frontier_tvac_18x24_ln2_dsub`)
2. **Environmental chamber -150 to 600 C with self-pressurising LN2 Dewar** (`tinius_olsen_environmental_chamber_m150_600_ln2`)
3. **Cryostream 800 Plus (80-500 K) with 800 Series controller, gas pump, AD51 dry air unit, Varibeam stand, ES60 dewar** (`oxford_cryosystems_cryostream_800_plus`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Mars surface thermal-cycle qualification of bonded Honeywell PRTs for MSL (-135 to 70 C qual cycles, +125 C planetary-protection bake) (`aero_mars_prt_thermal_cycling`) | FAIL | PASS | PASS |
| ECSS-E-ST-10-03C space-segment equipment thermal vacuum test (<= 1e-5 hPa, functional tests at hot and cold) (`aero_ecss_equipment_tvac`) | PASS | FAIL | FAIL |
| GSFC GEVS unit-level protoflight thermal-vacuum cycling (< 1.33e-3 Pa, AFT +/-10 C, 4 h plateaus, <= 1 C/min) (`aero_gevs_unit_tvac`) | PASS | FAIL | FAIL |

### Reasons and missing information

- `aero_mars_prt_thermal_cycling` × `laco_frontier_tvac_18x24_ln2_dsub`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'temperature.range'.
- `aero_mars_prt_thermal_cycling` × `tinius_olsen_environmental_chamber_m150_600_ln2`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `aero_mars_prt_thermal_cycling` × `oxford_cryosystems_cryostream_800_plus`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `aero_ecss_equipment_tvac` × `laco_frontier_tvac_18x24_ln2_dsub`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `aero_ecss_equipment_tvac` × `tinius_olsen_environmental_chamber_m150_600_ln2`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'vacuum.available', 'pressure.base'.
- `aero_ecss_equipment_tvac` × `oxford_cryosystems_cryostream_800_plus`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'vacuum.available', 'pressure.base'.
- `aero_gevs_unit_tvac` × `laco_frontier_tvac_18x24_ln2_dsub`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `aero_gevs_unit_tvac` × `tinius_olsen_environmental_chamber_m150_600_ln2`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'vacuum.available', 'pressure.base'.
- `aero_gevs_unit_tvac` × `oxford_cryosystems_cryostream_800_plus`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'vacuum.available', 'pressure.base'.

## Astronomy and astrophysics

1. **CRX-4K cryogen-free probe station, 2 probe arms installed (4.5 K base), standard vacuum** (`lakeshore_crx_4k`)
2. **attoDRY800 with Basic (standard) vacuum shroud, 36 DC wires, no magnet** (`attocube_attodry800_basic_shroud`)
3. **ProteoxLX, twin PTR, standard ISO100-2 Secondary Insert with experimental wiring, no magnet, no windows** (`quantum_design_oxford_proteox_lx_iso100`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Dark current, read noise and x-ray response of a germanium CCD prototype (256 x 256, 8.1 um) at 94.7 K on an LN2-cooled cold plate below 5e-5 torr (`astro_ge_ccd_nir_95k`) | PASS | PASS | FAIL |
| Cryogenic dark/pinhole characterization of a Teledyne HAWAII-2RG (2048x2048 HgCdTe) infrared array held at 35 K in a closed-cycle test cryostat at ~10 microTorr (`astro_h2rg_ir_array_35k`) | PASS | PASS | FAIL |
| Characterization of a 256-pixel NbSi TES bolometer array (CMB, 150 GHz) at ~320 mK with 128:1 SQUID time-domain multiplexing (QUBIC) (`astro_qubic_tes_array_320mk`) | FAIL | FAIL | PASS |

### Reasons and missing information

- `astro_ge_ccd_nir_95k` × `lakeshore_crx_4k`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `astro_ge_ccd_nir_95k` × `attocube_attodry800_basic_shroud`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `astro_ge_ccd_nir_95k` × `quantum_design_oxford_proteox_lx_iso100`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `astro_h2rg_ir_array_35k` × `lakeshore_crx_4k`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `astro_h2rg_ir_array_35k` × `attocube_attodry800_basic_shroud`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `astro_h2rg_ir_array_35k` × `quantum_design_oxford_proteox_lx_iso100`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `astro_qubic_tes_array_320mk` × `lakeshore_crx_4k`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.base', 'sample.diameter.max'.
- `astro_qubic_tes_array_320mk` × `attocube_attodry800_basic_shroud`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.base', 'sample.diameter.max'.
- `astro_qubic_tes_array_320mk` × `quantum_design_oxford_proteox_lx_iso100`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.

## Automotive and transportation

1. **BINDER MK 240 standard (9020-0376, 400 V)** (`binder_mk_240_standard`)
2. **ESPEC ADBC-T standard (three zones)** (`espec_adbc_t_standard`)
3. **Epsilon 2-10D LSCplus base machine, standard 5-shelf configuration (59 mm spacing)** (`martin_christ_epsilon_2_10d_lscplus_standard`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| IEC 62660-1:2018 capacity test of EV propulsion lithium-ion cells at 23 +/- 2 C and at low temperature (-20 C option) (`auto_iec62660_low_temp_capacity`) | PASS | PASS | PASS |
| ISO 16750-4:2023 clause 5.1 constant-temperature tests of automotive E/E components: low-temperature storage (-40 C, 24 h, unpowered), low-temperature operation (Tmin, 24 h, powered) and high-temperature storage (85 C, 48 h) (`auto_iso16750_constant_temperature`) | PASS | PASS | FAIL |
| ISO 16750-4:2023 clause 5.3.1.2 temperature cycling with specified change rate for small/lightweight DUT (Tmin to Tmax, 30 cycles, powered functional checks), operating-temperature code C (-40 C to 65 C) (`auto_iso16750_temperature_cycling`) | PASS | PASS | FAIL |

### Reasons and missing information

- `auto_iec62660_low_temp_capacity` × `binder_mk_240_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `auto_iec62660_low_temp_capacity` × `espec_adbc_t_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `auto_iec62660_low_temp_capacity` × `martin_christ_epsilon_2_10d_lscplus_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `auto_iso16750_constant_temperature` × `binder_mk_240_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `auto_iso16750_constant_temperature` × `espec_adbc_t_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `auto_iso16750_constant_temperature` × `martin_christ_epsilon_2_10d_lscplus_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `auto_iso16750_temperature_cycling` × `binder_mk_240_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `auto_iso16750_temperature_cycling` × `espec_adbc_t_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `auto_iso16750_temperature_cycling` × `martin_christ_epsilon_2_10d_lscplus_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.

## Biology and biotechnology

1. **CCS-800-205 with -205 cold head, water-cooled compressor and temperature controller** (`lake_shore_ccs_800_205_standard`)
2. **CryoAdvance 50 with Agile Temperature Sample Mount (ATSM), standard window assembly, water-cooled compressor** (`montana_instruments_cryoadvance_50_atsm`)
3. **CryoMed TSCM48XV 48 L, 220-230 V, no thermal printer, with vial/straw racks** (`thermo_scientific_cryomed_tscm48xv_standard`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Long-term -80 °C storage of plasmid-bearing bacteria as 25% glycerol stocks in 2 mL screw-top cryovials (Addgene protocol) (`bio_bacterial_glycerol_stock_minus80`) | PASS | PASS | PASS |
| Automated freeze substitution of high-pressure-frozen samples in a Leica AFS2: -90 °C hold, 5 °C/h to -20 °C, 10 °C/h to 20 °C (`bio_freeze_substitution_afs2`) | PASS | PASS | PASS |
| Macromolecular X-ray diffraction data collection at 100 K on a loop-mounted, liquid-nitrogen flash-cooled protein crystal in an Oxford Cryostream (`bio_mx_cryocrystallography_100k`) | FAIL | FAIL | PASS |

### Reasons and missing information

- `bio_bacterial_glycerol_stock_minus80` × `lake_shore_ccs_800_205_standard`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `bio_bacterial_glycerol_stock_minus80` × `montana_instruments_cryoadvance_50_atsm`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `bio_bacterial_glycerol_stock_minus80` × `thermo_scientific_cryomed_tscm48xv_standard`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `bio_freeze_substitution_afs2` × `lake_shore_ccs_800_205_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `bio_freeze_substitution_afs2` × `montana_instruments_cryoadvance_50_atsm`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `bio_freeze_substitution_afs2` × `thermo_scientific_cryomed_tscm48xv_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `bio_mx_cryocrystallography_100k` × `lake_shore_ccs_800_205_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'cryogen.type'.
- `bio_mx_cryocrystallography_100k` × `montana_instruments_cryoadvance_50_atsm`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'cryogen.type'.
- `bio_mx_cryocrystallography_100k` × `thermo_scientific_cryomed_tscm48xv_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.

## Chemistry and pharmaceuticals

1. **Linkam THMS600 with T96-S controller and LNP96-S liquid nitrogen pump** (`linkam_thms600_lnp96_t96`)
2. **OptistatDN-V standard (4 radial windows, blank axial window, MercuryiTC, experimental 10-pin connector)** (`oxford_instruments_optistatdn_v_standard`)
3. **OptistatDN-V liquid-nitrogen bath, sample-in-vacuum optical cryostat (OS-DN-V5-0-100)** (`qdoxford_optistatdn_v_ln2`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| In-situ low-temperature Raman spectroscopy on a Linkam THMS600 liquid-nitrogen stage (`chem_low_temperature_raman`) | PASS | PASS | PASS |
| Polarized optical microscopy of a crystallization / phase transition from 203 K to 393 K (`chem_phase_transition_pom`) | PASS | PASS | PASS |
| Temperature-dependent photoluminescence spectroscopy in an optical cryostat, 4–300 K (`chem_temperature_dependent_photoluminescence`) | FAIL | FAIL | FAIL |

### Reasons and missing information

- `chem_low_temperature_raman` × `linkam_thms600_lnp96_t96`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `chem_low_temperature_raman` × `oxford_instruments_optistatdn_v_standard`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `chem_low_temperature_raman` × `qdoxford_optistatdn_v_ln2`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `chem_phase_transition_pom` × `linkam_thms600_lnp96_t96`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `chem_phase_transition_pom` × `oxford_instruments_optistatdn_v_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `chem_phase_transition_pom` × `qdoxford_optistatdn_v_ln2`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `chem_temperature_dependent_photoluminescence` × `linkam_thms600_lnp96_t96`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'vacuum.available'.
- `chem_temperature_dependent_photoluminescence` × `oxford_instruments_optistatdn_v_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `chem_temperature_dependent_photoluminescence` × `qdoxford_optistatdn_v_ln2`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.

## Defense and security

1. **CRX-6.5K with 6 probe arms, no ring magnet, no PS-HTSTAGE** (`lakeshore_crx_6_5k_6arm`)
2. **Memmert TESTA TT300E75 standard** (`memmert_testa_tt300e75_standard`)
3. **Thermotron FA-16-CH-5-5 (temperature-only altitude chamber)** (`thermotron_fa_16_ch_5_5_standard`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| MIL-STD-810H Method 502.7 Procedure II low-temperature operation test at the Cold (C2) design extreme, -46 C, with at least 2 h soak after stabilization (`def_mil810_502_cold_operation_c2`) | PASS | PASS | PASS |
| MIL-STD-810H Method 502.7 Procedure I low-temperature storage of explosives/munitions at the Severe Cold (C3) extreme, -51 C, for at least 72 h after stabilization (`def_mil810_502_munitions_storage_c3`) | PASS | PASS | PASS |
| Operating a high-operating-temperature (HOT) T2SL MWIR focal-plane array at about 120 K in a vacuum dewar cooled by a linear Stirling cryocooler (integrated dewar cooler assembly) (`def_hot_mwir_idca_120k`) | PASS | FAIL | FAIL |

### Reasons and missing information

- `def_mil810_502_cold_operation_c2` × `lakeshore_crx_6_5k_6arm`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `def_mil810_502_cold_operation_c2` × `memmert_testa_tt300e75_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `def_mil810_502_cold_operation_c2` × `thermotron_fa_16_ch_5_5_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `def_mil810_502_munitions_storage_c3` × `lakeshore_crx_6_5k_6arm`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `def_mil810_502_munitions_storage_c3` × `memmert_testa_tt300e75_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `def_mil810_502_munitions_storage_c3` × `thermotron_fa_16_ch_5_5_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `def_hot_mwir_idca_120k` × `lakeshore_crx_6_5k_6arm`: **PASS**. Requirements met. All 5 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `def_hot_mwir_idca_120k` × `memmert_testa_tt300e75_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'vacuum.available'.
- `def_hot_mwir_idca_120k` × `thermotron_fa_16_ch_5_5_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'optical_access'.

## Energy and hydrogen

1. **NASA Cryostat-100 cylindrical absolute insulation calorimeter, standard 78 K / 293 K boundaries** (`expc_nasa_cryostat100_standard`)
2. **NPL helium-cooled tensile test configuration at 20 K for hydrogen-system materials** (`expc_npl_helium_tensile_20k`)
3. **VPF-100 optical, standard sample holder, wired feedthrough, without VPF-PM pumping manifold** (`lake_shore_vpf_100_standard_optical`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Cryogenic tensile characterization of hydrogen-system metal or composite at 20 K (NPL method class) (`expc_energy_tensile_20k`) | FAIL | PASS | FAIL |
| Critical current and n-value versus applied uniaxial axial strain of commercial REBCO tapes soldered to a Ti-6Al-4V U-spring at 77 K, self-field (`energy_rebco_ic_axial_strain_77k`) | FAIL | FAIL | PASS |
| Steady-state insulation heat-leak measurement at 78 K / 293 K (NASA Cryostat-100 procedure) (`expc_energy_insulation_boiloff`) | PASS | FAIL | UNKNOWN |

### Reasons and missing information

- `expc_energy_tensile_20k` × `expc_nasa_cryostat100_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `expc_energy_tensile_20k` × `expc_npl_helium_tensile_20k`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `expc_energy_tensile_20k` × `lake_shore_vpf_100_standard_optical`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `energy_rebco_ic_axial_strain_77k` × `expc_nasa_cryostat100_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `energy_rebco_ic_axial_strain_77k` × `expc_npl_helium_tensile_20k`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `energy_rebco_ic_axial_strain_77k` × `lake_shore_vpf_100_standard_optical`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `expc_energy_insulation_boiloff` × `expc_nasa_cryostat100_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `expc_energy_insulation_boiloff` × `expc_npl_helium_tensile_20k`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `expc_energy_insulation_boiloff` × `lake_shore_vpf_100_standard_optical`: **UNKNOWN**. Need more information. The available evidence does not establish: 'temperature.warm_boundary.range', 'module.boiloff_calorimetry'.

## Environmental science

1. **IceCube 14M-A (Ref. 16820/6000, 230 V) with double freezing racks** (`minitube_icecube_14_m`)
2. **MVE HEco 815P-190 with square-rack (P) inventory system** (`chart_mve_heco_815p_190_square_rack`)
3. **CG-400 Freezer/Mill, standard (manual LN2 filling)** (`cole_parmer_spex_cg_400_standard`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Long-term environmental specimen banking of cryo-homogenised sub-samples in the vapour phase above liquid nitrogen (below -150 C) (`env_specimen_bank_ln2_vapour_archive`) | PASS | PASS | PASS |
| Immersion-freezing INP spectra of filter-collected aerosol in 96-well PCR plates in an ethanol bath (FrESH, 0 to -35 C at 1 C/min) (`env_fresh_inp_plate_freezing`) | PASS | FAIL | FAIL |
| Cryogenic soil homogenization before volatile-contaminant analysis (`expansion_b_env_soil_cryogenic_preparation`) | FAIL | FAIL | FAIL |

### Reasons and missing information

- `env_specimen_bank_ln2_vapour_archive` × `minitube_icecube_14_m`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `env_specimen_bank_ln2_vapour_archive` × `chart_mve_heco_815p_190_square_rack`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `env_specimen_bank_ln2_vapour_archive` × `cole_parmer_spex_cg_400_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `env_fresh_inp_plate_freezing` × `minitube_icecube_14_m`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `env_fresh_inp_plate_freezing` × `chart_mve_heco_815p_190_square_rack`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'optical_access'.
- `env_fresh_inp_plate_freezing` × `cole_parmer_spex_cg_400_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `expansion_b_env_soil_cryogenic_preparation` × `minitube_icecube_14_m`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.base'.
- `expansion_b_env_soil_cryogenic_preparation` × `chart_mve_heco_815p_190_square_rack`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.base'.
- `expansion_b_env_soil_cryogenic_preparation` × `cole_parmer_spex_cg_400_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.base'.

## Food and agriculture

1. **Orange Ø100 quad-exchanger top-loading cryostat with helium pumping (1.5-320 K)** (`as_scientific_ill_orange_cryostat_100mm`)
2. **MM 500 control + cryoPad, liquid-nitrogen cooling, 125 ml screw-lock jars** (`retsch_mm_500_control_cryopad_ln2`)
3. **SPC-1 configured as nitrogen (re-)liquefier / LN2 sub-cooler** (`stirling_cryogenics_spc_1_n2_reliquefier`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Long-term ultra-low-temperature frozen storage of tuna meat at -45 °C or lower to prevent metmyoglobin (browning) formation (`food_tuna_ultralow_frozen_storage`) | PASS | PASS | PASS |
| Liquid-nitrogen quick freezing of 'Northcountry' blueberries at -80, -100 and -120 °C to below Tg' (-52.55 °C), compared with a -80 °C ultra-low freezer (`food_blueberry_ln2_quick_freezing`) | PASS | FAIL | PASS |
| Box (static liquid-nitrogen-vapour) freezing of bull semen straws: 10 min on a rack 4.5 cm above liquid nitrogen, then plunge into liquid nitrogen for storage (`food_bull_semen_ln2_vapour_box_freezing`) | PASS | FAIL | PASS |

### Reasons and missing information

- `food_tuna_ultralow_frozen_storage` × `as_scientific_ill_orange_cryostat_100mm`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `food_tuna_ultralow_frozen_storage` × `retsch_mm_500_control_cryopad_ln2`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `food_tuna_ultralow_frozen_storage` × `stirling_cryogenics_spc_1_n2_reliquefier`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `food_blueberry_ln2_quick_freezing` × `as_scientific_ill_orange_cryostat_100mm`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `food_blueberry_ln2_quick_freezing` × `retsch_mm_500_control_cryopad_ln2`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `food_blueberry_ln2_quick_freezing` × `stirling_cryogenics_spc_1_n2_reliquefier`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `food_bull_semen_ln2_vapour_box_freezing` × `as_scientific_ill_orange_cryostat_100mm`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `food_bull_semen_ln2_vapour_box_freezing` × `retsch_mm_500_control_cryopad_ln2`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `food_bull_semen_ln2_vapour_box_freezing` × `stirling_cryogenics_spc_1_n2_reliquefier`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.

## Geology and oceanography

1. **LTS420 standard stage with T96 controller and LNP96 liquid-nitrogen pump** (`linkam_lts420_lnp96`)
2. **PheniX standard (top-loading) cryostat with K450 compressor and included 20 mm flat/recessed sample mounts** (`oxford_cryosystems_phenix_standard`)
3. **7380 bath, standard configuration (insulated access cover, user-supplied ethanol/oil fluid)** (`fluke_7380_standard`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Top-down growth of artificial sea ice in 6.55 cm columns under a -5.1 C cryothermostat-cooled plate to quantify incorporation of particulate contaminants (`geo_sea_ice_column_contaminant_uptake`) | PASS | PASS | PASS |
| GO-SHIP seawater nutrient (N, P, Si) sample preservation by rapid freezing in a deep freezer at -20 C or colder (`geo_seawater_nutrient_frozen_storage`) | PASS | PASS | PASS |
| Cryogenic He/Ne separation for groundwater noble-gas and 3H/3He dating: Ne adsorbed on a 14 K sintered-steel cold trap (+/-0.1 K), released at 100 K, in a UHV extraction line with LN2 traps (`geo_noble_gas_he_ne_cryotrap`) | FAIL | PASS | FAIL |

### Reasons and missing information

- `geo_sea_ice_column_contaminant_uptake` × `linkam_lts420_lnp96`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `geo_sea_ice_column_contaminant_uptake` × `oxford_cryosystems_phenix_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `geo_sea_ice_column_contaminant_uptake` × `fluke_7380_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `geo_seawater_nutrient_frozen_storage` × `linkam_lts420_lnp96`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `geo_seawater_nutrient_frozen_storage` × `oxford_cryosystems_phenix_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `geo_seawater_nutrient_frozen_storage` × `fluke_7380_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `geo_noble_gas_he_ne_cryotrap` × `linkam_lts420_lnp96`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'temperature.base'.
- `geo_noble_gas_he_ne_cryotrap` × `oxford_cryosystems_phenix_standard`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `geo_noble_gas_he_ne_cryotrap` × `fluke_7380_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'temperature.base', 'vacuum.available'.

## Healthcare and medicine

1. **CryoTel CT standard system (cooler, passive balancer, Gen II controller, RTD, cables)** (`sunpower_cryotel_ct_standard`)
2. **400 MHz WB DNP-NMR with 263 GHz klystron, LT-MAS cabinet and 3.2 mm X/Y/H DNP probe** (`bruker_dnp_nmr_400_klystron_3_2mm`)
3. **8604 VSM (7 in magnet, standard pole caps) with 86-CRYO cryostat, liquid-helium operation** (`lake_shore_8604_vsm_86_cryo_lhe`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Rapid freezing of fresh frozen plasma in a contact shock freezer (core -30 C within 1 h, freezer at -50 C) and frozen storage at -40 C (`med_ffp_contact_shock_freezing`) | PASS | PASS | PASS |
| Long-term frozen storage of 40% (wt/vol) glycerol red blood cell units at -80 C (FDA/AABB: frozen at -65 C or colder, up to 10 years) (`med_glycerolized_rbc_frozen_storage`) | PASS | PASS | PASS |
| Public cord-blood-unit banking: controlled-rate freezing in 10% DMSO and long-term storage in the liquid phase of liquid nitrogen at -196 C (`med_cord_blood_unit_ln2_banking`) | FAIL | FAIL | PASS |

### Reasons and missing information

- `med_ffp_contact_shock_freezing` × `sunpower_cryotel_ct_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `med_ffp_contact_shock_freezing` × `bruker_dnp_nmr_400_klystron_3_2mm`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `med_ffp_contact_shock_freezing` × `lake_shore_8604_vsm_86_cryo_lhe`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `med_glycerolized_rbc_frozen_storage` × `sunpower_cryotel_ct_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `med_glycerolized_rbc_frozen_storage` × `bruker_dnp_nmr_400_klystron_3_2mm`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `med_glycerolized_rbc_frozen_storage` × `lake_shore_8604_vsm_86_cryo_lhe`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `med_cord_blood_unit_ln2_banking` × `sunpower_cryotel_ct_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'cryogen.type'.
- `med_cord_blood_unit_ln2_banking` × `bruker_dnp_nmr_400_klystron_3_2mm`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `med_cord_blood_unit_ln2_banking` × `lake_shore_8604_vsm_86_cryo_lhe`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.

## Manufacturing and industrial processing

1. **AL600 cold head with water-cooled CPA1114 compressor, 3 m flexible lines, 60 Hz supply** (`bluefors_cryomech_al600_cpa1114_60hz`)
2. **ESPEC EXT2.0 standard** (`espec_ext2_0_standard`)
3. **MVE HEco 1879P-190 with square-rack (P) inventory, 13 shelves per rack** (`mve_heco_1800_1879p_190`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Cryogenic comminution of whole passenger-car waste tyres: complete LN2 immersion (200-300 s, below Tg = 215 K) followed by a single pneumatic-hammer impact (`mfg_waste_tyre_ln2_impact_crumbing`) | FAIL | PASS | PASS |
| Charpy ISO-V impact energy and lateral expansion of austenitic stainless (304L/316L) LNG weld metal at -196 C (ASTM E23; ASME 0.38 mm / TUV 32 J acceptance) (`mfg_lng_austenitic_weld_charpy_minus196c`) | PASS | FAIL | FAIL |
| Differential scanning calorimetry of SBR rubber (`expansion_b_manufacturing_sbr_rubber_dsc`) | FAIL | FAIL | FAIL |

### Reasons and missing information

- `mfg_waste_tyre_ln2_impact_crumbing` × `bluefors_cryomech_al600_cpa1114_60hz`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'cryogen.type', 'sample.diameter.max'.
- `mfg_waste_tyre_ln2_impact_crumbing` × `espec_ext2_0_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mfg_waste_tyre_ln2_impact_crumbing` × `mve_heco_1800_1879p_190`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mfg_lng_austenitic_weld_charpy_minus196c` × `bluefors_cryomech_al600_cpa1114_60hz`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mfg_lng_austenitic_weld_charpy_minus196c` × `espec_ext2_0_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `mfg_lng_austenitic_weld_charpy_minus196c` × `mve_heco_1800_1879p_190`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `expansion_b_manufacturing_sbr_rubber_dsc` × `bluefors_cryomech_al600_cpa1114_60hz`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `expansion_b_manufacturing_sbr_rubber_dsc` × `espec_ext2_0_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `expansion_b_manufacturing_sbr_rubber_dsc` × `mve_heco_1800_1879p_190`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.

## Materials and nanotechnology

1. **CryoAdvance 50 standard configuration (standard I/O, 5 optical ports, no magneto-optic module, no 1.2 K option)** (`montana_instruments_cryoadvance50_standard`)
2. **CCS-400 optical high-temperature (500 K) sample-in-vacuum cryostat, 4 K-class cold head (408)** (`lakeshore_ccs_400`)
3. **MPMS 3 standard LHe dewar, 7 T, with SQUID-VSM, ETO and FOSH options** (`quantum_design_mpms3_lhe_vsm_eto_fosh`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| In-situ cryogenic nanobeam electron diffraction of CDW melting in 1T-TiSe2 nanoflakes from 20 K through the 210-230 K bulk transition (`mat_cryo_tem_cdw_nanoflakes`) | PASS | PASS | PASS |
| Confocal steady-state and time-resolved photoluminescence of exfoliated monolayer WSe2 at 4 K (4-120 K series) (`mat_monolayer_wse2_lowtemp_photoluminescence`) | PASS | PASS | PASS |
| In-situ low-temperature powder XRD of ammonium nitrate phase transitions from -190 C to 135 C in a TTK 600 chamber (`mat_lowtemp_xrd_phase_transitions_ttk600`) | FAIL | PASS | FAIL |

### Reasons and missing information

- `mat_cryo_tem_cdw_nanoflakes` × `montana_instruments_cryoadvance50_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mat_cryo_tem_cdw_nanoflakes` × `lakeshore_ccs_400`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mat_cryo_tem_cdw_nanoflakes` × `quantum_design_mpms3_lhe_vsm_eto_fosh`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mat_monolayer_wse2_lowtemp_photoluminescence` × `montana_instruments_cryoadvance50_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mat_monolayer_wse2_lowtemp_photoluminescence` × `lakeshore_ccs_400`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mat_monolayer_wse2_lowtemp_photoluminescence` × `quantum_design_mpms3_lhe_vsm_eto_fosh`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mat_lowtemp_xrd_phase_transitions_ttk600` × `montana_instruments_cryoadvance50_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `mat_lowtemp_xrd_phase_transitions_ttk600` × `lakeshore_ccs_400`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `mat_lowtemp_xrd_phase_transitions_ttk600` × `quantum_design_mpms3_lhe_vsm_eto_fosh`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.

## Metrology and calibration

1. **m-CFMS 5 T, 30 mm VTI, with DC resistivity/Hall (electrical transport) probe** (`cryogenic_ltd_mcfms_qhr_5t_30mm_transport`)
2. **L-Type Rapid 3P55 (three ADR units, Puck 55, DC wiring only)** (`kiutra_l_type_rapid_3p55`)
3. **6800C, CFMS-9T-30-H3: 9 T cryogen-free QHR system with 30 mm VTI and dual TO-8 probe** (`mi_6800c_cfms_9t_30_h3`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Calibration of long-stem standard platinum resistance thermometers at the ITS-90 triple point of argon (83.8058 K) in a liquid-nitrogen-cooled sealed argon cell (Isotech Model 471) (`metro_argon_triple_point_sprt`) | PASS | PASS | PASS |
| Realization of the ITS-90 from 3 K to 24.5561 K with a 3He/4He interpolating constant-volume gas thermometer (`metro_icvgt_3k_to_neon`) | PASS | PASS | PASS |
| Realization of the ITS-90 from 0.65 K to 5.0 K by 3He/4He vapour-pressure thermometry in a vacuum-isolated copper block (`metro_helium_vapour_pressure_scale`) | FAIL | PASS | FAIL |

### Reasons and missing information

- `metro_argon_triple_point_sprt` × `cryogenic_ltd_mcfms_qhr_5t_30mm_transport`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `metro_argon_triple_point_sprt` × `kiutra_l_type_rapid_3p55`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `metro_argon_triple_point_sprt` × `mi_6800c_cfms_9t_30_h3`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `metro_icvgt_3k_to_neon` × `cryogenic_ltd_mcfms_qhr_5t_30mm_transport`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `metro_icvgt_3k_to_neon` × `kiutra_l_type_rapid_3p55`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `metro_icvgt_3k_to_neon` × `mi_6800c_cfms_9t_30_h3`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `metro_helium_vapour_pressure_scale` × `cryogenic_ltd_mcfms_qhr_5t_30mm_transport`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'temperature.base'.
- `metro_helium_vapour_pressure_scale` × `kiutra_l_type_rapid_3p55`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `metro_helium_vapour_pressure_scale` × `mi_6800c_cfms_9t_30_h3`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'temperature.base'.

## Nuclear engineering and fusion

1. **ST-500 standard (LHe flow) with top window, unwired** (`lake_shore_st_500_lhe_standard`)
2. **OptistatDry BLV (bottom-loading, sample in vacuum), 4 Spectrosil WF windows, 12-pin DC wiring** (`oxford_optistatdry_blv`)
3. **CryoAdvance 100 closed-cycle optical cryostat, standard I/O, with agile temperature sample mount (ATSM)** (`montana_cryoadvance_100_atsm`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| In situ transient grating spectroscopy of thermal diffusivity and SAW speed of Cu-110 during 12.4 MeV Cu6+ ion irradiation at 30 K (variable 30-300 K, high vacuum) (`nuc_cryo_ion_irradiation_tgs`) | PASS | PASS | PASS |
| In-situ formation of solid D2 pellets at ~7 K in a cryogen-free pulse-tube cryostat for two-stage light-gas-gun launching at 2-4 km/s (ENEA-ORNL IPI) (`nuc_ipi_d2_pellet_high_speed`) | PASS | PASS | PASS |
| Fusion cable-in-conduit critical-current characterization at 4.5 K and 10.8 T (`expa_cicc_critical_current`) | FAIL | FAIL | FAIL |

### Reasons and missing information

- `nuc_cryo_ion_irradiation_tgs` × `lake_shore_st_500_lhe_standard`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `nuc_cryo_ion_irradiation_tgs` × `oxford_optistatdry_blv`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `nuc_cryo_ion_irradiation_tgs` × `montana_cryoadvance_100_atsm`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `nuc_ipi_d2_pellet_high_speed` × `lake_shore_st_500_lhe_standard`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `nuc_ipi_d2_pellet_high_speed` × `oxford_optistatdry_blv`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `nuc_ipi_d2_pellet_high_speed` × `montana_cryoadvance_100_atsm`: **PASS**. Requirements met. All 1 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `expa_cicc_critical_current` × `lake_shore_st_500_lhe_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'magnetic_field.max'.
- `expa_cicc_critical_current` × `oxford_optistatdry_blv`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `expa_cicc_critical_current` × `montana_cryoadvance_100_atsm`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'magnetic_field.max'.

## Photonics and telecommunications

1. **Proteox MX450 with 14 T solenoid and 72 mm bottom-loader puck (96 DC, 28 coax)** (`quantum_design_oxford_proteox_mx450_14t_bottom_loader`)
2. **DRY ICE 300mK Benchtop standard, customer DC wiring loom fitted, no windows, no magnet** (`iceoxford_dry_ice_300mk_benchtop_wired`)
3. **attoDRY2100 with 9 T solenoid and Basic Measurement Insert** (`attocube_attodry2100_9t_basic_insert`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Operation of a fibre-pigtailed, bias-tuned quantum-dot micropillar single-photon source in a compact 2.4 K two-stage G-M cryocooler (`photon_fibre_pigtailed_qd_source`) | PASS | PASS | PASS |
| Heralded amplification of telecom time-bin and Fock-state qubits with 70%-efficient MoSi SNSPDs at 2.5 K in a closed-cycle cryocooler (`photon_mosi_heralded_qubit_amplifier`) | PASS | PASS | PASS |
| Atomic-frequency-comb preparation on Zeeman sub-levels of an Er:Ti:LiNbO3 waveguide at ~0.7 K and 3 kG (telecom quantum memory) (`photon_er_linbo3_afc_memory`) | PASS | FAIL | FAIL |

### Reasons and missing information

- `photon_fibre_pigtailed_qd_source` × `quantum_design_oxford_proteox_mx450_14t_bottom_loader`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `photon_fibre_pigtailed_qd_source` × `iceoxford_dry_ice_300mk_benchtop_wired`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `photon_fibre_pigtailed_qd_source` × `attocube_attodry2100_9t_basic_insert`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `photon_mosi_heralded_qubit_amplifier` × `quantum_design_oxford_proteox_mx450_14t_bottom_loader`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `photon_mosi_heralded_qubit_amplifier` × `iceoxford_dry_ice_300mk_benchtop_wired`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `photon_mosi_heralded_qubit_amplifier` × `attocube_attodry2100_9t_basic_insert`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `photon_er_linbo3_afc_memory` × `quantum_design_oxford_proteox_mx450_14t_bottom_loader`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `photon_er_linbo3_afc_memory` × `iceoxford_dry_ice_300mk_benchtop_wired`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'magnetic_field.max'.
- `photon_er_linbo3_afc_memory` × `attocube_attodry2100_9t_basic_insert`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.base'.

## Physics and particle accelerators

1. **EMPX-H2 standard, up to 4 probe arms, LHe/LN2 flow, +/-0.6 T electromagnet** (`lakeshore_empx_h2_standard`)
2. **CUORE TeO2 bolometer cryostat, reported 10 mK configuration — documented configuration** (`expa_cuore_documented`)
3. **DRY ICE 3K INV (3 K cold head) with DC/RF wiring kit, no windows** (`iceoxford_dry_ice_3k_inv_wired`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Residual resistivity ratio (RRR) of SRF-grade niobium by four-point resistance at room temperature and ~10 K (`phys_niobium_rrr`) | PASS | FAIL | PASS |
| TeO2 crystal bolometer particle-energy calorimetry near 10 mK (`expa_teo2_bolometer`) | FAIL | PASS | FAIL |
| Cryogenic I-V, dark-count-rate and thermal-cycling qualification of 6x6 mm2 SiPMs at 77 K for a liquid-argon neutrino detector (`phys_lar_sipm_ln2_qualification`) | PASS | FAIL | FAIL |

### Reasons and missing information

- `phys_niobium_rrr` × `lakeshore_empx_h2_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `phys_niobium_rrr` × `expa_cuore_documented`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `phys_niobium_rrr` × `iceoxford_dry_ice_3k_inv_wired`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `expa_teo2_bolometer` × `lakeshore_empx_h2_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `expa_teo2_bolometer` × `expa_cuore_documented`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `expa_teo2_bolometer` × `iceoxford_dry_ice_3k_inv_wired`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `phys_lar_sipm_ln2_qualification` × `lakeshore_empx_h2_standard`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `phys_lar_sipm_ln2_qualification` × `expa_cuore_documented`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range'.
- `phys_lar_sipm_ln2_qualification` × `iceoxford_dry_ice_3k_inv_wired`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'cryogen.type'.

## Quantum computing and sensing

1. **OptiCool 7 T with X300 standard sample wiring and X310 RF coax wiring** (`quantum_design_opticool_7t_x300_x310`)
2. **XLDHehp, 2 x PT425-ENH, 3-section vacuum cans (776 mm), side-loading coaxial wiring, no magnet, no optical ports** (`bluefors_xldhehp_3section`)
3. **CCS-CP non-optical, 200 mm cold plate, 100 DC wires, 67 GHz RF feedthroughs** (`lake_shore_ccs_cp_200mm_wired`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Fibre-pigtailed micropillar quantum-dot single-photon source operated at 2.4 K in a compact closed-cycle Gifford-McMahon cryocooler (`quantum_fibre_pigtailed_photon_source`) | PASS | FAIL | FAIL |
| Heralded amplification of time-bin and Fock-state photonic qubits at 1550 nm with MoSi SNSPDs below 2.5 K (`quantum_heralded_qubit_amplifier`) | PASS | FAIL | FAIL |
| Cryogenic probing of 300-mm Si/SiGe spin-qubit wafers at 1.6 K for single-electron operating-voltage statistics (`quantum_spin_qubit_wafer_cryoprobing`) | FAIL | PASS | FAIL |

### Reasons and missing information

- `quantum_fibre_pigtailed_photon_source` × `quantum_design_opticool_7t_x300_x310`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `quantum_fibre_pigtailed_photon_source` × `bluefors_xldhehp_3section`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'optical_access'.
- `quantum_fibre_pigtailed_photon_source` × `lake_shore_ccs_cp_200mm_wired`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'optical_access'.
- `quantum_heralded_qubit_amplifier` × `quantum_design_opticool_7t_x300_x310`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `quantum_heralded_qubit_amplifier` × `bluefors_xldhehp_3section`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'optical_access'.
- `quantum_heralded_qubit_amplifier` × `lake_shore_ccs_cp_200mm_wired`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.base', 'optical_access'.
- `quantum_spin_qubit_wafer_cryoprobing` × `quantum_design_opticool_7t_x300_x310`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.base', 'sample.diameter.max'.
- `quantum_spin_qubit_wafer_cryoprobing` × `bluefors_xldhehp_3section`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `quantum_spin_qubit_wafer_cryoprobing` × `lake_shore_ccs_cp_200mm_wired`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.base', 'sample.diameter.max'.

## Scientific research

1. **PPMS DynaCool, 14 T magnet, ETO + VSM + Heat Capacity** (`qd_dynacool_14T_eto_vsm_hc`)
2. **CFM-9T-H3-IVTI-25 with VSM and electrical transport (resistivity/Hall) modules** (`cryogenic_ltd_cfms_9t_ivti25_vsm_transport`)
3. **TeslatronPT, 12 T solenoid magnet, standard VTI** (`oxford_teslatronpt_12T`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| Capacitance dilatometry (thermal expansion and magnetostriction) of thin single crystals in a PPMS, 2-50 K, up to 9 T (`sci_thin_crystal_dilatometry`) | PASS | PASS | PASS |
| Local and nonlocal quantum Hall transport of hBN/graphene Hall bars on YIG at 2.7 K and 9 K up to 12 T (`sci_graphene_yig_quantum_hall`) | PASS | FAIL | PASS |
| Synchrotron/VUV-laser ARPES energy-resolution test on polycrystalline gold at 7 K in UHV below 1E-10 mbar (`sci_arpes_gold_fermi_edge`) | FAIL | FAIL | FAIL |

### Reasons and missing information

- `sci_thin_crystal_dilatometry` × `qd_dynacool_14T_eto_vsm_hc`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `sci_thin_crystal_dilatometry` × `cryogenic_ltd_cfms_9t_ivti25_vsm_transport`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `sci_thin_crystal_dilatometry` × `oxford_teslatronpt_12T`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `sci_graphene_yig_quantum_hall` × `qd_dynacool_14T_eto_vsm_hc`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `sci_graphene_yig_quantum_hall` × `cryogenic_ltd_cfms_9t_ivti25_vsm_transport`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'magnetic_field.max'.
- `sci_graphene_yig_quantum_hall` × `oxford_teslatronpt_12T`: **PASS**. Requirements met. All 3 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `sci_arpes_gold_fermi_edge` × `qd_dynacool_14T_eto_vsm_hc`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'pressure.base', 'optical_access'.
- `sci_arpes_gold_fermi_edge` × `cryogenic_ltd_cfms_9t_ivti25_vsm_transport`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'vacuum.available', 'optical_access'.
- `sci_arpes_gold_fermi_edge` × `oxford_teslatronpt_12T`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'vacuum.available'.

## Semiconductors and electronics

1. **FWPX standard, up to 6 probe arms, LHe/LN2 flow (no PS-LT)** (`lakeshore_fwpx_6arm_standard`)
2. **BINDER MKFT 240 standard (9020-0383, 400 V)** (`binder_mkft_240_standard`)
3. **Platinous EPX-2J temperature & humidity chamber (-70 to 180 C, 225 L), standard equipment** (`espec_epx_2j_standard`)

| Experiment | Equipment 1 | Equipment 2 | Equipment 3 |
|---|---|---|---|
| AEC-Q100 Rev-H Grade 0 temperature cycling (-55 C to +150 C, 2000 cycles) and power temperature cycling (Ta -40 C to +150 C, 1000 cycles) (`semi_aecq100_grade0_tc_ptc`) | PASS | PASS | PASS |
| MIL-STD-883 Method 1010.8 temperature cycling, test condition C (-65 C to +150 C, at least 10 cycles, at least 10 min dwell) (`semi_mil883_tc_condition_c`) | PASS | PASS | PASS |
| DC transfer characterization of commercial 5 nm n/p-FinFETs from 300 K down to 10 K on a closed-cycle cryogenic probe station (`semi_finfet_5nm_cryo_probe`) | PASS | FAIL | FAIL |

### Reasons and missing information

- `semi_aecq100_grade0_tc_ptc` × `lakeshore_fwpx_6arm_standard`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `semi_aecq100_grade0_tc_ptc` × `binder_mkft_240_standard`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `semi_aecq100_grade0_tc_ptc` × `espec_epx_2j_standard`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `semi_mil883_tc_condition_c` × `lakeshore_fwpx_6arm_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `semi_mil883_tc_condition_c` × `binder_mkft_240_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `semi_mil883_tc_condition_c` × `espec_epx_2j_standard`: **PASS**. Requirements met. All 2 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `semi_finfet_5nm_cryo_probe` × `lakeshore_fwpx_6arm_standard`: **PASS**. Requirements met. All 4 applicable mandatory requirements and 0 coupled constraints are satisfied by the documented capabilities of this configuration.
- `semi_finfet_5nm_cryo_probe` × `binder_mkft_240_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'vacuum.available'.
- `semi_finfet_5nm_cryo_probe` × `espec_epx_2j_standard`: **FAIL**. Does not meet requirements. A documented limitation conflicts with: 'temperature.range', 'vacuum.available'.
