#!/usr/bin/env python3
"""Walk through the features panel, evaluate all capabilities as factors,
compute IC (Spearman correlation with forward returns) per factor per horizon."""
import sys, os
import json
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(__file__))
from capabilities import CAP_REGISTRY

BASE = os.path.expanduser('~/shared/materials/crypto_traders_distill')
FEATURES = pd.read_parquet(f'{BASE}/quant_factors/features.parquet')
print(f'features: {FEATURES.shape}')

def run_factors(feats: pd.DataFrame) -> pd.DataFrame:
    """Evaluate every registered capability on a features DataFrame.
    Returns columns = factor scores (signed, float)."""
    out = {}
    for cid, meta in CAP_REGISTRY.items():
        try:
            res = meta['fn'](feats)
            if hasattr(res, 'score'):
                score = res.score
            elif isinstance(res, dict):
                score = res.get('score', 0)
            else:
                score = res
            if hasattr(score, '__len__') and len(score) == len(feats):
                out[cid] = np.asarray(score, dtype=float)
            else:
                out[cid] = np.full(len(feats), float(score) if np.isscalar(score) else 0.0)
        except Exception as e:
            out[cid] = np.zeros(len(feats))
    return pd.DataFrame(out, index=feats.index)

# Build factor panel per symbol
all_factors = []
for sym in FEATURES.index.get_level_values(0).unique():
    sub = FEATURES.loc[sym].copy()
    fac = run_factors(sub)
    fac['symbol'] = sym
    fac['fwd_1d'] = sub['fwd_ret_1d']
    fac['fwd_7d'] = sub['fwd_ret_7d']
    fac['fwd_30d'] = sub['fwd_ret_30d']
    all_factors.append(fac)
panel = pd.concat(all_factors)
print(f'factor panel: {panel.shape}')

out_path = f'{BASE}/quant_factors/factors.parquet'
panel.to_parquet(out_path)
print(f'saved {out_path}')

# IC analysis
factor_cols = [c for c in panel.columns if c.startswith('cap_') or c.startswith('emg_')]
results = []
for fc in factor_cols:
    row = {'factor': fc, 'type': CAP_REGISTRY[fc]['type'], 'impl': CAP_REGISTRY[fc]['impl']}
    for h in ['fwd_1d','fwd_7d','fwd_30d']:
        df = panel[[fc, h]].dropna()
        if len(df) < 20 or df[fc].nunique() < 2:
            row[f'ic_{h}'] = np.nan
            row[f'n_{h}'] = 0
            continue
        ic, pval = stats.spearmanr(df[fc], df[h])
        row[f'ic_{h}'] = ic
        row[f'pval_{h}'] = pval
        row[f'n_{h}'] = len(df)
        # Triggers
        row[f'trig_count'] = (df[fc].abs() > 0.01).sum()
    # Hit rate: when factor signals long, was forward return positive?
    df_long = panel[(panel[fc] > 0.1)][['fwd_30d']].dropna()
    df_short = panel[(panel[fc] < -0.1)][['fwd_30d']].dropna()
    row['n_long_signals'] = len(df_long)
    row['n_short_signals'] = len(df_short)
    row['hit_rate_long_30d'] = (df_long['fwd_30d'] > 0).mean() if len(df_long) > 0 else np.nan
    row['hit_rate_short_30d'] = (df_short['fwd_30d'] < 0).mean() if len(df_short) > 0 else np.nan
    results.append(row)

ic_df = pd.DataFrame(results)
ic_df.to_csv(f'{BASE}/quant_factors/ic_results.csv', index=False)

# Print best and worst factors by IC 30d
ic_sorted = ic_df[ic_df['n_fwd_30d'] > 20].sort_values('ic_fwd_30d', ascending=False)

def _fmt_pct(x):
    return f'{x:.2f}' if not pd.isna(x) else 'nan'

print('\n=== Top 15 factors by 30d IC (positive = follow signal) ===')
for _, r in ic_sorted.head(15).iterrows():
    hl = _fmt_pct(r['hit_rate_long_30d'])
    hs = _fmt_pct(r['hit_rate_short_30d'])
    print(f"  {r['factor'][:38]:38s} IC={r['ic_fwd_30d']:+.3f}  hit_L={hl}/{int(r['n_long_signals'] or 0):4d}  hit_S={hs}/{int(r['n_short_signals'] or 0):4d}")

print('\n=== Bottom 15 factors by 30d IC (negative = reverse signal) ===')
for _, r in ic_sorted.tail(15).iterrows():
    hl = _fmt_pct(r['hit_rate_long_30d'])
    hs = _fmt_pct(r['hit_rate_short_30d'])
    print(f"  {r['factor'][:38]:38s} IC={r['ic_fwd_30d']:+.3f}  hit_L={hl}/{int(r['n_long_signals'] or 0):4d}  hit_S={hs}/{int(r['n_short_signals'] or 0):4d}")

# Summary stats
print(f'\n=== Summary ===')
print(f'Total factors: {len(ic_df)}')
print(f'Factors with signal (n_trig>20): {(ic_df["n_fwd_30d"]>20).sum()}')
print(f'Factors with |IC|>0.05: {((ic_df["ic_fwd_30d"].abs()>0.05) & (ic_df["n_fwd_30d"]>20)).sum()}')
print(f'Factors with |IC|>0.1: {((ic_df["ic_fwd_30d"].abs()>0.1) & (ic_df["n_fwd_30d"]>20)).sum()}')
