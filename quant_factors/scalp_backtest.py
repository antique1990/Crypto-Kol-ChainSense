#!/usr/bin/env python3
"""5-minute scalping backtest: adapt 20 compatible factors to 5m timeframe, compute IC, simulate PnL."""
import json, os
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.expanduser('~/shared/materials/crypto_traders_distill')
QF = f'{BASE}/quant_factors'

# Load 5m data
raw = json.load(open(f'{QF}/btc_5m_7d.json'))
df = pd.DataFrame(raw)
df['datetime'] = pd.to_datetime(df['date'])
df = df.set_index('datetime').sort_index()
print(f'5m candles: {len(df)}')

# ============================================================
# Feature engine (5-minute adapted)
# ============================================================
def sma(s, n): return s.rolling(n, min_periods=max(1, n//2)).mean()
def ema(s, n): return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    diff = s.diff()
    gain = diff.clip(lower=0)
    loss = (-diff).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

c, h, l, o, vol = df['close'], df['high'], df['low'], df['open'], df['volume']
feat = pd.DataFrame(index=df.index)
feat['close'] = c
feat['open'] = o
feat['high'] = h
feat['low'] = l
feat['volume'] = vol

# MAs (5m scale: 12 bars = 1h, 288 bars = 1d)
feat['ma12'] = sma(c, 12)    # ~1h
feat['ma48'] = sma(c, 48)    # ~4h
feat['ma288'] = sma(c, 288)  # ~1d
feat['ema12'] = ema(c, 12)
feat['ema48'] = ema(c, 48)

# RSI
feat['rsi14'] = rsi(c, 14)
feat['rsi14_prev'] = feat['rsi14'].shift(1)

# Bollinger Bands (20-bar = ~100min)
feat['bb_mid'] = sma(c, 20)
bb_std = c.rolling(20, min_periods=5).std(ddof=0)
feat['bb_upper'] = feat['bb_mid'] + 2*bb_std
feat['bb_lower'] = feat['bb_mid'] - 2*bb_std
feat['bb_width'] = (4*bb_std / feat['bb_mid'])
feat['bb_width_20pctile'] = feat['bb_width'].rolling(200, min_periods=50).quantile(0.2)

# ATR
tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
feat['atr14'] = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

# Rolling highs/lows
feat['high_24'] = h.rolling(24, min_periods=5).max()    # ~2h high
feat['low_24'] = l.rolling(24, min_periods=5).min()
feat['high_96'] = h.rolling(96, min_periods=20).max()   # ~8h high
feat['low_96'] = l.rolling(96, min_periods=20).min()
feat['high_288'] = h.rolling(288, min_periods=60).max()  # 1d high
feat['low_288'] = l.rolling(288, min_periods=60).min()

# Range position
rng = (feat['high_96'] - feat['low_96']).replace(0, np.nan)
feat['range_pos_96'] = (c - feat['low_96']) / rng

# Candle anatomy
body = (c - o).abs()
full_range = (h - l).replace(0, np.nan)
feat['body_pct'] = body / full_range
feat['upper_wick_pct'] = (h - c.where(c > o, o)) / full_range
feat['lower_wick_pct'] = (c.where(c < o, o) - l) / full_range
feat['is_green'] = (c > o).astype(int)

# Volume spike
feat['vol_sma20'] = sma(vol, 20)
feat['vol_spike'] = vol / feat['vol_sma20'].replace(0, np.nan)

# Forward returns (for IC calc)
for n in [1, 3, 6, 12, 24, 48]:  # 5m/15m/30m/1h/2h/4h forward
    feat[f'fwd_{n}'] = c.pct_change(n).shift(-n)

# ADX proxy (simplified for 5m)
up = h.diff(); dn = -l.diff()
plus_dm = np.where((up > dn) & (up > 0), up, 0)
minus_dm = np.where((dn > up) & (dn > 0), dn, 0)
atr_ = feat['atr14']
plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, min_periods=14, adjust=False).mean() / atr_
minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, min_periods=14, adjust=False).mean() / atr_
dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
feat['adx14'] = dx.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

print(f'features: {feat.shape}')

# ============================================================
# Scalp-adapted factor evaluators (20 factors)
# ============================================================
factors = pd.DataFrame(index=feat.index)

# 1. RSI oversold bounce (<25 on 5m, cross back above)
factors['rsi_oversold'] = np.where(
    (feat['rsi14'] > 25) & (feat['rsi14_prev'] <= 25), 0.6, 0.0
)

# 2. RSI overbought reversal (>75)
factors['rsi_overbought'] = np.where(
    (feat['rsi14'] < 75) & (feat['rsi14_prev'] >= 75), -0.6, 0.0
)

# 3. BB squeeze breakout
squeeze = (feat['bb_width'].shift(1) < feat['bb_width_20pctile'].shift(1)).fillna(False)
factors['bb_squeeze_up'] = np.where(squeeze & (c > feat['bb_upper']), 0.65, 0.0)
factors['bb_squeeze_dn'] = np.where(squeeze & (c < feat['bb_lower']), -0.65, 0.0)

# 4. SFP (swing failure pattern at 2h extremes)
factors['sfp_bull'] = np.where(
    (l < feat['low_24'].shift(1)) & (c > feat['low_24'].shift(1)) & (feat['lower_wick_pct'] > 0.5),
    0.7, 0.0
)
factors['sfp_bear'] = np.where(
    (h > feat['high_24'].shift(1)) & (c < feat['high_24'].shift(1)) & (feat['upper_wick_pct'] > 0.5),
    -0.7, 0.0
)

# 5. Range fade (8h range top/bottom)
in_range = feat['adx14'] < 20
factors['range_fade'] = np.where(
    in_range & (feat['range_pos_96'] > 0.9), -0.5,
    np.where(in_range & (feat['range_pos_96'] < 0.1), 0.5, 0.0)
)

# 6. Engulfing candle
prev_body = (feat['close'].shift(1) - feat['open'].shift(1)).abs()
curr_body = body
engulf_bull = (feat['is_green']==1) & (curr_body > prev_body) & (o < feat['close'].shift(1).where(c.shift(1)<o.shift(1), o.shift(1)))
engulf_bear = (feat['is_green']==0) & (curr_body > prev_body) & (o > feat['close'].shift(1).where(c.shift(1)>o.shift(1), o.shift(1)))
factors['engulf_bull'] = np.where(engulf_bull, 0.55, 0.0)
factors['engulf_bear'] = np.where(engulf_bear, -0.55, 0.0)

# 7. Pin bar rejection at 2h extreme
factors['pin_bull'] = np.where(
    (feat['lower_wick_pct'] > 0.6) & (body < full_range * 0.25) & (feat['range_pos_96'] < 0.2),
    0.6, 0.0
)
factors['pin_bear'] = np.where(
    (feat['upper_wick_pct'] > 0.6) & (body < full_range * 0.25) & (feat['range_pos_96'] > 0.8),
    -0.6, 0.0
)

# 8. FVG (fair value gap: 3-candle imbalance)
factors['fvg_bull'] = np.where(l > h.shift(2), 0.5, 0.0)
factors['fvg_bear'] = np.where(h < l.shift(2), -0.5, 0.0)

# 9. Liquidity grab (wick beyond 96-bar extreme then reversal)
factors['liq_grab_bull'] = np.where(
    (l < feat['low_96'].shift(1)) & (c > feat['low_96'].shift(1)) & (feat['lower_wick_pct'] > 0.4),
    0.7, 0.0
)
factors['liq_grab_bear'] = np.where(
    (h > feat['high_96'].shift(1)) & (c < feat['high_96'].shift(1)) & (feat['upper_wick_pct'] > 0.4),
    -0.7, 0.0
)

# 10. Volume spike reversal
factors['vol_spike_rev'] = np.where(
    (feat['vol_spike'] > 3) & (feat['is_green'] == 0) & (feat['range_pos_96'] > 0.8),
    -0.6, np.where(
    (feat['vol_spike'] > 3) & (feat['is_green'] == 1) & (feat['range_pos_96'] < 0.2),
    0.6, 0.0)
)

# 11. OHLC hourly anchor
hour_open = feat['open'].where(feat.index.minute == 0).ffill()
factors['hour_anchor'] = np.tanh((c - hour_open) / hour_open * 20) * 0.3

# 12. MA cross (12 vs 48 bar = 1h vs 4h)
factors['ma_cross_up'] = np.where(
    (feat['ema12'] > feat['ema48']) & (feat['ema12'].shift(1) <= feat['ema48'].shift(1)), 0.5, 0.0
)
factors['ma_cross_dn'] = np.where(
    (feat['ema12'] < feat['ema48']) & (feat['ema12'].shift(1) >= feat['ema48'].shift(1)), -0.5, 0.0
)

# 13. Range middle filter (no-trade zone)
factors['range_mid_filter'] = np.where(
    in_range & feat['range_pos_96'].between(0.35, 0.65), 0.0, np.nan  # NaN = don't filter, 0 = filter
)

# 14. Fake breakout (broke 24-bar high/low yesterday, came back)
factors['fake_break'] = np.where(
    (c.shift(1) > feat['high_24'].shift(2)) & (c < feat['high_24'].shift(2)), -0.6,
    np.where(
    (c.shift(1) < feat['low_24'].shift(2)) & (c > feat['low_24'].shift(2)), 0.6, 0.0)
)

factor_cols = [c for c in factors.columns if not c.startswith('fwd_')]
print(f'scalp factors: {len(factor_cols)}')

# ============================================================
# IC analysis (multiple horizons for scalping)
# ============================================================
print(f'\n{"="*70}')
print(f'  5 分钟级因子 IC 分析 (2016 bars)')
print(f'{"="*70}')

horizons = [
    ('fwd_1', '5m', 1),
    ('fwd_3', '15m', 3),
    ('fwd_6', '30m', 6),
    ('fwd_12', '1h', 12),
    ('fwd_24', '2h', 24),
    ('fwd_48', '4h', 48),
]

ic_results = []
for fc in factor_cols:
    row = {'factor': fc}
    for fwd_col, label, n in horizons:
        merged = pd.concat([factors[fc], feat[fwd_col]], axis=1).dropna()
        merged = merged[merged[fc].abs() > 0.01]
        if len(merged) < 10:
            row[f'ic_{label}'] = np.nan
            row[f'n_{label}'] = 0
            continue
        ic, pval = stats.spearmanr(merged[fc], merged[fwd_col])
        row[f'ic_{label}'] = ic
        row[f'n_{label}'] = len(merged)
        # Hit rate
        longs = merged[merged[fc] > 0.1]
        shorts = merged[merged[fc] < -0.1]
        row[f'hit_L_{label}'] = (longs[fwd_col] > 0).mean() if len(longs) > 0 else np.nan
        row[f'hit_S_{label}'] = (shorts[fwd_col] < 0).mean() if len(shorts) > 0 else np.nan
        row[f'nL_{label}'] = len(longs)
        row[f'nS_{label}'] = len(shorts)
    ic_results.append(row)

ic_df = pd.DataFrame(ic_results)

# Best horizon per factor
print(f'\n--- Top 20 因子 × 最佳周期 ---\n')
print(f'{"因子":<25s} {"最佳周期":>6s} {"IC":>7s} {"hit_L":>6s} {"nL":>5s} {"hit_S":>6s} {"nS":>5s}')
print('-' * 70)

best_rows = []
for _, r in ic_df.iterrows():
    best_ic = 0
    best_h = ''
    for _, label, _ in horizons:
        ic_val = r.get(f'ic_{label}', np.nan)
        if not np.isnan(ic_val) and abs(ic_val) > abs(best_ic):
            best_ic = ic_val
            best_h = label
    if best_h:
        best_rows.append({
            'factor': r['factor'],
            'horizon': best_h,
            'ic': best_ic,
            'hit_L': r.get(f'hit_L_{best_h}', np.nan),
            'nL': r.get(f'nL_{best_h}', 0),
            'hit_S': r.get(f'hit_S_{best_h}', np.nan),
            'nS': r.get(f'nS_{best_h}', 0),
        })

best_rows.sort(key=lambda x: -abs(x['ic']))
for b in best_rows[:20]:
    hl = f"{b['hit_L']:.2f}" if not np.isnan(b['hit_L']) else '  -'
    hs = f"{b['hit_S']:.2f}" if not np.isnan(b['hit_S']) else '  -'
    direction = '正' if b['ic'] > 0 else '反'
    print(f"  {b['factor']:<23s} {b['horizon']:>6s} {direction} {b['ic']:+.3f} {hl:>6s} {int(b['nL']):>5d} {hs:>6s} {int(b['nS']):>5d}")

# Count significant
sig = sum(1 for b in best_rows if abs(b['ic']) > 0.05)
strong = sum(1 for b in best_rows if abs(b['ic']) > 0.1)
print(f'\n显著因子 (|IC|>0.05): {sig}')
print(f'强因子 (|IC|>0.1): {strong}')

# ============================================================
# Simulated scalp PnL (best 5 factors, 1h horizon, $1000)
# ============================================================
print(f'\n{"="*70}')
print(f'  剥头皮模拟 — $1000 × 最强 5 因子组合 × 1h 持仓')
print(f'{"="*70}')

# Pick top 5 by absolute IC at 1h horizon
top5 = sorted(best_rows, key=lambda x: -abs(x.get('ic',0)))[:5]
top5_names = [t['factor'] for t in top5]
print(f'  选中因子: {top5_names}')

# Composite signal = mean of top 5
composite = factors[top5_names].mean(axis=1)

# Trade when |composite| > 0.15
THRESHOLD = 0.15
HOLD_BARS = 12  # 1 hour = 12 × 5m bars
CAPITAL = 1000.0

trades = []
i = 0
balance = CAPITAL
while i < len(composite) - HOLD_BARS:
    sig = composite.iloc[i]
    if abs(sig) < THRESHOLD:
        i += 1
        continue
    direction = 1 if sig > 0 else -1
    entry = feat['close'].iloc[i]
    exit_price = feat['close'].iloc[i + HOLD_BARS]
    ret = (exit_price - entry) / entry * direction
    pnl = ret * balance
    balance += pnl
    trades.append({
        'time': str(feat.index[i]),
        'direction': 'long' if direction > 0 else 'short',
        'entry': entry,
        'exit': exit_price,
        'ret': ret,
        'pnl': pnl,
        'balance': balance,
        'correct': ret > 0,
    })
    i += HOLD_BARS  # skip holding period

print(f'  总交易次数: {len(trades)}')
if trades:
    wins = sum(1 for t in trades if t['correct'])
    losses = len(trades) - wins
    win_rate = wins / len(trades)
    avg_win = np.mean([t['ret'] for t in trades if t['correct']]) if wins > 0 else 0
    avg_loss = np.mean([abs(t['ret']) for t in trades if not t['correct']]) if losses > 0 else 0
    total_ret = (balance - CAPITAL) / CAPITAL

    print(f'  胜率: {win_rate:.0%} ({wins}胜 / {losses}负)')
    print(f'  平均赢: {avg_win*100:.2f}% | 平均亏: {avg_loss*100:.2f}%')
    print(f'  盈亏比: {avg_win/avg_loss:.2f}' if avg_loss > 0 else '  盈亏比: inf')
    print(f'  最终余额: ${balance:.1f} ({total_ret*100:+.1f}%)')
    print(f'  最大单笔赢: ${max(t["pnl"] for t in trades):.1f}')
    print(f'  最大单笔亏: ${min(t["pnl"] for t in trades):.1f}')

    # Show last 10 trades
    print(f'\n  最近 10 笔交易:')
    print(f'  {"时间":>20s} {"方向":>4s} {"入场":>10s} {"出场":>10s} {"收益":>8s} {"余额":>10s}')
    for t in trades[-10:]:
        arrow = '✅' if t['correct'] else '❌'
        print(f"  {t['time'][:16]:>20s} {t['direction']:>4s} ${t['entry']:>9,.0f} ${t['exit']:>9,.0f} {t['ret']*100:>+7.2f}% ${t['balance']:>9,.1f} {arrow}")

    # Save
    pd.DataFrame(trades).to_csv(f'{QF}/scalp_trades.csv', index=False)
    print(f'\n  saved scalp_trades.csv')
