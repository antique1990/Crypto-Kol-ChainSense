"""Macro correlation capabilities (7 caps)."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

@register('cap_027_dxy_inverse_btc', 'macro_correlation', 'long', 0.5)
def dxy_inverse(f):
    """DXY rolling down → BTC bullish tilt."""
    trig = f.get('dxy_ret_20d', pd.Series(0, index=f.index)) < -0.01
    score = np.where(trig, 0.4, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.5)

@register('cap_028_spx_risk_on', 'macro_correlation', 'long', 0.5)
def spx_risk_on(f):
    trig = f.get('spx_ret_20d', pd.Series(0, index=f.index)) > 0.02
    score = np.where(trig, 0.4, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.5)

@register('cap_029_yields_liquidity', 'macro_correlation', 'long', 0.5)
def yields_liquidity(f):
    trig = f.get('y_ret_20d', pd.Series(0, index=f.index)) < -0.02
    score = np.where(trig, 0.4, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.5)

@register('cap_030_gold_safe_haven', 'macro_correlation', 'long', 0.45)
def gold_safe_haven(f):
    """Gold rallying + BTC holding → decoupling to safe haven narrative."""
    trig = f.get('gold_ret_20d', pd.Series(0, index=f.index)) > 0.05
    score = np.where(trig, 0.3, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.45)

@register('cap_062_m2_growth', 'macro_correlation', 'long', 0.5, impl='mock', na_reason='need global M2 series')
def m2_growth(f):
    n = len(f) if hasattr(f,'__len__') else 1
    return CapabilityOutput(triggered=np.zeros(n, bool), score=np.zeros(n), bias='long', confidence=0.0)

@register('cap_063_ism_pmi', 'macro_correlation', 'long', 0.5, impl='mock', na_reason='need ISM PMI series')
def ism_pmi(f):
    n = len(f) if hasattr(f,'__len__') else 1
    return CapabilityOutput(triggered=np.zeros(n, bool), score=np.zeros(n), bias='long', confidence=0.0)

@register('cap_064_credit_spreads', 'macro_correlation', 'short', 0.55, impl='mock', na_reason='need HY spread')
def credit_spreads(f):
    n = len(f) if hasattr(f,'__len__') else 1
    return CapabilityOutput(triggered=np.zeros(n, bool), score=np.zeros(n), bias='short', confidence=0.0)
