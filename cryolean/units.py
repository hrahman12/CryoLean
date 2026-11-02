"""Exact unit system.

Every unit is an exact rational scale to SI coherent units plus a dimension
vector over the seven SI base dimensions.  Conversion uses `fractions.Fraction`,
so nothing is rounded on the way to the Lean checker.

Conventions (documented in VERIFICATION_SCOPE.md):
* temperatures in °C are affine and are converted to kelvin *before* entering
  the catalog (the evidence record keeps the printed value);
* angles are dimensionless numbers expressed in degrees ("deg", "mdeg");
* oersted is converted to tesla with 1 Oe ↔ 1e-4 T (B = µ0·H in vacuum);
* logarithmic units (dB, dBm) and fractional exponents (V/√Hz) are not
  representable — such requirements are stored as linear quantities over a
  stated bandwidth or reported as unsupported.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

DIM_KEYS = ("K", "m", "kg", "s", "A", "mol", "cd")


@dataclass(frozen=True)
class Unit:
    symbol: str
    scale: Fraction            # SI value = value * scale
    dim: tuple[int, ...]       # exponents in DIM_KEYS order
    description: str = ""

    def dim_dict(self) -> dict[str, int]:
        return {k: v for k, v in zip(DIM_KEYS, self.dim) if v}


def _d(K=0, m=0, kg=0, s=0, A=0, mol=0, cd=0) -> tuple[int, ...]:
    return (K, m, kg, s, A, mol, cd)


ONE = _d()
KELVIN = _d(K=1)
METRE = _d(m=1)
KILOGRAM = _d(kg=1)
SECOND = _d(s=1)
AMPERE = _d(A=1)
WATT = _d(kg=1, m=2, s=-3)
JOULE = _d(kg=1, m=2, s=-2)
TESLA = _d(kg=1, s=-2, A=-1)
PASCAL = _d(kg=1, m=-1, s=-2)
HERTZ = _d(s=-1)
VOLT = _d(kg=1, m=2, s=-3, A=-1)
OHM = _d(kg=1, m=2, s=-3, A=-2)
K_PER_S = _d(K=1, s=-1)
T_PER_S = _d(kg=1, s=-3, A=-1)
CUBIC_METRE = _d(m=3)
W_PER_M_K = _d(kg=1, m=1, s=-3, K=-1)
K_PER_W = _d(K=1, kg=-1, m=-2, s=3)
PA_M3_PER_S = _d(kg=1, m=2, s=-3)       # leak rate, same dimension as W
M3_PER_S = _d(m=3, s=-1)

F = Fraction
UNITS: dict[str, Unit] = {}


def _u(symbol, scale, dim, description=""):
    UNITS[symbol] = Unit(symbol, Fraction(scale), dim, description)


# temperature
_u("K", 1, KELVIN, "kelvin"); _u("mK", F(1, 1000), KELVIN, "millikelvin"); _u("uK", F(1, 10**6), KELVIN, "microkelvin")
# length
_u("m", 1, METRE, "metre"); _u("mm", F(1, 1000), METRE, "millimetre"); _u("um", F(1, 10**6), METRE, "micrometre")
_u("nm", F(1, 10**9), METRE, "nanometre"); _u("cm", F(1, 100), METRE, "centimetre"); _u("inch", F(254, 10000), METRE, "inch (exact)")
# mass
_u("kg", 1, KILOGRAM, "kilogram"); _u("g", F(1, 1000), KILOGRAM, "gram"); _u("mg", F(1, 10**6), KILOGRAM, "milligram")
_u("ug", F(1, 10**9), KILOGRAM, "microgram")
# time
_u("s", 1, SECOND, "second"); _u("ms", F(1, 1000), SECOND, "millisecond"); _u("min", 60, SECOND, "minute"); _u("h", 3600, SECOND, "hour"); _u("d", 86400, SECOND, "day")
# current
_u("A", 1, AMPERE, "ampere"); _u("mA", F(1, 1000), AMPERE); _u("uA", F(1, 10**6), AMPERE); _u("nA", F(1, 10**9), AMPERE)
_u("pA", F(1, 10**12), AMPERE, "picoampere")
# power / energy
_u("W", 1, WATT, "watt"); _u("mW", F(1, 1000), WATT); _u("uW", F(1, 10**6), WATT); _u("nW", F(1, 10**9), WATT, "nanowatt")
_u("J", 1, JOULE, "joule")
# field
_u("T", 1, TESLA, "tesla"); _u("mT", F(1, 1000), TESLA, "millitesla"); _u("uT", F(1, 10**6), TESLA)
_u("Oe", F(1, 10**4), TESLA, "oersted, converted with B = mu0*H (1 Oe <-> 1e-4 T)")
_u("T_per_s", 1, T_PER_S); _u("mT_per_s", F(1, 1000), T_PER_S); _u("uT_per_s", F(1, 10**6), T_PER_S, "microtesla per second")
_u("Oe_per_s", F(1, 10**4), T_PER_S, "oersted per second (1e-4 T/s)"); _u("T_per_min", F(1, 60), T_PER_S)
# pressure
_u("Pa", 1, PASCAL, "pascal"); _u("uPa", F(1, 10**6), PASCAL, "micropascal"); _u("mbar", 100, PASCAL, "millibar")
_u("Torr", F(101325, 760), PASCAL, "torr (exact: 101325/760 Pa)")
# frequency
_u("Hz", 1, HERTZ); _u("kHz", 1000, HERTZ, "kilohertz"); _u("MHz", 10**6, HERTZ); _u("GHz", 10**9, HERTZ)
# electrical
_u("V", 1, VOLT); _u("mV", F(1, 1000), VOLT); _u("uV", F(1, 10**6), VOLT); _u("nV", F(1, 10**9), VOLT)
_u("Ohm", 1, OHM); _u("kOhm", 1000, OHM); _u("MOhm", 10**6, OHM); _u("mOhm", F(1, 1000), OHM); _u("uOhm", F(1, 10**6), OHM, "micro-ohm")
# rates
_u("K_per_s", 1, K_PER_S); _u("K_per_min", F(1, 60), K_PER_S); _u("mK_per_min", F(1, 60000), K_PER_S, "millikelvin per minute")
# dimensionless
_u("count", 1, ONE, "dimensionless count"); _u("1", 1, ONE, "dimensionless"); _u("percent", F(1, 100), ONE)
_u("ppm", F(1, 10**6), ONE, "parts per million"); _u("deg", 1, ONE, "angle in degrees (convention)"); _u("mdeg", F(1, 1000), ONE, "millidegree")
_u("NA", 1, ONE, "numerical aperture (dimensionless)"); _u("f_number", 1, ONE, "f-number (dimensionless)")
# volume / flow / transport
_u("m3", 1, CUBIC_METRE); _u("L", F(1, 1000), CUBIC_METRE, "litre")
_u("m3_per_s", 1, M3_PER_S); _u("L_per_min", F(1, 60000), M3_PER_S, "litre per minute")
_u("Pa_m3_per_s", 1, PA_M3_PER_S, "leak rate"); _u("mbar_L_per_s", F(1, 10), PA_M3_PER_S, "leak rate (1 mbar L/s = 0.1 Pa m3/s)")
_u("W_per_m_K", 1, W_PER_M_K, "thermal conductivity"); _u("K_per_W", 1, K_PER_W, "thermal resistance")


class UnitError(ValueError):
    pass


def unit(symbol: str) -> Unit:
    try:
        return UNITS[symbol]
    except KeyError:
        raise UnitError(f"unknown unit '{symbol}' (register it in cryolean/units.py)")


def to_si(value, symbol: str) -> Fraction:
    """Exact SI value. `value` may be int, Fraction or a decimal string; floats are refused."""
    if isinstance(value, float):
        raise UnitError("floating-point values are not accepted; pass an int, a Fraction or a decimal string")
    if isinstance(value, bool):
        raise UnitError("boolean is not a quantity")
    return Fraction(value) * unit(symbol).scale


def lean_quantity(value, symbol: str) -> dict:
    """{"num", "den", "dim"} document for the Lean checker."""
    si = to_si(value, symbol)
    return {"num": si.numerator, "den": si.denominator, "dim": unit(symbol).dim_dict()}


def from_lean(q: dict) -> Fraction:
    return Fraction(int(q["num"]), int(q["den"]))


def dims_of(q: dict) -> tuple[int, ...]:
    d = q.get("dim", {})
    return tuple(int(d.get(k, 0)) for k in DIM_KEYS)


_NAMED = {ONE: "", KELVIN: "K", METRE: "m", KILOGRAM: "kg", SECOND: "s", AMPERE: "A", WATT: "W", JOULE: "J",
          TESLA: "T", PASCAL: "Pa", HERTZ: "Hz", VOLT: "V", OHM: "Ω", K_PER_S: "K/s", T_PER_S: "T/s",
          CUBIC_METRE: "m³", W_PER_M_K: "W/(m·K)", K_PER_W: "K/W", M3_PER_S: "m³/s"}
_PREFIX = [(9, "G"), (6, "M"), (3, "k"), (0, ""), (-3, "m"), (-6, "µ"), (-9, "n"), (-12, "p")]


def display(si: Fraction, dim: tuple[int, ...], digits: int = 4) -> str:
    """Readable rendering with an SI prefix, e.g. 1.8 K, 12 µW, 9 T."""
    name = _NAMED.get(tuple(dim))
    if name is None:
        name = " ".join(f"{k}^{v}" if v != 1 else k for k, v in zip(DIM_KEYS, dim) if v)
        return f"{_fmt(si)} [{name}]"
    if name in ("", "kg", "K/s", "T/s", "W/(m·K)", "K/W") or si == 0:
        return f"{_fmt(si)} {name}".strip()
    for e, p in _PREFIX:
        if abs(si) >= Fraction(10) ** e:
            return f"{_fmt(si / Fraction(10) ** e)} {p}{name}"
    e, p = _PREFIX[-1]
    return f"{_fmt(si / Fraction(10) ** e)} {p}{name}"


def _fmt(x: Fraction) -> str:
    if x.denominator == 1:
        return str(x.numerator)
    s = f"{float(x):.6g}"
    return s


def display_catalog(value, symbol: str) -> str:
    u = unit(symbol)
    return display(to_si(value, symbol), u.dim)


def celsius_to_mK(celsius: str | int | Fraction) -> int:
    """Exact °C → mK for catalog entry; refuses inputs that do not give an integer mK."""
    mk = (Fraction(celsius) + Fraction(27315, 100)) * 1000
    if mk.denominator != 1:
        raise UnitError(f"{celsius} °C is not an integer number of millikelvin")
    return int(mk)
