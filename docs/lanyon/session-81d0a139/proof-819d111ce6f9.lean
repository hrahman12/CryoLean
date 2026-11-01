import Mathlib.Algebra.Order.Archimedean.Real.Basic
import Mathlib.Tactic.LinearCombination
import Mathlib.Analysis.Real.Sqrt
import Mathlib.Algebra.Order.Group.Unbundled.Abs
import Mathlib.Algebra.Order.Monoid.Unbundled.MinMax
import Mathlib.Analysis.Complex.Exponential

set_option linter.unusedVariables false
set_option linter.unusedTactic false
set_option linter.unreachableTactic false
set_option linter.unnecessarySeqFocus false
set_option maxHeartbeats 1000000

namespace transient_heat_diffusion_1d

structure Coordinates where
  x : Real

structure State where
  u : Real

structure Parameters where
  alpha : Real

structure Flux where
  flux_u : Real

structure Fluxes1D where
  xFlux : Flux

noncomputable def xFluxExprs (C : Coordinates) (P : Parameters) (U : State) : Flux :=
  let x := C.x
  let alpha := P.alpha
  let u := U.u
  {
    flux_u := 0
  }

noncomputable def fluxes (C : Coordinates) (P : Parameters) (U : State) : Fluxes1D :=
  {
    xFlux := xFluxExprs C P U
  }

structure WaveSpeed where
  mu1 : Real

structure WaveSpeedEstimate1D where
  xWaveSpeed : WaveSpeed

noncomputable def xWaveSpeedExprs (C : Coordinates) (P : Parameters) (U : State) : WaveSpeed :=
  let x := C.x
  let alpha := P.alpha
  let u := U.u
  {
    mu1 := 0
  }

noncomputable def wavespeeds (C : Coordinates) (P : Parameters) (U : State) : WaveSpeedEstimate1D :=
  {
    xWaveSpeed := xWaveSpeedExprs C P U
  }

structure StateGradient where
  d_u : Real

structure FluxJacobian where
  flux_u : StateGradient

structure FluxJacobians1D where
  xFluxJacobian : FluxJacobian

noncomputable def xFluxJacobianExprs (C : Coordinates) (P : Parameters) (U : State) : FluxJacobian :=
  let x := C.x
  let alpha := P.alpha
  let u := U.u
  {
    flux_u :=
      {
        d_u := 0
      }
  }

noncomputable def fluxJacobians (C : Coordinates) (P : Parameters) (U : State) : FluxJacobians1D :=
  {
    xFluxJacobian := xFluxJacobianExprs C P U
  }

structure FluxJacobianEigen where
  lambda1 : Real

structure FluxJacobianEigendecomposition1D where
  xFluxJacobianEigen : FluxJacobianEigen

noncomputable def xFluxJacobianEigenExprs (C : Coordinates) (P : Parameters) (U : State) : FluxJacobianEigen :=
  let x := C.x
  let alpha := P.alpha
  let u := U.u
  {
    lambda1 := 0
  }

noncomputable def fluxJacobianEigenvalues (C : Coordinates) (P : Parameters) (U : State) : FluxJacobianEigendecomposition1D :=
  {
    xFluxJacobianEigen := xFluxJacobianEigenExprs C P U
  }

theorem xHyperbolicity (C : Coordinates) (P : Parameters) (U : State) :
    (∃ r1 : Real, r1 = (xFluxJacobianEigenExprs C P U).lambda1) := by
  . refine ⟨(xFluxJacobianEigenExprs C P U).lambda1, rfl⟩

theorem xWaveStability (C : Coordinates) (P : Parameters) (U : State) :
    ((abs (xWaveSpeedExprs C P U).mu1) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda1)) := by
  . simp [xWaveSpeedExprs, xFluxJacobianEigenExprs] <;> ring_nf

structure SpatialGradient where
  u_x : Real

structure DiffusiveFlux where
  diffusive_flux_u : Real

structure DiffusiveFluxes1D where
  xDiffusiveFlux : DiffusiveFlux

noncomputable def xDiffusiveFluxExprs (C : Coordinates) (P : Parameters) (U : State) (DU : SpatialGradient) : DiffusiveFlux :=
  let x := C.x
  let alpha := P.alpha
  let u := U.u
  let u_x := DU.u_x
  {
    diffusive_flux_u := (alpha * u_x)
  }

noncomputable def diffusiveFluxes (C : Coordinates) (P : Parameters) (U : State) (DU : SpatialGradient) : DiffusiveFluxes1D :=
  {
    xDiffusiveFlux := xDiffusiveFluxExprs C P U DU
  }

theorem xDiffusiveFluxConsistency (C : Coordinates) (U : State) (P : Parameters) :
    let DU : SpatialGradient :=
      {
        u_x := 0
      }
    ((xDiffusiveFluxExprs C P U DU).diffusive_flux_u) = 0 := by
  . simp only [xDiffusiveFluxExprs] <;> ring_nf

structure Source where
  source_u : Real

noncomputable def SourceExprs (C : Coordinates) (P : Parameters) (U : State) : Source :=
  let x := C.x
  let alpha := P.alpha
  let u := U.u
  {
    source_u := 0
  }

structure SourceSpeed where
  mu1 : Real

noncomputable def SourceSpeedExprs (C : Coordinates) (P : Parameters) (U : State) : SourceSpeed :=
  let x := C.x
  let alpha := P.alpha
  let u := U.u
  {
    mu1 := 0
  }

structure SourceJacobian where
  source_u : StateGradient

noncomputable def SourceJacobianExprs (C : Coordinates) (P : Parameters) (U : State) : SourceJacobian :=
  let x := C.x
  let alpha := P.alpha
  let u := U.u
  {
    source_u :=
      {
        d_u := 0
      }
  }

structure SourceJacobianEigen where
  lambda1 : Real

noncomputable def SourceJacobianEigenExprs (C : Coordinates) (P : Parameters) (U : State) : SourceJacobianEigen :=
  let x := C.x
  let alpha := P.alpha
  let u := U.u
  {
    lambda1 := 0
  }

theorem SourceHyperbolicity (C : Coordinates) (P : Parameters) (U : State) :
    (∃ r1 : Real, r1 = (SourceJacobianEigenExprs C P U).lambda1) := by
  . refine ⟨(SourceJacobianEigenExprs C P U).lambda1, rfl⟩

theorem SourceStability (C : Coordinates) (P : Parameters) (U : State) :
    ((abs (SourceSpeedExprs C P U).mu1) ≥ (abs (SourceJacobianEigenExprs C P U).lambda1)) := by
  . simp [SourceSpeedExprs, SourceJacobianEigenExprs] <;> ring_nf

end transient_heat_diffusion_1d

namespace transient_heat_diffusion_1d_lax_friedrichs

open transient_heat_diffusion_1d

structure Wave where
  wave_u : Real

structure WaveFamily where
  wave1 : Wave
  wave2 : Wave

structure Waves1D where
  xWaveFamily : WaveFamily

noncomputable def xWaveFamilyExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : WaveFamily :=
  let x_L := CL.x
  let x_R := CR.x
  let u_L := UL.u
  let u_R := UR.u
  let alpha := P.alpha
  {
    wave1 :=
      {
        wave_u := ((1 / 2 : Real) * ((u_R - u_L) - (((0 * u_R) - (0 * u_L)) / (abs alpha))))
      }
    wave2 :=
      {
        wave_u := ((1 / 2 : Real) * ((u_R - u_L) + (((0 * u_R) - (0 * u_L)) / (abs alpha))))
      }
  }

noncomputable def waves (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Waves1D :=
  {
    xWaveFamily := xWaveFamilyExprs CL CR UL UR P
  }

theorem xWaveConsistency (C : Coordinates) (U : State) (P : Parameters) :
    ((xWaveFamilyExprs C C U U P).wave1.wave_u) = 0 ∧
    ((xWaveFamilyExprs C C U U P).wave2.wave_u) = 0 := by
  constructor
  . simp [xWaveFamilyExprs] <;> ring_nf <;> field_simp
  . simp [xWaveFamilyExprs] <;> ring_nf <;> field_simp

structure StateJump where
  jump_u : Real

structure StateJumps1D where
  xStateJump : StateJump

noncomputable def xStateJumpExprs (UL : State) (UR : State) : StateJump :=
  let u_L := UL.u
  let u_R := UR.u
  {
    jump_u := u_R - u_L
  }

noncomputable def stateJumps (UL : State) (UR : State) : StateJumps1D :=
  {
    xStateJump := xStateJumpExprs UL UR
  }

structure WaveSum where
  wave_sum_u : Real

structure WaveSums1D where
  xWaveSum : WaveSum

noncomputable def xWaveSumExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : WaveSum :=
  {
    wave_sum_u := (xWaveFamilyExprs CL CR UL UR P).wave1.wave_u + (xWaveFamilyExprs CL CR UL UR P).wave2.wave_u
  }

noncomputable def waveSums (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : WaveSums1D :=
  {
    xWaveSum := xWaveSumExprs CL CR UL UR P
  }

theorem xWaveJumpCondition (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) :
    ((xStateJumpExprs UL UR).jump_u = (xWaveSumExprs CL CR UL UR P).wave_sum_u) := by
  . simp [xStateJumpExprs, xWaveSumExprs, xWaveFamilyExprs] <;> (ring_nf)

structure SpeedFamily where
  speed1 : Real
  speed2 : Real

structure Speeds1D where
  xSpeedFamily : SpeedFamily

noncomputable def xSpeedFamilyExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : SpeedFamily :=
  let x_L := CL.x
  let x_R := CR.x
  let u_L := UL.u
  let u_R := UR.u
  let alpha := P.alpha
  {
    speed1 := -((abs alpha))
    speed2 := (abs alpha)
  }

noncomputable def speeds (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Speeds1D :=
  {
    xSpeedFamily := xSpeedFamilyExprs CL CR UL UR P
  }

structure Fluctuation where
  fluctuation_u : Real

structure Fluctuations1D where
  xFluctuation : Fluctuation

noncomputable def xLeftFluctuationExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuation :=
  {
    fluctuation_u := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_u * (min (xSpeedFamilyExprs CL CR UL UR P).speed1 0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_u * (min (xSpeedFamilyExprs CL CR UL UR P).speed2 0))
  }

noncomputable def xRightFluctuationExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuation :=
  {
    fluctuation_u := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_u * (max (xSpeedFamilyExprs CL CR UL UR P).speed1 0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_u * (max (xSpeedFamilyExprs CL CR UL UR P).speed2 0))
  }

noncomputable def leftFluctuations (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuations1D :=
  {
    xFluctuation := xLeftFluctuationExprs CL CR UL UR P
  }

noncomputable def rightFluctuations (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuations1D :=
  {
    xFluctuation := xRightFluctuationExprs CL CR UL UR P
  }

theorem xLeftFluctuationsConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xLeftFluctuationExprs C C U U P).fluctuation_u) = 0 := by
  . simp [xLeftFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs] <;> ring_nf <;> field_simp

theorem xRightFluctuationsConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xRightFluctuationExprs C C U U P).fluctuation_u) = 0 := by
  . simp [xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs] <;> ring_nf <;> field_simp

structure FluxJump where
  flux_jump_u : Real

structure FluxJumps1D where
  xFluxJump : FluxJump

noncomputable def xFluxJumpExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : FluxJump :=
  {
    flux_jump_u := (xFluxExprs CR P UR).flux_u - (xFluxExprs CL P UL).flux_u
  }

noncomputable def fluxJumps (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters): FluxJumps1D :=
  {
    xFluxJump := xFluxJumpExprs CL CR UL UR P
  }

structure FluctuationSum where
  fluctuation_sum_u : Real

structure FluctuationSums1D where
  xFluctuationSum : FluctuationSum

noncomputable def xFluctuationSumExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : FluctuationSum :=
  {
    fluctuation_sum_u := (xLeftFluctuationExprs CL CR UL UR P).fluctuation_u + (xRightFluctuationExprs CL CR UL UR P).fluctuation_u
  }

noncomputable def fluctuationSums (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : FluctuationSums1D :=
  {
    xFluctuationSum := xFluctuationSumExprs CL CR UL UR P
  }

lemma two_wave_flux_jump (sL sR J F w1 w2 : Real) (gap : sR - sL ≠ 0)
    (h1 : w1 = (1 / 2 : Real) * J + ((1 / 2 : Real) * ((sL + sR) * J) - F) / (sR - sL))
    (h2 : w2 = (1 / 2 : Real) * J - ((1 / 2 : Real) * ((sL + sR) * J) - F) / (sR - sL)) :
    F = w1 * sL + w2 * sR := by
  subst h1 h2
  field_simp
  ring

lemma Rinv_sym_gap (a : Real) : (a - -a)⁻¹ = (1 / 2 : Real) * a⁻¹ := by
  rw [show a - -a = 2 * a by ring, mul_inv]
  ring

theorem xFluxConservative (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) (SpeedGapNondegenerate : (
      let x_L := CL.x
      let x_R := CR.x
      let u_L := UL.u
      let u_R := UR.u
      let alpha := P.alpha
      ((abs alpha) - -((abs alpha)) ≠ 0))) :    ((xFluxJumpExprs CL CR UL UR P).flux_jump_u = (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_u) := by 
    set sL := (xSpeedFamilyExprs CL CR UL UR P).speed1 with hsL
    set sR := (xSpeedFamilyExprs CL CR UL UR P).speed2 with hsR
    have gap : sR - sL ≠ 0 := by simpa only [hsL, hsR, xSpeedFamilyExprs]
      using SpeedGapNondegenerate
    have fluctuationSum : ∀ w1 w2 : ℝ,
      w1 * min sL 0 + w2 * min sR 0 + (w1 * max sL 0 + w2 * max sR 0)
      = w1 * sL + w2 * sR := by
      intro w1 w2
      linear_combination w1 * min_add_max sL 0 + w2 * min_add_max sR 0
    . calc (xFluxJumpExprs CL CR UL UR P).flux_jump_u
        = (xWaveFamilyExprs CL CR UL UR P).wave1.wave_u * sL + (xWaveFamilyExprs CL CR UL UR P).wave2.wave_u * sR :=
              two_wave_flux_jump sL sR (xStateJumpExprs UL UR).jump_u _ _ _ gap
                (by simp only [hsL, hsR, xWaveFamilyExprs, xSpeedFamilyExprs, xStateJumpExprs,
                      xFluxJumpExprs, xFluxExprs, div_eq_mul_inv, Rinv_sym_gap] <;> first | rfl | ring)
                (by simp only [hsL, hsR, xWaveFamilyExprs, xSpeedFamilyExprs, xStateJumpExprs,
                      xFluxJumpExprs, xFluxExprs, div_eq_mul_inv, Rinv_sym_gap] <;> first | rfl | ring)
      _ = (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_u :=
                  (fluctuationSum _ _).symm

end transient_heat_diffusion_1d_lax_friedrichs

namespace transient_heat_diffusion_1d_minmod

open transient_heat_diffusion_1d

structure Reconstruction where
  reconstruction_u : Real

structure Reconstruction1D where
  xReconstruction : Reconstruction

noncomputable def xLeftReconstructionExprs (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction :=
  let x_L := CL.x
  let x := C.x
  let x_R := CR.x
  let u_L := UL.u
  let u := U.u
  let u_R := UR.u
  let alpha := P.alpha
  {
    reconstruction_u := (f - ((1 / 2 : Real) * ((max 0 (min (f - f_L) (f_R - f))) + (min 0 (max (f - f_L) (f_R - f))))))
  }

noncomputable def xRightReconstructionExprs (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction :=
  let x_L := CL.x
  let x := C.x
  let x_R := CR.x
  let u_L := UL.u
  let u := U.u
  let u_R := UR.u
  let alpha := P.alpha
  {
    reconstruction_u := (f + ((1 / 2 : Real) * ((max 0 (min (f - f_L) (f_R - f))) + (min 0 (max (f - f_L) (f_R - f))))))
  }

noncomputable def leftReconstruction (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction1D :=
  {
    xReconstruction := xLeftReconstructionExprs CL C CR UL U UR P
  }

noncomputable def rightReconstruction (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction1D :=
  {
    xReconstruction := xRightReconstructionExprs CL C CR UL U UR P
  }

theorem xLeftReconstructionConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xLeftReconstructionExprs C C C U U U P).reconstruction_u) = U.u := by
  . simp [xLeftReconstructionExprs] <;> ring_nf <;> simp

theorem xRightReconstructionConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xRightReconstructionExprs C C C U U U P).reconstruction_u) = U.u := by
  . simp [xRightReconstructionExprs] <;> ring_nf <;> simp

theorem xLeftReconstructionLinearityPreservation (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (U : State) (P : Parameters) (D : Real) :
    let UL : State :=
      {
        u := U.u - D
      }
    let UR : State :=
      {
        u := U.u + D
      }
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_u) = U.u - ((1 / 2 : Real) * D) := by
  . simp [xLeftReconstructionExprs] <;> ring_nf <;> simp

theorem xRightReconstructionLinearityPreservation (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (U : State) (P : Parameters) (D : Real) :
    let UL : State :=
      {
        u := U.u - D
      }
    let UR : State :=
      {
        u := U.u + D
      }
    ((xRightReconstructionExprs CL C CR UL U UR P).reconstruction_u) = U.u + ((1 / 2 : Real) * D) := by
  . simp [xRightReconstructionExprs] <;> ring_nf <;> simp

theorem xReconstructionSymmetric (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) :
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_u) = ((xRightReconstructionExprs CR C CL UR U UL P).reconstruction_u) := by
  . simp [xLeftReconstructionExprs, xRightReconstructionExprs] <;>
    ring_nf <;>
    field_simp <;>
    simp only [min_def, max_def] <;>
    split_ifs <;> linarith

end transient_heat_diffusion_1d_minmod

namespace transient_heat_diffusion_1d_ssp_rk3

open transient_heat_diffusion_1d

structure Stage where
  stage_u : Real

structure StageFamily where
  stage1 : Stage
  stage2 : Stage
  stage3 : Stage

structure Stages1D where
  xStageFamily : StageFamily
  sourceStageFamily : StageFamily

noncomputable def xStageFamilyExprs (C0 : Coordinates) (C1 : Coordinates) (C2 : Coordinates)
    (U0 : State) (U1 : State) (U2 : State) (U0_RHS : State) (U1_RHS : State) (U2_RHS : State)
    (P : Parameters) (dt : Real) : StageFamily :=  let x0 := C0.x
  let x1 := C1.x
  let x2 := C2.x
  let u0 := U0.u
  let u1 := U1.u
  let u2 := U2.u
  let u0_rhs := U0_RHS.u
  let u1_rhs := U1_RHS.u
  let u2_rhs := U2_RHS.u
  let alpha := P.alpha
  {
    stage1 :=
      {
        stage_u := (f0 + (dt * f0_rhs))
      }
    stage2 :=
      {
        stage_u := (((3 / 4 : Real) * f0) + ((1 / 4 : Real) * (f1 + (dt * f1_rhs))))
      }
    stage3 :=
      {
        stage_u := (((1 / 3) * f0) + ((2 / 3) * (f2 + (dt * f2_rhs))))
      }
  }

noncomputable def sourceStageFamilyExprs (C0 : Coordinates) (C1 : Coordinates) (C2 : Coordinates)
    (U0 : State) (U1 : State) (U2 : State) (U0_RHS : State) (U1_RHS : State) (U2_RHS : State)
    (P : Parameters) (dt : Real) : StageFamily :=  let x0 := C0.x
  let x1 := C1.x
  let x2 := C2.x
  let u0 := U0.u
  let u1 := U1.u
  let u2 := U2.u
  let u0_rhs := U0_RHS.u
  let u1_rhs := U1_RHS.u
  let u2_rhs := U2_RHS.u
  let alpha := P.alpha
  {
    stage1 :=
      {
        stage_u := (f0 + (dt * f0_rhs))
      }
    stage2 :=
      {
        stage_u := (((3 / 4 : Real) * f0) + ((1 / 4 : Real) * (f1 + (dt * f1_rhs))))
      }
    stage3 :=
      {
        stage_u := (((1 / 3) * f0) + ((2 / 3) * (f2 + (dt * f2_rhs))))
      }
  }

noncomputable def stages (C0 : Coordinates) (C1 : Coordinates) (C2 : Coordinates) (U0 : State) (U1 : State) (U2 : State)
    (U0_RHS : State) (U1_RHS : State) (U2_RHS : State)
    (P : Parameters) (dt : Real) : Stages1D :=
  {
    xStageFamily := xStageFamilyExprs C0 C1 C2 U0 U1 U2 U0_RHS U1_RHS U2_RHS P dt
    sourceStageFamily := sourceStageFamilyExprs C0 C1 C2 U0 U1 U2 U0_RHS U1_RHS U2_RHS P dt
  }

theorem xStageConsistency (C : Coordinates) (U : State) (U_RHS : State) (P : Parameters) :
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).stage1.stage_u) = U.u ∧
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).stage2.stage_u) = U.u ∧
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).stage3.stage_u) = U.u := by
  constructor
  . simp [xStageFamilyExprs] <;> ring_nf
  constructor
  . simp [xStageFamilyExprs] <;> ring_nf
  . simp [xStageFamilyExprs] <;> ring_nf

theorem sourceStageConsistency (C : Coordinates) (U : State) (U_RHS : State) (P : Parameters) :
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).stage1.stage_u) = U.u ∧
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).stage2.stage_u) = U.u ∧
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P 0).stage3.stage_u) = U.u := by
  constructor
  . simp [sourceStageFamilyExprs] <;> ring_nf
  constructor
  . simp [sourceStageFamilyExprs] <;> ring_nf
  . simp [sourceStageFamilyExprs] <;> ring_nf

theorem xStageEquilibriumPreservation (C : Coordinates) (U : State) (P : Parameters) (dt : Real) :
    let U_RHS : State :=
      {
        u := 0
      }
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).stage1.stage_u) = U.u ∧
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).stage2.stage_u) = U.u ∧
    ((xStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).stage3.stage_u) = U.u := by
  constructor
  . simp [xStageFamilyExprs] <;> ring_nf
  constructor
  . simp [xStageFamilyExprs] <;> ring_nf
  . simp [xStageFamilyExprs] <;> ring_nf

theorem sourceStageEquilibriumPreservation (C : Coordinates) (U : State) (P : Parameters) (dt : Real) :
    let U_RHS : State :=
      {
        u := 0
      }
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).stage1.stage_u) = U.u ∧
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).stage2.stage_u) = U.u ∧
    ((sourceStageFamilyExprs C C C U U U U_RHS U_RHS U_RHS P dt).stage3.stage_u) = U.u := by
  constructor
  . simp [sourceStageFamilyExprs] <;> ring_nf
  constructor
  . simp [sourceStageFamilyExprs] <;> ring_nf
  . simp [sourceStageFamilyExprs] <;> ring_nf

end transient_heat_diffusion_1d_ssp_rk3

namespace transient_heat_diffusion_1d_centered_diffusion

open transient_heat_diffusion_1d

structure InterfaceState where
  interface_u : Real

structure InterfaceState1D where
  xInterfaceState : InterfaceState

noncomputable def xInterfaceStateExprs (C_Lx : Coordinates) (C_Rx : Coordinates)
    (U_Lx : State) (U_Rx : State) (P : Parameters) : InterfaceState :=
  let x_Lx := C_Lx.x
  let x_Rx := C_Rx.x
  let u_Lx := U_Lx.u
  let u_Rx := U_Rx.u
  let alpha := P.alpha
  {
    interface_u := ((1 / 2 : Real) * (f_Lx + f_Rx))
  }

noncomputable def interfaceState (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : InterfaceState1D :=
  {
    xInterfaceState := xInterfaceStateExprs CL CR UL UR P
  }

theorem xInterfaceStateConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xInterfaceStateExprs C C U U P).interface_u) = U.u := by
  . simp [xInterfaceStateExprs] <;> (ring_nf)

theorem xInterfaceStateSymmetric (C_Lx : Coordinates) (C_Rx : Coordinates)
    (U_Lx : State) (U_Rx : State) (P : Parameters) :
    ((xInterfaceStateExprs C_Lx C_Rx U_Lx U_Rx P).interface_u) = ((xInterfaceStateExprs C_Rx C_Lx U_Rx U_Lx P).interface_u) := by
  . simp [xInterfaceStateExprs] <;> (ring_nf)

structure InterfaceGradient where
  interface_u_x : Real

structure InterfaceGradients1D where
  xInterfaceGradient : InterfaceGradient

noncomputable def xInterfaceGradientExprs (C_Lx : Coordinates) (C_Rx : Coordinates)
    (U_Lx: State) (U_Rx : State) (P : Parameters) : InterfaceGradient :=
  let x_Lx := C_Lx.x
  let x_Rx := C_Rx.x
  let u_Lx := U_Lx.u
  let u_Rx := U_Rx.u
  let alpha := P.alpha
  {
    interface_u_x := ((f_Rx - f_Lx) / (x_Rx - x_Lx))
  }

theorem xInterfaceGradientConsistency (C_Lx : Coordinates) (C_Rx : Coordinates)
    (Ux: State) (P : Parameters) :
    ((xInterfaceGradientExprs C_Lx C_Rx Ux Ux P).interface_u_x) = 0 := by
  . simp [xInterfaceGradientExprs] <;> ring_nf <;> field_simp

theorem xInterfaceGradientAntisymmetric (C_Lx : Coordinates) (C_Rx : Coordinates)
    (U_Lx : State) (U_Rx : State) (P : Parameters) :
    ((xInterfaceGradientExprs C_Lx C_Rx U_Lx U_Rx P).interface_u_x) = -((xInterfaceGradientExprs C_Lx C_Rx U_Rx U_Lx
      P).interface_u_x) := by
  . simp [xInterfaceGradientExprs] <;> (ring_nf)

end transient_heat_diffusion_1d_centered_diffusion