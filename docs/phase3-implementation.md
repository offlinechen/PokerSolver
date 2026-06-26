# Phase 3: Exploit Engine + AI 长期教练 + RAG 知识库 实施文档

> **前置**: Phase 2 完成（需玩家画像系统就绪）
>
> **目标**: 根据对手画像修正 GTO 建议 + AI 自动发现玩家漏洞 + 引入扑克理论知识库增强分析
>
> **周期**: 5 周
>
> **版本**: V2.0

---

## 1. 任务拆解总表

| 编号 | 任务 | 归属 | 周 | 预计工时 | 前置依赖 |
|------|------|------|-----|---------|---------|
| P3.1 | Exploit Engine 核心算法（对手行为偏差 → 策略修正） | Backend | W1-W2 | 12h | Phase2 P2.4 |
| P3.2 | Exploit 前后端链路（分析结果增加 Exploit 建议） | 全栈 | W2 | 6h | P3.1 |
| P3.3 | Exploit Sandbox（策略模拟：修改策略后 EV 对比） | Frontend | W2 | 8h | P3.2 |
| P3.4 | Leak Detector Engine（自动漏洞检测算法） | Backend | W3 | 10h | Phase2 P2.4 |
| P3.5 | AI Long-term Coach（历史数据 → 趋势分析 → 个性化建议） | Backend | W3 | 10h | P3.4 |
| P3.6 | Coach Dashboard 页面（漏洞总览 + 改善建议） | Frontend | W3-W4 | 12h | P3.5 |
| P3.7 | RAG 知识库搭建（文档摄入 + Embedding + 检索） | Backend | W4 | 10h | - |
| P3.8 | RAG 增强分析（分析引用理论来源） | Backend | W4 | 6h | P3.7 |
| P3.9 | Coach Personalities（GTO/Exploit/Tournament/Cash 四种教练） | Backend | W4-W5 | 8h | P3.5, P3.7 |
| P3.10 | Coach Personality Switcher（前端教练切换 UI） | Frontend | W5 | 6h | P3.9 |
| P3.11 | Training Journal（长期训练记录 + 进步追踪） | Frontend | W5 | 8h | P3.6 |
| P3.12 | 集成测试 + 端到端验证 | 全栈 | W5 | 8h | 全部 |

**总计**: 约 104 工时

---

## 2. Exploit Engine

### 2.1 核心思想

GTO 给出的是"不可被利用"的策略。Exploit Engine 在 GTO 基础上，根据对手的**可观测偏差**对策略进行**有向修正**：

```
GTO Strategy ──→ Exploit Engine ──→ Adjusted Strategy
                      │
              Player Profile
           (对手行为偏差数据)
```

### 2.2 修正模型

**输入**:

| 参数 | 来源 | 说明 |
|------|------|------|
| `gto_strategy` | SolverResult | {call: 60%, raise: 20%, fold: 20%} |
| `gto_ev` | SolverResult | {call_ev: 1.2, raise_ev: 0.6, fold_ev: -2.0} |
| `player_profile` | Profile Engine | 对手各项统计指标 |
| `game_state` | GameState | 当前牌局上下文 |
| `street` | GameState | 当前街道 |

**核心修正规则**:

```python
# backend/app/exploit/engine.py

class ExploitEngine:
    """
    基于对手画像修正 GTO 策略。

    原则：
    1. 对手过度弃牌 → 增加诈唬频率
    2. 对手过度跟注 → 减少诈唬，增加价值下注
    3. 对手过度激进 → 增加抓诈频率
    4. 对手被动跟注站 → 薄价值下注更多
    """

    def adjust_strategy(
        self,
        gto_strategy: dict[str, float],  # {'call': 60, 'raise': 20, 'fold': 20}
        gto_ev: dict[str, float],         # {'call': 1.2, 'raise': 0.6, 'fold': -2.0}
        profile: PlayerProfile,
        street: Street,
    ) -> ExploitResult:
        """
        返回调整后的策略和解释。
        """
        adjustments = []

        # 规则 1: 对手 FoldToCBet 过高 → 增加 CBet 频率
        if street == 'FLOP' and profile.fold_to_cbet > 0.65:
            adjustments.append(
                StrategyAdjustment(
                    action='raise',  # Bet = Raise on Flop
                    delta=+15,
                    reason=f'对手FoldToCBet={profile.fold_to_cbet:.0%}，过度弃牌，增加CBet诈唬频率'
                )
            )

        # 规则 2: 对手 WTSD 过高 → 减少诈唬，增加价值下注
        if profile.wtsd > 0.35:
            if gto_ev.get('raise', 0) < 0:  # GTO 中的负 EV Raise 是诈唬
                adjustments.append(
                    StrategyAdjustment(
                        action='raise',
                        delta=-10,
                        reason=f'对手WTSD={profile.wtsd:.0%}，跟注到底倾向高，减少纯诈唬'
                    )
                )

        # 规则 3: Aggression Factor 极端低 → 多下注
        if profile.aggression_factor < 1.0:
            adjustments.append(
                StrategyAdjustment(
                    action='raise',
                    delta=+10,
                    reason=f'对手AF={profile.aggression_factor:.1f}，被动型玩家，增加下注施压'
                )
            )

        # 规则 4: RiverBluff 频率极低 → River 大幅增加弃牌
        if street == 'RIVER' and profile.river_bluff_frequency < 0.10:
            adjustments.append(
                StrategyAdjustment(
                    action='fold',
                    delta=+25,
                    reason=f'对手RiverBluff<{profile.river_bluff_frequency:.0%}，河牌几乎不诈唬，大幅倾向弃牌'
                )
            )

        # 规则 5: 3Bet 过高 → 4Bet 范围收窄
        if street == 'PREFLOP' and profile.three_bet > 0.12:
            adjustments.append(
                StrategyAdjustment(
                    action='raise',  # 4Bet
                    delta=-8,
                    reason=f'对手3Bet={profile.three_bet:.0%}，3Bet频率高，收紧4Bet诈唬范围'
                )
            )

        # 应用修正，确保比例和为 100
        adjusted = self._apply_adjustments(gto_strategy, adjustments)

        return ExploitResult(
            gto_strategy=gto_strategy,
            adjusted_strategy=adjusted,
            adjustments=adjustments,
            summary=self._build_summary(adjustments)
        )

    def _apply_adjustments(
        self,
        gto: dict[str, float],
        adjustments: list[StrategyAdjustment]
    ) -> dict[str, float]:
        """应用调整并重新归一化到 100%"""
        result = dict(gto)
        for adj in adjustments:
            if adj.action in result:
                result[adj.action] = max(0, min(100, result[adj.action] + adj.delta))

        # 重新归一化
        total = sum(result.values())
        if total > 0:
            result = {k: round(v / total * 100, 1) for k, v in result.items()}

        return result
```

### 2.3 ExploitResult 数据结构

```python
class StrategyAdjustment(BaseModel):
    action: str          # 'call' | 'raise' | 'fold'
    delta: float         # 修正量（百分点），正=增加，负=减少
    reason: str          # 修正原因

class ExploitResult(BaseModel):
    gto_strategy: dict[str, float]      # 原始 GTO 策略
    adjusted_strategy: dict[str, float]  # 修正后策略
    adjustments: list[StrategyAdjustment] # 所有修正项
    summary: str                         # 一句话总结

    # 示例
    # {
    #   "gto_strategy": {"call": 60, "raise": 20, "fold": 20},
    #   "adjusted_strategy": {"call": 65, "raise": 28, "fold": 7},
    #   "adjustments": [
    #     {"action": "raise", "delta": +8, "reason": "对手FoldToCBet=72%，过度弃牌"},
    #     {"action": "fold", "delta": -13, "reason": "对手RiverBluff=4%，几乎不诈唬"}
    #   ],
    #   "summary": "建议增加下注频率，减少河牌弃牌"
    # }
```

### 2.4 修正规则矩阵

| 对手特征 | 阈值 | 对策略的影响 |
|---------|------|------------|
| FoldToCBet 高 | > 65% | CBet ↑ (更多诈唬) |
| FoldToCBet 低 | < 35% | CBet ↓ (减少诈唬) |
| WTSD 高 | > 35% | Bluff ↓, Value Bet ↑ |
| AF 低 (< 1.5) | - | Bet ↑ (施压被动玩家) |
| AF 高 (> 3.0) | - | Check-Call ↑ (引诱诈唬) |
| RiverBluff 低 | < 10% | Fold ↑ (信任对手有牌) |
| RiverBluff 高 | > 25% | Call ↑ (抓诈唬) |
| 3Bet 高 | > 12% | 4Bet 范围 ↓, Call 3Bet ↑ |
| FoldTo3Bet 高 | > 65% | 3Bet ↑ (高频3Bet施压) |
| FoldTo3Bet 低 | < 40% | 3Bet ↓ (减少3Bet诈唬) |

### 2.5 Exploit Sandbox（前端交互）

```
ExploitSandbox (分析结果页的 Tab)
├── StrategyComparison
│   ├── GTOStrategyBar (蓝色)
│   └── ExploitStrategyBar (橙色，叠加对比)
│
├── AdjustmentList
│   ├── AdjustmentCard × N
│   │   ├── ActionIcon (Call/Raise/Fold)
│   │   ├── DeltaBadge (+8% / -13%)
│   │   └── Reason (解释文字)
│   └── Summary
│
└── EVSimulator (可选：模拟调整后 EV 变化)
    ├── GTO_EV vs Exploit_EV 对比
    └── SensitivitySlider (调参数看 EV 变化)
```

---

## 3. Leak Detector (漏洞检测引擎)

### 3.1 检测维度

| 维度 | 检测项 | 正常范围 | 严重漏洞阈值 |
|------|--------|---------|------------|
| **Preflop** | VPIP 过高/过低 | 18-28% | >35% 或 <12% |
| **Preflop** | PFR 与 VPIP 差距 | PFR/VPIP > 0.6 | PFR/VPIP < 0.4 |
| **Preflop** | FoldTo3Bet | 50-60% | >70% (过度弃牌) 或 <35% |
| **Preflop** | BTN VPIP 与 UTG VPIP 差距 | BTN > UTG*1.5 | BTN ≈ UTG (位置意识差) |
| **Flop** | CBet 频率 | 55-70% | >80% (过度CBet) 或 <40% |
| **Flop** | FoldToCBet | 45-55% | >65% 或 <35% |
| **Turn** | Turn CBet | 50-65% | >75% 或 <35% |
| **Turn** | Turn Aggression Drop | Flop AF vs Turn AF 变化 < 40% | AF 骤降 > 50% |
| **River** | 过度Call Down | WTSD > 32% | WTSD > 38% (Calling Station) |
| **River** | 过度Fold | FoldToRiverBet > 60% | >70% |
| **全局** | 位置感知弱 | VPIP by Position 差异小 | 各位置 VPIP 差异 < 5% |
| **全局** | Winrate | > -5bb/100 | < -15bb/100 (严重亏损) |

### 3.2 实现

```python
# backend/app/coach/leak_detector.py

class LeakDetector:

    def detect(self, profile: PlayerProfile, detailed_stats: dict) -> list[Leak]:
        """
        扫描玩家画像，返回按严重程度排序的漏洞列表。
        每个漏洞包含：描述、严重程度、改善建议。
        """
        leaks = []

        # === Preflop Leaks ===
        if profile.vpip > 0.35:
            leaks.append(Leak(
                category='Preflop',
                severity=Severity.HIGH,
                title='入池率过高',
                description=f'VPIP={profile.vpip:.0%}，远高于推荐范围18-28%',
                impact='入池过多导致翻后处于不利位置，长期被剥削',
                suggestion='收紧前位开池范围，UTG弃掉同花连张以下手牌',
                target={'vpip': 0.25},
            ))

        if profile.fold_to_three_bet > 0.70:
            leaks.append(Leak(
                category='Preflop',
                severity=Severity.HIGH,
                title='面对3Bet过度弃牌',
                description=f'FoldTo3Bet={profile.fold_to_three_bet:.0%}，对手可用任意两张牌3Bet剥削你',
                impact='每次被3Bet即弃牌，对手可无限3Bet盈利',
                suggestion='练习4Bet诈唬范围，或Call 3Bet防守至少35%范围',
                target={'fold_to_three_bet': 0.55},
            ))

        # === Postflop Leaks ===
        if profile.cbet_flop > 0.80:
            leaks.append(Leak(
                category='Flop',
                severity=Severity.MEDIUM,
                title='Flop CBet 过高',
                description=f'Flop CBet={profile.cbet_flop:.0%}，几乎所有牌都CBet',
                impact='对手会跟注更多，且你Check时对手知道你完全没牌',
                suggestion='在干燥牌面上Check部分中等牌，保护Check范围',
                target={'cbet_flop': 0.65},
            ))

        # === Positional Leaks ===
        vpip_by_pos = detailed_stats.get('vpip_by_position', {})
        if vpip_by_pos:
            btn_vpip = vpip_by_pos.get('BTN', 0)
            utg_vpip = vpip_by_pos.get('UTG', 0)
            if utg_vpip > 0 and btn_vpip / utg_vpip < 1.3:
                leaks.append(Leak(
                    category='Position',
                    severity=Severity.MEDIUM,
                    title='位置意识不足',
                    description=f'BTN VPIP={btn_vpip:.0%} vs UTG VPIP={utg_vpip:.0%}，差异过小',
                    impact='无法利用位置优势盈利',
                    suggestion='BTN应比UTG松至少50%，在按钮位多玩投机牌',
                    target={'btn_utg_ratio': 1.8},
                ))

        # 按严重程度排序
        leaks.sort(key=lambda l: l.severity.value, reverse=True)
        return leaks
```

---

## 4. AI 长期教练 (Long-term Coach)

### 4.1 设计理念

MVP 的 AI 教练是**单局分析**。Phase 3 升级为**跨局趋势分析**：

```
单局教练 (MVP):     "这一手你应该Call因为..."
长期教练 (Phase 3):  "最近1000手你在BTN FoldTo3Bet 72%，这是一个需要改进的模式..."
```

### 4.2 工作流程

```
Player Profile (全局统计)
    │
    ▼
Leak Detector (漏洞列表)
    │
    ▼
Historical Trends (趋势数据)
    │
    ▼
Prompt Builder (长期分析模板)
    │
    ▼
LLM Coach (生成个性化训练计划)
    │
    ▼
Coaching Report (长期报告)
```

### 4.3 Prompt 设计

```python
# backend/app/ai/coach_prompts.py

LONG_TERM_COACH_SYSTEM = """你是一位职业扑克教练，拥有 GTO 理论深厚功底和丰富的实战教学经验。

你的学员已经使用本系统记录了大量手牌数据。你需要根据统计数据分析学员的长期漏洞，
并给出具体、可操作的改进建议。

## 分析要求
1. 指出 TOP 3 最严重的漏洞，按优先级排序
2. 每个漏洞用具体数据支撑（不要泛泛而谈）
3. 给出可操作的练习方案（具体到哪些手牌范围需要调整）
4. 设定改进目标和时间节点
5. 语气专业但鼓励性，不要打击学员信心

## 禁止
- 不要给出笼统建议（如"多思考"）
- 不要夸大数据（必须基于真实统计）
- 不要自行编造 EV 或 Equity 数据
"""

LONG_TERM_COACH_USER_TEMPLATE = """## 学员数据概览
- 总手数: {total_hands}
- 胜率: {winrate} bb/100
- 玩家分类: {player_type}

## 核心统计
- VPIP: {vpip}
- PFR: {pfr}
- 3Bet: {three_bet}
- Fold to 3Bet: {fold_to_three_bet}
- Aggression Factor: {af}
- CBet Flop: {cbet_flop}
- WTSD: {wtsd}
- W$SD: {wsd}

## 检测到的漏洞
{leaks_text}

## 位置分解
{position_breakdown}

## 趋势数据
- VPIP 趋势（最近500手）: {vpip_trend}
- PFR 趋势（最近500手）: {pfr_trend}
- Winrate 趋势: {winrate_trend}

请给出详细的分析报告和训练计划。"""
```

### 4.4 Coaching Report 结构

```json
{
  "report_id": "uuid",
  "player_name": "HeroPlayer",
  "period": {
    "from": "2026-06-01",
    "to": "2026-06-25",
    "total_hands": 5432
  },
  "summary": {
    "player_type": "Slightly Loose Passive",
    "winrate": -3.2,
    "overall_assessment": "你在翻前入池偏松，翻后过度被动，需要在激进度和位置意识上加强"
  },
  "top_leaks": [
    {
      "title": "BTN FoldTo3Bet 过高(72%)",
      "severity": "high",
      "impact": "对手可在BTN无限3Bet剥削你",
      "suggestion": "练习4Bet诈唬范围：A5s-A2s, KQo, AJo",
      "target": "降至55%",
      "timeline": "2周内改善"
    }
  ],
  "position_analysis": {
    "strength": "SB位置防守较好，FoldToSteal仅58%",
    "weakness": "CO位置过度跟注，3Bet仅4.2%"
  },
  "training_plan": [
    {
      "focus": "3Bet防守",
      "drills": ["面对BTN 3Bet时，用A5s-A2s做4Bet诈唬"],
      "weekly_goal": "本周FoldTo3Bet降至60%"
    }
  ],
  "progress_tracking": {
    "last_report_score": 62,
    "current_score": 65,
    "improvement": "+3"
  }
}
```

---

## 5. RAG 知识库

### 5.1 架构

```
┌─────────────────────────────────────┐
│          RAG Knowledge Pipeline      │
│                                      │
│  Document Ingestion                  │
│  ┌──────────┐    ┌───────────┐      │
│  │ PDF/MD   │───►│ Chunker    │      │
│  │ Import   │    │ (512 tokens)│     │
│  └──────────┘    └─────┬─────┘      │
│                        │             │
│                        ▼             │
│              ┌─────────────┐         │
│              │ Embedding    │         │
│              │ (OpenAI ada) │         │
│              └──────┬──────┘         │
│                     │                │
│                     ▼                │
│         ┌───────────────────┐        │
│         │ pgvector          │        │
│         │ knowledge_chunks  │        │
│         └────────┬──────────┘        │
│                  │                   │
│  Retrieval       ▼                   │
│  ┌───────────────────────┐          │
│  │ Query → Embedding      │          │
│  │ → Cosine Similarity    │          │
│  │ → Top-K Results        │          │
│  └───────────┬───────────┘          │
│              │                       │
│              ▼                       │
│  Augmented Prompt                    │
│  ┌────────────────────────┐         │
│  │ System: 你是扑克教练    │         │
│  │ Context: [检索到的理论]  │         │
│  │ Question: [用户牌局]     │         │
│  └────────────────────────┘         │
└─────────────────────────────────────┘
```

### 5.2 知识来源（首批）

| 来源 | 类型 | 说明 |
|------|------|------|
| Modern Poker Theory | 书籍摘要 | GTO 核心理论 |
| Applications of No-Limit Hold'em | 书籍摘要 | 翻前/翻后决策框架 |
| GTO Wizard Blog | 公开文章 | 最新 GTO 分析 |
| Upswing Poker Articles | 公开文章 | 实战策略 |
| 自定义 FAQ | 用户维护 | 常见场景解析 |

> **合规注意**: 仅摄入用户可以合法使用的公开内容或自有内容。不自动抓取付费内容。

### 5.3 实现

```python
# backend/app/rag/ingestion.py

class DocumentIngestor:
    """文档摄入管道"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunker = TextChunker(chunk_size, chunk_overlap)
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-small")

    async def ingest(self, file_path: str, metadata: dict) -> int:
        """摄入单个文档，返回 chunk 数量"""
        # 1. 解析文件
        text = await self._parse_file(file_path)

        # 2. 分块
        chunks = self.chunker.split(text)

        # 3. 生成 Embedding
        embeddings = await self.embedder.embed_batch(chunks)

        # 4. 存储到 PostgreSQL + pgvector
        doc = KnowledgeDocument(title=metadata['title'], source=metadata['source'])
        db.add(doc)
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            db.add(KnowledgeChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk,
                embedding=emb
            ))

        return len(chunks)

# backend/app/rag/retriever.py

class KnowledgeRetriever:
    """知识检索"""

    async def retrieve(
        self, query: str, top_k: int = 5, min_similarity: float = 0.75
    ) -> list[RetrievedChunk]:
        """检索与查询最相关的知识片段"""
        query_embedding = await self.embedder.embed(query)

        results = await db.execute(
            select(KnowledgeChunk)
            .order_by(
                KnowledgeChunk.embedding.cosine_distance(query_embedding)
            )
            .limit(top_k)
        )
        return [
            RetrievedChunk(content=r.content, similarity=1 - r.distance, source=r.document.source)
            for r in results
            if 1 - r.distance >= min_similarity
        ]
```

### 5.4 RAG 增强 Prompt

```python
RAG_ENHANCED_SYSTEM = """你是一位职业扑克教练。

## 参考理论（从知识库检索）
{retrieved_contexts}

## 分析要求
1. 基于 GTO Solver 结果给出建议
2. 引用上述理论来源支持你的分析
3. 在引用时注明来源（如 "根据 Modern Poker Theory..."）
4. 不要编造不存在的理论或数据
"""
```

### 5.5 技术选型：pgvector vs 专用向量数据库

选择 **pgvector**（PostgreSQL 扩展）：
- 已在用 PostgreSQL，零额外运维成本
- 数据量预估 < 10 万条 chunk，pgvector 性能足够
- Embedding 和数据在同一事务中，一致性有保障
- 支持 IVFFlat / HNSW 索引

---

## 6. Coach Personalities（教练人格）

### 6.1 四种教练

| 教练 | 分析风格 | 适用场景 | System Prompt 特征 |
|------|---------|---------|-------------------|
| **GTO Coach** | 严谨、数学驱动 | 学习 GTO 基线 | 强调平衡、频率、不可剥削性 |
| **Exploit Coach** | 务实、对手驱动 | 实战剥削 | 强调对手漏洞、偏离 GTO 的理由 |
| **Tournament Coach** | ICM 导向 | 锦标赛 | 强调生存、ICM 压力、盲注结构 |
| **Cash Coach** | 深度筹码 | 现金局 | 强调深筹码策略、隐含赔率 |

### 6.2 Personality 实现

```python
# backend/app/ai/personalities.py

class CoachPersonality:
    """Base personality definition"""

    name: str
    system_prompt: str
    analysis_focus: list[str]
    tone: str  # 'analytical' | 'practical' | 'aggressive' | 'cautious'

GTO_COACH = CoachPersonality(
    name="GTO Coach",
    system_prompt="""你是一位纯粹的 GTO 策略教练。你的分析完全基于 Solver 计算结果。
    你从不建议偏离 GTO，除非在 Exploit 章节中明确标注。
    你使用精确的频率和百分比，避免模糊表述。
    你的座右铭：长期来看，GTO 是唯一不被剥削的策略。""",
    analysis_focus=["balance", "frequencies", "range_construction"],
    tone="analytical"
)

EXPLOIT_COACH = CoachPersonality(
    name="Exploit Coach",
    system_prompt="""你是一位实战导向的剥削型教练。GTO 是你的参考基线，但你会毫不犹豫地建议偏离。
    当对手有明显漏洞时，你优先考虑如何最大化剥削，而不是理论平衡。
    你的座右铭：GTO 保证不输，Exploit 才能赢钱。""",
    analysis_focus=["opponent_tendencies", "exploit_opportunities", "deviation_justification"],
    tone="aggressive"
)

TOURNAMENT_COACH = CoachPersonality(
    name="Tournament Coach",
    system_prompt="""你是一位锦标赛专家。你的分析始终考虑 ICM 压力、盲注级别和生命周期阶段。
    你会提醒玩家注意生存价值，而不只是 Chip EV。
    你的座右铭：锦标赛不是赢最多筹码，而是活得最久。""",
    analysis_focus=["icm_pressure", "stack_depth", "bubble_factor", "survival"],
    tone="cautious"
)

CASH_COACH = CoachPersonality(
    name="Cash Coach",
    system_prompt="""你是一位现金局专家。你以 bb/100 为唯一成功标准。
    你关注深筹码策略、隐含赔率和多街规划。
    你的座右铭：每个决策都是独立的投资，追求最大化期望价值。""",
    analysis_focus=["deep_stack", "implied_odds", "multi_street", "value_betting"],
    tone="practical"
)
```

### 6.3 前端 Personality Switcher

```
CoachPersonalitySwitcher
├── PersonalityCard × 4 (Grid)
│   ├── Avatar + Name
│   ├── StyleTag (分析型/实战型/激进型/谨慎型)
│   ├── FocusList (分析重点)
│   └── SelectButton (当前选中高亮)
│
└── ActiveIndicator (当前激活教练的徽章)
```

---

## 7. Training Journal（训练日志）

### 7.1 功能设计

```
TrainingJournalPage
├── ProgressOverview (进步总览)
│   ├── ScoreCard (当前评分 /100)
│   ├── ScoreTrendChart (评分变化折线图，按周)
│   └── StreakTracker (连续练习天数)
│
├── LeakTracker (漏洞追踪)
│   ├── LeakCard × N
│   │   ├── LeakTitle
│   │   ├── CurrentValue vs TargetValue (进度条)
│   │   ├── ImprovementTrend (改善趋势箭头)
│   │   └── AssignedAt / Deadline
│   └── NewLeakAlert (新漏洞提醒 Badge)
│
├── SessionLog (练习记录)
│   ├── CalendarHeatmap (每日练习量热力图)
│   └── SessionList (按日期分组)
│       └── SessionCard
│           ├── Date + Duration
│           ├── Hands Analyzed
│           └── Key Takeaway
│
└── Milestones (里程碑)
    ├── "完成100手分析" → Badge
    ├── "VPIP 改善至目标" → Badge
    └── "连续7天练习" → Badge
```

---

## 8. API 扩展

### 8.1 Exploit API

```
POST /api/v1/analyze            # 扩展: 返回增加 exploit_result 字段
GET  /api/v1/exploit/simulate   # 策略模拟: 调整参数看 EV 变化
```

### 8.2 Leak API

```
GET  /api/v1/coach/leaks/{player_name}       # 获取玩家漏洞列表
GET  /api/v1/coach/report/{player_name}       # 生成长期训练报告
GET  /api/v1/coach/progress/{player_name}     # 获取进步趋势
```

### 8.3 RAG API

```
POST /api/v1/knowledge/ingest      # 摄入文档
GET  /api/v1/knowledge/search?q=   # 搜索知识库
GET  /api/v1/knowledge/sources     # 列出已摄入的知识来源
```

### 8.4 Coach Personality API

```
GET  /api/v1/coach/personalities                # 列出可用教练人格
PUT  /api/v1/coach/personalities/active          # 切换激活的教练
POST /api/v1/analyze?coach=exploit               # 指定教练分析（Query参数）
```

---

## 9. 验收标准

### 功能
- [ ] Exploit Engine 基于对手画像正确修正 GTO 策略（覆盖 10+ 条修正规则）
- [ ] Exploit Sandbox 可展示 GTO vs Exploit 策略对比
- [ ] Leak Detector 检测出至少 8 类常见漏洞
- [ ] AI 长期教练生成包含 TOP3 漏洞 + 训练计划的完整报告
- [ ] RAG 知识库摄入至少 5 份文档，检索命中率 > 80%
- [ ] AI 分析引用理论知识来源
- [ ] 四种教练人格产出差异化分析（GTO vs Exploit 建议不同）
- [ ] Training Journal 追踪至少 3 项指标的长期趋势

### 性能
- [ ] Exploit Engine 计算 < 200ms
- [ ] Leak Detector 扫描 10000 手数据 < 3s
- [ ] RAG 检索（含 Embedding） < 500ms
- [ ] 长期报告生成 < 30s（含 LLM 响应）

### 产品
- [ ] 用户可按教练人格切换获得不同风格的分析
- [ ] 漏洞检测结果与实际表现一致（人工验证 50 个样本 > 90% 准确率）
- [ ] RAG 引用不编造来源

---

## 10. 技术决策

### 10.1 Exploit 修正方式：规则引擎 vs ML 模型

选择**规则引擎**：MVP 阶段到 Phase 3 的数据量不足以训练可靠的 ML 模型。规则引擎透明、可解释、可调优，符合"AI 只做解释"的架构原则。未来数据量充足后可引入 RL 微调 Solver 参数。

### 10.2 向量存储：pgvector vs Pinecone/Weaviate

选择 **pgvector**：降低运维复杂度，与现有 PostgreSQL 统一。数据规模（<10 万 chunk）在 pgvector + HNSW 索引下完全够用。

### 10.3 Coach Personality 的实现方式

不改动 Solver 或 Exploit Engine 的逻辑，**纯靠 System Prompt 差异**实现不同人格。这保证核心计算一致，只是解释风格不同，避免维护多份计算逻辑。
