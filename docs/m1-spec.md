# M1 规格书

> **状态**: 已实现
> **日期**: 2026-06-27

---

## M1 目标

```text
输入: 模式 + 手牌 + 位置 + 轮次 + 公共牌
输出: Equity + EV + 策略建议
```

**不包含**（M2 实现）：

```text
❌ 行动历史分析
❌ 对手画像
❌ Exploit 引擎
❌ ICM 调整
❌ 生存 EV 模型
❌ Push/Fold 表
```

---

## 支持的游戏模式

| 模式 ID | 名称 | M1 能力 | M2 计划 |
|---------|------|---------|---------|
| `standard` | 标准德州 | 52 张牌完整 Solver | - |
| `shortdeck` | 短牌模式 | 36 张牌独立 Solver | - |
| `sng` | SNG 模式 | 标准 EV（占位） | ICM + Push/Fold |
| `squid` | 鱿鱼模式 | 标准 EV（占位） | 生存 EV 模型 |

---

## API

### POST /api/v1/analyze

```json
{
  "mode": "standard",
  "hero_cards": ["Ah", "Kh"],
  "board_cards": ["Ad", "Tc", "3h"],
  "hero_position": "BTN",
  "stack_size_bb": 100,
  "pot_size_bb": 20.5,
  "actions": []
}
```

**Response**:

```json
{
  "hand_id": "uuid",
  "analysis_id": "uuid",
  "recommendation": "Raise",
  "equity": 58.4,
  "call_ev": 2.1,
  "raise_ev": 3.5,
  "fold_ev": 0.0,
  "strategy": { "call": 20, "raise": 75, "fold": 5 },
  "gto_analysis": "...",
  "risk_analysis": "...",
  "exploit_analysis": "暂无利用分析",
  "learning_points": ["..."]
}
```

### GET /api/v1/modes

```json
{
  "modes": [
    { "id": "standard", "name": "标准德州", "description": "52张牌标准德州扑克" },
    { "id": "shortdeck", "name": "短牌模式", "description": "36张牌(6-A)，同花>葫芦" },
    { "id": "sng", "name": "SNG模式", "description": "坐满即开锦标赛 (ICM将于M2加入)" },
    { "id": "squid", "name": "鱿鱼模式", "description": "生存淘汰赛制 (将于M2加入)" }
  ]
}
```

---

## Solver 引擎架构

```
game_state.mode
      │
      ▼
  get_solver(mode)           ← factory.py
      │
      ├─ "standard"  → TexasSolver     。mode = "standard"
      ├─ "shortdeck" → ShortDeckSolver  。mode = "shortdeck"
      ├─ "sng"       → SNGSolver       。mode = "standard" (M1)
      └─ "squid"     → SquidSolver     。mode = "standard" (M1)
      │
      ▼
  SolverBase.solve(game_state)
      │
      ├─ _estimate_equity()  → calculate_equity(mode=self.mode)
      │       │
      │       ├─ get_deck_config(mode) ──→ DeckConfig
      │       ├─ HandEvaluator(deck)  ──→ mode-aware scoring
      │       └─ _generate_range()    ──→ mode-specific ranges
      │
      ├─ _calculate_ev()     → 线性 Cash EV
      └─ _build_strategy()   → 基于 equity 的频率建议
```

**关键文件**：

| 文件 | 职责 |
|------|------|
| `solver/engine/deck.py` | DeckConfig — 牌组大小、有效等级、排名顺序 |
| `solver/engine/hand_evaluator.py` | HandEvaluator — 模式感知 5/7 张牌评估 |
| `solver/equity_calculator.py` | Monte Carlo equity 计算（接受 mode 参数） |
| `solver/texas_solver.py` | 4 个具体 Solver（共享 SolverBase） |
| `solver/factory.py` | 模式路由 + 支持模式列表 |
| `solver/ranges/standard.py` | 9 人桌标准范围表 |
| `solver/ranges/shortdeck.py` | 短牌专用范围表 |

---

## M1 → M2 升级路径

| M2 功能 | 需要新增的模块 | 需修改的模块 |
|---------|-------------|------------|
| 行动历史分析 | — | `texas_solver.py`（对手范围贝叶斯收窄） |
| 玩家画像 | `profiles/engine.py` | — |
| Exploit Engine | `exploit/engine.py` | `analysis_service.py` |
| ICM 调整 | `solver/engine/icm_calculator.py` | `SNGSolver` |
| 生存 EV | `solver/engine/survival_ev.py` | `SquidSolver` |
| Push/Fold 表 | `solver/ranges/sng_push_fold.py` | `SNGSolver.solve()` |
