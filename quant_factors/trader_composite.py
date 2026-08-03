#!/usr/bin/env python3
"""Turn each of 90 trader profiles into a weighted factor composite.

Each trader profile lists capabilities_used with weights. Their 'composite signal'
at time t = sum(weight_i * factor_score_i(t)) for the factors they use.

Then we analyze:
- Which traders have the strongest forward-IC on their own composite?
- Which traders' self-description aligns with factor reality vs diverges?
- Cross-trader consensus at any given date = distribution of composite signals.
"""
import os, json, sys
import numpy as np
import pandas as pd
from scipy import stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from capabilities import CAP_REGISTRY

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
QF = os.path.join(BASE, 'quant_factors')
os.makedirs(QF, exist_ok=True)
FACTORS = pd.read_parquet(f'{QF}/factors.parquet')
print(f'factors panel: {FACTORS.shape}')

factor_cols = [c for c in FACTORS.columns if c.startswith('cap_')]
print(f'factor columns: {len(factor_cols)}')


def get_symbol():
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTCUSDT'
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        symbol += 'USDT'
    return symbol

SYMBOL = get_symbol()
print(f'building trader composite for symbol: {SYMBOL}')


def load_json(path: str):
    """Load JSON from disk with a fallback across common encodings."""
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'cp1252']
    last_error = None
    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as handle:
                return json.load(handle)
        except UnicodeDecodeError as exc:
            last_error = exc
    with open(path, 'r', encoding='utf-8', errors='replace') as handle:
        return json.load(handle)


# Load all 90 profiles
profiles = {}
prof_dir = f'{BASE}/profiles_v2'
for f in sorted(os.listdir(prof_dir)):
    if not f.endswith('.json'):
        continue
    p = load_json(f'{prof_dir}/{f}')
    profiles[f.replace('.json', '')] = p
print(f'profiles loaded: {len(profiles)}')

# For each trader, build their weight vector over factor_cols
# Profile weights use ids like cap_013_range_fade_high_low, but our registry has cap_013_range_fade
# Need fuzzy id match
def match_cap(profile_cap_id: str) -> str | None:
    """Map a profile's capability_id to a registered factor id."""
    if profile_cap_id in factor_cols:
        return profile_cap_id
    # Try prefix match on the id number
    # e.g. cap_013_range_fade_high_low -> cap_013_range_fade
    parts = profile_cap_id.split('_')
    if len(parts) >= 2 and parts[0] == 'cap' and parts[1].isdigit():
        prefix = f'cap_{parts[1]}'
        matches = [c for c in factor_cols if c.startswith(prefix + '_')]
        if matches:
            return matches[0]
    return None

# Build weight matrix: (trader, factor)
W = pd.DataFrame(0.0, index=sorted(profiles.keys()), columns=factor_cols)
mismatch_log = []
for handle, p in profiles.items():
    used = p.get('capabilities_used', []) or []
    for c in used:
        cid = c.get('id','')
        w = float(c.get('weight', 0))
        match = match_cap(cid)
        if match:
            W.loc[handle, match] += w
        else:
            mismatch_log.append((handle, cid))

# Also add weights from new_capabilities_proposed → emg_ factors
# Look up which emg_ factor came from which trader via emerged_caps_analysis
import os
emerged_path = f'{BASE}/emerged_caps_analysis.json'
if os.path.exists(emerged_path):
    emerged = load_json(emerged_path)
    # Build trader → emerged caps mapping
    # emg_ factors have ids like emg_001_quarterly_vwap which roughly correspond to a proposer
    # Look in clusters: each cluster has 'traders' field
    emg_factors_in_registry = [c for c in factor_cols if c.startswith('emg_')]
    # Match by name keyword: emg_NNN_xxx → cluster name with similar zh
    emg_to_traders = {}
    for emg_id in emg_factors_in_registry:
        # Use the cap_id suffix to find proposer
        # Default: assign weight to all traders whose proposed name appears in the emerged data
        suffix = '_'.join(emg_id.split('_')[2:]).lower()
        for cluster in emerged['clusters']:
            rep = cluster['representative']
            name = (rep.get('name','') + ' ' + rep.get('name_zh','')).lower()
            # Heuristic match: if any keyword from suffix in name
            if any(k in name for k in suffix.split('_') if len(k) > 3):
                emg_to_traders.setdefault(emg_id, []).extend(cluster['traders'])
                break
    # Assign default weight 0.7 to each emerged factor for its proposing trader
    emg_mapped = 0
    for emg_id, traders in emg_to_traders.items():
        for h in traders:
            if h in W.index:
                W.loc[h, emg_id] = max(W.loc[h, emg_id], 0.7)
                emg_mapped += 1
    print(f'Emerged factor → trader mappings added: {emg_mapped}')

print(f'\nTotal profile->factor mappings: {(W != 0).sum().sum()}')
print(f'Mismatches (profile used cap not in registry): {len(mismatch_log)}')

# Normalize each trader row so sum = 1 (equal total capital)
W_norm = W.div(W.abs().sum(axis=1).replace(0, 1), axis=0)

# factors.parquet is indexed by date with symbol column — filter to requested symbol
panel = FACTORS[FACTORS['symbol'] == SYMBOL]
factors_df = panel[factor_cols].fillna(0)

trader_signals = pd.DataFrame(index=panel.index, columns=W.index)
for handle in W.index:
    w = W_norm.loc[handle]
    trader_signals[handle] = factors_df.dot(w)

fwd_30d = panel['fwd_30d']
trader_ic = []
for handle in W.index:
    sig = trader_signals[handle]
    df = pd.concat([sig, fwd_30d], axis=1).dropna()
    if len(df) < 50:
        continue
    ic, pval = stats.spearmanr(df[handle], df['fwd_30d'])
    # Hit rate: when composite > 0.1 (long), forward 30d positive?
    long_signals = df[df[handle] > 0.1]['fwd_30d']
    short_signals = df[df[handle] < -0.1]['fwd_30d']
    trader_ic.append({
        'handle': handle,
        'school': profiles[handle].get('school_primary','?'),
        'bias_default': profiles[handle].get('bias_default','?'),
        'ic_30d': ic,
        'pval': pval,
        'n_obs': len(df),
        'mean_signal': df[handle].mean(),
        'std_signal': df[handle].std(),
        'long_signal_days': (df[handle] > 0.1).sum(),
        'short_signal_days': (df[handle] < -0.1).sum(),
        'hit_long_30d': (long_signals > 0).mean() if len(long_signals) > 0 else np.nan,
        'hit_short_30d': (short_signals < 0).mean() if len(short_signals) > 0 else np.nan,
    })

ic_df = pd.DataFrame(trader_ic).sort_values('ic_30d', ascending=False)
ic_df.to_csv(f'{BASE}/quant_factors/trader_composite_ic_{SYMBOL}.csv', index=False)

print('\n=== Top 15 traders by composite IC 30d (positive = self-description aligns with reality) ===')
for _, r in ic_df.head(15).iterrows():
    hl = f"{r['hit_long_30d']:.2f}" if not pd.isna(r['hit_long_30d']) else 'nan'
    hs = f"{r['hit_short_30d']:.2f}" if not pd.isna(r['hit_short_30d']) else 'nan'
    print(f"  @{r['handle'][:22]:22s} school={r['school'][:10]:10s} IC={r['ic_30d']:+.3f}  hit_L={hl}/{int(r['long_signal_days']):4d}  hit_S={hs}/{int(r['short_signal_days']):4d}  bias={r['bias_default'][:12]}")

print('\n=== Bottom 15 traders (composite reversed from reality) ===')
for _, r in ic_df.tail(15).iterrows():
    hl = f"{r['hit_long_30d']:.2f}" if not pd.isna(r['hit_long_30d']) else 'nan'
    hs = f"{r['hit_short_30d']:.2f}" if not pd.isna(r['hit_short_30d']) else 'nan'
    print(f"  @{r['handle'][:22]:22s} school={r['school'][:10]:10s} IC={r['ic_30d']:+.3f}  hit_L={hl}/{int(r['long_signal_days']):4d}  hit_S={hs}/{int(r['short_signal_days']):4d}  bias={r['bias_default'][:12]}")

# Save trader signal panel for later consensus rendering
trader_signals.to_parquet(f'{BASE}/quant_factors/trader_signals_{SYMBOL}.parquet')

print(f'\n=== Stats ===')
print(f'traders scored: {len(ic_df)}')
print(f'positive IC: {(ic_df["ic_30d"] > 0).sum()}')
print(f'negative IC: {(ic_df["ic_30d"] < 0).sum()}')
print(f'|IC| > 0.1: {(ic_df["ic_30d"].abs() > 0.1).sum()}')
print(f'\nsaved trader_composite_ic_{SYMBOL}.csv + trader_signals_{SYMBOL}.parquet')
