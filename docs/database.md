# Database Design

## Overview

PokerCoachAI 使用 PostgreSQL 作为主数据库。

设计原则：

```text
所有分析都来源于牌局数据

所有画像都来源于行动数据

所有AI分析都可追溯
```

核心实体：

```text
User

Session

Hand

Action

Player

PlayerProfile

Analysis
```

关系图：

```text
User
 │
 ├── Sessions
 │
 ├── Hands
 │
 └── Analyses


Hand
 │
 ├── Players
 │
 ├── Actions
 │
 └── Analysis
```

---

# Users

用户表

## users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,

    username VARCHAR(64),

    email VARCHAR(128),

    created_at TIMESTAMP,

    updated_at TIMESTAMP
);
```

---

# Sessions

一次游戏会话。

例如：

```text
2026-07-01

NL50

PokerStars

4小时
```

对应一个 Session。

---

## sessions

```sql
CREATE TABLE sessions (

    id UUID PRIMARY KEY,

    user_id UUID,

    platform VARCHAR(64),

    game_type VARCHAR(32),

    stake VARCHAR(32),

    started_at TIMESTAMP,

    ended_at TIMESTAMP,

    created_at TIMESTAMP
);
```

---

# Hands

核心表。

每一手牌对应一条记录。

---

## hands

```sql
CREATE TABLE hands (

    id UUID PRIMARY KEY,

    session_id UUID,

    hero_position VARCHAR(16),

    hero_cards VARCHAR(16),

    board_cards VARCHAR(32),

    stack_size DECIMAL,

    pot_size DECIMAL,

    result_bb DECIMAL,

    created_at TIMESTAMP
);
```

---

字段说明：

```text
hero_cards

AhKh
```

```text
board_cards

AdTc3hKd2s
```

---

# Players

牌局中的玩家。

支持：

```text
Hero

Villain1

Villain2

Villain3
```

---

## players

```sql
CREATE TABLE players (

    id UUID PRIMARY KEY,

    hand_id UUID,

    seat_number INT,

    nickname VARCHAR(128),

    position VARCHAR(16),

    stack_size DECIMAL
);
```

---

# Actions

系统最重要的表。

所有统计都来自这里。

---

## actions

```sql
CREATE TABLE actions (

    id UUID PRIMARY KEY,

    hand_id UUID,

    player_id UUID,

    street VARCHAR(16),

    action_type VARCHAR(16),

    amount DECIMAL,

    action_order INT
);
```

---

street

```text
PREFLOP

FLOP

TURN

RIVER
```

---

action_type

```text
FOLD

CHECK

CALL

BET

RAISE

ALL_IN
```

---

示例：

```text
Preflop

UTG Raise

BTN Call

BB Fold
```

数据库：

```text
1 Raise

2 Call

3 Fold
```

---

# Analysis

保存分析结果。

避免重复调用 Solver。

---

## analyses

```sql
CREATE TABLE analyses (

    id UUID PRIMARY KEY,

    hand_id UUID,

    recommendation VARCHAR(32),

    equity DECIMAL,

    call_ev DECIMAL,

    raise_ev DECIMAL,

    fold_ev DECIMAL,

    gto_analysis TEXT,

    exploit_analysis TEXT,

    created_at TIMESTAMP
);
```

---

# Solver Cache

缓存Solver结果。

---

## solver_cache

```sql
CREATE TABLE solver_cache (

    id UUID PRIMARY KEY,

    state_hash VARCHAR(128),

    result_json JSONB,

    created_at TIMESTAMP
);
```

---

state_hash

例如：

```text
hero_cards

board

position

stack

pot
```

计算SHA256。

相同状态直接命中缓存。

---

# AI Cache

避免重复消耗Token。

---

## ai_cache

```sql
CREATE TABLE ai_cache (

    id UUID PRIMARY KEY,

    prompt_hash VARCHAR(128),

    response TEXT,

    created_at TIMESTAMP
);
```

---

# Player Profile

长期画像。

---

## player_profiles

```sql
CREATE TABLE player_profiles (

    id UUID PRIMARY KEY,

    player_name VARCHAR(128),

    sample_size INT,

    vpip DECIMAL,

    pfr DECIMAL,

    three_bet DECIMAL,

    fold_to_three_bet DECIMAL,

    cbet_flop DECIMAL,

    cbet_turn DECIMAL,

    wtsd DECIMAL,

    wsd DECIMAL,

    aggression_factor DECIMAL,

    river_bluff_frequency DECIMAL,

    updated_at TIMESTAMP
);
```

---

# Advanced Statistics

高级统计。

单独拆表。

---

## player_statistics

```sql
CREATE TABLE player_statistics (

    id UUID PRIMARY KEY,

    player_profile_id UUID,

    stat_key VARCHAR(64),

    stat_value DECIMAL,

    sample_size INT
);
```

---

示例：

```text
turn_check_raise

15%
```

```text
river_probe

22%
```

```text
fold_to_probe

58%
```

---

# Hand Replay

保存回放状态。

---

## hand_replays

```sql
CREATE TABLE hand_replays (

    id UUID PRIMARY KEY,

    hand_id UUID,

    replay_json JSONB,

    created_at TIMESTAMP
);
```

---

示例：

```json
{
  "preflop": [],
  "flop": [],
  "turn": [],
  "river": []
}
```

---

# Knowledge Base

未来RAG使用。

---

## knowledge_documents

```sql
CREATE TABLE knowledge_documents (

    id UUID PRIMARY KEY,

    title VARCHAR(256),

    source VARCHAR(256),

    content TEXT,

    created_at TIMESTAMP
);
```

---

## knowledge_chunks

```sql
CREATE TABLE knowledge_chunks (

    id UUID PRIMARY KEY,

    document_id UUID,

    chunk_index INT,

    content TEXT,

    embedding VECTOR(1536)
);
```

---

# Recommended Indexes

## Hands

```sql
CREATE INDEX idx_hands_session
ON hands(session_id);
```

---

## Actions

```sql
CREATE INDEX idx_actions_hand
ON actions(hand_id);

CREATE INDEX idx_actions_player
ON actions(player_id);
```

---

## Profiles

```sql
CREATE INDEX idx_profile_name
ON player_profiles(player_name);
```

---

# Data Flow

录入牌局：

```text
Hand

↓

Players

↓

Actions
```

---

分析：

```text
Hand

↓

Solver

↓

Analysis
```

---

画像更新：

```text
Actions

↓

Statistics Engine

↓

Player Profile
```

---

# Future Migration

V1阶段：

```text
Users

Sessions

Hands

Players

Actions

Analyses
```

---

V2阶段：

```text
Player Profiles

Replay
```

---

V3阶段：

```text
Knowledge Base

Embeddings

RAG
```

---

# Final Principle

数据库永远只保存事实：

```text
玩家做了什么
```

而不是：

```text
玩家应该做什么
```

事实来自牌局。

策略来自Solver。

解释来自AI。

三者必须彻底分离。

```
```
