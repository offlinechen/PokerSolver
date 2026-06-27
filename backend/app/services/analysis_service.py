"""Analysis Service — orchestrates Solver → AI → Persist pipeline."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_coach
from app.models.action import Action
from app.models.analysis import Analysis
from app.models.hand import Hand
from app.models.player import Player
from app.schemas.analysis import AnalysisResponse, StrategyBreakdown
from app.schemas.game_state import GameStateRequest, GameMode
from app.schemas.solver import SolverResult
from app.services.cache_service import cache_service
from app.solver.factory import get_solver
from app.utils.hash import compute_game_state_hash


class AnalysisService:
    """Orchestrates the full analysis pipeline."""

    async def analyze(
        self, db: AsyncSession, game_state: GameStateRequest
    ) -> AnalysisResponse:
        """
        Full analysis pipeline:
        1. Check Solver cache → if hit, skip Solver
        2. Run Solver (mode-aware)
        3. Check AI cache → if hit, skip AI
        4. Run AI Coach
        5. Persist results
        """
        mode = game_state.mode.value if isinstance(game_state.mode, GameMode) else game_state.mode

        # 1. Build state hash (includes mode for cache key uniqueness)
        state_hash = compute_game_state_hash(
            hero_cards=game_state.hero_cards,
            board_cards=game_state.board_cards,
            position=game_state.hero_position.value,
            stack_size=game_state.stack_size_bb,
            pot_size=game_state.pot_size_bb,
            actions=[a.model_dump() for a in game_state.actions],
            mode=mode,
        )

        # 2. Solver (with cache, mode-aware)
        solver_result = await cache_service.get_solver_result(state_hash)
        if solver_result is None:
            solver = get_solver(mode)
            solver_result = await solver.solve(game_state)
            await cache_service.set_solver_result(state_hash, solver_result)

        # 3. Persist hand + actions in DB
        hand = await self._save_hand(db, game_state)

        # 4. AI Coach (with cache)
        coach = get_coach()
        prompt_hash = compute_game_state_hash(
            game_state.hero_cards,
            game_state.board_cards,
            game_state.hero_position.value,
            solver_result.equity,
            solver_result.model_dump(),
        )

        ai_text = await cache_service.get_ai_result(prompt_hash)
        if ai_text is None:
            ai_text = await coach.analyze(game_state, solver_result)
            await cache_service.set_ai_result(prompt_hash, ai_text)

        # 5. Parse AI output into structured sections
        gto, exploit, risk, points = self._parse_ai_output(ai_text)

        # 6. Determine recommendation
        strategy = solver_result.strategy
        recommendation = max(
            [("Call", strategy.call), ("Raise", strategy.raise_), ("Fold", strategy.fold)],
            key=lambda x: x[1],
        )[0]

        # 7. Persist analysis
        analysis = await self._save_analysis(
            db,
            hand_id=hand.id,
            solver_result=solver_result,
            recommendation=recommendation,
            gto_analysis=gto,
            exploit_analysis=exploit,
            risk_analysis=risk,
            learning_points=points,
        )

        return AnalysisResponse(
            hand_id=hand.id,
            analysis_id=analysis.id,
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
            exploit_analysis=exploit,
            risk_analysis=risk,
            learning_points=points,
            created_at=analysis.created_at,
        )

    async def _save_hand(
        self, db: AsyncSession, game_state: GameStateRequest
    ) -> Hand:
        """Persist hand and its actions to database."""
        hand = Hand(
            id=str(uuid4()),
            hero_position=game_state.hero_position.value,
            hero_cards="".join(game_state.hero_cards),
            board_cards="".join(game_state.board_cards) if game_state.board_cards else None,
            stack_size_bb=game_state.stack_size_bb,
            pot_size_bb=game_state.pot_size_bb,
        )
        db.add(hand)

        # Create players
        hero_player = Player(
            id=str(uuid4()),
            hand_id=hand.id,
            seat_number=0,
            player_type="Hero",
            position=game_state.hero_position.value,
            stack_size_bb=game_state.stack_size_bb,
        )
        db.add(hero_player)

        villain_player = Player(
            id=str(uuid4()),
            hand_id=hand.id,
            seat_number=1,
            player_type="Villain",
            position="BB",  # Simplified for MVP
            stack_size_bb=game_state.stack_size_bb,
        )
        db.add(villain_player)

        # Create actions
        for i, action in enumerate(game_state.actions):
            player = hero_player if action.actor.value == "Hero" else villain_player
            db_action = Action(
                id=str(uuid4()),
                hand_id=hand.id,
                player_id=player.id,
                street=action.street.value,
                action_type=action.action.value,
                amount=action.amount,
                action_order=i + 1,
            )
            db.add(db_action)

        await db.flush()
        return hand

    async def _save_analysis(
        self,
        db: AsyncSession,
        hand_id: str,
        solver_result: SolverResult,
        recommendation: str,
        gto_analysis: str,
        exploit_analysis: str,
        risk_analysis: str,
        learning_points: list[str],
    ) -> Analysis:
        """Persist analysis result."""
        analysis = Analysis(
            id=str(uuid4()),
            hand_id=hand_id,
            recommendation=recommendation,
            equity=solver_result.equity,
            call_ev=solver_result.call_ev,
            raise_ev=solver_result.raise_ev,
            fold_ev=solver_result.fold_ev,
            strategy=json.dumps(solver_result.strategy.model_dump()),
            gto_analysis=gto_analysis,
            exploit_analysis=exploit_analysis,
            risk_analysis=risk_analysis,
            learning_points=json.dumps(learning_points),
        )
        db.add(analysis)
        await db.flush()
        return analysis

    def _parse_ai_output(self, ai_text: str) -> tuple[str, str, str, list[str]]:
        """Parse the AI's markdown output into structured sections.

        Returns:
            Tuple of (gto_analysis, exploit_analysis, risk_analysis, learning_points)
        """
        gto = ""
        exploit = ""
        risk = ""
        points: list[str] = []

        # Simple parsing based on markdown headings
        lines = ai_text.split("\n")
        current_section = ""

        for line in lines:
            if "### GTO" in line or "## GTO" in line:
                current_section = "gto"
                continue
            elif "### 利用" in line or "## 利用" in line or "### Exploit" in line or "## Exploit" in line:
                current_section = "exploit"
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
            elif current_section == "exploit":
                exploit += line + "\n"
            elif current_section == "risk":
                risk += line + "\n"
            elif current_section == "points":
                stripped = line.strip()
                if stripped.startswith("- "):
                    points.append(stripped[2:])

        return (
            gto.strip() or "暂无GTO分析",
            exploit.strip() or "暂无利用分析",
            risk.strip() or "暂无风险分析",
            points if points else ["持续练习，关注Solver建议"],
        )
