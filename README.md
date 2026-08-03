# 锁妖塔 Skill —— 炼化 99 个加密交易员

把 99 个顶级加密交易员的推特"关进锁妖塔"，用 LLM 炼出他们的交易直觉，变成 87 个可回测的量化因子。

每天问一句"大家怎么看"，99 个交易员同时告诉你方向。

## 炼了什么

| 原料 | 数量 |
|---|---|
| S 级交易员 | 99 人（从 1000+ 候选中三轮筛选） |
| 推文 | 39,843 条（2024-01 → 2026-04） |
| K 线截图 | 17,657 张（1.7 GB） |
| 蒸馏 profile | 99 份（每人 15-25 个能力 + 口头禅 + 信心词汇） |
| 能力库 | 470 条（70 种子 + 400 涌现） |
| 量化因子 | 87 个 Python 评估器 |
| 价格数据 | 832 天日线 × BTC/ETH/SOL/DOGE + DXY/黄金/美债/SPX |

## 炼出了什么

### 87 个量化因子，16 个统计显著

从 99 人的推文和图表里提取出 470 个"交易直觉"（比如"200 周均线附近机械买入"、"4 年周期派发阶段做空"、"假突破后反手"），然后把它们转成 Python 规则，在 832 天历史上回测 IC（信息系数）。

**最强 5 个因子：**

| 因子 | IC | 来源交易员 | 说明 |
|---|---|---|---|
| 200W MA 价值区 | **+0.297** (SOL) | @LedgerStatus | 价格在 200 周均线附近 = 历史级买点 |
| 200W MA 机械买 | **+0.220** (BTC) | @IvanOnTech | 触碰 200 周均线直接买，不想理由 |
| 4 年周期论 | **+0.201** (BTC) | @rektcapital | 减半后 18 月进入派发/熊段 |
| OHLC 锚点 | **+0.109** | @KillaXBT | 周开盘价作为日内支撑阻力 |
| 强势下行趋势 | **+0.098** | @DrProfitCrypto | 价格在 200 日均线下方 + 死叉 |

**最强反指因子（应反向使用）：**

| 因子 | IC | 说明 |
|---|---|---|
| 黄金避险 | **-0.218** (SOL) | 黄金大涨时做多 BTC？错！BTC 常脱钩下跌 |
| 强势上升趋势 | **-0.100** (BTC) | "趋势跟随做多"在周期后段反而是见顶信号 |

### 99 个交易员的信任分

每个交易员的"自述经验"被量化为一个 composite signal，和历史走势做回归：

- **58 人正 IC**（自述方法和真实盈亏方向一致 → 可以跟）
- **41 人负 IC**（自述方向和真实方向相反 → 当反指用）
- **21 人 |IC| > 0.1**（强信号）

**最值得跟的 5 人：**
@Yodaskk (+0.145) · @dpuellARK (+0.110) · @AnalysisElliott (+0.106) · @Tree_of_Alpha (+0.103) · @ToneVays (+0.099)

**最强反指 5 人：**
@christiaandefi (-0.201) · @shufen46250836 (-0.180) · @WClementeIII (-0.158) · @Engineercryptoo (-0.157) · @GugaOnChain (-0.143)

### 实时共识输出

跑一次 `/consensus`，输出：

1. **🔴 BEARISH / 🟢 BULLISH** 大字判定
2. 99 人投票：多 X / 空 X / 中性 X
3. 30 天隐含价格区间（多头 box + 空头 box）
4. 当前触发的因子列表
5. 交互式 K 线图（Plotly HTML）
6. 交易员信号面板

### 回测验证

**BTC 日线（近 7 天）：**
- 跟信号方向：胜率 57%，$1000 → $1079（+7.9%）

**BTC 剥头皮（日线定方向 × 5m 入场）：**
- 日线共识做方向过滤 → 胜率从 50% 提升到 59%（+9%）
- 盈亏比 1.28

## 使用方式

**方式 1：Claude Code skill**
```
/consensus              # 用缓存数据（秒出）
/consensus --refresh-ohlc  # 拉最新 Binance 行情
/consensus eth           # 看 ETH
```

**方式 2：直接跑 Python**
```bash
python3 quant_factors/run_consensus.py --refresh-ohlc
# 输出 consensus_snapshot.html + consensus_snapshot.json
```

## 可扩展

- **加交易员**：跑 codex 蒸馏 → 自动进因子库
- **加数据源**：Binance perpetual (funding/OI) / Glassnode (MVRV/NVT) / FRED (M2/PMI) → 激活 20 个 mock 因子
- **加自定义因子**：在 capabilities/ 里写 Python 函数即可
- **多时间框架**：接 5m K 线 → 剥头皮模式

## 文件结构

```
├── quant_factors/
│   ├── run_consensus.py        # 一键运行
│   ├── feature_engine.py       # 88 特征
│   ├── capabilities/           # 87 个因子评估器
│   ├── backtest.py             # IC 回测
│   ├── trader_composite.py     # 信任分
│   ├── consensus_now.py        # 共识快照
│   └── render_consensus.py     # Plotly 渲染
├── profiles_v2/                # 99 份交易员 profile
├── capabilities_v1.json        # 470 条能力库
├── ohlc_daily.json             # 价格数据
└── macro_daily.json            # 宏观数据
```

## ⚠️ 声明

这是研究项目，不是交易建议。回测 ≠ 实盘。7 天样本不具统计意义。请自行承担风险。

## License

MIT
