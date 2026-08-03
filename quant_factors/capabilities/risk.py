"""Risk rule capabilities (3 caps). These are meta-rules — they act as filters rather than directional signals."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

@register('cap_041_dont_catch_falling_knives', 'risk_rule', 'neutral', 0.7)
def dont_catch_knives(f):
    """4h sharp drop (proxy: daily <-8%) + no reversal signal → no-action filter."""
    waterfall = f['ret_1d'] < -0.08
    no_reversal = f['is_green'] == 0
    trig = waterfall & no_reversal
    # Signed: strong short (momentum continuation expectation)
    score = np.where(trig, -0.55, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.7)

@register('cap_042_position_sizing', 'risk_rule', 'neutral', 1.0, impl='mock', na_reason='meta rule, not a signal')
def position_sizing(f):
    n = len(f) if hasattr(f,'__len__') else 1
    return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n), bias='neutral', confidence=0.0)

@register('cap_043_cut_losses_early', 'risk_rule', 'neutral', 1.0, impl='mock', na_reason='meta rule, not a signal')
def cut_losses(f):
    n = len(f) if hasattr(f,'__len__') else 1
    return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n), bias='neutral', confidence=0.0)
