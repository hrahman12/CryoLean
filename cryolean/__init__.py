"""CryoLean: local, research-grounded multiphysics compatibility verifier for cryogenic equipment.

Pipeline: experiment -> requirements -> Lean 4 verdict (trusted) -> Z3 suggestions (each re-checked by Lean).
Entry point for desktop frontends: ``cryolean.bridge.CryoLeanAPI``.
"""
__version__ = "2.0.0"
