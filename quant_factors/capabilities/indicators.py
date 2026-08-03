"""Indicator rule capabilities (9 caps)."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

@register('cap_015_rsi_bullish_divergence', 'indicator_rule', 'long', 0.6)
def rsi_bullish_div(f):
    """Price lower-low but RSI higher-low over 20 bars (simplified)."""
    low20 = f['low_20d']
    price_ll = (f['close'] < f['close'].shift(20)) & (f['close'] < low20.shift(1))
    rsi_hl = f['rsi14'] > f['rsi14'].shift(20)
    trig = price_ll & rsi_hl
    score = np.where(trig, 0.7, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.6)

@register('cap_016_rsi_bearish_divergence', 'indicator_rule', 'short', 0.6)
def rsi_bearish_div(f):
    high20 = f['high_20d']
    price_hh = (f['close'] > f['close'].shift(20)) & (f['close'] > high20.shift(1))
    rsi_lh = f['rsi14'] < f['rsi14'].shift(20)
    trig = price_hh & rsi_lh
    score = np.where(trig, -0.7, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.6)

@register('cap_017_rsi_oversold_bounce', 'indicator_rule', 'long', 0.5)
def rsi_oversold_bounce(f):
    """RSI cross back above 30 from below."""
    trig = (f['rsi14'] > 30) & (f['rsi14_prev'] <= 30)
    score = np.where(trig, 0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.5)

@register('cap_018_ma_golden_cross', 'indicator_rule', 'long', 0.55)
def golden_cross(f):
    """50MA crosses above 200MA today."""
    trig = (f['ma50'] > f['ma200']) & (f['ma50'].shift(1) <= f['ma200'].shift(1))
    score = np.where(trig, 0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.55)

@register('cap_019_ma_death_cross', 'indicator_rule', 'short', 0.55)
def death_cross(f):
    trig = (f['ma50'] < f['ma200']) & (f['ma50'].shift(1) >= f['ma200'].shift(1))
    score = np.where(trig, -0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.55)

@register('cap_020_macd_histogram_cross', 'indicator_rule', 'neutral', 0.5)
def macd_hist_cross(f):
    """MACD histogram zero cross (both directions)."""
    up_cross = (f['macd_hist'] > 0) & (f['macd_hist'].shift(1) <= 0)
    dn_cross = (f['macd_hist'] < 0) & (f['macd_hist'].shift(1) >= 0)
    trig = up_cross | dn_cross
    score = np.where(up_cross, 0.5, np.where(dn_cross, -0.5, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.5)

@register('cap_021_bb_squeeze_breakout', 'indicator_rule', 'neutral', 0.55)
def bb_squeeze_breakout(f):
    """BB narrow (width < 20pctile) followed by price outside bands."""
    squeeze = (f['bb_width'].shift(1) < f['bb_width_20pctile'].shift(1)).fillna(False)
    breakout_up = squeeze & (f['close'] > f['bb_upper'])
    breakout_dn = squeeze & (f['close'] < f['bb_lower'])
    trig = breakout_up | breakout_dn
    score = np.where(breakout_up, 0.6, np.where(breakout_dn, -0.6, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

@register('cap_022_fib_618_support', 'indicator_rule', 'long', 0.6)
def fib_618_support(f):
    """Close within ±2% of fib 0.618 level and bounces (+ve day)."""
    near = (f['close'] - f['fib_618']).abs() / f['close'] < 0.02
    trig = near & (f['is_green'] == 1) & (f['close'].shift(1) <= f['fib_618'])
    score = np.where(trig, 0.55, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.6)

@register('cap_069_moving_average_reclaim', 'indicator_rule', 'long', 0.6)
def ma_reclaim(f):
    """Close reclaims MA200 after 3+ days below."""
    trig = (f['close'] > f['ma200']) & (f['days_below_ma200'].shift(1) >= 3)
    score = np.where(trig, 0.65, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.6)
