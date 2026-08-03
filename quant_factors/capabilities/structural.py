"""Structural bias (8 caps — Wyckoff/SMC/ICT/Elliott/BTC.D)."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

@register('cap_023_elliott_wave_3', 'structural_bias', 'long', 0.55, impl='approx')
def elliott_wave_3(f):
    """Rule approx: strong up impulse — ret_30d > 20% AND RSI 60-80 (not yet overbought) AND higher-highs."""
    trig = (f['ret_30d'] > 0.20) & (f['rsi14'].between(55, 80)) & (f['hh_count_20d'] > f['ll_count_20d'])
    score = np.where(trig, 0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.55, notes='approx for wave 3 impulse')

@register('cap_024_wyckoff_accumulation_spring', 'structural_bias', 'long', 0.7, impl='approx')
def wyckoff_spring(f):
    """Rule approx: At range low, sharp wick-down then close back above prior low."""
    near_low = f['close'] < f['low_50d'] * 1.03  # close within 3% of 50d low
    wick_below = f['low'] < f['low_50d'].shift(1)  # today's low pierced prior 50d low
    close_above = f['close'] > f['low_50d'].shift(1)  # but closed back above
    trig = near_low & wick_below & close_above & (f['lower_wick_pct'] > 0.4)
    score = np.where(trig, 0.75, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.7)

@register('cap_025_wyckoff_distribution_upthrust', 'structural_bias', 'short', 0.7, impl='approx')
def wyckoff_upthrust(f):
    near_high = f['close'] > f['high_50d'] * 0.97
    wick_above = f['high'] > f['high_50d'].shift(1)
    close_below = f['close'] < f['high_50d'].shift(1)
    trig = near_high & wick_above & close_below & (f['upper_wick_pct'] > 0.4)
    score = np.where(trig, -0.75, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.7)

@register('cap_026_smc_order_block_retest', 'structural_bias', 'neutral', 0.6, impl='approx')
def smc_order_block_retest(f):
    """Rule approx: Price retesting prior breakout candle close (proxy: retracing to 5-day prior high/low after breakout)."""
    # Very rough: up breakout + retest to 5 bars ago
    was_breakout = f['close'].shift(5) > f['high_20d'].shift(6)
    retest_area = (f['close'] < f['close'].shift(5) * 1.02) & (f['close'] > f['close'].shift(5) * 0.98)
    trig = was_breakout & retest_area
    score = np.where(trig, 0.5, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.6)

@register('cap_048_ict_breaker_block', 'structural_bias', 'neutral', 0.6, impl='approx', na_reason='partial: approx only')
def ict_breaker_block(f):
    """Rule approx: Prior support becomes resistance (or vice versa). Use 20d range break + retest."""
    was_support = f['low_20d'].shift(5)
    broke_down = f['close'].shift(4) < was_support
    retest = (f['close'] > was_support * 0.98) & (f['close'] < was_support * 1.02)
    trig = broke_down & retest
    score = np.where(trig, -0.5, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='short', confidence=0.6)

@register('cap_049_ict_fair_value_gap', 'structural_bias', 'neutral', 0.55, impl='approx')
def ict_fvg(f):
    """3-candle imbalance: today low > 2 days ago high (bullish FVG) or today high < 2 days ago low (bearish FVG)."""
    bull_fvg = f['low'] > f['high'].shift(2)
    bear_fvg = f['high'] < f['low'].shift(2)
    trig = bull_fvg | bear_fvg
    score = np.where(bull_fvg, 0.5, np.where(bear_fvg, -0.5, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

@register('cap_065_btcd_shift', 'structural_bias', 'neutral', 0.55, impl='mock', na_reason='need BTC dominance series')
def btc_dominance_shift(f):
    """Mock: we don't have BTC dominance data. Returns 0 always."""
    n = len(f) if hasattr(f, '__len__') else 1
    return CapabilityOutput(triggered=np.zeros(n, bool), score=np.zeros(n), bias='neutral', confidence=0.0,
                            notes='N/A without BTC.D series')

# one more approx: higher-low defense (CastilloTrading style)
@register('cap_hh_defense', 'structural_bias', 'long', 0.6, impl='approx')
def higher_low_defense(f):
    """Recent higher-lows holding: last low > prev low, uptrend label."""
    trig = (f['low_20d'] > f['low_50d']) & (f['uptrend_20d']) & (f['close'] > f['low_20d'] * 1.02)
    score = np.where(trig, 0.55, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.6)
