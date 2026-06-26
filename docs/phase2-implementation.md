# Phase 2: 回放系统 + 玩家画像与统计引擎 实施文档

> **前置**: Phase 1 MVP 完成
>
> **目标**: 完善牌局回放体验 + 建立玩家长期画像 + HUD 统计展示
>
> **周期**: 4 周
>
> **版本**: V1.0

---

## 1. 任务拆解总表

| 编号 | 任务 | 归属 | 周 | 预计工时 | 前置依赖 |
|------|------|------|-----|---------|---------|
| P2.1 | Replay Engine 重构（从 MVP 基础版升级） | Backend | W1 | 8h | Phase1 T5.2 |
| P2.2 | Replay 页面增强（逐行动播放 + 动画过渡 + 牌桌渲染） | Frontend | W1-W2 | 12h | Phase1 T5.1 |
| P2.3 | EV 图表增强（多维度对比 + 交互缩放） | Frontend | W2 | 6h | P2.2 |
| P2.4 | Profile Engine 核心算法（VPIP/PFR/3Bet 等统计计算） | Backend | W2 | 10h | Phase1 DB |
| P2.5 | 玩家自动分类引擎（Nit/TAG/LAG/Fish/Calling Station/Maniac） | Backend | W3 | 6h | P2.4 |
| P2.6 | HUD 组件（浮动统计面板 + 实时更新） | Frontend | W3 | 8h | P2.4 |
| P2.7 | 玩家画像展示页（详细统计 + 趋势图 + 分类标签） | Frontend | W3-W4 | 10h | P2.4, P2.5 |
| P2.8 | 画像 API（CRUD + 批量查询 + 刷新触发） | Backend | W3 | 6h | P2.4 |
| P2.9 | 画像数据聚合（Session 级别 + 全局级别） | Backend | W4 | 5h | P2.4 |
| P2.10 | 集成测试 + 性能优化（Profile 计算异步化） | 全栈 | W4 | 8h | 全部 |

**总计**: 约 79 工时

---

## 2. 回放系统增强

### 2.1 从 MVP 基础版升级

MVP 回放仅支持按 Street 分步（PREFLOP/FLOP/TURN/RIVER），Phase 2 升级为**逐行动回放**：

```
MVP 级别:  [Preflop] → [Flop] → [Turn] → [River]
Phase 2:   [Raise 2.5bb] → [Call] → [Check] → [Bet 33%] → [Raise] → ...
```

### 2.2 前端组件设计

```
ReplayPage
├── ReplayHeader
│   ├── HandSummary (手牌 + 公共牌)
│   └── SpeedControl (1x / 2x / 4x)
│
├── ReplayMain
│   ├── TableCanvas (SVG/Canvas 牌桌渲染)
│   │   ├── CommunityCards (5个卡位)
│   │   ├── SeatPosition × 6 (各玩家座位)
│   │   │   ├── PlayerAvatar
│   │   │   ├── HoleCards (仅 Hero 可见)
│   │   │   ├── ChipStack (筹码堆)
│   │   │   └── ActionBadge (当前行动标记)
│   │   └── PotDisplay (底池金额)
│   │
│   └── ActionLog (右侧行动日志，高亮当前步)
│
├── ReplayControls
│   ├── PlayPauseButton
│   ├── StepForward / StepBackward
│   ├── JumpToStreet (跳转到指定 Street)
│   ├── ProgressBar (进度条，可拖拽)
│   └── ActionDescription (当前行动描述文字)
│
└── EVPanel (底部可折叠)
    ├── EVLineChart (EV 变化折线图)
    ├── EquityComparison (Hero vs Range 对比)
    └── PotOddsTimeline (底池赔率变化)
```

### 2.3 Replay API 增强

```
GET /api/v1/replay/{hand_id}?detail=full
```

**Response**:

```json
{
  "hand_id": "uuid",
  "hero_cards": "AhKh",
  "board_cards": "AdTc3hKd2s",
  "hero_position": "BTN",
  "total_actions": 12,
  "timeline": [
    {
      "seq": 1,
      "street": "PREFLOP",
      "actor_position": "UTG",
      "actor_type": "Villain",
      "action": "RAISE",
      "amount_bb": 2.5,
      "pot_after_bb": 3.75,
      "hero_equity": 65.3,
      "hero_ev": 0.0,
      "pot_odds": null,
      "gto_frequency": {"call": 70, "raise": 25, "fold": 5},
      "spr": 38.0
    },
    {
      "seq": 2,
      "street": "PREFLOP",
      "actor_position": "BTN",
      "actor_type": "Hero",
      "action": "RAISE",
      "amount_bb": 7.5,
      "pot_after_bb": 11.25,
      "hero_equity": 65.3,
      "hero_ev": 0.8,
      "pot_odds": null,
      "gto_frequency": {"call": 30, "raise_3bet": 60, "fold": 10},
      "spr": 12.3
    }
  ],
  "summary": {
    "hero_profit_bb": 15.5,
    "went_to_showdown": true,
    "final_hand_strength": "Top Pair Top Kicker"
  }
}
```

每个 timeline 节点携带该时刻的**GTO 参考值**，让用户回放时了解"在这一步 GTO 推荐怎么做"。

### 2.4 牌桌渲染方案

使用 SVG 绘制牌桌，原因：
- 与 React 声明式组件模型匹配
- 缩放不失真
- 动画支持好（CSS transition / framer-motion）
- 不依赖 Canvas 库

牌桌布局（6人桌）：

```
        [Seat 3]
   [Seat 2]    [Seat 4]
[Seat 1]          [Seat 5]
   [Hero/BTN]  [Seat 6/BB]
        [Board]
        [Pot]
```

### 2.5 EV 图表增强

除了 MVP 的 EV 折线图，Phase 2 增加：

| 图表 | 说明 |
|------|------|
| EV 对比图 | Call EV vs Raise EV vs Fold EV 叠加折线 |
| Equity 变动图 | Hero Equity 在每个 Street 的变化 |
| Pot Odds 对比 | 当前底池赔率 vs 所需胜率 |
| GTO 偏差图 | 玩家实际频率 vs GTO 推荐频率的偏差 |

全部使用 Recharts，支持缩放（zoom）和 tooltip 交互。

---

## 3. 玩家画像引擎（Profile Engine）

### 3.1 统计指标定义

每个指标的计算都基于 `actions` 表中的原始数据：

#### 基础指标

| 指标 | 全称 | 计算方式 | 数据库来源 |
|------|------|---------|-----------|
| **VPIP** | Voluntarily Put $ In Pot | (非盲注主动入池次数) / 总手数 | actions(action_type IN Raise/Call, PREFLOP, NOT position IN BB/SB AND action_type=Check) |
| **PFR** | Preflop Raise | Preflop Raise次数 / 总手数 | actions(action_type=Raise, PREFLOP) |
| **3Bet** | 3Bet Frequency | 面对Raise再Raise次数 / 面对Raise机会次数 | 前置action是Raise，自己action是Raise |
| **FoldTo3Bet** | Fold to 3Bet | Raise后面对3Bet弃牌次数 / Raise后面对3Bet次数 | 自己Raise → 对手Raise → 自己Fold |
| **AF** | Aggression Factor | (Bet次数 + Raise次数) / Call次数 | 所有Street |
| **CBetFlop** | Flop C-Bet | Preflop Raise后在Flop Bet次数 / Preflop Raise后Flop机会 | PREFLOP Raise → FLOP Bet |
| **CBetTurn** | Turn C-Bet | Flop CBet后在Turn Bet次数 / Flop CBet后Turn机会 | 同上逻辑 |
| **WTSD** | Went To Showdown | 打到摊牌手数 / 看到Flop手数 | 有RIVER行动或摊牌标记 |
| **W$SD** | Won $ At Showdown | 摊牌赢利手数 / 摊牌手数 | 结果分析 |

#### 进阶指标

| 指标 | 计算方式 |
|------|---------|
| **FoldToCBet** | 面对Flop CBet Fold次数 / 面对Flop CBet次数 |
| **RaiseCBet** | 面对Flop CBet Raise次数 / 面对Flop CBet次数 |
| **RiverBluffFreq** | River Bet/Raise + 未摊牌赢 × 估算系数 |
| **FoldToRiverBet** | River面对Bet Fold次数 / River面对Bet次数 |
| **CheckRaiseFlop** | Flop Check后Raise次数 / Flop Check后面对Bet次数 |
| **DonkBet** | 非Preflop Raise者在Flop先Bet次数 / 机会次数 |

### 3.2 统计算法实现

```python
# backend/app/profiles/engine.py

class ProfileEngine:
    """基于 Action 表实时计算玩家画像"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def compute_profile(
        self, player_name: str, hand_ids: list[UUID] | None = None
    ) -> PlayerProfile:
        """
        计算指定玩家的画像。
        hand_ids 为 None 时计算所有手牌，否则仅计算指定手牌。
        """
        actions = await self._fetch_actions(player_name, hand_ids)
        hands = await self._fetch_hands(player_name, hand_ids)

        return PlayerProfile(
            player_name=player_name,
            sample_size=len(hands),
            vpip=self._calc_vpip(actions, hands),
            pfr=self._calc_pfr(actions, hands),
            three_bet=self._calc_threebet(actions),
            fold_to_three_bet=self._calc_fold_to_3bet(actions),
            aggression_factor=self._calc_af(actions),
            cbet_flop=self._calc_cbet(actions, 'FLOP'),
            cbet_turn=self._calc_cbet(actions, 'TURN'),
            wtsd=self._calc_wtsd(actions, hands),
            wsd=self._calc_wsd(hands),
            river_bluff_frequency=self._calc_river_bluff(actions, hands),
            fold_to_cbet=self._calc_fold_to_cbet(actions),
            check_raise_flop=self._calc_check_raise(actions, 'FLOP'),
            # ... 更多指标
        )

    def _calc_vpip(self, actions, hands) -> float:
        """VPIP = 主动入池次数 / 总手数"""
        total = len(hands)
        if total == 0:
            return 0.0
        # 非盲注位置的 Call/Raise 视为主动入池
        voluntarily_entered = sum(
            1 for a in actions
            if a.street == 'PREFLOP'
            and a.position not in ('SB', 'BB')
            and a.action_type in ('CALL', 'RAISE')
        )
        return voluntarily_entered / total

    def _calc_pfr(self, actions, hands) -> float:
        """PFR = Preflop Raise 次数 / 总手数"""
        total = len(hands)
        if total == 0:
            return 0.0
        raises = sum(
            1 for a in actions
            if a.street == 'PREFLOP' and a.action_type == 'RAISE'
        )
        return raises / total

    def _calc_threebet(self, actions) -> float:
        """3Bet = 3Bet次数 / 面对Raise机会次数"""
        opportunities = 0
        threebets = 0
        # 按 hand_id 分组处理
        for hand_actions in self._group_by_hand(actions):
            for i, action in enumerate(hand_actions):
                if action.street != 'PREFLOP':
                    continue
                if i > 0 and hand_actions[i-1].action_type == 'RAISE':
                    opportunities += 1
                    if action.action_type == 'RAISE':
                        threebets += 1
        if opportunities == 0:
            return 0.0
        return threebets / opportunities

    # ... 其余指标实现类似模式
```

### 3.3 自动玩家分类

```python
# backend/app/profiles/classifier.py

from enum import Enum

class PlayerType(str, Enum):
    NIT = "Nit"
    TAG = "TAG"
    LAG = "LAG"
    FISH = "Fish"
    CALLING_STATION = "Calling Station"
    MANIAC = "Maniac"
    UNKNOWN = "Unknown"

class PlayerClassifier:
    """
    根据画像指标自动分类玩家。

    分类规则（经验值，可调整）：
    - Nit:       VPIP < 15, PFR < 10
    - TAG:       15 ≤ VPIP ≤ 25, PFR ≥ VPIP * 0.7
    - LAG:       VPIP > 25, PFR ≥ VPIP * 0.7
    - Fish:      VPIP > 30, PFR < VPIP * 0.5
    - Calling Station: VPIP > 25, AF < 1.0
    - Maniac:    VPIP > 30, PFR > 25, 3Bet > 15
    """

    MIN_SAMPLE = 50  # 样本量不足时返回 Unknown

    def classify(self, profile: PlayerProfile) -> PlayerType:
        if profile.sample_size < self.MIN_SAMPLE:
            return PlayerType.UNKNOWN

        v = profile.vpip
        p = profile.pfr
        af = profile.aggression_factor
        t3 = profile.three_bet

        pfr_ratio = p / v if v > 0 else 0

        if v < 0.15 and p < 0.10:
            return PlayerType.NIT
        if v > 0.30 and pfr_ratio < 0.5:
            return PlayerType.FISH
        if v > 0.25 and af < 1.0:
            return PlayerType.CALLING_STATION
        if v > 0.30 and p > 0.25 and t3 > 0.15:
            return PlayerType.MANIAC
        if 0.15 <= v <= 0.25 and pfr_ratio >= 0.7:
            return PlayerType.TAG
        if v > 0.25 and pfr_ratio >= 0.7:
            return PlayerType.LAG

        return PlayerType.UNKNOWN
```

### 3.4 画像更新策略

- **触发时机**: 每次新录入手牌后，异步更新相关玩家画像
- **增量更新**: 不重新计算全部历史，只对新增手牌计算增量值
- **缓存**: Redis 中缓存最近计算的画像，TTL=1h
- **数据库持久化**: `player_profiles` 表存储最新全量画像快照

---

## 4. HUD 设计

### 4.1 HUD 组件结构

```
HUDOverlay (浮动叠加层)
├── HUDMainPanel
│   ├── PlayerTypeBadge (分类标签：鱼/Nit/TAG等)
│   ├── StatLine1: VPIP / PFR / 3Bet (核心三件)
│   ├── StatLine2: AF / CBet / FoldToCBet
│   ├── StatLine3: WTSD / W$SD
│   └── SampleSize (样本量指示 50/100/500+)
│
└── HUDDetailPopup (Hover 展开)
    ├── PositionBreakdown (按位置分解 VPIP/PFR)
    ├── StreetAggression (按 Street 拆解 AF)
    └── RecentTrend (最近 N 手趋势)
```

### 4.2 HUD 颜色编码

| 指标 | 低值颜色 | 中值颜色 | 高值颜色 |
|------|---------|---------|---------|
| VPIP | 蓝 (<18) | 绿 (18-28) | 红 (>28) |
| PFR | 青 (<12) | 绿 (12-22) | 橙 (>22) |
| 3Bet | 蓝 (<5) | 绿 (5-10) | 红 (>10) |
| AF | 蓝 (<1.5) | 绿 (1.5-3) | 红 (>3) |
| FoldTo3Bet | 青 (<50) | 绿 (50-65) | 红 (>65) |

---

## 5. 玩家画像页面

### 5.1 页面设计

```
PlayerProfilePage
├── ProfileHeader
│   ├── PlayerAvatar + Name
│   ├── PlayerTypeBadge (大号分类标签)
│   └── LastUpdated (最后更新时间)
│
├── StatsOverview (统计概览仪表盘)
│   ├── CoreStatsCard × 4 (VPIP / PFR / 3Bet / AF，带变化箭头)
│   └── SampleSizeIndicator (进度环)
│
├── PositionBreakdownTable (位置分解表格)
│   │ Pos | Hands | VPIP | PFR | 3Bet | AF | W$SD |
│   │ UTG | 120   | 18   | 15  | 3    | 2.1| 52   |
│   │ MP  | 145   | 22   | 18  | 5    | 2.5| 48   |
│   │ ... |
│
├── AggressionByStreet (各街道激进程度柱状图)
│   Preflop | Flop | Turn | River
│
├── TrendCharts (趋势图区)
│   ├── VPIP Over Time (折线图，最近500手)
│   ├── PFR Over Time
│   └── W$SD Over Time
│
└── RecentHands (最近手牌列表)
    └── HandCard × 10 (小卡片，点击跳转详情)
```

### 5.2 相关 API

```
GET  /api/v1/profiles/{player_name}           # 获取画像
GET  /api/v1/profiles/{player_name}/trend     # 获取趋势数据
GET  /api/v1/profiles/{player_name}/breakdown # 按位置分解
POST /api/v1/profiles/refresh/{player_name}    # 强制刷新画像
GET  /api/v1/profiles/search?q=name            # 搜索玩家
GET  /api/v1/profiles?type=fish&limit=10       # 按类型筛选玩家列表
```

---

## 6. 验收标准

- [ ] 回放可逐行动播放，动画流畅（60fps）
- [ ] 牌桌渲染正确显示玩家位置、手牌、筹码、底池
- [ ] EV 图表支持 4 种视图切换（EV对比/Equity/PotOdds/GTO偏差）
- [ ] Profile Engine 正确计算全部 11 项基础指标 + 5 项进阶指标
- [ ] 玩家自动分类准确率 > 85%（人工抽查 100 个样本）
- [ ] 画像刷新在 10000 手牌数据量下 < 2s
- [ ] HUD 面板正确展示核心统计 + 颜色编码
- [ ] 画像页面提供按位置分解 + 趋势图
- [ ] 画像数据在 Redis 中缓存，重复请求 < 50ms

---

## 7. 技术决策

### 7.1 画像计算：实时 vs 预计算

选择**混合方案**：基础指标实时计算（直接 SQL 聚合），复杂指标（如 RiverBluffFreq）预计算并缓存。VPIP/PFR 等高频简单指标走实时避免存储冗余；RiverBluff 等低频复杂指标走缓存。

### 7.2 画像存储：快照 vs 纯实时

`player_profiles` 表存储最新快照，供 HUD 快速查询。每次新录入手牌时异步更新快照。趋势数据从 `actions` 表实时查询（有索引保证性能）。
