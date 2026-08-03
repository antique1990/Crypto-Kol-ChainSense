"""Cycle/time capabilities (2 caps)."""
import numpy as np
import pandas as pd
from datetime import datetime
from .registry import register, CapabilityOutput

# BTC halvings (approximate):
HALVINGS = [
    pd.Timestamp('2012-11-28'),
    pd.Timestamp('2016-07-09'),
    pd.Timestamp('2020-05-11'),
    pd.Timestamp('2024-04-19'),
    pd.Timestamp('2028-04'),  # projected
]

def _days_since_last_halving(dates):
    """For each date, compute days since most-recent halving."""
    result = []
    for d in dates:
        last = None
        for h in HALVINGS:
            if h <= d:
                last = h
        if last is None:
            result.append(np.nan)
        else:
            result.append((d - last).days)
    return pd.Series(result, index=dates)

@register('cap_037_halving_cycle', 'cycle_time', 'neutral', 0.55)
def halving_cycle(f):
    """Days since halving → phase. 0-180: accumulation (neutral), 180-540: parabolic (long bias), 540-720: distribution (short), 720+: bear (short)."""
    if hasattr(f, 'index') and isinstance(f.index, pd.DatetimeIndex):
        dates = f.index
    elif hasattr(f, 'name') and isinstance(f.name, pd.Timestamp):
        dates = pd.DatetimeIndex([f.name])
    else:
        dates = None

    if dates is None:
        n = len(f) if hasattr(f,'__len__') else 1
        return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n), bias='neutral', confidence=0.0)

    days = _days_since_last_halving(dates)
    score = pd.Series(0.0, index=dates)
    score[(days >= 180) & (days < 540)] = 0.6   # parabolic long
    score[(days >= 540) & (days < 720)] = -0.5  # distribution short
    score[days >= 720] = -0.3                    # bear short
    trig = score != 0
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

@register('cap_038_4year_cycle', 'cycle_time', 'neutral', 0.5)
def four_year_cycle(f):
    """Same as halving but framed as 4-year. Use same phase math with coarser buckets."""
    if hasattr(f, 'index') and isinstance(f.index, pd.DatetimeIndex):
        dates = f.index
    else:
        n = len(f) if hasattr(f,'__len__') else 1
        return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n), bias='neutral', confidence=0.0)

    days = _days_since_last_halving(dates)
    # Bullish in months 6-18 post halving; bearish 18-36
    score = pd.Series(0.0, index=dates)
    score[(days >= 180) & (days < 540)] = 0.5
    score[(days >= 540) & (days < 1080)] = -0.4
    trig = score != 0
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.5)
