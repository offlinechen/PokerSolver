# Architecture

## Overview

PokerCoachAI 采用分层架构设计。

核心原则：

```text
UI 与 Solver 解耦

Solver 与 AI 解耦

AI 与 数据存储解耦
```

所有模块通过统一数据结构进行通信。

---

# High Level Architecture

```text
Frontend
    │
    ▼
FastAPI API Layer
    │
    ▼
Application Services
    │
 ┌──┼──────────────┐
 │  │              │
 ▼  ▼              ▼

Solver Service
Profile Service
Replay Service

 │
 ▼

AI Coach Service

 │
 ▼

Database
```

---

# Core Design Principles

## Single Source of Truth

整个系统只有一个牌局状态对象：

```python
GameState
```

所有模块都依赖该对象。

包括：

* Solver
* Replay
* AI分析
* 数据库存储

---

## Provider Pattern

所有第三方能力统一接口。

例如：

```python
class SolverProvider:
    async def solve(game_state):
        pass
```

---

支持：

```text
TexasSolver

PioSolver

Simple Postflop

GTO Wizard API
```

无需修改业务逻辑。

---

AI Provider 同理：

```python
class CoachProvider:
    async def analyze(...)
```

支持：

```text
OpenAI

Claude

Gemini
```

---

# Backend Architecture

```text
backend/

├── api/
├── models/
├── services/
├── solver/
├── ai/
├── profiles/
├── replay/
├── database/
└── utils/
```

---

# API Layer

职责：

* 参数校验
* 权限控制
* 请求转发

禁止：

```text
业务逻辑

Solver计算

数据库操作
```

示例：

```python
@router.post("/analyze")
async def analyze_hand():
    pass
```

---

# Service Layer

系统核心。

负责：

* 调用Solver
* 调用Profile
* 调用AI
* 聚合结果

例如：

```python
class AnalysisService:
    async def analyze():
        pass
```

---

# Solver Module

目录：

```text
solver/

├── providers/
│
├── texas_solver.py
├── pio_solver.py
│
├── models.py
└── factory.py
```

---

统一输出：

```python
class SolverResult:

    equity: float

    call_ev: float

    raise_ev: float

    fold_ev: float

    strategy: dict
```

---

# AI Module

目录：

```text
ai/

├── providers/
│
├── openai_provider.py
├── claude_provider.py
├── gemini_provider.py
│
├── prompt_builder.py
└── service.py
```

---

职责：

生成：

```text
GTO分析

Exploit分析

风险分析

错误分析
```

---

AI禁止：

```text
自行计算EV

自行计算Equity

自行计算Solver结果
```

AI只负责解释。

---

# Profile Module

职责：

维护玩家长期统计。

输入：

```text
HandHistory
```

输出：

```python
PlayerProfile
```

---

示例：

```python
class PlayerProfile:

    vpip: float

    pfr: float

    threebet: float

    fold_to_threebet: float

    aggression_factor: float

    river_bluff_frequency: float
```

---

# Replay Module

职责：

保存完整行动序列。

例如：

```text
Preflop

Raise

Call

Flop

Bet

Raise

Call
```

支持：

```text
时间轴回放

节点跳转

EV变化分析
```

---

# Database Layer

PostgreSQL

原则：

所有数据持久化。

包括：

```text
Users

Hands

Actions

Profiles

Analysis
```

---

# Cache Layer

Redis

缓存：

```text
Solver结果

AI分析结果

会话状态
```

---

# Event Flow

用户提交牌局：

```text
Frontend

↓

API

↓

AnalysisService

↓

Solver

↓

Profile

↓

AI

↓

Response
```

---

# Future Extensions

## Multi-table Support

支持同时分析多个牌桌。

---

## Real-time HUD

实时统计对手行为。

---

## RAG Knowledge Base

支持：

```text
Modern Poker Theory

Applications of NL Hold'em

GTO Wizard Articles
```

知识检索增强。

---

## Coach Personalities

支持：

```text
GTO Coach

Exploit Coach

Tournament Coach

Cash Coach
```

不同分析风格。
