"""OpenAI Coach Provider — uses GPT-4o to generate coaching analysis."""

from app.config import settings
from app.ai.base import CoachProvider
from app.ai.prompt_builder import PromptBuilder
from app.schemas.game_state import GameStateRequest
from app.schemas.solver import SolverResult


class OpenAIProvider(CoachProvider):
    """Coach provider using OpenAI's GPT models."""

    def __init__(self):
        self.model = settings.openai_model
        self.prompt_builder = PromptBuilder()

    async def analyze(
        self,
        game_state: GameStateRequest,
        solver_result: SolverResult,
    ) -> str:
        """Generate analysis using OpenAI API."""
        system_prompt, user_prompt = self.prompt_builder.build(
            game_state, solver_result
        )

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                max_tokens=1500,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            # Fallback: return a formatted summary without AI
            return self._fallback_analysis(game_state, solver_result)

    async def get_provider_name(self) -> str:
        return "OpenAI"

    def _fallback_analysis(self, game_state: GameStateRequest, solver_result: SolverResult) -> str:
        """Generate a basic analysis when AI is unavailable."""
        cards = " ".join(game_state.hero_cards)
        position = game_state.hero_position.value
        equity = solver_result.equity
        strategy = solver_result.strategy

        best_action = max(
            [("Call", strategy.call), ("Raise", strategy.raise_), ("Fold", strategy.fold)],
            key=lambda x: x[1],
        )

        return f"""## GTO 分析

**手牌**: {cards}  
**位置**: {position}  
**胜率(Equity)**: {equity:.1f}%

**GTO 推荐策略**:
- Call: {strategy.call:.1f}%
- Raise: {strategy.raise_:.1f}%
- Fold: {strategy.fold:.1f}%

**建议**: 推荐以 **{best_action[0]}** 为主（{best_action[1]:.1f}%），这是当前局面下EV最高的选择。

**EV 对比**:
- Call EV: {solver_result.call_ev:+.3f}bb
- Raise EV: {solver_result.raise_ev:+.3f}bb
- Fold EV: {solver_result.fold_ev:+.3f}bb

*(AI 服务暂时不可用，以上为基础数据摘要)*
"""
