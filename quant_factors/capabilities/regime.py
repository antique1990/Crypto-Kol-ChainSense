"""Regime classifiers (5 caps)."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

@register('cap_044_regime_trending_up', 'regime_classifier', 'long', 0.7)
def regime_trending_up(f):
    """Strong uptrend: price > MA200 & MA50 > MA200 & ADX > 25"""
    trig = (f['close'] > f['ma200']) & (f['ma50'] > f['ma200']) & (f['adx14'] > 25)
    score = np.where(trig, 1.0, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.7, notes='price>MA200 & golden & adx>25')

@register('cap_045_regime_trending_down', 'regime_classifier', 'short', 0.7)
def regime_trending_down(f):
    trig = (f['close'] < f['ma200']) & (f['ma50'] < f['ma200']) & (f['adx14'] > 25)
    score = np.where(trig, -1.0, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.7)

@register('cap_046_regime_ranging', 'regime_classifier', 'neutral', 0.6)
def regime_ranging(f):
    """ADX < 20 and BB width below 50th percentile — chop."""
    trig = (f['adx14'] < 20) & (f['bb_width'] < f['bb_width_20pctile']).fillna(False)
    # In ranging, bias depends on position in range
    # Score = -1 near top, +1 near bottom
    range_pos = ((f['close'] - f['low_20d']) / (f['high_20d'] - f['low_20d']).replace(0, np.nan)).clip(0,1).fillna(0.5)
    score = np.where(trig, (0.5 - range_pos) * 2, 0.0)  # -1 at top, +1 at bottom
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.6)

@register('cap_047_regime_volatile', 'regime_classifier', 'neutral', 0.6)
def regime_high_vol(f):
    """RV30 above 80th percentile of its 200-day history."""
    trig = f['rv30_pctile'].fillna(0) > 0.8
    # High vol = bias to cautious/no-action; signed score = 0 but triggered = True
    return CapabilityOutput(triggered=trig, score=np.zeros(len(f)) if isinstance(f, pd.DataFrame) else 0,
                            bias='neutral', confidence=0.6)

@register('cap_070_parabolic_exhaustion', 'regime_classifier', 'short', 0.6)
def parabolic_exhaustion(f):
    """Exponential acceleration: 7d return >25% AND RSI>80."""
    trig = (f['ret_7d'] > 0.25) & (f['rsi14'] > 80)
    score = np.where(trig, -1.0, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.6)
