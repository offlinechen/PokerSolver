# PokerCoachAI

> AI-Powered Texas Hold'em GTO Analysis & Coaching Platform

## 项目简介

PokerCoachAI 是一款面向德州扑克玩家的智能分析平台。

项目核心目标并非重新发明 Solver，而是在成熟 GTO Solver 的基础上，构建一个能够提供：

* GTO分析
* EV计算
* 对手画像
* Exploit策略
* AI教练讲解
* 牌局复盘
* 长期学习记录

的一体化扑克训练系统。

传统 Solver 擅长计算，但不擅长解释。

大语言模型擅长解释，但缺乏严格数学支撑。

PokerCoachAI 将两者结合：

```text
Solver负责计算

LLM负责解释

玩家画像负责利用
```

最终目标：

让普通玩家拥有一位全天候职业扑克教练。

---

# 项目目标

## MVP阶段

实现以下功能：

### GTO分析

输入：

* Hero手牌
* 公共牌
* 筹码深度
* 底池大小
* 行动历史

输出：

* Equity
* Pot Odds
* EV
* GTO建议
* 推荐操作

---

### AI教练

基于Solver结果生成自然语言解释。

例如：

```text
Hero: AhKh

Board:
Ad Tc 3h

Villain:
BTN Bet 33%
```

输出：

```text
你的AK在当前牌面拥有较强顶对组合。

根据Solver计算，
Call EV最高。

Raise会使大量诈唬牌弃牌，
因此长期EV略低。

建议以Call为主。
```

---

### 牌局记录

支持：

* 单局记录
* 行动历史记录
* 节点回溯

---

## 第二阶段

增加：

### 牌局回放

支持：

* 时间轴回放
* EV变化曲线
* 节点跳转分析

---

### 玩家画像

记录：

* VPIP
* PFR
* 3Bet
* Fold To 3Bet
* CBet
* WTSD
* W$SD

形成长期统计。

---

## 第三阶段

增加：

### Exploit Engine

根据对手行为修正GTO建议。

例如：

GTO：

```text
River:
Call 60%
Fold 40%
```

玩家画像：

```text
River Bluff Frequency:
3%
```

输出：

```text
Exploit建议：

Fold 90%

该玩家河牌极少诈唬，
长期跟注EV为负。
```

---

### AI长期教练

自动发现玩家漏洞。

例如：

```text
你在BTN位置存在过度弃牌问题。

最近1000手牌：

Fold To 3Bet:
72%

建议降低至55%左右。
```

---

# 系统架构

```text
┌─────────────────────┐
│      Frontend       │
│ React + TypeScript  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│      FastAPI        │
│      Backend        │
└─────────┬───────────┘
          │
 ┌────────┼─────────┐
 │        │         │
 ▼        ▼         ▼

Solver   Profile   Replay
Engine   Engine    Engine

 │         │
 ▼         ▼

GTO      Player Stats

 └──────┬───────┘
        ▼

    AI Coach

        ▼

   Final Result
```

---

# 技术选型

## 前端

### React

原因：

* 开发效率高
* 生态成熟
* 图表支持完善

技术栈：

```text
React
TypeScript
Vite
```

主要依赖：

```text
Material UI

TanStack Query

Zustand

React Router

Recharts
```

---

## 桌面端

后续支持：

```text
Tauri
```

优点：

* 体积小
* 内存占用低
* Rust生态

---

# 后端

技术栈：

```text
Python
FastAPI
```

原因：

* AI生态成熟
* Solver集成方便
* 开发效率高

---

目录结构：

```text
backend/

├── api/
├── ai/
├── solver/
├── profiles/
├── replay/
├── database/
├── models/
└── services/
```

---

# Solver模块

项目原则：

不自行开发Solver。

使用成熟方案。 - TexasSolver

---

## MVP方案

TexasSolver

统一接口：

```python
class SolverProvider:

    async def solve(self, game_state):
        pass
```

---

## 后续扩展

支持：

* TexasSolver
* PioSolver
* Simple Postflop
* GTO Wizard API

所有Solver统一输出格式。

---

# AI模块

支持多模型切换。

接口设计：

```python
class CoachProvider:

    async def analyze(
        game_state,
        solver_result,
        player_profile
    ):
        pass
```

---

支持：

```text
OpenAI

Claude

Gemini
```

---

# 数据库设计

## PostgreSQL

存储：

```text
Users

Hands

HandActions

Sessions

PlayerProfiles

SolverCache

AnalysisHistory
```

---

## Redis

缓存：

```text
Solver结果缓存

LLM结果缓存

会话状态缓存
```

---

# 核心模块设计

## 1. Game State Engine

统一描述牌局状态。

```python
class GameState:

    hero_cards

    board_cards

    stack_size

    pot_size

    position

    action_history
```

所有模块只依赖GameState。

---

## 2. Hand History Engine

负责记录：

```text
Preflop

Flop

Turn

River
```

所有行动。

例如：

```text
UTG Raise

BTN Call

BB Fold

Flop

Check

Bet

Raise

Call
```

---

## 3. Solver Engine

输入：

```text
GameState
```

输出：

```json
{
  "equity": 58.2,
  "call_ev": 1.4,
  "raise_ev": 0.8,
  "fold_ev": -3.1,
  "strategy": {
    "call": 82,
    "raise": 13,
    "fold": 5
  }
}
```

---

## 4. Player Profile Engine

维护长期玩家画像。

记录：

```text
VPIP

PFR

3Bet

FoldTo3Bet

AggressionFactor

WTSD

W$SD

RiverBluffFrequency
```

---

自动分类：

```text
Nit

TAG

LAG

Fish

Calling Station

Maniac
```

---

示例：

```json
{
  "vpip": 42,
  "pfr": 8,
  "threebet": 1.2,
  "river_bluff": 4.1
}
```

自动生成：

```text
Loose Passive Fish
```

---

## 5. AI Coach Engine

工作流程：

```text
Game State

↓

Solver

↓

Player Profile

↓

Prompt Builder

↓

LLM

↓

Coaching Report
```

---

输出内容：

### GTO分析

```text
当前最优策略
```

### Exploit分析

```text
针对当前对手调整
```

### 风险分析

```text
操作风险等级
```

### 错误分析

```text
与GTO偏差
```

---

# API设计

## Analyze Hand

```http
POST /api/analyze
```

请求：

```json
{
  "hero_cards": ["Ah", "Kh"],
  "board": ["Ad", "Tc", "3h"],
  "pot_size": 20,
  "stack_size": 100,
  "history": []
}
```

返回：

```json
{
  "equity": 58.4,
  "recommendation": "Call",
  "analysis": "..."
}
```

---

## Get Profile

```http
GET /api/profile/{player_id}
```

返回：

```json
{
  "vpip": 42,
  "pfr": 8
}
```

---

# 目录结构

```text
PokerCoachAI/

├── docs/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   ├── stores/
│   ├── services/
│   └── types/
│
├── backend/
│
│   ├── api/
│   ├── ai/
│   ├── solver/
│   ├── profiles/
│   ├── replay/
│   ├── database/
│   ├── models/
│   └── services/
│
├── scripts/
│
├── tests/
│
├── deployments/
│
├── docker/
│
├── .env
├── docker-compose.yml
├── README.md
└── LICENSE
```

---

# 开发路线图

## V0.1

* 基础牌局录入
* Solver接入
* EV计算

---

## V0.2

* GPT分析
* 策略解释

---

## V0.3

* 牌局历史
* 回放系统

---

## V0.4

* 玩家画像
* HUD统计

---

## V0.5

* Exploit Engine

---

## V1.0

* AI扑克教练
* 长期训练记录
* 漏洞分析报告

---

# 项目愿景

PokerCoachAI 并不是另一个Solver工具。

它是建立在Solver之上的智能扑克学习平台。

通过：

```text
GTO计算

+

玩家画像

+

AI解释
```

帮助玩家真正理解扑克决策背后的逻辑。

最终实现：

```text
让每位玩家都拥有自己的职业扑克教练。
```
