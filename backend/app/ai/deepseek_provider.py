"""DeepSeek Coach Provider — uses DeepSeek V4-Pro for Chinese-language coaching analysis.

DeepSeek's API is OpenAI-compatible. We use the `openai` SDK with a custom base URL.
V4-Pro supports extended reasoning via `thinking` and `reasoning_effort` parameters.
"""

from app.config import settings
from app.ai.base import CoachProvider
from app.ai.prompt_builder import PromptBuilder
from app.schemas.game_state import GameStateRequest
from app.schemas.solver import SolverResult


DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekProvider(CoachProvider):
    """Coach provider using DeepSeek V4-Pro.

    Key parameters (V4-Pro specific):
    - reasoning_effort: "low" | "medium" | "high" — controls depth of reasoning chain
    - thinking: "enabled" | "disabled" — enables extended reasoning phase

    For poker coaching, we enable thinking with medium effort for balanced
    analysis quality vs. response time.
    """

    def __init__(self):
        self.model = settings.deepseek_model
        self.api_key = settings.deepseek_api_key
        self.reasoning_effort = settings.deepseek_reasoning_effort
        self.thinking_enabled = settings.deepseek_thinking == "enabled"
        self.prompt_builder = PromptBuilder()

    async def analyze(
        self,
        game_state: GameStateRequest,
        solver_result: SolverResult,
    ) -> str:
        """Generate analysis using DeepSeek V4-Pro API."""
        system_prompt, user_prompt = self.prompt_builder.build(
            game_state, solver_result
        )

        if not self.api_key:
            return self._fallback_analysis(game_state, solver_result)

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=DEEPSEEK_BASE_URL,
            )

            # Pass DeepSeek-specific params via extra_body (openai SDK compatible)
            extra_body = {
                "thinking": {"type": "enabled"} if self.thinking_enabled else {"type": "disabled"},
                "reasoning_effort": self.reasoning_effort,
            }

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                max_tokens=1500,
                extra_body=extra_body,
            )
            content = response.choices[0].message.content
            return content or self._fallback_analysis(game_state, solver_result)

        except Exception as e:
            return self._fallback_analysis(game_state, solver_result, str(e))

    async def get_provider_name(self) -> str:
        thinking = "+thinking" if self.thinking_enabled else ""
        return f"DeepSeek V4-Pro{thinking}"


    def _fallback_analysis(
        self,
        game_state: GameStateRequest,
        solver_result: SolverResult,
        error: str = "",
    ) -> str:
        """Generate a basic analysis when AI is unavailable."""
        cards = " ".join(game_state.hero_cards)
        position = game_state.hero_position.value
        equity = solver_result.equity
        strategy = solver_result.strategy

        best_action = max(
            [("Call", strategy.call), ("Raise", strategy.raise_), ("Fold", strategy.fold)],
            key=lambda x: x[1],
        )

        error_note = f"\n*(AI 接口返回错误: {error[:100]})*" if error else ""

        return f"""## GTO 分析

**手牌**: {cards}  
**位置**: {position}  
**胜率(Equity)**: {equity:.1f}%

**GTO 推荐策略分布**:
- Call: {strategy.call:.1f}%
- Raise: {strategy.raise_:.1f}%
- Fold: {strategy.fold:.1f}%

**建议**: 推荐以 **{best_action[0]}** 为主（{best_action[1]:.1f}%），这是当前局面下EV最高的选择。

**EV 对比**:
- Call EV: {solver_result.call_ev:+.3f}bb
- Raise EV: {solver_result.raise_ev:+.3f}bb
- Fold EV: {solver_result.fold_ev:+.3f}bb

{error_note}
*(AI 服务暂时不可用，以上为基础数据摘要)*
"""
