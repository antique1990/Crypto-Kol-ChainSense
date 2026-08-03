#!/usr/bin/env python3
"""Render interactive Plotly HTML: BTC candles + consensus box + trader lines."""
import os, json, sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

import argparse
parser = argparse.ArgumentParser(description='Render consensus HTML')
parser.add_argument('symbol', nargs='?', default='BTCUSDT', help='Symbol (BTCUSDT/ETHUSDT/SOLUSDT/DOGEUSDT)')
parser.add_argument('--output-dir', default=None, help='Custom output directory for HTML and snapshot JSON')
args = parser.parse_args()

SYMBOL = args.symbol.upper()
if not SYMBOL.endswith('USDT'):
    SYMBOL += 'USDT'

output_dir = args.output_dir or os.path.join(BASE, 'quant_factors')
os.makedirs(output_dir, exist_ok=True)

# Load data
features = pd.read_parquet(f'{BASE}/quant_factors/features.parquet')
factors = pd.read_parquet(f'{BASE}/quant_factors/factors.parquet')
signals = pd.read_parquet(f'{BASE}/quant_factors/trader_signals_{SYMBOL}.parquet')
ic_df = pd.read_csv(f'{BASE}/quant_factors/trader_composite_ic_{SYMBOL}.csv').set_index('handle')
snap = json.load(open(os.path.join(output_dir, f'consensus_snapshot_{SYMBOL}.json'), 'r', encoding='utf-8'))

symbol_feats = features.loc[SYMBOL].sort_index()
symbol_factors = factors[factors['symbol'] == SYMBOL].sort_index()

# Show last 240 days + project 30 days of consensus
lookback_days = 240
proj_days = 30
cutoff = symbol_feats.index[-1] - pd.Timedelta(days=lookback_days)
view = symbol_feats[symbol_feats.index >= cutoff].copy()

latest_date = symbol_feats.index[-1]
latest = symbol_feats.iloc[-1]
latest_close = float(symbol_feats.iloc[-1]['close'])
proj_end = latest_date + pd.Timedelta(days=proj_days)

# ============================================================
# Compute consensus bands from firing factors
# ============================================================
firing_factors = snap['firing_factors']
firing_dir = {}
for f in firing_factors:
    firing_dir[f['id']] = f['score']

# For each firing factor, look up historical fwd_30d distribution and compute implied price box
factor_cols = [c for c in symbol_factors.columns if c.startswith('cap_') or c.startswith('emg_')]
consensus_boxes = []
for cid, score in firing_dir.items():
    if cid not in factor_cols: continue
    direction = 'long' if score > 0 else 'short'
    # rows where factor had same sign
    matching = symbol_factors[symbol_factors[cid] * score > 0]
    fwds = matching['fwd_30d'].dropna()
    if len(fwds) < 5: continue
    p25 = fwds.quantile(0.25)
    p50 = fwds.quantile(0.5)
    p75 = fwds.quantile(0.75)
    hit = ((fwds > 0) if direction == 'long' else (fwds < 0)).mean()
    consensus_boxes.append({
        'cap_id': cid,
        'direction': direction,
        'score': score,
        'implied_low': latest_close * (1 + p25),
        'implied_mid': latest_close * (1 + p50),
        'implied_high': latest_close * (1 + p75),
        'hit_rate': float(hit),
        'n_hist': len(fwds),
    })

# Pool all factor boxes by direction, weight by (hit_rate * n_hist)
long_boxes = [b for b in consensus_boxes if b['direction'] == 'long']
short_boxes = [b for b in consensus_boxes if b['direction'] == 'short']

def pool_box(boxes):
    if not boxes: return None
    weights = np.array([b['hit_rate'] * np.log1p(b['n_hist']) for b in boxes])
    weights = np.where(weights <= 0, 0.01, weights)
    w = weights / weights.sum()
    return {
        'lo': float(np.average([b['implied_low'] for b in boxes], weights=w)),
        'mid': float(np.average([b['implied_mid'] for b in boxes], weights=w)),
        'hi': float(np.average([b['implied_high'] for b in boxes], weights=w)),
        'n': len(boxes),
    }

long_pool = pool_box(long_boxes)
short_pool = pool_box(short_boxes)

print(f'Long pool:  {long_pool}')
print(f'Short pool: {short_pool}')

# ============================================================
# Build figure
# ============================================================
display_symbol = SYMBOL[:-4] if SYMBOL.endswith('USDT') else SYMBOL
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    row_heights=[0.72, 0.28],
    vertical_spacing=0.04,
    subplot_titles=(f'{display_symbol}/USD · 共识 box （{latest_date.date()} @ ${latest_close:,.0f}）', '90 交易员 composite 信号 (IC ≥ +0.05)'),
)

# 1. Candlestick
fig.add_trace(
    go.Candlestick(
        x=view.index,
        open=view['open'], high=view['high'], low=view['low'], close=view['close'],
        name=display_symbol, increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
        showlegend=False,
    ),
    row=1, col=1,
)

# 2. Moving averages
for ma_col, color, w in [('ma50','#ffb74d', 1.2), ('ma200','#e57373', 1.4)]:
    fig.add_trace(
        go.Scatter(x=view.index, y=view[ma_col], mode='lines', name=ma_col.upper(),
                   line=dict(color=color, width=w), showlegend=True),
        row=1, col=1,
    )

# 3. Consensus boxes (rectangles projected forward)
proj_x = [latest_date, proj_end, proj_end, latest_date, latest_date]

if short_pool:
    fig.add_trace(
        go.Scatter(
            x=proj_x,
            y=[short_pool['lo'], short_pool['lo'], short_pool['hi'], short_pool['hi'], short_pool['lo']],
            fill='toself', fillcolor='rgba(239,83,80,0.16)',
            line=dict(color='rgba(239,83,80,0.5)', width=1),
            name=f'看空共识 box ({short_pool["n"]} 因子)',
            hovertext=f'空头共识 ${short_pool["lo"]:,.0f} ~ ${short_pool["hi"]:,.0f}<br>中枢 ${short_pool["mid"]:,.0f}',
            hoverinfo='text',
        ),
        row=1, col=1,
    )
    # Midline
    fig.add_trace(
        go.Scatter(
            x=[latest_date, proj_end],
            y=[short_pool['mid']]*2,
            mode='lines',
            line=dict(color='rgba(239,83,80,0.7)', width=2, dash='dash'),
            name=f'空头中枢 ${short_pool["mid"]:,.0f}',
            showlegend=False,
        ),
        row=1, col=1,
    )

if long_pool:
    fig.add_trace(
        go.Scatter(
            x=proj_x,
            y=[long_pool['lo'], long_pool['lo'], long_pool['hi'], long_pool['hi'], long_pool['lo']],
            fill='toself', fillcolor='rgba(38,166,154,0.14)',
            line=dict(color='rgba(38,166,154,0.5)', width=1),
            name=f'看多共识 box ({long_pool["n"]} 因子)',
            hovertext=f'多头共识 ${long_pool["lo"]:,.0f} ~ ${long_pool["hi"]:,.0f}<br>中枢 ${long_pool["mid"]:,.0f}',
            hoverinfo='text',
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[latest_date, proj_end],
            y=[long_pool['mid']]*2,
            mode='lines',
            line=dict(color='rgba(38,166,154,0.7)', width=2, dash='dash'),
            name=f'多头中枢 ${long_pool["mid"]:,.0f}',
            showlegend=False,
        ),
        row=1, col=1,
    )

# 4. Current price marker (horizontal line from today)
fig.add_trace(
    go.Scatter(
        x=[latest_date, proj_end],
        y=[latest_close, latest_close],
        mode='lines',
        line=dict(color='#ffffff', width=1.5, dash='dot'),
        name=f'当前 ${latest_close:,.0f}',
    ),
    row=1, col=1,
)

# 5. Bottom subplot: composite signals for top IC traders
top_traders = ic_df[ic_df['ic_30d'] > 0.05].sort_values('ic_30d', ascending=False).head(15).index.tolist()
school_colors = {
    'cycle': '#ffa726',
    'mixed': '#64b5f6',
    'pure_TA': '#ba68c8',
    'structural': '#4db6ac',
    'macro': '#90a4ae',
    'content_creator': '#f48fb1',
    'derivatives': '#81c784',
    'onchain': '#fff176',
    'contrarian': '#e57373',
}

for h in top_traders:
    if h not in signals.columns: continue
    sig_series = signals[h].loc[signals.index >= cutoff]
    school = ic_df.loc[h, 'school']
    color = school_colors.get(school, '#bdbdbd')
    ic_val = ic_df.loc[h, 'ic_30d']
    fig.add_trace(
        go.Scatter(
            x=sig_series.index, y=sig_series.values,
            mode='lines', name=f'{h} IC={ic_val:+.2f}',
            line=dict(color=color, width=1.3),
            opacity=0.85,
            hovertemplate=f'<b>{h}</b><br>%{{x|%Y-%m-%d}}: %{{y:.3f}}<extra></extra>',
        ),
        row=2, col=1,
    )

# Zero line on bottom
fig.add_hline(y=0, line_dash='dot', line_color='rgba(255,255,255,0.3)', row=2, col=1)

# Mean signal line
mean_sig = signals[top_traders].loc[signals.index >= cutoff].mean(axis=1)
fig.add_trace(
    go.Scatter(x=mean_sig.index, y=mean_sig.values, mode='lines', name='Top 15 均值',
               line=dict(color='#ffffff', width=2.5), opacity=0.95),
    row=2, col=1,
)

# Layout
fig.update_layout(
    template='plotly_dark',
    title=dict(
        text=f"<b>90 交易员共识预言机 · {display_symbol}/USD</b> &nbsp;·&nbsp; <span style='font-size:14px;color:#9ca3af'>量化因子合成 · {latest_date.date()}</span>",
        x=0.02, xanchor='left',
    ),
    height=860,
    xaxis_rangeslider_visible=False,
    legend=dict(orientation='v', yanchor='top', y=0.98, xanchor='left', x=1.02,
                bgcolor='rgba(0,0,0,0.3)', font=dict(size=10)),
    margin=dict(l=60, r=220, t=90, b=60),
    hovermode='x unified',
)
fig.update_yaxes(title_text=f'{display_symbol} Price (USD)', row=1, col=1)
fig.update_yaxes(title_text='Composite Signal', row=2, col=1, range=[-0.2, 0.2])
fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.08)')

# Big BULL/BEAR verdict banner
bias_val = snap['consensus']['trust_adjusted']
if bias_val < -0.01:
    verdict = 'BEARISH'
    verdict_color = '#ef5350'
    verdict_emoji = '🔴'
elif bias_val > 0.01:
    verdict = 'BULLISH'
    verdict_color = '#26a69a'
    verdict_emoji = '🟢'
else:
    verdict = 'NEUTRAL'
    verdict_color = '#9ca3af'
    verdict_emoji = '⚪'

eq = snap['consensus']['equal_weight']
fig.add_annotation(
    xref='paper', yref='paper', x=0.5, y=1.12,
    text=(
        f"<span style='font-size:28px;color:{verdict_color};font-weight:bold'>{verdict_emoji} {verdict}</span>"
        f"&nbsp;&nbsp;<span style='font-size:16px;color:#9ca3af'>Trust-adjusted: {bias_val:+.3f}</span>"
        f"<br><span style='font-size:13px;color:#d1d5db'>99 Traders: Long {eq['long']} · Short {eq['short']} · Neutral {eq['neutral']}</span>"
    ),
    showarrow=False, font=dict(size=14), align='center',
)

# Stats panel (left side)
schools = snap.get('by_school', {})
school_lines = []
for s, d in sorted(schools.items(), key=lambda x: x[1].get('mean_signal', 0)):
    if d['count'] < 3: continue
    ms = d['mean_signal']
    arrow = '🔴' if ms < -0.02 else '🟢' if ms > 0.02 else '⚪'
    school_lines.append(f"{arrow} {s}: {d['count']}人 avg={ms:+.3f}")

firing_lines = []
for ff in snap['firing_factors']:
    d = '🔴' if ff['score'] < 0 else '🟢'
    name = ff['id'].replace('cap_','').replace('emg_','')[:25]
    firing_lines.append(f"{d} {name} {ff['score']:+.2f}")

annotation_text = (
    f"<b>触发因子 ({len(snap['firing_factors'])})</b><br>"
    + '<br>'.join(firing_lines[:8])
    + f"<br><br><b>流派共识</b><br>"
    + '<br>'.join(school_lines[:6])
)
fig.add_annotation(
    xref='paper', yref='paper', x=0.01, y=0.65,
    text=annotation_text, showarrow=False,
    font=dict(size=10, color='#e5e7eb'),
    align='left', bgcolor='rgba(0,0,0,0.6)', bordercolor='rgba(255,255,255,0.15)',
    borderwidth=1, borderpad=8,
)

# Save a self-contained, presentation-ready HTML report. Plotly is embedded so
# the file can be opened on another computer without internet access.
out_html = os.path.join(output_dir, f'consensus_snapshot_{SYMBOL}.html')
chart_html = fig.to_html(
    full_html=False,
    include_plotlyjs=True,
    config={'displaylogo': False, 'responsive': True, 'scrollZoom': True},
)
active_factor_rows = ''.join(
    f"<div class='factor'><span class='dot {'up' if f['score'] > 0 else 'down'}'></span>"
    f"<span>{f['id']}</span><strong>{f['score']:+.2f}</strong></div>"
    for f in snap['firing_factors'][:10]
)
report_html = f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{display_symbol} Consensus Report — {latest_date.date()}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#08101f;color:#e5edf8;font-family:Inter,Segoe UI,Arial,sans-serif}}
.shell{{max-width:1480px;margin:auto;padding:36px 32px 48px}} .eyebrow{{color:#38bdf8;font-size:12px;font-weight:700;letter-spacing:.14em}}
h1{{margin:8px 0 6px;font-size:32px;letter-spacing:-.04em}} .sub{{color:#8fa1b9;font-size:14px}}
.top{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;border-bottom:1px solid #223049;padding-bottom:26px}}
.verdict{{text-align:right;color:{verdict_color};font-size:21px;font-weight:800;letter-spacing:.08em}} .verdict small{{display:block;color:#8fa1b9;font-size:12px;letter-spacing:0;margin-top:6px;font-weight:500}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:24px 0}} .card{{background:#101b30;border:1px solid #223049;border-radius:12px;padding:16px}}
.label{{font-size:11px;letter-spacing:.08em;color:#8fa1b9;font-weight:700}} .metric{{font-size:22px;font-weight:750;margin-top:8px}} .positive{{color:#34d399}} .negative{{color:#fb7185}}
.section{{background:#101b30;border:1px solid #223049;border-radius:14px;padding:18px;margin-top:16px}} .section h2{{font-size:14px;margin:0 0 14px;letter-spacing:.04em}}
.factor-list{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 20px}} .factor{{display:flex;gap:9px;align-items:center;font-family:ui-monospace,Consolas,monospace;font-size:12px;color:#bfcee1}} .factor strong{{margin-left:auto;color:#e5edf8}} .dot{{width:8px;height:8px;border-radius:99px;display:inline-block}} .up{{background:#34d399}} .down{{background:#fb7185}}
.chart{{padding:6px 0 0}} .foot{{color:#64748b;font-size:11px;margin:22px 0 0;text-align:center}}
@media(max-width:760px){{.shell{{padding:22px 14px}}.top{{display:block}}.verdict{{text-align:left;margin-top:18px}}.grid{{grid-template-columns:repeat(2,1fr)}}.factor-list{{grid-template-columns:1fr}}}}
</style></head><body><main class='shell'>
<header class='top'><div><div class='eyebrow'>CRYPTO CONSENSUS · QUANTITATIVE MARKET BRIEF</div><h1>{display_symbol} / USD</h1><div class='sub'>Snapshot date {latest_date.date()} · 30-day factor consensus horizon</div></div>
<div class='verdict'>{verdict}<small>Trust-adjusted bias {bias_val:+.3f}</small></div></header>
<section class='grid'><div class='card'><div class='label'>LAST PRICE</div><div class='metric'>${latest_close:,.0f}</div></div>
<div class='card'><div class='label'>TRADER CONSENSUS</div><div class='metric'>{eq['long']} / {eq['short']} / {eq['neutral']}</div><div class='sub'>Long / Short / Neutral</div></div>
<div class='card'><div class='label'>ACTIVE FACTORS</div><div class='metric'>{len(firing_factors)}</div><div class='sub'>Signals above activation threshold</div></div>
<div class='card'><div class='label'>30D RETURN</div><div class='metric {'positive' if latest['ret_30d'] >= 0 else 'negative'}'>{latest['ret_30d'] * 100:+.1f}%</div><div class='sub'>Latest observed return</div></div></section>
<section class='section'><h2>ACTIVE FACTORS</h2><div class='factor-list'>{active_factor_rows or '<span class="sub">No factors exceeded the activation threshold.</span>'}</div></section>
<section class='section chart'><h2>PRICE, CONSENSUS RANGE &amp; TRADER SIGNALS</h2>{chart_html}</section>
<p class='foot'>Generated by Crypto Consensus Terminal. This report is analytical information, not investment advice.</p>
</main></body></html>"""
with open(out_html, 'w', encoding='utf-8') as handle:
    handle.write(report_html)
print(f'\nsaved {out_html}')
print(f'file size: {os.path.getsize(out_html)//1024} KB')
