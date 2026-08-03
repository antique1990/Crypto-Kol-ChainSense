"""Derivatives signal capabilities (7 caps) — all mocked (no funding/OI/options data yet)."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

def _mock(n, bias='neutral'):
    return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n), bias=bias, confidence=0.0)

@register('cap_031_funding_extreme_neg', 'derivatives_signal', 'long', 0.65, impl='mock', na_reason='need funding')
def funding_neg(f): return _mock(len(f), 'long')

@register('cap_032_funding_extreme_pos', 'derivatives_signal', 'short', 0.6, impl='mock', na_reason='need funding')
def funding_pos(f): return _mock(len(f), 'short')

@register('cap_033_oi_climb', 'derivatives_signal', 'neutral', 0.5, impl='mock', na_reason='need OI')
def oi_climb(f): return _mock(len(f))

@register('cap_034_liquidation_cluster', 'derivatives_signal', 'neutral', 0.55, impl='mock', na_reason='need heatmap')
def liq_cluster(f): return _mock(len(f))

@register('cap_059_funding_divergence', 'derivatives_signal', 'long', 0.55, impl='mock', na_reason='need funding')
def funding_div(f): return _mock(len(f), 'long')

@register('cap_060_basis_blowout', 'derivatives_signal', 'short', 0.55, impl='mock', na_reason='need basis')
def basis_blowout(f): return _mock(len(f), 'short')

@register('cap_061_options_skew', 'derivatives_signal', 'long', 0.5, impl='mock', na_reason='need options skew')
def options_skew(f): return _mock(len(f), 'long')
