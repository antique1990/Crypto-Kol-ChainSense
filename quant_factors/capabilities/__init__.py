"""Capability registry: each capability = a function taking a features row/panel
and returning a score dict {triggered, score, bias, confidence, notes}."""
from .registry import CAP_REGISTRY, register, evaluate_all, CapabilityOutput
from . import regime, indicators, structural, patterns, macro, cycle, risk, derivatives, onchain, events, emerged

__all__ = ['CAP_REGISTRY','register','evaluate_all','CapabilityOutput']
