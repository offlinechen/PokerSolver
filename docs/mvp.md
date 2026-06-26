# MVP

## Goal

在最短时间内验证产品价值。

目标：

```text
用户录入一手牌

系统给出GTO建议

AI解释为什么这样打
```

这是第一阶段唯一目标。

---

# MVP Scope

包含：

✅ 手牌录入

✅ 行动记录

✅ Solver接入

✅ EV计算

✅ AI分析

---

不包含：

❌ HUD

❌ 多桌支持

❌ 自动抓牌

❌ 对手长期画像

❌ RAG知识库

❌ 用户系统

---

# User Flow

## Step 1

录入牌局。

输入：

```text
Hero Hand

Board

Position

Pot Size

Stack Size

Action History
```

---

示例：

```text
Hero

Ah Kh

BTN

100bb

Preflop

Hero Raise 2.5bb

BB Call

Flop

Ad Tc 3h

BB Check

Hero Bet 33%

BB Raise
```

---

## Step 2

构建GameState。

```python
GameState
```

---

## Step 3

调用Solver。

返回：

```json
{
  "equity":58.4,
  "call_ev":1.2,
  "raise_ev":0.6,
  "fold_ev":-2.0
}
```

---

## Step 4

生成Prompt。

示例：

```text
你是一名职业扑克教练。

请根据以下Solver结果分析：

...
```

---

## Step 5

调用LLM。

输出：

```text
GTO建议

Exploit建议

关键风险

学习建议
```

---

# MVP Screens

## Home

功能：

开始分析

---

## Hand Editor

功能：

录入牌局。

字段：

```text
Hero Cards

Board

Position

Pot Size

Stack Size
```

---

## Action Editor

支持：

```text
Fold

Check

Call

Bet

Raise
```

---

## Analysis Result

显示：

```text
Equity

EV

Solver Strategy

AI Coach
```

---

# MVP Data Models

## GameState

```python
class GameState:

    hero_cards

    board_cards

    position

    stack_size

    pot_size

    action_history
```

---

## SolverResult

```python
class SolverResult:

    equity

    call_ev

    raise_ev

    fold_ev

    strategy
```

---

## AnalysisResult

```python
class AnalysisResult:

    recommendation

    gto_analysis

    exploit_analysis

    risk_analysis
```

---

# MVP API

## Analyze Hand

```http
POST /api/analyze
```

请求：

```json
{
  "hero_cards":["Ah","Kh"],
  "board":["Ad","Tc","3h"]
}
```

响应：

```json
{
  "equity":58.4,
  "recommendation":"Call"
}
```

---

# MVP Tech Stack

Frontend

```text
React

TypeScript

Vite
```

---

Backend

```text
Python

FastAPI
```

---

Database

```text
PostgreSQL
```

---

Cache

```text
Redis
```

---

AI

```text
OpenAI GPT

Claude
```

---

Solver

```text
TexasSolver
```

---

# Success Metrics

MVP成功标准：

## Functional

能够完成：

```text
输入牌局

获得Solver结果

获得AI分析
```

---

## Performance

目标：

```text
Solver响应

< 3秒

AI分析

< 10秒
```

---

## Product

用户能够回答：

```text
为什么应该Call？

为什么不应该Raise？

如何针对弱玩家调整？
```

如果用户能够从分析中学习，

MVP即视为成功。

---

# Estimated Timeline

Week 1

项目初始化

数据模型设计

---

Week 2

牌局录入界面

GameState实现

---

Week 3

TexasSolver接入

EV计算

---

Week 4

OpenAI接入

Prompt设计

---

Week 5

分析页面

结果展示

---

Week 6

测试

Bug修复

MVP发布

---

# Exit Criteria

满足以下条件即可进入V0.2：

✅ Solver正常运行

✅ AI正常分析

✅ 支持完整牌局录入

✅ 支持分析结果展示

✅ 可完成至少100手牌测试

届时开始开发：

```text
Player Profile

Replay System

Exploit Engine
```
