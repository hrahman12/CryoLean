# A 2–3 minute guided walkthrough

Launch the real engine with:

```powershell
python -m cryolean.desktop --frontend frontend\dist\index.html
```

The header should say **Desktop backend connected**. In a normal web browser,
the same site honestly provides exploration and an unavailable check state.

## Normal product (30 seconds)

The starting selection is the researched low-temperature resistance experiment,
`mat_electrical_resistance_low_temperature`, on `qd_dynacool_9T_eto_res`.
Choose **Experiment** to inspect the sample puck and four distinct contacts.
Review its actual procedure requirements, tick confirmation and click **Check
my setup**. The catalog currently lacks mandatory sample clearance data, so the
real result is **Need more information**. Open its checks and evidence.

All industry labels, all 11 researched experiments and all 26 configurations
remain available. The product is not restricted to the following guided pairs.

## Try a demo (90 seconds)

Click **Try a demo**. This loads inputs into the same product; it never confirms
or checks automatically.

1. **A · Compatible** — `chem_phase_transition_pom` with
   `linkam_thms600_lnp96_t96`. Review and confirm. The real checker returns
   **Requirements met**. Inspect the stage and optical-access checks. **How we
   checked** opens actual theorem/axiom/input metadata.
2. **B · Incompatible** — `mat_magnetoresistance_10T` with
   `qd_dynacool_9T_eto_res`. Review and confirm. The 9 T documented field cannot
   satisfy the 10 T requirement. The magnet highlights. Change only the machine
   to `qd_dynacool_14T_eto_vsm_hc`; the old result immediately disappears. Check
   again: the stronger magnet still lacks mandatory sample clearance evidence.
3. **C · Missing information** loads that exact 14 T pair directly, for a
   reproducible **Need more information** example. Unknown never becomes pass.

## Coupled physics (30–45 seconds)

Choose **Coupled physics**: `quantum_mxc_wiring_heat_budget` on
`bluefors_ld400_hdw`. Explore the dilution stages and wiring; confirm and check.
The coupled model reports **14.592 µW > 12 µW**. Inspect its equation, sources
and assumptions. Z3 proposes `n_flux_lines = 39`; click **Review this change**,
confirm again, then check. A fresh Lean evaluation accepts **11.985 µW ≤ 12 µW**.

Click **Return to normal mode** at any time. The mode label changes; the engine,
input semantics, viewer, evidence panels and verification adapter do not.

The optional **Frozen tissue** example loads the real Leica profile/configuration
and illustrates the specimen chuck, cutting blade and collection slide.

These frontend Demo A/B/C labels are the requested UI tour sequence. They do not
rename the older A/B/C demonstrations in `python -m cryolean demo`; in particular,
the temporary new-industry profile from the legacy Demo C is not silently added
to the normal catalog.
