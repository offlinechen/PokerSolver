"""TexasSolver — Monte Carlo GTO equity calculator for Standard Hold'em.

Uses the engine modules (DeckConfig, HandEvaluator) and range tables
to compute equity, EV, and strategy for each game mode.
"""

from app.schemas.game_state import GameStateRequest
from app.schemas.solver import SolverResult, StrategyBreakdown
from app.solver.base import SolverProvider
from app.solver.equity_calculator import calculate_equity

DEFAULT_SIMULATIONS = 5000


class SolverBase(SolverProvider):
    """Shared logic for all game-mode solvers.

    Subclasses set `self.mode` to determine deck config, ranges, and strategy.
    """

    mode: str = "standard"
    simulations: int = DEFAULT_SIMULATIONS

    async def solve(self, game_state: GameStateRequest) -> SolverResult:
        equity = await self._estimate_equity(game_state)
        face_amount = self._extract_face_amount(game_state)
        ev_data = self._calculate_ev(game_state, equity, face_amount)
        strategy = self._build_strategy(equity, game_state)

        return SolverResult(
            equity=round(equity, 1),
            call_ev=round(ev_data["call_ev"], 4),
            raise_ev=round(ev_data["raise_ev"], 4),
            fold_ev=round(ev_data["fold_ev"], 4),
            strategy=strategy,
        )

    async def get_provider_name(self) -> str:
        return f"{self.mode.title()} Solver (Monte Carlo)"

    # ------------------------------------------------------------------ helpers

    async def _estimate_equity(self, gs: GameStateRequest) -> float:
        return calculate_equity(
            hero_cards=gs.hero_cards,
            board_cards=gs.board_cards,
            hero_position=gs.hero_position.value,
            mode=self.mode,
            simulations=self.simulations,
        )

    @staticmethod
    def _extract_face_amount(gs: GameStateRequest) -> float:
        if not gs.actions:
            return 0.0
        for action in reversed(gs.actions):
            if action.actor == "Villain" and action.action in ("BET", "RAISE", "ALL_IN"):
                return action.amount or 0.0
        return 0.0

    @staticmethod
    def _calculate_ev(
        gs: GameStateRequest, equity: float, face_amount: float
    ) -> dict[str, float]:
        pot = gs.pot_size_bb
        stack = gs.stack_size_bb
        eq = equity / 100.0

        fold_ev = 0.0

        if face_amount > 0:
            total_pot_after_call = pot + face_amount
            call_ev = eq * total_pot_after_call - face_amount
        else:
            call_ev = eq * pot

        raise_sizing = (
            face_amount * 3 if face_amount > 0 else pot * 0.67
        )
        raise_sizing = min(raise_sizing, stack)

        fold_equity_rate = 0.35

        if raise_sizing >= stack:
            total_pot_after_allin = pot + raise_sizing
            raise_ev = eq * total_pot_after_allin - raise_sizing
        else:
            continuing_equity = eq * 0.85
            total_pot_after_raise = pot + raise_sizing
            raise_ev = (
                fold_equity_rate * pot
                + (1 - fold_equity_rate)
                * (continuing_equity * total_pot_after_raise - raise_sizing)
            )

        return {
            "call_ev": call_ev,
            "raise_ev": raise_ev,
            "fold_ev": fold_ev,
        }

    @staticmethod
    def _build_strategy(equity: float, gs: GameStateRequest) -> StrategyBreakdown:
        stack = gs.stack_size_bb
        is_shallow = stack < 30

        if equity >= 70:
            fold_pct = 2.0
            raise_pct = 80.0 if is_shallow else 65.0
            call_pct = 100.0 - fold_pct - raise_pct
        elif equity >= 55:
            fold_pct = 5.0
            raise_pct = 50.0
            call_pct = 45.0
        elif equity >= 40:
            fold_pct = 15.0
            raise_pct = 25.0
            call_pct = 60.0
        elif equity >= 25:
            fold_pct = 50.0
            raise_pct = 5.0
            call_pct = 45.0
        else:
            fold_pct = 85.0
            raise_pct = 3.0
            call_pct = 12.0

        return StrategyBreakdown(
            call=round(call_pct, 1),
            raise_=round(raise_pct, 1),
            fold=round(fold_pct, 1),
        )


class TexasSolver(SolverBase):
    """Standard 52-card Texas Hold'em solver."""
    mode = "standard"


class ShortDeckSolver(SolverBase):
    """36-card Short Deck (6+) Hold'em solver.

    Key differences from Standard:
    - 36-card deck (6-A, removing 2-5)
    - Flush beats Full House
    - Wheel = A-6-7-8-9
    - Wider villain ranges (equity is flatter)
    """
    mode = "shortdeck"


class SNGSolver(SolverBase):
    """SNG solver — standard deck with ICM adjustments (M2).

    M1: Uses standard EV (placeholder).
    M2: Adds ICM conversion and push/fold tables.
    """
    mode = "standard"  # Uses standard deck; ICM layer to be added in M2


class SquidSolver(SolverBase):
    """Squid Game survival-mode solver (M2).

    M1: Uses standard EV (placeholder).
    M2: Adds survival probability model and rank-based adjustments.
    """
    mode = "standard"  # Uses standard deck; survival EV to be added in M2
