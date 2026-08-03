"""Pattern setups (22 caps — mostly rule approximations of visual patterns)."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

def _blank(n): return CapabilityOutput(triggered=np.zeros(n, bool), score=np.zeros(n), bias='neutral', confidence=0.0)

@register('cap_001_falling_wedge_breakout', 'pattern_setup', 'long', 0.65, impl='approx')
def falling_wedge(f):
    """Approx: 30-day decline with decreasing volatility + today breakout above 5-day high."""
    ret30_neg = f['ret_30d'] < -0.05
    vol_compressing = f['rv30'] < f['rv30'].shift(20) * 0.9
    breakout = f['close'] > f['high'].rolling(5, min_periods=1).max().shift(1)
    trig = ret30_neg & vol_compressing & breakout
    score = np.where(trig, 0.65, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.65)

@register('cap_002_rising_wedge_breakdown', 'pattern_setup', 'short', 0.6, impl='approx')
def rising_wedge(f):
    ret30_pos = f['ret_30d'] > 0.05
    vol_compressing = f['rv30'] < f['rv30'].shift(20) * 0.9
    breakdown = f['close'] < f['low'].rolling(5, min_periods=1).min().shift(1)
    trig = ret30_pos & vol_compressing & breakdown
    score = np.where(trig, -0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.6)

@register('cap_003_bull_flag', 'pattern_setup', 'long', 0.7, impl='approx')
def bull_flag(f):
    """Sharp up run (5d +10%+) then consolidation then continuation."""
    flagpole = f['ret_5d'].shift(5) > 0.10
    consolidation = (f['ret_5d'].abs() < 0.03) & (f['adx14'] < 20)
    breakout = f['close'] > f['high'].rolling(3, min_periods=1).max().shift(1)
    trig = flagpole & consolidation.shift(1) & breakout
    score = np.where(trig, 0.7, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.7)

@register('cap_004_bear_flag', 'pattern_setup', 'short', 0.7, impl='approx')
def bear_flag(f):
    flagpole = f['ret_5d'].shift(5) < -0.10
    consolidation = (f['ret_5d'].abs() < 0.03) & (f['adx14'] < 20)
    breakdown = f['close'] < f['low'].rolling(3, min_periods=1).min().shift(1)
    trig = flagpole & consolidation.shift(1) & breakdown
    score = np.where(trig, -0.7, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.7)

@register('cap_005_head_shoulders_top', 'pattern_setup', 'short', 0.7, impl='approx')
def head_shoulders_top(f):
    """Approx: 3 peaks in 60d with middle highest, then break neckline."""
    # Very rough: close breaks below recent (30d) low during period where 60d high is older
    high60 = f['high'].rolling(60, min_periods=20).max()
    high_age = 60 - f['high'].rolling(60, min_periods=20).apply(lambda x: x.argmax(), raw=True)
    trig = (f['close'] < f['low_20d']) & (high_age > 10) & (f['rsi14'] < 50)
    score = np.where(trig, -0.5, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.6)

@register('cap_006_inverse_head_shoulders', 'pattern_setup', 'long', 0.7, impl='approx')
def inverse_hs(f):
    low60 = f['low'].rolling(60, min_periods=20).min()
    low_age = 60 - f['low'].rolling(60, min_periods=20).apply(lambda x: x.argmin(), raw=True)
    trig = (f['close'] > f['high_20d']) & (low_age > 10) & (f['rsi14'] > 50)
    score = np.where(trig, 0.5, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.6)

@register('cap_007_double_top', 'pattern_setup', 'short', 0.65, impl='approx')
def double_top(f):
    """Two peaks within 3% over 30 days + breakdown."""
    peak_recent = f['high'].rolling(15, min_periods=5).max()
    peak_prior = f['high'].rolling(15, min_periods=5).max().shift(15)
    equal_peaks = ((peak_recent - peak_prior).abs() / peak_recent) < 0.03
    breakdown = f['close'] < f['low_20d']
    trig = equal_peaks & breakdown
    score = np.where(trig, -0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.65)

@register('cap_008_double_bottom', 'pattern_setup', 'long', 0.65, impl='approx')
def double_bottom(f):
    low_recent = f['low'].rolling(15, min_periods=5).min()
    low_prior = f['low'].rolling(15, min_periods=5).min().shift(15)
    equal_lows = ((low_recent - low_prior).abs() / low_recent) < 0.03
    breakout = f['close'] > f['high_20d']
    trig = equal_lows & breakout
    score = np.where(trig, 0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.65)

@register('cap_009_cup_and_handle', 'pattern_setup', 'long', 0.6, impl='approx', na_reason='shape hard to approx')
def cup_and_handle(f):
    """Approx: smooth 90-day bottoming then new 90d high breakout."""
    was_near_low = f['close'].shift(60) < f['low_200d'].shift(60) * 1.1
    smooth = f['rv30'].shift(30) < 0.5
    breakout = f['close'] > f['high'].rolling(90, min_periods=30).max().shift(1)
    trig = was_near_low & smooth & breakout
    score = np.where(trig, 0.5, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.5)

@register('cap_010_ascending_triangle', 'pattern_setup', 'long', 0.65, impl='approx')
def asc_triangle(f):
    """Flat recent high (20d) + rising lows, then break above."""
    flat_high = (f['high_20d'] - f['high_20d'].shift(10)).abs() / f['high_20d'] < 0.02
    rising_lows = f['low_20d'] > f['low_20d'].shift(10)
    breakout = f['close'] > f['high_20d']
    trig = flat_high & rising_lows & breakout
    score = np.where(trig, 0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.65)

@register('cap_011_descending_triangle', 'pattern_setup', 'short', 0.65, impl='approx')
def desc_triangle(f):
    flat_low = (f['low_20d'] - f['low_20d'].shift(10)).abs() / f['low_20d'] < 0.02
    falling_highs = f['high_20d'] < f['high_20d'].shift(10)
    breakdown = f['close'] < f['low_20d']
    trig = flat_low & falling_highs & breakdown
    score = np.where(trig, -0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.65)

@register('cap_012_sfp', 'pattern_setup', 'neutral', 0.6, impl='approx')
def sfp(f):
    """Swing failure: wick beyond 20d high/low then close back inside."""
    wick_above = (f['high'] > f['high_20d'].shift(1)) & (f['close'] < f['high_20d'].shift(1))
    wick_below = (f['low'] < f['low_20d'].shift(1)) & (f['close'] > f['low_20d'].shift(1))
    trig = wick_above | wick_below
    score = np.where(wick_above, -0.6, np.where(wick_below, 0.6, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.6)

@register('cap_013_range_fade', 'pattern_setup', 'neutral', 0.55, impl='approx')
def range_fade(f):
    """In range (adx<20): fade top, long bottom."""
    in_range = f['adx14'] < 20
    range_pos = ((f['close'] - f['low_20d']) / (f['high_20d'] - f['low_20d']).replace(0, np.nan)).clip(0,1)
    trig = in_range & ((range_pos > 0.85) | (range_pos < 0.15))
    score = np.where(in_range & (range_pos > 0.85), -0.5,
             np.where(in_range & (range_pos < 0.15), 0.5, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

@register('cap_014_trend_pullback', 'pattern_setup', 'long', 0.6, impl='approx')
def trend_pullback(f):
    """Uptrend + pulls to MA50/MA200 + bounces (green day)."""
    uptrend = f['ma50_above_ma200'] == 1
    near_ma50 = (f['close'] - f['ma50']).abs() / f['close'] < 0.02
    bounce = f['is_green'] == 1
    trig = uptrend & near_ma50 & bounce
    score = np.where(trig, 0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.6)

@register('cap_050_three_drives', 'pattern_setup', 'neutral', 0.55, impl='approx', na_reason='rough')
def three_drives(f):
    """Very rough: 3 successive local highs in 30 days."""
    hh = (f['high'] > f['high'].shift(1))
    three_hh = hh.rolling(10, min_periods=3).sum() >= 5
    trig = three_hh & (f['rsi14'] > 70)
    score = np.where(trig, -0.5, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.5)

@register('cap_051_quasimodo', 'pattern_setup', 'neutral', 0.55, impl='approx', na_reason='rough')
def quasimodo(f):
    """Higher high followed by lower low (failed breakout reversal)."""
    had_hh = f['close'].shift(5) > f['high'].rolling(30, min_periods=10).max().shift(6)
    now_ll = f['close'] < f['low'].rolling(20, min_periods=5).min().shift(1)
    trig = had_hh & now_ll
    score = np.where(trig, -0.55, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.55)

@register('cap_052_liquidity_grab', 'pattern_setup', 'neutral', 0.65, impl='approx')
def liquidity_grab(f):
    """Wick beyond 10d extreme with large wick ratio + reversal close."""
    wick_up = (f['high'] > f['high'].rolling(10, min_periods=3).max().shift(1)) & (f['upper_wick_pct'] > 0.5) & (f['close'] < f['open'])
    wick_dn = (f['low'] < f['low'].rolling(10, min_periods=3).min().shift(1)) & (f['lower_wick_pct'] > 0.5) & (f['close'] > f['open'])
    trig = wick_up | wick_dn
    score = np.where(wick_dn, 0.65, np.where(wick_up, -0.65, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.65)

@register('cap_053_doji', 'pattern_setup', 'neutral', 0.45, impl='approx')
def doji(f):
    """Small body at key level."""
    small_body = f['body_pct'] < 0.1
    at_key = (f['close'] - f['ma50']).abs() / f['close'] < 0.02
    trig = small_body & at_key
    # Direction ambiguous — signal as neutral zero
    return CapabilityOutput(triggered=trig, score=np.zeros(len(f)), bias='neutral', confidence=0.45)

@register('cap_054_engulfing', 'pattern_setup', 'neutral', 0.55, impl='approx')
def engulfing(f):
    """Body > prior body in opposite direction."""
    body = (f['close'] - f['open']).abs()
    prev_body = (f['close'].shift(1) - f['open'].shift(1)).abs()
    engulf = body > prev_body
    bullish = engulf & (f['is_green'] == 1) & (f['open'] < f['close'].shift(1)) & (f['close'] > f['open'].shift(1))
    bearish = engulf & (f['is_green'] == 0) & (f['open'] > f['close'].shift(1)) & (f['close'] < f['open'].shift(1))
    trig = bullish | bearish
    score = np.where(bullish, 0.55, np.where(bearish, -0.55, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

@register('cap_055_pin_bar', 'pattern_setup', 'neutral', 0.55, impl='approx')
def pin_bar(f):
    """Long wick (>2x body) rejecting key level."""
    body = (f['close'] - f['open']).abs()
    range_ = f['high'] - f['low']
    upper_pin = (f['upper_wick_pct'] > 0.6) & (body < range_ * 0.25) & ((f['high'] - f['high_20d']).abs() / f['high'] < 0.01)
    lower_pin = (f['lower_wick_pct'] > 0.6) & (body < range_ * 0.25) & ((f['low'] - f['low_20d']).abs() / f['low'] < 0.01)
    trig = upper_pin | lower_pin
    score = np.where(upper_pin, -0.55, np.where(lower_pin, 0.55, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

@register('cap_056_double_needle_bottom', 'pattern_setup', 'long', 0.6, impl='approx')
def double_needle_bottom(f):
    """Two bars in 10 window with long lower wicks at similar level."""
    big_lower_wick = f['lower_wick_pct'] > 0.4
    big_lower_wick_count = big_lower_wick.rolling(10, min_periods=2).sum()
    trig = big_lower_wick_count >= 2
    score = np.where(trig, 0.55, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.55)

@register('cap_057_fake_breakout', 'pattern_setup', 'neutral', 0.6, impl='approx')
def fake_breakout(f):
    """Price broke 20d high/low yesterday but returned inside today."""
    broke_up = f['close'].shift(1) > f['high_20d'].shift(2)
    back_inside_dn = f['close'] < f['high_20d'].shift(2)
    fake_up = broke_up & back_inside_dn
    broke_dn = f['close'].shift(1) < f['low_20d'].shift(2)
    back_inside_up = f['close'] > f['low_20d'].shift(2)
    fake_dn = broke_dn & back_inside_up
    trig = fake_up | fake_dn
    score = np.where(fake_up, -0.55, np.where(fake_dn, 0.55, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.6)

@register('cap_058_triple_bottom', 'pattern_setup', 'long', 0.65, impl='approx')
def triple_bottom(f):
    """Three lows within 3% in 45 days + breakout."""
    min_30d = f['low'].rolling(30, min_periods=5).min()
    count_equal = ((f['low'] - min_30d).abs() / min_30d < 0.03).rolling(45, min_periods=3).sum()
    breakout = f['close'] > f['high_20d']
    trig = (count_equal >= 3) & breakout
    score = np.where(trig, 0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.65)
