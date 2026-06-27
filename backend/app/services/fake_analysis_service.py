"""Fake Analysis Service — M1 demo mode, no DB / Redis required.

Runs the real Solver in-memory + real AI (DeepSeek V4-Pro) via api key.
Returns full AnalysisResponse without any persistence.
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.ai.factory import get_coach
from app.schemas.analysis import AnalysisResponse, StrategyBreakdown
from app.schemas.game_state import GameStateRequest, GameMode
from app.solver.factory import get_solver


class FakeAnalysisService:
    """In-memory analysis pipeline for M1 development / demo.

    Uses:
      - Real Monte Carlo Solver (mode-aware equity_calculator)
      - Real AI Coach (DeepSeek V4-Pro — requires DEEPSEEK_API_KEY in .env)
      - No database persistence
      - No Redis caching
    """

    async def analyze(self, game_state: GameStateRequest) -> AnalysisResponse:
        mode = game_state.mode.value if isinstance(game_state.mode, GameMode) else game_state.mode
        solver = get_solver(mode)
        coach = get_coach()

        # 1. Real Solver (mode-aware)
        solver_result = await solver.solve(game_state)

        # 2. AI (will use fallback since no API key by default)
        ai_text = await coach.analyze(game_state, solver_result)

        # 3. Parse AI output
        gto, risk, points = self._parse_ai_output(ai_text)

        # 4. Get recommendation
        strategy = solver_result.strategy
        recommendation = max(
            [("Call", strategy.call), ("Raise", strategy.raise_), ("Fold", strategy.fold)],
            key=lambda x: x[1],
        )[0]

        # 5. Generate mock IDs
        hand_id = str(uuid4())
        analysis_id = str(uuid4())

        return AnalysisResponse(
            hand_id=hand_id,
            analysis_id=analysis_id,
            recommendation=recommendation,
            equity=solver_result.equity,
            call_ev=solver_result.call_ev,
            raise_ev=solver_result.raise_ev,
            fold_ev=solver_result.fold_ev,
            strategy=StrategyBreakdown(
                call=strategy.call,
                raise_=strategy.raise_,
                fold=strategy.fold,
            ),
            gto_analysis=gto,
            risk_analysis=risk,
            exploit_analysis="暂无利用分析",
            learning_points=points,
            created_at=datetime.now(timezone.utc),
        )

    def _parse_ai_output(self, ai_text: str) -> tuple[str, str, list[str]]:
        """Parse AI markdown into structured sections."""
        gto = ""
        risk = ""
        points: list[str] = []

        lines = ai_text.split("\n")
        current_section = ""

        for line in lines:
            if "### GTO" in line or "## GTO" in line or "**GTO" in line:
                current_section = "gto"
                continue
            elif "### 风险" in line or "## 风险" in line:
                current_section = "risk"
                continue
            elif "### 学习要点" in line or "## 学习要点" in line:
                current_section = "points"
                continue
            elif line.startswith("### ") or line.startswith("## "):
                current_section = ""
                continue

            if current_section == "gto":
                gto += line + "\n"
            elif current_section == "risk":
                risk += line + "\n"
            elif current_section == "points":
                stripped = line.strip()
                if stripped.startswith("- "):
                    points.append(stripped[2:])

        return (
            gto.strip() or ai_text[:500],
            risk.strip() or "暂无显著风险",
            points if points else ["基于Solver建议做出决策", "注意底池赔率与胜率的关系"],
        )


fake_analysis_service = FakeAnalysisService()
