# Phase 1: MVP 实施文档

> **目标**: 用户录入一手牌 → 系统给出 GTO 建议 → AI 解释为什么这样打
>
> **周期**: 6 周（Week 1 ~ Week 6）
>
> **版本**: V0.1 ~ V0.5

---

## 1. 任务拆解总表

| 编号 | 任务 | 归属 | 周 | 预计工时 | 前置依赖 |
|------|------|------|-----|---------|---------|
| T1.1 | 项目脚手架搭建（Monorepo + Docker Compose） | 基础 | W1 | 4h | - |
| T1.2 | 数据库 Migration 脚本（users/sessions/hands/players/actions/analyses） | Backend | W1 | 4h | T1.1 |
| T1.3 | GameState / SolverResult / AnalysisResult Pydantic 模型 | Backend | W1 | 3h | T1.1 |
| T1.4 | SolverProvider 抽象 + TexasSolver 实现 | Backend | W1-W2 | 6h | T1.3 |
| T1.5 | Frontend 脚手架（Vite + React + MUI + Router + Zustand） | Frontend | W1 | 4h | T1.1 |
| T2.1 | Hand Editor 页面（手牌选择 + Board 选择 + 位置/筹码输入） | Frontend | W2 | 8h | T1.5 |
| T2.2 | Action Editor 组件（Fold/Check/Call/Bet/Raise 交互） | Frontend | W2 | 6h | T2.1 |
| T2.3 | POST /api/analyze 端到端链路 | Backend | W2 | 6h | T1.4 |
| T2.4 | Solver 结果缓存（SHA256 → Redis + DB 双缓存） | Backend | W2 | 3h | T1.4 |
| T3.1 | CoachProvider 抽象 + OpenAI Provider 实现 | Backend | W3 | 6h | T2.3 |
| T3.2 | Prompt Builder（GTO 分析模板 + Exploit 模板 + 风险分析模板） | Backend | W3 | 6h | T3.1 |
| T3.3 | AI 结果缓存（prompt_hash → Redis + DB） | Backend | W3 | 2h | T3.1 |
| T3.4 | AnalysisService 编排层（Solver → Profile → AI 聚合） | Backend | W3 | 5h | T2.3, T3.1 |
| T4.1 | Analysis Result 展示页（Equity/EV/Strategy/AI 解释） | Frontend | W4 | 8h | T2.2, T3.4 |
| T4.2 | 手牌历史列表页 | Frontend | W4 | 6h | T2.1 |
| T4.3 | GET /api/hands + GET /api/hands/{id} + GET /api/analyses/{id} | Backend | W4 | 4h | T2.3 |
| T5.1 | Hand Replay 基础版（按 Street 分步回放） | Frontend | W5 | 8h | T4.1 |
| T5.2 | Hand Replay 后端（回放数据构建 + GET /api/replay/{hand_id}） | Backend | W5 | 4h | T4.3 |
| T5.3 | EV 变化曲线图（Recharts 折线图） | Frontend | W5 | 5h | T5.1 |
| T6.1 | 集成测试（至少 100 手牌测试） | 全栈 | W6 | 8h | 全部 |
| T6.2 | 错误处理与边界情况 | 全栈 | W6 | 6h | T6.1 |
| T6.3 | README 更新 + API 文档（OpenAPI） | 文档 | W6 | 3h | T6.1 |
| T6.4 | Docker Compose 一键启动验证 | DevOps | W6 | 3h | T6.1 |

**总计**: 约 105 工时

---

## 2. 前端详细设计

### 2.1 路由表

| 路径 | 页面组件 | 说明 |
|------|---------|------|
| `/` | `HomePage` | 首页，入口导航 |
| `/hand/new` | `HandEditorPage` | 新建手牌录入 |
| `/hand/:id` | `HandDetailPage` | 手牌详情 + 分析结果 |
| `/hand/:id/replay` | `ReplayPage` | 手牌回放 |
| `/history` | `HistoryPage` | 手牌历史列表 |

### 2.2 组件树

```
App
├── Layout (AppBar + Drawer + Content)
│   ├── HomePage
│   │   ├── HeroBanner
│   │   └── QuickStartButton
│   │
│   ├── HandEditorPage
│   │   ├── PositionSelector       # 位置选择（BTN/UTG/BB等）
│   │   ├── CardSelector           # 手牌选择（52张扑克牌网格）
│   │   ├── BoardSelector          # 公共牌选择（最多5张）
│   │   ├── StackInput             # 筹码深度输入
│   │   ├── PotInput               # 底池大小输入
│   │   ├── ActionEditor           # 行动编辑器
│   │   │   ├── StreetTabs          # Preflop/Flop/Turn/River Tab
│   │   │   ├── ActionButtonGroup   # Fold/Check/Call/Bet/Raise 按钮
│   │   │   └── ActionTimeline      # 已添加行动的时间轴
│   │   └── SubmitButton           # 提交分析
│   │
│   ├── HandDetailPage
│   │   ├── HandSummary            # 手牌摘要信息
│   │   ├── BoardDisplay           # 公共牌展示
│   │   ├── EquityBar              # Equity 进度条
│   │   ├── EVComparison           # Call/Raise/Fold EV 对比
│   │   ├── StrategyBreakdown      # GTO 策略拆解（饼图）
│   │   └── CoachAnalysis          # AI 教练分析文本
│   │       ├── GtoSection          # GTO 建议
│   │       ├── ExploitSection      # Exploit 建议
│   │       └── RiskSection         # 风险提示
│   │
│   ├── ReplayPage
│   │   ├── ReplayControls         # 播放/暂停/上一步/下一步
│   │   ├── TableView              # 牌桌视图（卡牌+玩家位置）
│   │   └── EVChart                # EV 变化折线图
│   │
│   └── HistoryPage
│       └── HandList               # 手牌列表（支持分页/筛选）
│           └── HandCard            # 单条手牌卡片（日期/手牌/结果）
```

### 2.3 Zustand Store 设计

```typescript
// stores/handEditorStore.ts
interface HandEditorStore {
  // 手牌状态
  heroCards: [Card, Card] | null;
  boardCards: Card[];
  heroPosition: Position;
  stackSizeBB: number;
  potSizeBB: number;
  
  // 行动历史
  actions: ActionRecord[];
  
  // 操作
  setHeroCards: (cards: [Card, Card]) => void;
  setBoardCards: (cards: Card[]) => void;
  setPosition: (pos: Position) => void;
  addAction: (action: ActionRecord) => void;
  removeAction: (index: number) => void;
  reset: () => void;
}

// stores/analysisStore.ts
interface AnalysisStore {
  currentResult: AnalysisResult | null;
  isLoading: boolean;
  error: string | null;
  
  fetchAnalysis: (handId: string) => Promise<void>;
  clearResult: () => void;
}
```

### 2.4 关键类型定义

```typescript
// types/poker.ts
type Suit = 'h' | 'd' | 'c' | 's';
type Rank = 'A' | 'K' | 'Q' | 'J' | 'T' | '9' | '8' | '7' | '6' | '5' | '4' | '3' | '2';

interface Card {
  rank: Rank;
  suit: Suit;
}

type Position = 'UTG' | 'MP' | 'HJ' | 'CO' | 'BTN' | 'SB' | 'BB';
type Street = 'PREFLOP' | 'FLOP' | 'TURN' | 'RIVER';
type ActionType = 'FOLD' | 'CHECK' | 'CALL' | 'BET' | 'RAISE' | 'ALL_IN';

interface ActionRecord {
  street: Street;
  actor: 'Hero' | 'Villain';
  action: ActionType;
  amount?: number; // BB
}

// types/analysis.ts
interface SolverResult {
  equity: number;
  call_ev: number;
  raise_ev: number;
  fold_ev: number;
  strategy: {
    call: number;
    raise: number;
    fold: number;
  };
}

interface AnalysisResult {
  id: string;
  hand_id: string;
  recommendation: 'Call' | 'Raise' | 'Fold';
  equity: number;
  call_ev: number;
  raise_ev: number;
  fold_ev: number;
  strategy: SolverResult['strategy'];
  gto_analysis: string;
  exploit_analysis: string;
  risk_analysis: string;
  created_at: string;
}
```

---

## 3. 后端详细设计

### 3.1 目录结构

```
backend/
├── alembic/
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.py                # 配置管理（环境变量）
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py            # 顶层路由聚合
│   │   ├── deps.py              # 依赖注入（get_db 等）
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── analyze.py       # POST /api/v1/analyze
│   │       ├── hands.py         # GET /api/v1/hands
│   │       ├── analyses.py      # GET /api/v1/analyses/{id}
│   │       └── replay.py        # GET /api/v1/replay/{hand_id}
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy Base + engine + session
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── hand.py
│   │   ├── player.py
│   │   ├── action.py
│   │   └── analysis.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── game_state.py        # GameState Pydantic
│   │   ├── solver.py            # SolverResult
│   │   ├── analysis.py          # AnalysisRequest/Response
│   │   └── hand.py              # Hand schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analysis_service.py  # AnalysisService 编排层
│   │   └── cache_service.py     # Redis 缓存服务
│   ├── solver/
│   │   ├── __init__.py
│   │   ├── base.py              # SolverProvider 抽象基类
│   │   ├── texas_solver.py      # TexasSolver 实现
│   │   └── factory.py           # Solver 工厂函数
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base.py              # CoachProvider 抽象基类
│   │   ├── openai_provider.py   # OpenAI 实现
│   │   ├── prompt_builder.py    # Prompt 构建器
│   │   └── factory.py           # AI 工厂函数
│   └── utils/
│       ├── __init__.py
│       └── hash.py              # SHA256 哈希工具
├── requirements.txt
├── Dockerfile
└── alembic.ini
```

### 3.2 核心数据流

```
HTTP POST /api/v1/analyze
        │
        ▼
    api/v1/analyze.py
    (参数校验，Pydantic 反序列化)
        │
        ▼
    services/analysis_service.py
    AnalysisService.analyze()
        │
        ├──► solver/texas_solver.py
        │    TexasSolver.solve(game_state)
        │    返回: SolverResult
        │
        ├──► services/cache_service.py
        │    检查/写入 Solver 缓存
        │
        ├──► ai/prompt_builder.py
        │    build_gto_prompt(game_state, solver_result)
        │    返回: str (prompt)
        │
        ├──► ai/openai_provider.py
        │    OpenAIProvider.analyze(prompt)
        │    返回: str (analysis text)
        │
        ├──► services/cache_service.py
        │    检查/写入 AI 缓存
        │
        └──► models/ (SQLAlchemy)
             保存 hand + actions + analysis 到 PostgreSQL
             返回: AnalysisResult
                     │
                     ▼
                 HTTP Response
```

### 3.3 缓存策略

```
Solver 缓存:
  cache_key = SHA256(hero_cards + board + position + stack + pot + action_history)
  
  Redis: solver:{cache_key} → JSON(SolverResult), TTL=24h
  PostgreSQL: solver_cache 表，作为冷数据持久化

AI 缓存:
  cache_key = SHA256(prompt_text)
  
  Redis: ai:{cache_key} → response_text, TTL=7d
  PostgreSQL: ai_cache 表
```

---

## 4. API 契约

### 4.1 POST /api/v1/analyze

**Request**:

```json
{
  "hero_cards": ["Ah", "Kh"],
  "board_cards": ["Ad", "Tc", "3h", "Kd", "2s"],
  "hero_position": "BTN",
  "stack_size_bb": 100,
  "pot_size_bb": 20.5,
  "actions": [
    {
      "street": "PREFLOP",
      "actor": "Hero",
      "action": "RAISE",
      "amount": 2.5
    },
    {
      "street": "PREFLOP",
      "actor": "Villain",
      "action": "CALL",
      "amount": 2.5
    },
    {
      "street": "FLOP",
      "actor": "Villain",
      "action": "CHECK",
      "amount": null
    },
    {
      "street": "FLOP",
      "actor": "Hero",
      "action": "BET",
      "amount": 6.6
    }
  ]
}
```

**Response (200)**:

```json
{
  "hand_id": "uuid-string",
  "analysis_id": "uuid-string",
  "recommendation": "Call",
  "equity": 58.4,
  "call_ev": 1.2,
  "raise_ev": 0.6,
  "fold_ev": -2.0,
  "strategy": {
    "call": 82,
    "raise": 13,
    "fold": 5
  },
  "gto_analysis": "你的AK在当前牌面拥有较强的顶对顶踢脚组合。根据Solver计算，Call的EV最高（+1.2bb），因为对手在Flop的Check-Raise范围中包含较多强牌（Set、两对）和少量诈唬。直接Raise会使对手弃掉诈唬部分，降低长期收益。建议以Call为主，在Turn上根据对手行动重新评估。",
  "exploit_analysis": "尚未收集到该对手足够数据，暂按GTO基线建议。",
  "risk_analysis": "对手在Flop的Check-Raise可能代表强牌范围。当前手牌在面对两对以上牌力时胜率明显下降，建议控制底池。",
  "learning_points": [
    "在湿润牌面（有顺子/同花听牌可能），顶对顶踢脚的Call通常优于Raise",
    "注意对手Check-Raise的范围通常极化，Call保留其诈唬范围"
  ]
}
```

**Response (422) - 校验失败**:

```json
{
  "detail": [
    {
      "loc": ["body", "hero_cards"],
      "msg": "Must contain exactly 2 cards",
      "type": "value_error"
    }
  ]
}
```

### 4.2 GET /api/v1/hands

**Query Parameters**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页数量，默认 20，最大 100 |
| `sort_by` | string | 否 | 排序字段，默认 `created_at` |
| `order` | string | 否 | `asc` / `desc`，默认 `desc` |

**Response (200)**:

```json
{
  "items": [
    {
      "id": "uuid",
      "hero_cards": "AhKh",
      "board_cards": "AdTc3h",
      "hero_position": "BTN",
      "recommendation": "Call",
      "result_bb": null,
      "created_at": "2026-06-25T10:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

### 4.3 GET /api/v1/hands/{hand_id}

**Response (200)**:

```json
{
  "id": "uuid",
  "hero_cards": "AhKh",
  "board_cards": "AdTc3hKd2s",
  "hero_position": "BTN",
  "stack_size_bb": 100,
  "pot_size_bb": 20.5,
  "actions": [
    {
      "street": "PREFLOP",
      "player_position": "BTN",
      "action_type": "RAISE",
      "amount": 2.5,
      "action_order": 1
    }
  ],
  "created_at": "2026-06-25T10:30:00Z"
}
```

### 4.4 GET /api/v1/analyses/{analysis_id}

**Response (200)**: 同 `POST /api/v1/analyze` 的 Response body

### 4.5 GET /api/v1/replay/{hand_id}

**Response (200)**:

```json
{
  "hand_id": "uuid",
  "streets": {
    "PREFLOP": [
      {
        "action_order": 1,
        "actor": "Hero",
        "action": "RAISE",
        "amount": 2.5,
        "pot_after": 3.75,
        "hero_equity": 65.3
      }
    ],
    "FLOP": [
      {
        "action_order": 2,
        "actor": "Villain",
        "action": "CHECK",
        "amount": null,
        "pot_after": 3.75,
        "hero_equity": 58.4
      }
    ]
  },
  "equity_curve": [
    {"action_order": 0, "equity": 65.3},
    {"action_order": 1, "equity": 65.3},
    {"action_order": 2, "equity": 58.4}
  ]
}
```

---

## 5. 周排期

### Week 1 — 项目骨架

| 日 | 任务 |
|----|------|
| Mon | T1.1 Docker Compose + Monorepo 结构 |
| Tue | T1.2 数据库 Migration（全部表） |
| Wed | T1.3 Pydantic 核心模型 |
| Thu | T1.4 SolverProvider 抽象 + TexasSolver 集成（开始） |
| Fri | T1.5 Frontend 脚手架 |

**Week 1 交付物**:
- `docker-compose up` 可启动 PostgreSQL + Redis + Backend + Frontend
- 数据库 Migration 可执行
- GameState / SolverResult 模型定义完成
- Frontend 空白 App Shell 可访问

### Week 2 — 牌局录入 + Solver

| 日 | 任务 |
|----|------|
| Mon | T1.4 Solver 完成 + 单元测试 |
| Tue | T2.1 Hand Editor 页面（CardSelector + PositionSelector） |
| Wed | T2.1 Hand Editor 完成（Stack/Pot/Board Input） |
| Thu | T2.2 Action Editor 组件 |
| Fri | T2.3 POST /api/analyze + T2.4 缓存 |

**Week 2 交付物**:
- 可完整录入一手牌含行动历史
- TexasSolver 返回 EV/Equity/Strategy
- Solver 结果缓存生效

### Week 3 — AI 教练

| 日 | 任务 |
|----|------|
| Mon | T3.1 CoachProvider 抽象 + OpenAI 集成 |
| Tue | T3.2 Prompt Builder（3 个模板） |
| Wed | T3.2 Prompt 调优 + T3.3 AI 缓存 |
| Thu | T3.4 AnalysisService 编排层 |
| Fri | 端到端联调 + 异常处理 |

**Week 3 交付物**:
- OpenAI 返回结构化分析
- Prompt 模板质量满足要求
- 端到端：录入 → Solver → AI → 结果 JSON

### Week 4 — 结果展示 + 历史

| 日 | 任务 |
|----|------|
| Mon | T4.1 Analysis Result 页面（Equity + EV + Strategy） |
| Tue | T4.1 AI 分析展示 + Markdown 渲染 |
| Wed | T4.2 手牌历史列表页 + T4.3 后端 API |
| Thu | 分页/筛选 + T4.3 完成 |
| Fri | UI 打磨 + 响应式适配 |

**Week 4 交付物**:
- 分析结果页面完整可交互
- 历史列表可浏览、分页、跳转详情

### Week 5 — 回放系统

| 日 | 任务 |
|----|------|
| Mon | T5.2 回放 API |
| Tue | T5.1 ReplayControls + Street 分步展示 |
| Wed | T5.1 牌桌视图 |
| Thu | T5.3 EV 变化曲线图 |
| Fri | 回放交互打磨 |

**Week 5 交付物**:
- 可按 Street 逐步回放牌局
- EV 曲线随行动变化

### Week 6 — 测试 + 发布

| 日 | 任务 |
|----|------|
| Mon | T6.1 集成测试用例编写 |
| Tue | T6.1 执行 100+ 手牌测试 |
| Wed | T6.2 错误处理（无效输入/极限情况/Solver超时） |
| Thu | T6.3 README + OpenAPI 文档 |
| Fri | T6.4 一键部署验证 + 发布 |

---

## 6. 验收标准

### 功能验收

- [ ] 用户可从 52 张牌中选出 Hero 手牌（2 张）和公共牌（0~5 张）
- [ ] 用户可选择位置（UTG/MP/HJ/CO/BTN/SB/BB）
- [ ] 用户可按 Street 录入 Fold/Check/Call/Bet/Raise/All-In 行动
- [ ] 提交后返回 Solver 结果（Equity/EV/Strategy）
- [ ] 返回 AI 教练分析（GTO 建议 + 风险分析 + 学习要点）
- [ ] 相同输入命中缓存，< 500ms 返回
- [ ] 手牌历史列表可分页浏览
- [ ] 点击历史手牌可查看详细分析结果
- [ ] 回放页面可按 Street 逐步播放行动
- [ ] 回放页面展示 EV 变化曲线图

### 性能验收

- [ ] Solver 响应时间 < 3s（无缓存）
- [ ] AI 分析时间 < 10s（无缓存）
- [ ] 缓存命中响应 < 500ms
- [ ] 前端首屏加载 < 3s

### 产品验收

- [ ] 完成至少 100 手牌测试，分析结果合理
- [ ] 用户能从分析中回答："为什么该 Call？""为什么不该 Raise？"
- [ ] Docker Compose 一键启动全部服务

---

## 7. 技术决策记录

### 7.1 为什么 MVP 不做用户系统？

MVP 阶段目标是验证"录入→分析→教练"核心价值。用户系统（注册/登录/权限）会额外引入 1-2 周工作量，且与核心价值无关。MVP 使用匿名模式，所有手牌直接存入数据库，后续 V1.0 再加用户系统。

### 7.2 TexasSolver 的选择

TexasSolver 是开源、轻量级的 Hold'em Solver，适合 MVP 快速集成。通过 `SolverProvider` 抽象，后续可无缝切换到 PioSolver 或 GTO Wizard API。

### 7.3 为什么 AI 不做流式输出

MVP 阶段优先保证功能完整性。流式 SS E 输出虽提升体验，但增加前后端复杂度。V0.2 可作为优化项加入。

### 7.4 Recharts vs D3

选择 Recharts 而非 D3：Recharts 基于 React 声明式组件，与 MUI 搭配自然，配置简单。EV 曲线图复杂度不高，D3 的性能优势在此场景无意义。
