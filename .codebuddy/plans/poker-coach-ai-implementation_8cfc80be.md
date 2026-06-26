---
name: poker-coach-ai-implementation
overview: 先编写三阶段详细实施文档（Phase 1 MVP/Phase 2 画像回放/Phase 3 Exploit AI教练），然后从 Phase 1 开始搭建项目框架和核心代码。
todos:
  - id: explore-existing-docs
    content: 使用 [subagent:code-explorer] 深度提取现有 4 份设计文档中的所有接口定义、数据模型、架构约束和模块职责
    status: completed
  - id: gen-phase1-doc
    content: 编写 docs/phase1-implementation.md：MVP 详细实施文档，含任务拆解表、前端组件树与路由、后端模块接口与数据流、完整 API 契约、周排期、验收标准
    status: completed
    dependencies:
      - explore-existing-docs
  - id: gen-phase2-doc
    content: 编写 docs/phase2-implementation.md：回放系统 + 玩家画像与统计引擎详细实施文档，含组件设计、Profile Engine 算法、HUD 设计
    status: completed
    dependencies:
      - explore-existing-docs
  - id: gen-phase3-doc
    content: 编写 docs/phase3-implementation.md：Exploit Engine + AI 长期教练 + RAG 知识库详细实施文档，含 Exploit 算法、Coach Personalities 设计、Embedding 方案
    status: completed
    dependencies:
      - explore-existing-docs
  - id: scaffold-backend
    content: 搭建 Backend 脚手架：FastAPI 项目结构、SQLAlchemy async engine、Alembic 初始化、Docker Compose（PostgreSQL + Redis + Backend）、Pydantic models（GameState/SolverResult/AnalysisResult）
    status: completed
    dependencies:
      - gen-phase1-doc
  - id: scaffold-frontend
    content: 搭建 Frontend 脚手架：Vite + React + TypeScript + Material UI + React Router + Zustand store + TanStack Query 配置
    status: completed
    dependencies:
      - gen-phase1-doc
  - id: implement-mvp-core
    content: 实现 Phase 1 MVP 核心链路：Hand Editor 页面 → API → SolverProvider(TexasSolver) → CoachProvider(OpenAI) → AnalysisService → 分析结果展示页，含 Solver/AI 缓存、数据库读写
    status: completed
    dependencies:
      - scaffold-backend
      - scaffold-frontend
---

## 用户要求

先为 PokerCoachAI 三个阶段分别生成详细的实施文档，再开始搭建项目脚手架和编写代码。

## 当前项目状态

项目仅有 `docs/` 下的 4 份高层设计文档（readme、Architecture、database、mvp），缺少三阶段各自的详细实施文档（任务拆解、前端组件树、后端模块接口、API 契约、数据流细节），也无任何代码。

## 输出目标

1. 三份阶段性实施文档，每份包含：任务拆解表、前端组件树与路由设计、后端模块接口与数据流、API 完整契约、数据库变更说明
2. Phase 1 完整代码脚手架与 MVP 核心功能实现

## 技术栈（沿用现有设计）

| 层 | 技术 |
| --- | --- |
| 前端 | React 18 + TypeScript + Vite + Material UI + Zustand + TanStack Query + Recharts |
| 后端 | Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2.0 (async) + Alembic |
| 数据库 | PostgreSQL 16 + Redis 7 |
| AI | OpenAI GPT-4o / Claude / Gemini（Provider Pattern 抽象） |
| Solver | TexasSolver（Provider Pattern），预留扩展接口 |
| 部署 | Docker Compose（PostgreSQL + Redis + Backend + Frontend） |


## 实施策略

### 文档先行策略

先产出三个阶段的实施文档，每个文档作为该阶段唯一权威的实施参考，后续编码严格对照文档执行。这避免边写边改设计、减少返工。

### Phase 1 编码策略

MVP 阶段仅实现 `POST /api/analyze` 一条核心链路，覆盖以下模块（按文档中已有设计）：

- **Backend**: models(GameState/SolverResult/AnalysisResult) → solver(Provider + TexasSolver) → ai(Provider + OpenAI + prompt_builder) → services(AnalysisService) → api(analyze router) → database(SQLAlchemy models + Alembic migration)
- **Frontend**: App shell → Hand Editor page → Action Editor 组件 → 分析结果展示页

### 性能考量

- Solver 结果用 SHA256(state_hash) 做 Redis + DB 双缓存，避免重复计算
- AI 分析结果用 prompt_hash 缓存，节省 Token 开销
- API 层响应时间目标：Solver < 3s，AI < 10s

### 架构约束（严格遵循现有设计）

- API 层禁止业务逻辑/Solver计算/数据库操作
- AI 只做解释，绝不自行计算 EV/Equity
- 所有模块依赖 GameState 单一数据源
- Solver/Coach 均使用 Provider Pattern 抽象，可切换底层实现

## SubAgent

- **code-explorer**
- 用途：在生成实施文档前，深度探索 docs/ 下现有设计文档的完整内容，确保实施文档与已有架构设计完全一致，不产生矛盾
- 预期结果：提取所有接口定义、数据模型、架构约束，作为实施文档的编写依据