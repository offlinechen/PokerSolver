"""Prompt Builder — builds structured prompts for LLM analysis."""

from app.schemas.game_state import GameStateRequest
from app.schemas.solver import SolverResult


class PromptBuilder:
    """Builds prompts for the AI coach based on game state and Solver results."""

    SYSTEM_PROMPT = """你是一位职业德州扑克教练，精通 GTO (Game Theory Optimal) 策略。

你的任务是：根据 Solver 计算出的 GTO 数据，用通俗易懂的中文向学员解释当前局面的最优决策。

## 分析要求：
1. **GTO分析**: 解释为什么 GTO 推荐当前的策略比例，从范围构建、牌面纹理角度分析
2. **风险分析**: 指出当前决策的主要风险和对手的可能范围
3. **学习要点**: 提炼 2-3 条可迁移的扑克知识，帮助学员举一反三

## 输出格式（使用Markdown）：
### GTO分析
[详细分析，包括范围推理和手牌价值评估]

### 风险分析
[指出主要风险和需要注意的情况]

### 学习要点
- 要点1
- 要点2
- 要点3

## 禁止：
- 不要编造 Solver 数据（EV、Equity等由系统提供，你只需解释）
- 不要给出赌徒式的建议（如"相信直觉"）
- 不要评价对手的"运气"
- 控制字数在 300-500 字"""

    def build(
        self, game_state: GameStateRequest, solver_result: SolverResult
    ) -> tuple[str, str]:
        """Build system and user prompts.

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        hero_cards = " ".join(game_state.hero_cards)
        board = " ".join(game_state.board_cards) if game_state.board_cards else "（翻前）"
        position = game_state.hero_position.value
        stack = game_state.stack_size_bb
        pot = game_state.pot_size_bb
        mode = game_state.mode.value if hasattr(game_state.mode, 'value') else str(game_state.mode)

        mode_names = {
            "standard": "标准德州（52张牌）",
            "shortdeck": "短牌模式（36张牌，6-A，同花>葫芦）",
            "sng": "SNG锦标赛模式",
            "squid": "鱿鱼生存模式",
        }
        mode_display = mode_names.get(mode, mode)

        # Build action history
        action_lines = []
        if game_state.actions:
            for action in game_state.actions:
                action_lines.append(
                    f"- [{action.street.value}] {action.actor.value}: {action.action.value}"
                    + (f" {action.amount}bb" if action.amount else "")
                )
        action_text = "\n".join(action_lines) if action_lines else "（无行动记录）"

        strategy = solver_result.strategy

        user_prompt = f"""## 当前牌局

**游戏模式**: {mode_display}
**Hero手牌**: {hero_cards}
**公共牌**: {board}
**位置**: {position}
**筹码深度**: {stack}bb
**底池大小**: {pot}bb

## 行动历史
{action_text}

## Solver 计算结果

**胜率 (Equity)**: {solver_result.equity:.1f}%

**GTO 策略分布**:
- Call: {strategy.call:.1f}%
- Raise: {strategy.raise_:.1f}%
- Fold: {strategy.fold:.1f}%

**各行动 EV**:
- Call EV: {solver_result.call_ev:+.3f}bb
- Raise EV: {solver_result.raise_ev:+.3f}bb
- Fold EV: {solver_result.fold_ev:+.3f}bb

---

请根据以上数据，给出详细的扑克分析。"""

        return self.SYSTEM_PROMPT, user_prompt
