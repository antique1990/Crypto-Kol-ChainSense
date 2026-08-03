"""Emerged factors — top 18 from the 400 LLM-proposed capabilities,
implemented as Python rule evaluators using the existing features panel.
Each factor has emg_ID matching the analysis ranking."""
import numpy as np
import pandas as pd
from .registry import register, CapabilityOutput

# ---------------------- VWAP / level magnets ----------------------

@register('emg_001_quarterly_vwap', 'indicator_rule', 'neutral', 0.55, impl='approx')
def quarterly_vwap_magnet(f):
    """AnalysisElliott: anchored quarterly VWAP as support/resistance magnet.
    Score: long if price below qvwap and bouncing, short if above and rejected."""
    if 'qvwap' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    diff = (f['close'] - f['qvwap']) / f['qvwap']
    near = diff.abs() < 0.015
    bullish = near & (f['close'] > f['qvwap']) & (f['is_green'] == 1)
    bearish = near & (f['close'] < f['qvwap']) & (f['is_green'] == 0)
    trig = bullish | bearish
    score = np.where(bullish, 0.5, np.where(bearish, -0.5, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

# ---------------------- Cycle / time ----------------------

@register('emg_005_4year_same_day_compare', 'cycle_time', 'neutral', 0.5, impl='rule')
def same_day_4y_compare(f):
    """ChartsBTC: compare today's price with same calendar day 4 years ago.
    If 4y return strongly positive AND in cycle accumulation phase, bullish."""
    if 'ret_4y' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    ret4y = f['ret_4y']
    bullish = ret4y > 1.5  # >150% in 4 years
    bearish = ret4y < 0.3  # <30% in 4 years
    trig = bullish | bearish
    score = np.where(bullish, 0.4, np.where(bearish, -0.4, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.5)

@register('emg_006_days_in_tight_range', 'cycle_time', 'neutral', 0.55, impl='rule')
def days_in_range(f):
    """ChartsBTC: days in tight horizontal range — long consolidation precedes breakout.
    Score = positive when streak gets long (breakout pending)."""
    if 'tight_range_streak' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    streak = f['tight_range_streak']
    trig = streak > 30
    # Direction depends on trend bias: in uptrend, breakout up; in downtrend, breakout down
    in_up = f['ma50_above_ma200'] == 1
    score = np.where(trig & in_up, 0.5, np.where(trig & ~in_up, -0.5, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

# ---------------------- HTF reclaim / retest ----------------------

@register('emg_007_htf_reclaim_retest', 'structural_bias', 'long', 0.65, impl='approx')
def htf_reclaim_retest(f):
    """ColdBloodShill: weekly level reclaim + retest confirmation."""
    # Approx: close back above 20W MA after being below for 5+ days, then retest within 5 bars
    above_now = f['close'] > f['ma_20w']
    was_below = (f['close'].shift(5) < f['ma_20w'].shift(5))
    retest = (f['low'] - f['ma_20w']).abs() / f['close'] < 0.02  # touched within 2%
    trig = above_now & was_below & retest
    score = np.where(trig, 0.6, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.65)

@register('emg_008_w50ema_bull_bear_divider', 'indicator_rule', 'long', 0.6, impl='rule')
def w50ema_divider(f):
    """CrypNuevo: 1W 50EMA = bull/bear divider. Reclaim = strong long signal."""
    if 'ema_50w' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    above = f['close'] > f['ema_50w']
    above_prev = f['close'].shift(1) <= f['ema_50w'].shift(1)
    reclaim = above & above_prev
    lose = (~above) & (f['close'].shift(1) > f['ema_50w'].shift(1))
    score = np.where(reclaim, 0.7, np.where(lose, -0.7, 0))
    trig = reclaim | lose
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.6)

# ---------------------- Filters ----------------------

@register('emg_009_range_middle_filter', 'risk_rule', 'neutral', 0.55, impl='rule')
def range_middle_filter(f):
    """CryptoCred: when in range middle, no position. Sets cap to neutral."""
    range_pos = ((f['close'] - f['low_50d']) / (f['high_50d'] - f['low_50d']).replace(0, np.nan)).clip(0,1)
    in_middle = range_pos.between(0.4, 0.6)
    in_range = f['adx14'] < 20
    trig = in_middle & in_range
    return CapabilityOutput(triggered=trig, score=np.zeros(len(f)), bias='neutral', confidence=0.55,
                            notes='filter — sets bias to none')

# ---------------------- Patterns ----------------------

@register('emg_010_broadening_wedge', 'pattern_setup', 'neutral', 0.55, impl='approx')
def broadening_wedge(f):
    """CryptoFaibik: widening BB indicates broadening wedge expansion."""
    bb_widening = f['bb_width'] > f['bb_width'].shift(20) * 1.5
    breakout_up = f['close'] > f['bb_upper']
    breakout_dn = f['close'] < f['bb_lower']
    trig = bb_widening & (breakout_up | breakout_dn)
    score = np.where(bb_widening & breakout_up, 0.55,
             np.where(bb_widening & breakout_dn, -0.55, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

@register('emg_013_box_breakout', 'pattern_setup', 'neutral', 0.6, impl='approx')
def box_breakout(f):
    """CryptoMichNL: tight horizontal box → breakout direction."""
    box = (f['tight_range_streak'] > 15)  # consolidation
    up = box & (f['close'] > f['high_20d'].shift(1))
    dn = box & (f['close'] < f['low_20d'].shift(1))
    trig = up | dn
    score = np.where(up, 0.65, np.where(dn, -0.65, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.6)

@register('emg_014_horizontal_reclaim', 'indicator_rule', 'long', 0.6, impl='approx')
def horizontal_reclaim(f):
    """CryptoTony__: reclaim a previously-lost key level."""
    # Use 50d high as proxy for "key level"
    lost_50d = f['close'].shift(10) < f['high_50d'].shift(10) * 0.97
    reclaim = (f['close'] > f['high_50d'].shift(10)) & lost_50d
    score = np.where(reclaim, 0.6, 0.0)
    return CapabilityOutput(triggered=reclaim, score=score, bias='long', confidence=0.6)

@register('emg_017_break_target_projection', 'pattern_setup', 'neutral', 0.55, impl='approx')
def break_target_projection(f):
    """GarethSoloway: confirmed level break → momentum continuation."""
    # Strong close beyond 20d level by >2%
    big_break_up = (f['close'] > f['high_20d'].shift(1) * 1.02) & (f['is_green'] == 1)
    big_break_dn = (f['close'] < f['low_20d'].shift(1) * 0.98) & (f['is_green'] == 0)
    trig = big_break_up | big_break_dn
    score = np.where(big_break_up, 0.55, np.where(big_break_dn, -0.55, 0))
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.55)

# ---------------------- 200W MA family ----------------------

@register('emg_022_200w_mechanical_buy', 'indicator_rule', 'long', 0.7, impl='rule')
def w200_buy(f):
    """IvanOnTech: touch 200W MA = mechanical accumulation zone."""
    if 'ma_200w' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    near = (f['close'] - f['ma_200w']).abs() / f['ma_200w'] < 0.05
    score = np.where(near, 0.7, 0.0)
    return CapabilityOutput(triggered=near, score=score, bias='long', confidence=0.7)

@register('emg_028_20w_200w_double_reclaim', 'indicator_rule', 'long', 0.75, impl='rule')
def double_w_reclaim(f):
    """LedgerStatus: simultaneous reclaim of 20W + 200W MAs = optimal entry."""
    if 'ma_200w' not in f.columns or 'ma_20w' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    above_both = (f['close'] > f['ma_20w']) & (f['close'] > f['ma_200w'])
    was_below_either = (f['close'].shift(3) < f['ma_20w'].shift(3)) | (f['close'].shift(3) < f['ma_200w'].shift(3))
    trig = above_both & was_below_either
    score = np.where(trig, 0.75, 0.0)
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.75)

@register('emg_029_200w_value_zone', 'indicator_rule', 'long', 0.65, impl='rule')
def w200_value_zone(f):
    """LedgerStatus: price within 8% of 200W MA = long-term value zone."""
    if 'pct_from_ma_200w' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    in_zone = f['pct_from_ma_200w'].abs() < 0.08
    score = np.where(in_zone, 0.6, 0.0)
    return CapabilityOutput(triggered=in_zone, score=score, bias='long', confidence=0.65)

# ---------------------- HTF anchors / closes ----------------------

@register('emg_027_ohlc_anchor_framework', 'structural_bias', 'neutral', 0.5, impl='approx')
def ohlc_anchors(f):
    """KillaXBT: weekly/monthly opens as core S/R anchors."""
    # Weekly open: take Monday close as proxy. Use day_of_week.
    if 'day_of_week' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    # Forward-fill weekly open from Monday's open
    week_open = f['open'].where(f['day_of_week'] == 0).ffill()
    above = (f['close'] > week_open).astype(int)
    # Just count days above week open, score based on bias
    pct_diff = (f['close'] - week_open) / week_open
    score = np.tanh(pct_diff * 5) * 0.4  # smooth signal
    trig = pct_diff.abs() > 0.01
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.5)

@register('emg_030_htf_close_anchor', 'structural_bias', 'long', 0.55, impl='rule')
def htf_close_anchor(f):
    """MacroCRG: weekly close above key MA = trend continuation."""
    # Sunday/Monday close above 20W MA
    if 'ma_20w' not in f.columns or 'day_of_week' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    is_sunday = f['day_of_week'] == 6
    week_close_strong = is_sunday & (f['close'] > f['ma_20w'])
    week_close_weak = is_sunday & (f['close'] < f['ma_20w'])
    score = np.where(week_close_strong, 0.55, np.where(week_close_weak, -0.55, 0))
    trig = week_close_strong | week_close_weak
    return CapabilityOutput(triggered=trig, score=score, bias='long', confidence=0.55)

# ---------------------- Seasonality ----------------------

@register('emg_023_monthly_seasonality', 'cycle_time', 'long', 0.5, impl='rule')
def monthly_seasonality(f):
    """JakeGagain: certain months historically bullish (BTC: Oct-Dec strong, Jan-Feb weak)."""
    if 'month' not in f.columns:
        n = len(f); return CapabilityOutput(triggered=np.zeros(n,bool), score=np.zeros(n))
    bullish_months = f['month'].isin([3, 4, 10, 11, 12])
    bearish_months = f['month'].isin([1, 6, 9])
    score = np.where(bullish_months, 0.35, np.where(bearish_months, -0.35, 0))
    trig = bullish_months | bearish_months
    return CapabilityOutput(triggered=trig, score=score, bias='neutral', confidence=0.5)
