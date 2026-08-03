#!/usr/bin/env python3
"""Feature engine: turns raw OHLC + macro into a features panel (one row per bar per instrument).

Reads:  ohlc_daily.json (BTCUSDT/ETHUSDT/SOLUSDT/DOGEUSDT)
        macro_daily.json (DXY/GOLD/US2Y/SPX)

Writes: features.parquet — vectorized pandas DataFrame indexed by (symbol, date)
        ~30 features per bar: MAs, RSI, MACD, BB, ADX, ATR, returns, rolling stats, pivots
"""
import json, os, sys
import numpy as np
import pandas as pd


def resolve_base():
    def looks_like_project_root(candidate):
        if not candidate:
            return False
        candidate = os.path.abspath(candidate)
        return (
            os.path.isdir(os.path.join(candidate, 'quant_factors'))
            and os.path.isdir(os.path.join(candidate, 'profiles_v2'))
            and os.path.isfile(os.path.join(candidate, 'ohlc_daily.json'))
            and os.path.isfile(os.path.join(candidate, 'macro_daily.json'))
        )

    candidates = []
    if getattr(sys, 'frozen', False):
        mei = getattr(sys, '_MEIPASS', None)
        if mei:
            candidates.append(mei)
        if sys.executable:
            candidates.append(os.path.dirname(sys.executable))
            candidates.append(os.path.dirname(os.path.dirname(sys.executable)))
    candidates.extend([
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ])

    for candidate in candidates:
        if looks_like_project_root(candidate):
            return os.path.abspath(candidate)

    def walk_up(start):
        current = os.path.abspath(start)
        while True:
            if looks_like_project_root(current):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return None

    for start in [os.getcwd(), os.path.dirname(os.path.abspath(__file__)), os.path.dirname(sys.executable) if sys.executable else None]:
        if not start:
            continue
        found = walk_up(start)
        if found:
            return found

    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE = resolve_base()

def load_ohlc():
    ohlc = json.load(open(f'{BASE}/ohlc_daily.json'))
    macro = json.load(open(f'{BASE}/macro_daily.json'))
    frames = {}
    for sym, candles in {**ohlc, **macro}.items():
        df = pd.DataFrame(candles)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        frames[sym] = df
    return frames

def sma(s, n): return s.rolling(n, min_periods=1).mean()
def ema(s, n): return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    diff = s.diff()
    gain = diff.clip(lower=0)
    loss = (-diff).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def macd(close, fast=12, slow=26, sig=9):
    f = ema(close, fast)
    s = ema(close, slow)
    line = f - s
    sigline = ema(line, sig)
    hist = line - sigline
    return line, sigline, hist

def bollinger(close, n=20, k=2):
    m = sma(close, n)
    sd = close.rolling(n, min_periods=1).std(ddof=0)
    return m + k*sd, m, m - k*sd, (2*k*sd/m)  # upper, mid, lower, width_pct

def atr(h, l, c, n=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, min_periods=n, adjust=False).mean()

def adx(h, l, c, n=14):
    up = h.diff()
    dn = -l.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr_ = tr.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=h.index).ewm(alpha=1/n, min_periods=n, adjust=False).mean() / atr_
    minus_di = 100 * pd.Series(minus_dm, index=h.index).ewm(alpha=1/n, min_periods=n, adjust=False).mean() / atr_
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1/n, min_periods=n, adjust=False).mean()

def stoch_rsi(rsi_series, n=14):
    low = rsi_series.rolling(n, min_periods=1).min()
    high = rsi_series.rolling(n, min_periods=1).max()
    return (rsi_series - low) / (high - low).replace(0, np.nan)

def rolling_high(s, n): return s.rolling(n, min_periods=1).max()
def rolling_low(s, n): return s.rolling(n, min_periods=1).min()

def build_features_single(df):
    """Compute features for one symbol's OHLC dataframe."""
    c, h, l, o = df['close'], df['high'], df['low'], df['open']
    out = pd.DataFrame(index=df.index)
    out['close'] = c
    out['open'] = o
    out['high'] = h
    out['low'] = l

    # Moving averages (daily)
    out['ma20'] = sma(c, 20)
    out['ma50'] = sma(c, 50)
    out['ma100'] = sma(c, 100)
    out['ma200'] = sma(c, 200)
    out['ema20'] = ema(c, 20)
    out['ema50'] = ema(c, 50)
    # Weekly equivalents (5 trading days/week, but crypto is 7d/week → use 7d multiplier)
    out['ma_20w'] = sma(c, 140)   # 20 weeks
    out['ma_50w'] = sma(c, 350)   # 50 weeks
    out['ma_200w'] = sma(c, 1400) # 200 weeks (will be NaN initially)
    out['ema_50w'] = ema(c, 350)

    # Momentum
    out['rsi14'] = rsi(c, 14)
    out['rsi14_prev'] = out['rsi14'].shift(1)
    out['rsi14_prev2'] = out['rsi14'].shift(2)
    out['stoch_rsi'] = stoch_rsi(out['rsi14'], 14)

    macd_line, macd_sig, macd_hist = macd(c)
    out['macd'] = macd_line
    out['macd_sig'] = macd_sig
    out['macd_hist'] = macd_hist
    out['macd_hist_prev'] = macd_hist.shift(1)

    # Bollinger
    bb_u, bb_m, bb_l, bb_w = bollinger(c, 20, 2)
    out['bb_upper'] = bb_u
    out['bb_mid'] = bb_m
    out['bb_lower'] = bb_l
    out['bb_width'] = bb_w
    out['bb_width_20pctile'] = bb_w.rolling(100, min_periods=30).quantile(0.2)
    out['bb_width_80pctile'] = bb_w.rolling(100, min_periods=30).quantile(0.8)

    # Volatility / trend
    out['atr14'] = atr(h, l, c, 14)
    out['adx14'] = adx(h, l, c, 14)

    # Returns
    for n in [1, 5, 7, 14, 30, 60, 90]:
        out[f'ret_{n}d'] = c.pct_change(n)
    out['fwd_ret_1d'] = c.pct_change(1).shift(-1)
    out['fwd_ret_7d'] = c.pct_change(7).shift(-7)
    out['fwd_ret_30d'] = c.pct_change(30).shift(-30)

    # Realized volatility
    logret = np.log(c / c.shift(1))
    out['rv30'] = logret.rolling(30, min_periods=10).std() * np.sqrt(365)
    out['rv30_pctile'] = out['rv30'].rolling(200, min_periods=60).rank(pct=True)

    # Swing highs / lows
    out['high_20d'] = rolling_high(h, 20)
    out['low_20d'] = rolling_low(l, 20)
    out['high_50d'] = rolling_high(h, 50)
    out['low_50d'] = rolling_low(l, 50)
    out['high_200d'] = rolling_high(h, 200)
    out['low_200d'] = rolling_low(l, 200)
    out['pct_from_high_50d'] = (c - out['high_50d']) / out['high_50d']
    out['pct_from_low_50d'] = (c - out['low_50d']) / out['low_50d']
    out['pct_from_high_200d'] = (c - out['high_200d']) / out['high_200d']

    # Bar shape (candle anatomy)
    body = (c - o).abs()
    rng = (h - l).replace(0, np.nan)
    upper_wick = h - c.where(c > o, o)
    lower_wick = c.where(c < o, o) - l
    out['body_pct'] = body / rng
    out['upper_wick_pct'] = upper_wick / rng
    out['lower_wick_pct'] = lower_wick / rng
    out['is_green'] = (c > o).astype(int)

    # Higher-highs / lower-lows counters (5-day lookback)
    out['hh_count_20d'] = (h > h.shift(1)).rolling(20, min_periods=1).sum()
    out['ll_count_20d'] = (l < l.shift(1)).rolling(20, min_periods=1).sum()
    out['uptrend_20d'] = out['hh_count_20d'] > out['ll_count_20d']
    out['downtrend_20d'] = out['ll_count_20d'] > out['hh_count_20d']

    # MA relationships
    out['price_above_ma200'] = (c > out['ma200']).astype(int)
    out['price_above_ma50'] = (c > out['ma50']).astype(int)
    out['ma50_above_ma200'] = (out['ma50'] > out['ma200']).astype(int)
    out['ma50_above_ma200_prev'] = out['ma50_above_ma200'].shift(1)
    out['days_below_ma200'] = (c < out['ma200']).groupby((c >= out['ma200']).cumsum()).cumcount()

    # Fib anchors (simple: from recent 50d swing)
    out['fib_382'] = out['high_50d'] - 0.382 * (out['high_50d'] - out['low_50d'])
    out['fib_500'] = out['high_50d'] - 0.500 * (out['high_50d'] - out['low_50d'])
    out['fib_618'] = out['high_50d'] - 0.618 * (out['high_50d'] - out['low_50d'])
    out['fib_786'] = out['high_50d'] - 0.786 * (out['high_50d'] - out['low_50d'])

    # Calendar / seasonality
    out['month'] = df.index.month
    out['day_of_week'] = df.index.dayofweek
    out['is_q1'] = (df.index.month <= 3).astype(int)
    out['is_q4'] = (df.index.month >= 10).astype(int)

    # Range tightness counter (consecutive days where price stays in 5% band)
    pct_range = (out['high_20d'] - out['low_20d']) / c
    out['tight_range_20d'] = (pct_range < 0.08).astype(int)
    out['tight_range_streak'] = out['tight_range_20d'].groupby((out['tight_range_20d']==0).cumsum()).cumcount()

    # Quarter-anchored VWAP-like (volume-less proxy: typical price weighted by daily range)
    typ = (h + l + c) / 3
    weight = (h - l).fillna(0) + 1e-9
    quarter = pd.PeriodIndex(df.index, freq='Q')
    out['_quarter'] = quarter.astype(str)
    # cumulative typ*weight / cumulative weight per quarter
    grouped = pd.DataFrame({'tw': typ*weight, 'w': weight, 'q': out['_quarter']})
    out['qvwap'] = grouped.groupby('q').apply(lambda g: (g['tw'].cumsum() / g['w'].cumsum()), include_groups=False).droplevel(0)
    out = out.drop(columns=['_quarter'])

    # Same-day cycle compare: 4 years ago return
    out['ret_4y'] = c.pct_change(365*4)

    # Days below/above 200W MA
    out['days_below_ma_200w'] = (c < out['ma_200w']).groupby((c >= out['ma_200w']).cumsum()).cumcount()

    # Distance from 200W MA in % terms
    out['pct_from_ma_200w'] = (c - out['ma_200w']) / out['ma_200w']
    out['pct_from_ma_50w'] = (c - out['ma_50w']) / out['ma_50w']

    return out

def attach_macro(features_by_sym, frames):
    """Attach DXY / GOLD / US2Y / SPX data as cross-sectional features."""
    macro = {}
    if 'DXY' in frames:
        dxy = frames['DXY']['close']
        macro['dxy'] = dxy
        macro['dxy_ret_20d'] = dxy.pct_change(20)
        macro['dxy_trend_down'] = (dxy.pct_change(20) < -0.01).astype(int)
    if 'GOLD' in frames:
        gold = frames['GOLD']['close']
        macro['gold_ret_20d'] = gold.pct_change(20)
    if 'US2Y' in frames:
        y = frames['US2Y']['close']
        macro['y_ret_20d'] = y.pct_change(20)
        macro['y_slope_20d_neg'] = (y.diff(20) < 0).astype(int)
    if 'SPX' in frames:
        s = frames['SPX']['close']
        macro['spx_ret_20d'] = s.pct_change(20)
        macro['spx_trend_up'] = (s.pct_change(20) > 0).astype(int)
    macro_df = pd.DataFrame(macro)

    # Join onto each symbol
    out = {}
    for sym, df in features_by_sym.items():
        joined = df.join(macro_df, how='left')
        joined['symbol'] = sym
        out[sym] = joined
    return out

def build_panel():
    frames = load_ohlc()
    features = {}
    for sym in ['BTCUSDT','ETHUSDT','SOLUSDT','DOGEUSDT']:
        if sym in frames:
            features[sym] = build_features_single(frames[sym])
    features = attach_macro(features, frames)
    panel = pd.concat(features.values(), keys=features.keys(), names=['symbol','date'])
    return panel

if __name__ == '__main__':
    panel = build_panel()
    out_path = f'{BASE}/quant_factors/features.parquet'
    panel.to_parquet(out_path)
    print(f'saved {out_path}')
    print(f'shape: {panel.shape}')
    print(f'columns: {len(panel.columns)}')
    print(f'symbols: {panel.index.get_level_values(0).unique().tolist()}')
    print(f'date range: {panel.index.get_level_values(1).min()} → {panel.index.get_level_values(1).max()}')
    # Peek at BTC latest
    btc = panel.loc['BTCUSDT'].tail(3)
    cols_peek = ['close','ma200','rsi14','adx14','bb_width','rv30','price_above_ma200','ma50_above_ma200']
    print('\nLast 3 BTC rows (selected cols):')
    print(btc[cols_peek].to_string())
