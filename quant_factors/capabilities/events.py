"""Event reaction capabilities (2 caps) — mocked (no FOMC/ETF calendar in pipeline yet)."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

def _mock(n, bias='neutral'):
    return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n), bias=bias, confidence=0.0)

@register('cap_039_fomc_risk_off', 'event_reaction', 'neutral', 0.6, impl='mock', na_reason='need FOMC calendar')
def fomc_risk_off(f): return _mock(len(f))

@register('cap_040_etf_flows_proxy', 'event_reaction', 'long', 0.55, impl='mock', na_reason='need ETF flow series')
def etf_flows(f): return _mock(len(f), 'long')
