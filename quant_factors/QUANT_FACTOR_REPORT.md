# 量化因子提取报告

**生成日期**: 2026-04-12  
**数据基础**: 99 个 S 级交易员 profile + 70 seed 能力 + 400 涌现能力 = 470 候选因子

## 一、当前激活的因子库

共 **71 个 Python 因子评估器**已实现，划分为：

| 类型 | 数量 | rule | approx | mock |
|---|---|---|---|---|
| pattern_setup | 26 | 0 | 26 | 0 |
| indicator_rule | 15 | 13 | 2 | 0 |
| structural_bias | 11 | 1 | 9 | 1 |
| macro_correlation | 7 | 4 | 0 | 3 |
| derivatives_signal | 7 | 0 | 0 | 7 |
| regime_classifier | 5 | 5 | 0 | 0 |
| cycle_time | 5 | 5 | 0 | 0 |
| onchain_signal | 5 | 0 | 0 | 5 |
| risk_rule | 4 | 2 | 0 | 2 |
| event_reaction | 2 | 0 | 0 | 2 |

- **rule** = 直接规则实现
- **approx** = LLM 形态识别的规则近似
- **mock** = 等待外部数据源的占位（funding/onchain/event 等）

## 二、IC 显著的因子（|IC 30d| > 0.05）

共 **16** 个统计显著的因子：

| 因子 | 类型 | IC 30d | hit_long | hit_short | n_long | n_short |
|---|---|---|---|---|---|---|
| **emg_029_200w_value_zone** (emg_029_200w_value_zone) | indicator_rule | **+0.178** | 0.63 | - | 809 | 0 |
| **emg_022_200w_mechanical_buy** (emg_022_200w_mechanical_buy) | indicator_rule | **+0.158** | 0.65 | - | 537 | 0 |
| **4 年周期论** (cap_038_4year_cycle) | cycle_time | **+0.146** | 0.51 | 0.73 | 1440 | 612 |
| **cap_037_halving_cycle** (cap_037_halving_cycle) | cycle_time | **+0.125** | 0.51 | 0.58 | 1440 | 1048 |
| **emg_027_ohlc_anchor_framework** (emg_027_ohlc_anchor_framework) | structural_bias | **+0.109** | 0.53 | 0.62 | 691 | 684 |
| **强势下降趋势** (cap_045_regime_trending_down) | regime_classifier | **+0.098** | - | 0.60 | 0 | 658 |
| **emg_014_horizontal_reclaim** (emg_014_horizontal_reclaim) | indicator_rule | **+0.084** | 0.58 | - | 276 | 0 |
| **emg_023_monthly_seasonality** (emg_023_monthly_seasonality) | cycle_time | **+0.071** | 0.48 | 0.52 | 1272 | 852 |
| **emg_028_20w_200w_double_reclaim** (emg_028_20w_200w_double_reclai) | indicator_rule | **+0.068** | 0.63 | - | 108 | 0 |
| **金叉（50/200 均线）** (cap_018_ma_golden_cross) | indicator_rule | **+0.065** | 0.83 | - | 12 | 0 |
| **emg_007_htf_reclaim_retest** (emg_007_htf_reclaim_retest) | structural_bias | **+0.053** | 0.59 | - | 76 | 0 |
| **降息降收益率 → 流动性改善** (cap_029_yields_liquidity) | macro_correlation | **-0.097** | 0.41 | - | 744 | 0 |
| **强势上升趋势** (cap_044_regime_trending_up) | regime_classifier | **-0.100** | 0.40 | - | 710 | 0 |
| **cap_013_range_fade** (cap_013_range_fade) | pattern_setup | **-0.101** | 0.63 | 0.26 | 54 | 136 |
| **cap_050_three_drives** (cap_050_three_drives) | pattern_setup | **-0.106** | - | 0.36 | 0 | 251 |
| **cap_030_gold_safe_haven** (cap_030_gold_safe_haven) | macro_correlation | **-0.181** | 0.39 | - | 788 | 0 |

### 解读

- **正 IC** = 信号方向预测正确（顺向使用）
- **负 IC** = 信号方向被打脸（应反向使用，作为反指）
- 当前样本期 (2024-01 ~ 2026-04) 处于减半周期 18+ 月段，**周期因子最强**：cap_038 4年周期 IC=+0.146 / cap_037 减半周期 IC=+0.125
- **趋势跟随因子（cap_044 强势上升趋势）反向**：在周期后段触发往往是顶部信号
- **黄金避险因子（cap_030）IC=-0.181**：黄金大涨时 BTC 常脱钩下跌，是真实统计反指

## 三、交易员 composite trust score

**99 个交易员**的 self-described composite signal 历史 IC：

- 正 IC: **58** 人（自述方法学与因子真相一致）
- 负 IC: **41** 人（自述方向与因子真相相反，反指）
- |IC| > 0.1: **21** 人（强信号）

### Top 10 高信任交易员（应顺向跟）

| 排名 | Handle | 流派 | IC 30d | 自述 bias |
|---|---|---|---|---|
| 1 | @Yodaskk | mixed | **+0.145** | contrarian |
| 2 | @dpuellARK | mixed | **+0.110** | long_tilted |
| 3 | @AnalysisElliott | cycle | **+0.106** | long_tilted |
| 4 | @Tree_of_Alpha | mixed | **+0.103** | contrarian |
| 5 | @ToneVays | mixed | **+0.099** | contrarian |
| 6 | @pierre_crypt0 | pure_TA | **+0.099** | neutral |
| 7 | @Jiangzhuoer2 | cycle | **+0.098** | long_tilted |
| 8 | @KillaXBT | mixed | **+0.097** | contrarian |
| 9 | @ChartsBTC | cycle | **+0.093** | long_tilted |
| 10 | @inmortalcrypto | cycle | **+0.093** | long_tilted |

### Top 10 反指交易员（应反向用）

| 排名 | Handle | 流派 | IC 30d | 自述 bias |
|---|---|---|---|---|
| 1 | @christiaandefi | mixed | **-0.201** | long_tilted |
| 2 | @shufen46250836 | mixed | **-0.180** | long_tilted |
| 3 | @WClementeIII | macro | **-0.158** | long_tilted |
| 4 | @Engineercryptoo | mixed | **-0.157** | long_tilted |
| 5 | @GugaOnChain | onchain | **-0.143** | neutral |
| 6 | @fundstrat | mixed | **-0.142** | long_tilted |
| 7 | @Sheldon_Sniper | pure_TA | **-0.142** | long_tilted |
| 8 | @CryptoCred | mixed | **-0.140** | neutral |
| 9 | @CastilloTrading | structural | **-0.128** | long_tilted |
| 10 | @ColdBloodShill | mixed | **-0.126** | long_tilted |

## 四、涌现能力中最适合"量化化"的 Top 30

99 profile 总共涌现 **400** 个新能力（不在 seed 库里）。下面按"可量化得分"排序，建议优先转 Python rule：

| # | 能力 | 类型 | 提议人 | 简述 |
|---|---|---|---|---|
| 1 | **季度 VWAP 磁吸位** | indicator_rule | @AnalysisElliott | 使用锚定/季度 VWAP 作为被防守的支撑与未触及的价格磁吸位，给出短中期方向框架。 |
| 2 | **期权成交量远超未平仓量异动** | derivatives_signal | @BullTheoryio | 识别同日或超短期期权在多个相邻执行价上出现“成交量显著高于未平仓量”的情况，作为新仓大举进场或情绪/信息流异动信号。 |
| 3 | **大宗商品逆风估值过滤器** | macro_correlation | @BullTheoryio | 把高油价等投入成本压力当作宏观过滤器：当商品价格过高时，不追逐股票 beta，只在大跌日分批买入。 |
| 4 | **抬高低点防守** | structural_bias | @CastilloTrading | 只要抬高低点结构还在，即使市场情绪偏空、价格尚未突破关键阻力，也维持偏多判断。 |
| 5 | **同日跨周期对照** | cycle_time | @ChartsBTC | 把当前日期与 4/8/12 年前同一天对照，比较价格、CAGR 和周期位置，用于估算当前所处阶段和潜在路径。 |
| 6 | **价格区间停留时长** | cycle_time | @ChartsBTC | 统计比特币在各价格区间停留的天数，用于判断成熟度、价值接受度，以及向下一数量级价格区间迁移的概率。 |
| 7 | **高周期水平位收复与回踩确认** | structural_bias | @ColdBloodShill | 价格收复关键周线/3日水平位，收盘站上后回踩确认支撑，再做趋势延续判断。 |
| 8 | **周线50EMA牛熊分界支撑** | indicator_rule | @CrypNuevo | 将 1W50EMA 作为最核心的牛市支撑/熊市阻力。价格对该均线的反应决定是否做波段多、减仓，或等待收复确认。 |
| 9 | **区间中部禁做过滤器** | risk_rule | @CryptoCred | 当价格位于清晰区间中部、上下边界都不占优时，主动空仓，等待到区间边缘或等待突破解决方向。 |
| 10 | **扩张楔形突破** | pattern_setup | @CryptoFaibik | 价格在两条发散趋势线之间震荡，最终向上或向下突破；目标通常取形态最宽处做投射。 |
| 11 | **多头三角旗突破** | pattern_setup | @CryptoFaibik | 强势拉升后，价格缩进为小型收敛三角旗，向上突破后延续原趋势。 |
| 12 | **对称三角形突破** | pattern_setup | @CryptoFaibik | 价格在抬高低点与降低高点之间收敛，对称三角形突破方向决定后续偏向。 |
| 13 | **箱体整理后突破** | pattern_setup | @CryptoMichNL | 冲高后进入清晰水平箱体，反复测试阻力或守住支撑，表示蓄势待突破；目标通常看向更高周期的下一个阻力区。 |
| 14 | **水平关键位收复入场** | indicator_rule | @CryptoTony__ | 把前期失守或反复争夺的水平位作为核心触发条件，只有在价格重新收复并最好收盘站稳后才入场。 |
| 15 | **比特币生产成本底部框架** | onchain_signal | @DrProfitCrypto | 把比特币生产成本当作估值底部。现货跌破生产成本时，视为历史上不对称的做多机会。 |
| 16 | **交易所内部转账甄别** | onchain_signal | @EmberCN | 区分真实的入所/出所与交易所内部热冷钱包调拨、钱包重平衡、跨链中转，避免把内部转账误判成真实买卖信号。 |
| 17 | **关键位破位确认后做目标投射** | pattern_setup | @GarethSoloway | 先定义重大支撑/阻力区，等待日线收盘或确认破位，再推演下一目标区，而不是抢跑预判。 |
| 18 | **土狗筹码质量筛选** | onchain_signal | @GuruMemeCoin | 在做 memecoin 之前，先看狙击比例、捆绑持仓、创建者占比、内幕/集群集中度、持有人结构和平台用户等筹码质量指标。 |
| 19 | **OBV 领先确认** | indicator_rule | @IncomeSharks | 把 OBV 当作领先指标使用：OBV 先突破或先走强，则预期价格随后跟进；若 OBV 走弱或背离，则不追多或分批减仓。 |
| 20 | **上涨分批止盈** | risk_rule | @IncomeSharks | 不是一次性清仓，而是在目标位、突破后拉升段、情绪过热区按固定比例分批止盈。 |
| 21 | **CME 缺口回补磁吸** | event_reaction | @IvanOnTech | 把 BTC CME 期货缺口视为未完成目标位。价格回补缺口后，认为市场‘清障完成’，随后应启动新的趋势推进。 |
| 22 | **200 周均线机械接多** | indicator_rule | @IvanOnTech | 把 200 周均线当作预先设定的机械化接多区域，不依赖主观盘中判断，属于周期级别的规则化吸筹。 |
| 23 | **月份季节性看涨框架** | cycle_time | @JakeGagain | 把特定月份或日历窗口直接当作行情催化，先给出方向性看涨判断，图表确认反而是次要的。 |
| 24 | **流动性到 BTC 的滞后传导模型** | macro_correlation | @Jamie1Coutts | 用固定或自适应滞后来建模流动性扩张/收缩对 BTC 的传导，通常把比特币视为全球货币扩张的延迟高 beta 表达。 |
| 25 | **算力恢复均线交叉** | indicator_rule | @Jamie1Coutts | 用比特币算力恢复及短长均线交叉作为网络健康和趋势恢复信号。 |
| 26 | **期货与现货指数背离** | structural_bias | @JamieSaettele | 当股指期货创新高但现货指数不确认时，视为行情末端衰竭或拐点预警。 |
| 27 | **开收盘锚点位框架** | structural_bias | @KillaXBT | 把日/周/月/季/年开收盘与影线高低点当作核心结构锚点，用于验证、拒绝和反转判断。 |
| 28 | **20周/200周均线重夺** | indicator_rule | @LedgerStatus | 价格在回调后同时重新站上 20 周均线和 200 周均线，把这种“双均线重夺”视为历史上较优的风险暴露窗口。 |
| 29 | **200周均线深度价值买区** | indicator_rule | @LedgerStatus | 当主流币触及或略微跌破 200 周均线时，将其视为长期统计意义上的优质吸筹区。 |
| 30 | **高周期收盘锚定框架** | structural_bias | @MacroCRG | 把周线、月线、季度线收盘视为趋势确认核心节点；强收盘提高趋势延续概率，弱收盘则降低信心或等待确认。 |

## 五、关键缺口（mock 因子待数据源）

20 个能力等待外部数据接入，激活后预计将显著增强因子库：

### 衍生品（7）— 需要 Binance perpetual API
cap_031/032 资金费率极值, cap_033 OI 爬升, cap_034 清算热力图, cap_059 资金费/价格背离, cap_060 基差爆表, cap_061 期权 skew

### 链上（5）— 需要 Glassnode / CryptoQuant
cap_035 大额入所, cap_036 LTH 持有, cap_066 稳定币供应, cap_067 NVT, cap_068 MVRV Z

### 宏观（3）— 需要 FRED
cap_062 全球 M2, cap_063 ISM PMI, cap_064 信用利差

### 事件（2）— 需要 economic calendar
cap_039 FOMC 周, cap_040 ETF 资金流

