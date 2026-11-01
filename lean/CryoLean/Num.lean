import CryoLean.Model
/-!
# Exact rational arithmetic for physical quantities

`Q.le` is the order on rationals written by cross-multiplication; it is the
order used by both the checker and the specification.  The lemmas below show
it is a property of the represented *number*, not of the chosen representation
(scaling numerator and denominator by the same positive factor changes nothing).
-/

namespace CryoLean

/-- `a ≤ b` for rationals with positive denominators. -/
def Q.le (a b : Q) : Prop := a.num * (b.den : Int) ≤ b.num * (a.den : Int)

instance (a b : Q) : Decidable (Q.le a b) := by unfold Q.le; infer_instance

def Q.add (a b : Q) : Q := ⟨a.num * b.den + b.num * a.den, a.den * b.den⟩
def Q.mul (a b : Q) : Q := ⟨a.num * b.num, a.den * b.den⟩
def Q.neg (a : Q) : Q := ⟨-a.num, a.den⟩
def Q.sub (a b : Q) : Q := Q.add a (Q.neg b)
def Q.ofNat (n : Nat) : Q := ⟨n, 1⟩

/-- Scaling a representation by a positive factor. -/
def Q.scale (a : Q) (k : Nat) : Q := ⟨a.num * k, a.den * k⟩

def Quantity.add (x y : Quantity) : Quantity := ⟨Q.add x.val y.val, x.dim⟩
def Quantity.sub (x y : Quantity) : Quantity := ⟨Q.sub x.val y.val, x.dim⟩
def Quantity.mul (x y : Quantity) : Quantity := ⟨Q.mul x.val y.val, Dim.mul x.dim y.dim⟩
def Quantity.neg (x : Quantity) : Quantity := ⟨Q.neg x.val, x.dim⟩

/-- The comparison does not depend on the representation of the left operand. -/
theorem Q.le_scale_left (a b : Q) (k : Nat) (hk : 0 < k) :
    Q.le (a.scale k) b ↔ Q.le a b := by
  unfold Q.le Q.scale
  simp only [Int.natCast_mul]
  have hk' : (0 : Int) < (k : Int) := by omega
  constructor
  · intro h
    have h2 : (a.num * (b.den : Int)) * (k : Int) ≤ (b.num * (a.den : Int)) * (k : Int) := by
      grind
    exact Int.le_of_mul_le_mul_right h2 hk'
  · intro h
    have := Int.mul_le_mul_of_nonneg_right h (Int.le_of_lt hk')
    grind

/-- The comparison does not depend on the representation of the right operand. -/
theorem Q.le_scale_right (a b : Q) (k : Nat) (hk : 0 < k) :
    Q.le a (b.scale k) ↔ Q.le a b := by
  unfold Q.le Q.scale
  simp only [Int.natCast_mul]
  have hk' : (0 : Int) < (k : Int) := by omega
  constructor
  · intro h
    have h2 : (a.num * (b.den : Int)) * (k : Int) ≤ (b.num * (a.den : Int)) * (k : Int) := by
      grind
    exact Int.le_of_mul_le_mul_right h2 hk'
  · intro h
    have := Int.mul_le_mul_of_nonneg_right h (Int.le_of_lt hk')
    grind

theorem Q.le_refl (a : Q) : Q.le a a := by
  unfold Q.le; exact Int.le_refl _

/-- Products of positive denominators stay positive, so evaluated quantities stay well formed. -/
theorem Q.add_den_pos {a b : Q} (ha : 0 < a.den) (hb : 0 < b.den) : 0 < (Q.add a b).den := by
  simp [Q.add]; exact Nat.mul_pos ha hb

theorem Q.mul_den_pos {a b : Q} (ha : 0 < a.den) (hb : 0 < b.den) : 0 < (Q.mul a b).den := by
  simp [Q.mul]; exact Nat.mul_pos ha hb

end CryoLean
