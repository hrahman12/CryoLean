From Stdlib Require Import Reals.
From Stdlib Require Import Lra.
Open Scope R_scope.

Module transient_heat_diffusion_1d.

Module Coordinates.
    Record t := mk {
          x : R;
    }.
End Coordinates.

Module State.
    Record t := mk {
          u : R;
    }.
End State.

Module Parameters.
    Record t := mk {
          alpha : R;
    }.
End Parameters.

Module Flux.
    Record t := mk {
          flux_u : R;
    }.
End Flux.

Module Fluxes1D.
    Record t := mk {
          xFlux : Flux.t;
    }.
End Fluxes1D.

Definition xFluxExprs (C : Coordinates.t) (P : Parameters.t) (U : State.t) : Flux.t :=
  let x := C.(Coordinates.x) in
  let alpha := P.(Parameters.alpha) in
  let u := U.(State.u) in
  {|
    Flux.flux_u := 0;
  |}.

Definition fluxes (C : Coordinates.t) (P : Parameters.t) (U : State.t) : Fluxes1D.t :=
  {|
    Fluxes1D.xFlux := xFluxExprs C P U;
  |}.

Module WaveSpeed.
    Record t := mk {
          mu1 : R;
    }.
End WaveSpeed.

Module WaveSpeedEstimate1D.
    Record t := mk {
          xWaveSpeed : WaveSpeed.t;
    }.
End WaveSpeedEstimate1D.

Definition xWaveSpeedExprs (C : Coordinates.t) (P : Parameters.t) (U : State.t) : WaveSpeed.t :=
  let x := C.(Coordinates.x) in
  let alpha := P.(Parameters.alpha) in
  let u := U.(State.u) in
  {|
    WaveSpeed.mu1 := 0;
  |}.

Definition wavespeeds (C : Coordinates.t) (P : Parameters.t) (U : State.t) : WaveSpeedEstimate1D.t :=
  {|
    WaveSpeedEstimate1D.xWaveSpeed := xWaveSpeedExprs C P U;
  |}.

Module StateGradient.
    Record t := mk {
          d_u : R;
    }.
End StateGradient.

Module FluxJacobian.
    Record t := mk {
          flux_u : StateGradient.t;
    }.
End FluxJacobian.

Module FluxJacobians1D.
    Record t := mk {
          xFluxJacobian : FluxJacobian.t;
    }.
End FluxJacobians1D.

Definition xFluxJacobianExprs (C : Coordinates.t) (P : Parameters.t) (U : State.t) : FluxJacobian.t :=
  let x := C.(Coordinates.x) in
  let alpha := P.(Parameters.alpha) in
  let u := U.(State.u) in
  {|
    FluxJacobian.flux_u :=
      {|
        StateGradient.d_u := 0;
      |};
  |}.

Definition fluxJacobians (C : Coordinates.t) (P : Parameters.t) (U : State.t) : FluxJacobians1D.t :=
  {|
    FluxJacobians1D.xFluxJacobian := xFluxJacobianExprs C P U;
  |}.

Module FluxJacobianEigen.
    Record t := mk {
          lambda1 : R;
    }.
End FluxJacobianEigen.

Module FluxJacobianEigendecomposition1D.
    Record t := mk {
          xFluxJacobianEigen : FluxJacobianEigen.t;
    }.
End FluxJacobianEigendecomposition1D.

Definition xFluxJacobianEigenExprs (C : Coordinates.t) (P : Parameters.t) (U : State.t) : FluxJacobianEigen.t :=
  let x := C.(Coordinates.x) in
  let alpha := P.(Parameters.alpha) in
  let u := U.(State.u) in
  {|
    FluxJacobianEigen.lambda1 := 0;
  |}.

Definition fluxJacobianEigenvalues (C : Coordinates.t) (P : Parameters.t) (U : State.t) : FluxJacobianEigendecomposition1D.t :=
  {|
    FluxJacobianEigendecomposition1D.xFluxJacobianEigen := xFluxJacobianEigenExprs C P U;
  |}.

Theorem xHyperbolicity (C : Coordinates.t) (P : Parameters.t) (U : State.t) :
    (exists r1 : R, r1 = (xFluxJacobianEigenExprs C P U).(FluxJacobianEigen.lambda1)).
Proof. repeat split; [ exists (xFluxJacobianEigenExprs C P U).(FluxJacobianEigen.lambda1); reflexivity ].
Qed.

Theorem xWaveStability (C : Coordinates.t) (P : Parameters.t) (U : State.t) :
    ((Rabs (xFluxJacobianEigenExprs C P U).(FluxJacobianEigen.lambda1)) <= (Rabs (xWaveSpeedExprs C P U).(WaveSpeed.mu1))).
Proof. intros;  repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

Module SpatialGradient.
    Record t := mk {
          u_x : R;
    }.
End SpatialGradient.

Module DiffusiveFlux.
    Record t := mk {
          diffusive_flux_u : R;
    }.
End DiffusiveFlux.

Module DiffusiveFluxes1D.
    Record t := mk {
          xDiffusiveFlux : DiffusiveFlux.t;
    }.
End DiffusiveFluxes1D.

Definition xDiffusiveFluxExprs (C : Coordinates.t) (P : Parameters.t) (U : State.t) (DU : SpatialGradient.t) : DiffusiveFlux.t :=
  let x := C.(Coordinates.x) in
  let alpha := P.(Parameters.alpha) in
  let u := U.(State.u) in
  let u_x := DU.(SpatialGradient.u_x) in
  {|
    DiffusiveFlux.diffusive_flux_u := (alpha * u_x);
  |}.

Definition diffusiveFluxes (C : Coordinates.t) (P : Parameters.t) (U : State.t) (DU : SpatialGradient.t) : DiffusiveFluxes1D.t :=
  {|
    DiffusiveFluxes1D.xDiffusiveFlux := xDiffusiveFluxExprs C P U DU;
  |}.

Theorem xDiffusiveFluxConsistency (C : Coordinates.t) (U : State.t) (P : Parameters.t) :
    let DU : SpatialGradient.t :=
      {|
        SpatialGradient.u_x := 0;
      |} in
    ((xDiffusiveFluxExprs C P U DU).(DiffusiveFlux.diffusive_flux_u)) = 0.
Proof. intros;  repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

Module Source.
    Record t := mk {
          source_u : R;
    }.
End Source.

Definition SourceExprs (C : Coordinates.t) (P : Parameters.t) (U : State.t) : Source.t :=
  let x := C.(Coordinates.x) in
  let alpha := P.(Parameters.alpha) in
  let u := U.(State.u) in
  {|
    Source.source_u := 0;
  |}.

Module SourceSpeed.
    Record t := mk {
          mu1 : R;
    }.
End SourceSpeed.

Definition SourceSpeedExprs (C : Coordinates.t) (P : Parameters.t) (U : State.t) : SourceSpeed.t :=
  let x := C.(Coordinates.x) in
  let alpha := P.(Parameters.alpha) in
  let u := U.(State.u) in
  {|
    SourceSpeed.mu1 := 0;
  |}.

Module SourceJacobian.
    Record t := mk {
          source_u : StateGradient.t;
    }.
End SourceJacobian.

Definition SourceJacobianExprs (C : Coordinates.t) (P : Parameters.t) (U : State.t) : SourceJacobian.t :=
  let x := C.(Coordinates.x) in
  let alpha := P.(Parameters.alpha) in
  let u := U.(State.u) in
  {|
    SourceJacobian.source_u :=
      {|
        StateGradient.d_u := 0;
      |};
  |}.

Module SourceJacobianEigen.
    Record t := mk {
          lambda1 : R;
    }.
End SourceJacobianEigen.

Definition SourceJacobianEigenExprs (C : Coordinates.t) (P : Parameters.t) (U : State.t) : SourceJacobianEigen.t :=
  let x := C.(Coordinates.x) in
  let alpha := P.(Parameters.alpha) in
  let u := U.(State.u) in
  {|
    SourceJacobianEigen.lambda1 := 0;
  |}.

Theorem SourceHyperbolicity (C : Coordinates.t) (P : Parameters.t) (U : State.t) :
    (exists r1 : R, r1 = (SourceJacobianEigenExprs C P U).(SourceJacobianEigen.lambda1)).
Proof. repeat split; [ exists (SourceJacobianEigenExprs C P U).(SourceJacobianEigen.lambda1); reflexivity] .
Qed.

Theorem SourceStability (C : Coordinates.t) (P : Parameters.t) (U : State.t) :
    ((Rabs (SourceJacobianEigenExprs C P U).(SourceJacobianEigen.lambda1)) <= (Rabs (SourceSpeedExprs C P U).(SourceSpeed.mu1))).
Proof. intros;  repeat match goal with |- _ /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

End transient_heat_diffusion_1d.

Module transient_heat_diffusion_1d_lax_friedrichs.

Import transient_heat_diffusion_1d.

Module Wave.
    Record t := mk {
          wave_u : R;
    }.
End Wave.

Module WaveFamily.
    Record t := mk {
          wave1 : Wave.t;
  wave2 : Wave.t;
    }.
End WaveFamily.

Module Waves1D.
    Record t := mk {
          xWaveFamily : WaveFamily.t;
    }.
End Waves1D.

Definition xWaveFamilyExprs (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : WaveFamily.t :=
  let x_L := CL.(Coordinates.x) in
  let x_R := CR.(Coordinates.x) in
  let u_L := UL.(State.u) in
  let u_R := UR.(State.u) in
  let alpha := P.(Parameters.alpha) in
  {|
    WaveFamily.wave1 :=
      {|
        Wave.wave_u := ((1 / 2 : R) * ((u_R - u_L) - (((0 * u_R) - (0 * u_L)) / (Rabs alpha))));
      |};
    WaveFamily.wave2 :=
      {|
        Wave.wave_u := ((1 / 2 : R) * ((u_R - u_L) + (((0 * u_R) - (0 * u_L)) / (Rabs alpha))));
      |};
  |}.

Definition waves (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : Waves1D.t :=
  {|
    Waves1D.xWaveFamily := xWaveFamilyExprs CL CR UL UR P;
  |}.

Theorem xWaveConsistency (C : Coordinates.t) (U : State.t) (P : Parameters.t) :
    ((xWaveFamilyExprs C C U U P).(WaveFamily.wave1).(Wave.wave_u)) = 0 /\
    ((xWaveFamilyExprs C C U U P).(WaveFamily.wave2).(Wave.wave_u)) = 0.
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | simpl; field | simpl; nra ] | solve [ reflexivity | simpl; field | simpl; nra ]].
Qed.

Module StateJump.
    Record t := mk {
          jump_u : R;
    }.
End StateJump.

Module StateJumps1D.
    Record t := mk {
          xStateJump : StateJump.t;
    }.
End StateJumps1D.

Definition xStateJumpExprs (UL : State.t) (UR : State.t) : StateJump.t :=
  let u_L := UL.(State.u) in
  let u_R := UR.(State.u) in
  {|
    StateJump.jump_u := u_R - u_L;
  |}.

Definition stateJumps (UL : State.t) (UR : State.t) : StateJumps1D.t :=
  {|
    StateJumps1D.xStateJump := xStateJumpExprs UL UR;
  |}.

Module WaveSum.
    Record t := mk {
          wave_sum_u : R;
    }.
End WaveSum.

Module WaveSums1D.
    Record t := mk {
          xWaveSum : WaveSum.t;
    }.
End WaveSums1D.

Definition xWaveSumExprs (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : WaveSum.t :=
  {|
    WaveSum.wave_sum_u := (xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave1).(Wave.wave_u) + (xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave2).(Wave.wave_u)
  |}.

Definition waveSums (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : WaveSums1D.t :=
  {|
    WaveSums1D.xWaveSum := xWaveSumExprs CL CR UL UR P;
  |}.

Theorem xWaveJumpCondition (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) :
    ((xStateJumpExprs UL UR).(StateJump.jump_u) = (xWaveSumExprs CL CR UL UR P).(WaveSum.wave_sum_u)).
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | simpl; field | simpl; nra ]].
Qed.

Module SpeedFamily.
    Record t := mk {
          speed1 : R;
  speed2 : R;
    }.
End SpeedFamily.

Module Speeds1D.
    Record t := mk {
          xSpeedFamily : SpeedFamily.t;
    }.
End Speeds1D.

Definition xSpeedFamilyExprs (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : SpeedFamily.t :=
  let x_L := CL.(Coordinates.x) in
  let x_R := CR.(Coordinates.x) in
  let u_L := UL.(State.u) in
  let u_R := UR.(State.u) in
  let alpha := P.(Parameters.alpha) in
  {|
    SpeedFamily.speed1 := -((Rabs alpha));
    SpeedFamily.speed2 := (Rabs alpha);
  |}.

Definition speeds (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : Speeds1D.t :=
  {|
    Speeds1D.xSpeedFamily := xSpeedFamilyExprs CL CR UL UR P;
  |}.

Module Fluctuation.
    Record t := mk {
          fluctuation_u : R;
    }.
End Fluctuation.

Module Fluctuations1D.
    Record t := mk {
          xFluctuation : Fluctuation.t;
    }.
End Fluctuations1D.

Definition xLeftFluctuationExprs (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : Fluctuation.t :=
  {|
    Fluctuation.fluctuation_u := 
      (xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave1).(Wave.wave_u) * (Rmin (xSpeedFamilyExprs CL CR UL UR P).(SpeedFamily.speed1) 0) +
      (xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave2).(Wave.wave_u) * (Rmin (xSpeedFamilyExprs CL CR UL UR P).(SpeedFamily.speed2) 0)
  |}.

Definition xRightFluctuationExprs (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : Fluctuation.t :=
  {|
    Fluctuation.fluctuation_u := 
      (xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave1).(Wave.wave_u) * (Rmax (xSpeedFamilyExprs CL CR UL UR P).(SpeedFamily.speed1) 0) +
      (xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave2).(Wave.wave_u) * (Rmax (xSpeedFamilyExprs CL CR UL UR P).(SpeedFamily.speed2) 0)
  |}.

Definition leftFluctuations (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : Fluctuations1D.t :=
  {|
    Fluctuations1D.xFluctuation := xLeftFluctuationExprs CL CR UL UR P;
  |}.

Definition rightFluctuations (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : Fluctuations1D.t :=
  {|
    Fluctuations1D.xFluctuation := xRightFluctuationExprs CL CR UL UR P;
  |}.

Theorem xLeftFluctuationsConsistent (C : Coordinates.t) (U : State.t) (P : Parameters.t) :
    ((xLeftFluctuationExprs C C U U P).(Fluctuation.fluctuation_u)) = 0.
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | simpl; field | simpl; nra ]].
Qed.

Theorem xRightFluctuationsConsistent (C : Coordinates.t) (U : State.t) (P : Parameters.t) :
    ((xRightFluctuationExprs C C U U P).(Fluctuation.fluctuation_u)) = 0.
Proof. intros;  repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | simpl; field | simpl; nra ]].
Qed.

Module FluxJump.
    Record t := mk {
          flux_jump_u : R;
    }.
End FluxJump.

Module FluxJumps1D.
    Record t := mk {
          xFluxJump : FluxJump.t;
    }.
End FluxJumps1D.

Definition xFluxJumpExprs (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : FluxJump.t :=
  {|
    FluxJump.flux_jump_u := (xFluxExprs CR P UR).(Flux.flux_u) - (xFluxExprs CL P UL).(Flux.flux_u)
  |}.

Definition fluxJumps (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t): FluxJumps1D.t :=
  {|
    FluxJumps1D.xFluxJump := xFluxJumpExprs CL CR UL UR P;
  |}.

Module FluctuationSum.
    Record t := mk {
          fluctuation_sum_u : R;
    }.
End FluctuationSum.

Module FluctuationSums1D.
    Record t := mk {
          xFluctuationSum : FluctuationSum.t;
    }.
End FluctuationSums1D.

Definition xFluctuationSumExprs (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : FluctuationSum.t :=
  {|
    FluctuationSum.fluctuation_sum_u := (xLeftFluctuationExprs CL CR UL UR P).(Fluctuation.fluctuation_u) + (xRightFluctuationExprs CL CR UL UR P).(Fluctuation.fluctuation_u)
  |}.

Definition fluctuationSums (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : FluctuationSums1D.t :=
  {|
    FluctuationSums1D.xFluctuationSum := xFluctuationSumExprs CL CR UL UR P;
  |}.

Lemma two_wave_flux_jump (sL sR J F w1 w2 : R) :
  sR - sL <> 0 ->
  w1 = (1 / 2) * J + ((1 / 2) * ((sL + sR) * J) - F) / (sR - sL) ->
  w2 = (1 / 2) * J - ((1 / 2) * ((sL + sR) * J) - F) / (sR - sL) ->
  F = w1 * sL + w2 * sR.
Proof. intros gap -> ->. field. exact gap. Qed.

Lemma Rinv_sym_gap (a : R) : / (a - - a) = (1 / 2) * / a.
Proof.
  replace (a - - a) with (2 * a) by ring.
  rewrite Rinv_mult. f_equal. field.
Qed.

Theorem xFluxConservative (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) (SpeedGapNondegenerate : (
      let x_L := CL.(Coordinates.x) in
      let x_R := CR.(Coordinates.x) in
      let u_L := UL.(State.u) in
      let u_R := UR.(State.u) in
      let alpha := P.(Parameters.alpha) in
      ((Rabs alpha) - -((Rabs alpha)) <> 0))) :    ((xFluxJumpExprs CL CR UL UR P).(FluxJump.flux_jump_u) = (xFluctuationSumExprs CL CR UL UR P).(FluctuationSum.fluctuation_sum_u)).
Proof.
  set (sL := (xSpeedFamilyExprs CL CR UL UR P).(SpeedFamily.speed1));
  set (sR := (xSpeedFamilyExprs CL CR UL UR P).(SpeedFamily.speed2));
  assert (gap : (sR - sL <> 0)) by exact SpeedGapNondegenerate;
  assert (fluctuationSum : forall w1 w2 : R,
            w1 * Rmin sL 0 + w2 * Rmin sR 0 + (w1 * Rmax sL 0 + w2 * Rmax sR 0) = w1 * sL + w2 * sR) by (
            intros w1 w2;
            replace (Rmin sL 0) with (sL - Rmax sL 0) by (unfold Rmin, Rmax; destruct (Rle_dec sL 0); lra);
            replace (Rmin sR 0) with (sR - Rmax sR 0) by (unfold Rmin, Rmax; destruct (Rle_dec sR 0); lra);
            ring).
  repeat match goal with |- _  /\ _ => split end;
    [ transitivity ((xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave1).(Wave.wave_u) * sL + (xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave2).(Wave.wave_u) * sR); [ 
                    eapply (two_wave_flux_jump sL sR (StateJump.jump_u (xStateJumpExprs UL UR)));
                    [ exact gap | unfold sL, sR; simpl; unfold Rdiv; rewrite ?Rinv_sym_gap; unfold Rdiv; ring | unfold sL, sR; simpl; unfold Rdiv; rewrite ?Rinv_sym_gap; unfold Rdiv; ring ]
                    | unfold xFluctuationSumExprs, xLeftFluctuationExprs, xRightFluctuationExprs;
                    cbn [FluctuationSum.fluctuation_sum_u Fluctuation.fluctuation_u];
                    rewrite <- (fluctuationSum (xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave1).(Wave.wave_u) (xWaveFamilyExprs CL CR UL UR P).(WaveFamily.wave2).(Wave.wave_u));
                    fold sL; fold sR; reflexivity ]
 ].
Qed.

End transient_heat_diffusion_1d_lax_friedrichs.

Module transient_heat_diffusion_1d_minmod.

Import transient_heat_diffusion_1d.

Module Reconstruction.
    Record t := mk {
          reconstruction_u : R;
    }.
End Reconstruction.

Module Reconstruction1D.
    Record t := mk {
          xReconstruction : Reconstruction.t;
    }.
End Reconstruction1D.

Definition xLeftReconstructionExprs (CL : Coordinates.t) (C : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (U : State.t) (UR : State.t) (P : Parameters.t) : Reconstruction.t :=
  let x_L := CL.(Coordinates.x) in 
  let x := C.(Coordinates.x) in
  let x_R := CR.(Coordinates.x) in
  let u_L := UL.(State.u) in 
  let u := U.(State.u) in
  let u_R := UR.(State.u) in
  let alpha := P.(Parameters.alpha) in
  {|
    Reconstruction.reconstruction_u := (f - ((1 / 2 : R) * ((Rmax 0 (Rmin (f - f_L) (f_R - f))) + (Rmin 0 (Rmax (f -
      f_L) (f_R - f))))))
  |}.

Definition xRightReconstructionExprs (CL : Coordinates.t) (C : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (U : State.t) (UR : State.t) (P : Parameters.t) : Reconstruction.t :=
  let x_L := CL.(Coordinates.x) in
  let x := C.(Coordinates.x) in
  let x_R := CR.(Coordinates.x) in
  let u_L := UL.(State.u) in
  let u := U.(State.u) in 
  let u_R := UR.(State.u) in
  let alpha := P.(Parameters.alpha) in 
  {|
    Reconstruction.reconstruction_u := (f + ((1 / 2 : R) * ((Rmax 0 (Rmin (f - f_L) (f_R - f))) + (Rmin 0 (Rmax (f -
      f_L) (f_R - f))))))
  |}.

Definition leftReconstruction (CL : Coordinates.t) (C : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (U : State.t) (UR : State.t) (P : Parameters.t) : Reconstruction1D.t :=
  {|
    Reconstruction1D.xReconstruction := xLeftReconstructionExprs CL C CR UL U UR P;
  |}.

Definition rightReconstruction (CL : Coordinates.t) (C : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (U : State.t) (UR : State.t) (P : Parameters.t) : Reconstruction1D.t :=
  {|
    Reconstruction1D.xReconstruction := xRightReconstructionExprs CL C CR UL U UR P;
  |}.

Theorem xLeftReconstructionConsistent (C : Coordinates.t) (U : State.t) (P : Parameters.t) :
    ((xLeftReconstructionExprs C C C U U U P).(Reconstruction.reconstruction_u)) = U.(State.u).
Proof. intros. repeat match goal with |- _  /\ _ => split end; [ 
  simpl in *; 
  unfold Rabs, Rmax, Rmin in *; unfold Rabs, Rmax, Rmin;
  repeat match goal with 
    | |- context[Rcase_abs ?x] => destruct (Rcase_abs x)
    | |- context[Rle_dec ?x ?y] => destruct (Rle_dec x y)
  end;
  repeat match goal with
    | H : context[- - ?x] |- _ => rewrite Ropp_involutive in H
  end;
  repeat match goal with
    | H : ~ (?x <= ?y) |- _ => apply Rnot_le_lt in H
  end; 
  repeat match goal with
    | H : context[Rle_dec ?x ?y] |- _ => destruct (Rle_dec x y)
  end; solve [ assumption | field | lra | nra ] ].
Qed.

Theorem xRightReconstructionConsistent (C : Coordinates.t) (U : State.t) (P : Parameters.t) :
    ((xRightReconstructionExprs C C C U U U P).(Reconstruction.reconstruction_u)) = U.(State.u).
Proof. intros. repeat match goal with |- _  /\ _ => split end; [ 
  simpl in *; 
  unfold Rabs, Rmax, Rmin in *; unfold Rabs, Rmax, Rmin;
  repeat match goal with 
    | |- context[Rcase_abs ?x] => destruct (Rcase_abs x)
    | |- context[Rle_dec ?x ?y] => destruct (Rle_dec x y)
  end;
  repeat match goal with
    | H : context[- - ?x] |- _ => rewrite Ropp_involutive in H
  end;
  repeat match goal with
    | H : ~ (?x <= ?y) |- _ => apply Rnot_le_lt in H
  end; 
  repeat match goal with
    | H : context[Rle_dec ?x ?y] |- _ => destruct (Rle_dec x y)
  end; solve [ assumption | field | lra | nra ] ].
Qed.

Theorem xLeftReconstructionLinearityPreservation (CL : Coordinates.t) (C : Coordinates.t) (CR : Coordinates.t)
    (U : State.t) (P : Parameters.t) (D : R) :
    let UL : State.t :=
      {|
        State.u := U.(State.u) - D;
      |} in
    let UR : State.t :=
      {|
        State.u := U.(State.u) + D;
      |} in
    ((xLeftReconstructionExprs CL C CR UL U UR P).(Reconstruction.reconstruction_u)) = U.(State.u) - ((1 / 2) * D).
Proof. intros. repeat match goal with |- _  /\ _ => split end; [ 
  simpl in *; 
  unfold Rabs, Rmax, Rmin in *; unfold Rabs, Rmax, Rmin;
  repeat match goal with 
    | |- context[Rcase_abs ?x] => destruct (Rcase_abs x)
    | |- context[Rle_dec ?x ?y] => destruct (Rle_dec x y)
  end;
  repeat match goal with
    | H : context[- - ?x] |- _ => rewrite Ropp_involutive in H
  end;
  repeat match goal with
    | H : ~ (?x <= ?y) |- _ => apply Rnot_le_lt in H
  end; 
  repeat match goal with
    | H : context[Rle_dec ?x ?y] |- _ => destruct (Rle_dec x y)
  end; solve [ assumption | field | lra | nra ] ].
Qed.

Theorem xRightReconstructionLinearityPreservation (CL : Coordinates.t) (C : Coordinates.t) (CR : Coordinates.t)
    (U : State.t) (P : Parameters.t) (D : R) :
    let UL : State.t :=
      {|
        State.u := U.(State.u) - D;
      |} in
    let UR : State.t :=
      {|
        State.u := U.(State.u) + D;
      |} in
    ((xRightReconstructionExprs CL C CR UL U UR P).(Reconstruction.reconstruction_u)) = U.(State.u) + ((1 / 2) * D).
Proof. intros. repeat match goal with |- _  /\ _ => split end; [ 
  simpl in *; 
  unfold Rabs, Rmax, Rmin in *; unfold Rabs, Rmax, Rmin;
  repeat match goal with 
    | |- context[Rcase_abs ?x] => destruct (Rcase_abs x)
    | |- context[Rle_dec ?x ?y] => destruct (Rle_dec x y)
  end;
  repeat match goal with
    | H : context[- - ?x] |- _ => rewrite Ropp_involutive in H
  end;
  repeat match goal with
    | H : ~ (?x <= ?y) |- _ => apply Rnot_le_lt in H
  end; 
  repeat match goal with
    | H : context[Rle_dec ?x ?y] |- _ => destruct (Rle_dec x y)
  end; solve [ assumption | field | lra | nra ] ].
Qed.

Theorem xReconstructionSymmetric (CL : Coordinates.t) (C : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (U : State.t) (UR : State.t) (P : Parameters.t) :
    ((xLeftReconstructionExprs CL C CR UL U UR P).(Reconstruction.reconstruction_u)) = ((xRightReconstructionExprs CR C CL UR U UL P).(Reconstruction.reconstruction_u)).
Proof. intros. repeat match goal with |- _  /\ _ => split end; [ 
  simpl in *; 
  unfold Rabs, Rmax, Rmin in *; unfold Rabs, Rmax, Rmin;
  repeat match goal with 
    | |- context[Rcase_abs ?x] => destruct (Rcase_abs x)
    | |- context[Rle_dec ?x ?y] => destruct (Rle_dec x y)
  end;
  repeat match goal with
    | H : context[- - ?x] |- _ => rewrite Ropp_involutive in H
  end;
  repeat match goal with
    | H : ~ (?x <= ?y) |- _ => apply Rnot_le_lt in H
  end; 
  repeat match goal with
    | H : context[Rle_dec ?x ?y] |- _ => destruct (Rle_dec x y)
  end; solve [ assumption | field | lra | nra ] ].
Qed.

End transient_heat_diffusion_1d_minmod.

Module transient_heat_diffusion_1d_ssp_rk3.

Import transient_heat_diffusion_1d.

Module Stage.
    Record t := mk {
        stage_u : R;
    }.
End Stage.

Module StageFamily.
    Record t := mk {
        stage1 : Stage.t;
  stage2 : Stage.t;
  stage3 : Stage.t;
    }.
End StageFamily.

Module Stages1D.
    Record t := mk {
        xStageFamily : StageFamily.t;
  sourceStageFamily : StageFamily.t;
    }.
End Stages1D.

Definition xStageFamilyExprs (C0 : Coordinates.t) (C1 : Coordinates.t) (C2 : Coordinates.t)
    (U0 : State.t) (U1 : State.t) (U2 : State.t) (U0_RHS : State.t) (U1_RHS : State.t) (U2_RHS : State.t)
    (P : Parameters.t) (dt : R) : StageFamily.t :=  let x0 := C0.(Coordinates.x) in
  let x1 := C1.(Coordinates.x) in
  let x2 := C2.(Coordinates.x) in
  let u0 := U0.(State.u) in
  let u1 := U1.(State.u) in
  let u2 := U2.(State.u) in
  let u0_rhs := U0_RHS.(State.u) in
  let u1_rhs := U1_RHS.(State.u) in
  let u2_rhs := U2_RHS.(State.u) in
  let alpha := P.(Parameters.alpha) in
  {|
    StageFamily.stage1 :=
      {|
        Stage.stage_u := (f0 + (dt * f0_rhs));
      |};
    StageFamily.stage2 :=
      {|
        Stage.stage_u := (((3 / 4 : R) * f0) + ((1 / 4 : R) * (f1 + (dt * f1_rhs))));
      |};
    StageFamily.stage3 :=
      {|
        Stage.stage_u := (((1 / 3) * f0) + ((2 / 3) * (f2 + (dt * f2_rhs))));
      |};
  |}.

Definition sourceStageFamilyExprs (C0 : Coordinates.t) (C1 : Coordinates.t) (C2 : Coordinates.t)
    (U0 : State.t) (U1 : State.t) (U2 : State.t) (U0_RHS : State.t) (U1_RHS : State.t) (U2_RHS : State.t)
    (P : Parameters.t) (dt : R) : StageFamily.t :=  let x0 := C0.(Coordinates.x) in
  let x1 := C1.(Coordinates.x) in
  let x2 := C2.(Coordinates.x) in
  let u0 := U0.(State.u) in
  let u1 := U1.(State.u) in
  let u2 := U2.(State.u) in
  let u0_rhs := U0_RHS.(State.u) in
  let u1_rhs := U1_RHS.(State.u) in
  let u2_rhs := U2_RHS.(State.u) in
  let alpha := P.(Parameters.alpha) in
  {|
    StageFamily.stage1 :=
      {|
        Stage.stage_u := (f0 + (dt * f0_rhs));
      |};
    StageFamily.stage2 :=
      {|
        Stage.stage_u := (((3 / 4 : R) * f0) + ((1 / 4 : R) * (f1 + (dt * f1_rhs))));
      |};
    StageFamily.stage3 :=
      {|
        Stage.stage_u := (((1 / 3) * f0) + ((2 / 3) * (f2 + (dt * f2_rhs))));
      |};
  |}.

Definition stages (C0 : Coordinates.t) (C1 : Coordinates.t) (C2 : Coordinates.t) (U0 : State.t) (U1 : State.t) (U2 : State.t)
    (U0_RHS : State.t) (U1_RHS : State.t) (U2_RHS : State.t)
    (P : Parameters.t) (dt : R) : Stages1D.t :=
  {|
    Stages1D.xStageFamily := xStageFamilyExprs C0 C1 C2 U0 U1 U2 U0_RHS U1_RHS U2_RHS P dt;
    Stages1D.sourceStageFamily := sourceStageFamilyExprs C0 C1 C2 U0 U1 U2 U0_RHS U1_RHS U2_RHS P dt;
  |}.

Theorem xStageConsistency (C : Coordinates.t) (U : State.t) (U_RHS : State.t) (P : Parameters.t) :
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).(StageFamily.stage1).(Stage.stage_u)) = U.(State.u) /\
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).(StageFamily.stage2).(Stage.stage_u)) = U.(State.u) /\
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).(StageFamily.stage3).(Stage.stage_u)) = U.(State.u).
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ] | solve [ reflexivity | (simpl; field) | simpl; nra ] | solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

Theorem sourceStageConsistency (C : Coordinates.t) (U : State.t) (U_RHS : State.t) (P : Parameters.t) :
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).(StageFamily.stage1).(Stage.stage_u)) = U.(State.u) /\
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).(StageFamily.stage2).(Stage.stage_u)) = U.(State.u) /\
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).(StageFamily.stage3).(Stage.stage_u)) = U.(State.u).
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ] | solve [ reflexivity | (simpl; field) | simpl; nra ] | solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

Theorem xStageEquilibriumPreservation (C : Coordinates.t) (U : State.t) (P : Parameters.t) (dt : R) :
    let U_RHS : State.t :=
      {|
        State.u := 0;
      |} in
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).(StageFamily.stage1).(Stage.stage_u)) = U.(State.u) /\
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).(StageFamily.stage2).(Stage.stage_u)) = U.(State.u) /\
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).(StageFamily.stage3).(Stage.stage_u)) = U.(State.u).
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ] | solve [ reflexivity | (simpl; field) | simpl; nra ] | solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

Theorem sourceStageEquilibriumPreservation (C : Coordinates.t) (U : State.t) (P : Parameters.t) (dt : R) :
    let U_RHS : State.t :=
      {|
        State.u := 0;
      |} in
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).(StageFamily.stage1).(Stage.stage_u)) = U.(State.u) /\
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).(StageFamily.stage2).(Stage.stage_u)) = U.(State.u) /\
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).(StageFamily.stage3).(Stage.stage_u)) = U.(State.u).
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ] | solve [ reflexivity | (simpl; field) | simpl; nra ] | solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

End transient_heat_diffusion_1d_ssp_rk3.

Module transient_heat_diffusion_1d_centered_diffusion.

Import transient_heat_diffusion_1d.

Module InterfaceState.
    Record t := mk {
      interface_u : R;
    }.
End InterfaceState.

Module InterfaceState1D.
    Record t := mk {
      xInterfaceState : InterfaceState.t;
    }.
End InterfaceState1D.

Definition xInterfaceStateExprs (C_Lx : Coordinates.t) (C_Rx : Coordinates.t)
    (U_Lx : State.t) (U_Rx : State.t) (P : Parameters.t) : InterfaceState.t :=
  let x_Lx := C_Lx.(Coordinates.x) in
  let x_Rx := C_Rx.(Coordinates.x) in
  let u_Lx := U_Lx.(State.u) in
  let u_Rx := U_Rx.(State.u) in
  let alpha := P.(Parameters.alpha) in
  {|
    InterfaceState.interface_u := ((1 / 2 : R) * (f_Lx + f_Rx));
  |}.

Definition interfaceState (CL : Coordinates.t) (CR : Coordinates.t)
    (UL : State.t) (UR : State.t) (P : Parameters.t) : InterfaceState1D.t :=
  {|     InterfaceState1D.xInterfaceState := xInterfaceStateExprs CL CR UL UR P; |}.

Theorem xInterfaceStateConsistent (C : Coordinates.t) (U : State.t) (P : Parameters.t) :
    ((xInterfaceStateExprs C C U U P).(InterfaceState.interface_u)) = U.(State.u).
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

Theorem xInterfaceStateSymmetric (C_Lx : Coordinates.t) (C_Rx : Coordinates.t)
    (U_Lx : State.t) (U_Rx : State.t) (P : Parameters.t) :
    ((xInterfaceStateExprs C_Lx C_Rx U_Lx U_Rx P).(InterfaceState.interface_u)) = ((xInterfaceStateExprs C_Rx C_Lx U_Rx U_Lx P).(InterfaceState.interface_u)).
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

Module InterfaceGradient.
    Record t := mk {
      interface_u_x : R;
    }.
End InterfaceGradient.

Module InterfaceGradients1D.
    Record t := mk {
      xInterfaceGradient : InterfaceGradient.t;
    }.
End InterfaceGradients1D.

Definition xInterfaceGradientExprs (C_Lx : Coordinates.t) (C_Rx : Coordinates.t)
    (U_Lx: State.t) (U_Rx : State.t) (P : Parameters.t) : InterfaceGradient.t :=
  let x_Lx := C_Lx.(Coordinates.x) in
  let x_Rx := C_Rx.(Coordinates.x) in
  let u_Lx := U_Lx.(State.u) in
  let u_Rx := U_Rx.(State.u) in
  let alpha := P.(Parameters.alpha) in
  {|
    InterfaceGradient.interface_u_x := ((f_Rx - f_Lx) / (x_Rx - x_Lx));
  |}.

Theorem xInterfaceGradientConsistency (C_Lx : Coordinates.t) (C_Rx : Coordinates.t)
    (Ux: State.t) (U_Lx : State.t) (U_Rx : State.t) (P : Parameters.t) :
    ((xInterfaceGradientExprs C_Lx C_Rx Ux Ux P).(InterfaceGradient.interface_u_x)) = 0.
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

Theorem xInterfaceGradientAntisymmetric (C_Lx : Coordinates.t) (C_Rx : Coordinates.t)
    (U_Lx : State.t) (U_Rx : State.t) (P : Parameters.t) :
    ((xInterfaceGradientExprs C_Lx C_Rx U_Lx U_Rx P).(InterfaceGradient.interface_u_x)) = -((xInterfaceGradientExprs
      C_Lx C_Rx U_Rx U_Lx P).(InterfaceGradient.interface_u_x)).
Proof. intros; repeat match goal with |- _  /\ _ => split end; [
solve [ reflexivity | (simpl; field) | simpl; nra ]].
Qed.

End transient_heat_diffusion_1d_centered_diffusion.