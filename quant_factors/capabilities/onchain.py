"""On-chain signal capabilities (5 caps) — mocked (no on-chain data pipeline)."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

def _mock(n, bias='neutral'):
    return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n), bias=bias, confidence=0.0)

@register('cap_035_exchange_inflow', 'onchain_signal', 'short', 0.55, impl='mock', na_reason='need exchange flows')
def exchange_inflow(f): return _mock(len(f), 'short')

@register('cap_036_lth_holding', 'onchain_signal', 'long', 0.55, impl='mock', na_reason='need LTH supply')
def lth_holding(f): return _mock(len(f), 'long')

@register('cap_066_stablecoin_supply', 'onchain_signal', 'long', 0.5, impl='mock', na_reason='need stablecoin mcap')
def stablecoin_supply(f): return _mock(len(f), 'long')

@register('cap_067_nvt_extreme', 'onchain_signal', 'neutral', 0.5, impl='mock', na_reason='need NVT')
def nvt_extreme(f): return _mock(len(f))

@register('cap_068_mvrv_zscore', 'onchain_signal', 'neutral', 0.6, impl='mock', na_reason='need MVRV Z-score')
def mvrv_zscore(f): return _mock(len(f))
