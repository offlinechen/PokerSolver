"""TexasSolver — Monte Carlo GTO equity calculator.

Uses the equity_calculator module to perform real Monte Carlo simulations
for hand equity, then derives EV and strategy recommendations from the results.
"""

from app.schemas.game_state import GameStateRequest, Street
from app.schemas.solver import SolverResult, StrategyBreakdown
from app.solver.base import SolverProvider
from app.solver.equity_calculator import calculate_equity


# Simulation rounds — higher = more accurate but slower
DEFAULT_SIMULATIONS = 5000


class TexasSolver(SolverProvider):
    """Real equity-based solver using Monte Carlo simulation.

    Calculates hand equity against position-based villain ranges,
    derives Expected Value (EV) for each action, and recommends
    a GTO-aligned strategy breakdown.
    """

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
        return "TexasSolver (Monte Carlo)"

    # ------------------------------------------------------------------ helpers

    async def _estimate_equity(self, gs: GameStateRequest) -> float:
        """Run Monte Carlo simulation for hero equity against villain range."""
        return calculate_equity(
            hero_cards=gs.hero_cards,
            board_cards=gs.board_cards,
            hero_position=gs.hero_position.value,
            simulations=DEFAULT_SIMULATIONS,
        )

    @staticmethod
    def _extract_face_amount(gs: GameStateRequest) -> float:
        """Determine how much hero needs to call (the 'facing bet').

        If hero is last to act and facing a bet/raise, extract it.
        Otherwise, assume hero is first to act (no bet to call yet).
        """
        if not gs.actions:
            return 0.0

        # Look at the most recent villain bet/raise
        for action in reversed(gs.actions):
            if action.actor == "Villain" and action.action in ("BET", "RAISE", "ALL_IN"):
                return action.amount or 0.0

        return 0.0

    @staticmethod
    def _calculate_ev(
        gs: GameStateRequest, equity: float, face_amount: float
    ) -> dict[str, float]:
        """Calculate Expected Value for fold / call / raise.

        Pot is assumed to already include villain's bet (face_amount).
        So calling means putting in face_amount to win pot + face_amount.

        fold_ev = 0   (we don't lose more, we just forfeit our equity)
        call_ev = equity * (pot + face) - (1 - equity) * face
        raise_ev = estimate based on fold equity + equity when called
        """
        pot = gs.pot_size_bb
        stack = gs.stack_size_bb
        eq = equity / 100.0

        # Fold EV is always 0 (BBs already committed are sunk cost)
        fold_ev = 0.0

        # Call EV: how much we expect to win/lose if we call
        if face_amount > 0:
            total_pot_after_call = pot + face_amount
            call_ev = eq * total_pot_after_call - face_amount
        else:
            # Hero is first to act — a call would be a check
            # Checking has 0 immediate cost, EV is our equity share of pot
            call_ev = eq * pot

        # Raise EV: simplified model
        # Assume a standard raise of 3x the face bet (or 2/3 pot if no face)
        raise_sizing = (
            face_amount * 3 if face_amount > 0 else pot * 0.67
        )
        raise_sizing = min(raise_sizing, stack)  # can't raise more than stack

        # When we raise, villain folds X% of the time and calls (1-X)%.
        # Fold equity: if villain folds, we win the pot immediately.
        # When called: our equity against their continuing range.
        fold_equity_rate = 0.35  # Estimated fold-to-raise rate

        if raise_sizing >= stack:
            # All-in — no fold equity, only equity when called
            total_pot_after_allin = pot + raise_sizing
            raise_ev = eq * total_pot_after_allin - raise_sizing
        else:
            # Standard raise with fold equity
            # Win pot immediately when villain folds
            # When called, equity against a stronger continuing range
            continuing_equity = eq * 0.85  # tighter range = lower equity
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
        """Build GTO strategy frequencies from equity.

        Strategy is derived from equity thresholds and stack depth,
        rather than returned as random values.
        """
        stack = gs.stack_size_bb
        is_shallow = stack < 30

        # Base frequencies from equity
        if equity >= 70:
            # Strong hand — primarily raise
            fold_pct = 2.0
            raise_pct = 80.0 if is_shallow else 65.0
            call_pct = 100.0 - fold_pct - raise_pct
        elif equity >= 55:
            # Good hand — mix call and raise
            fold_pct = 5.0
            raise_pct = 50.0
            call_pct = 45.0
        elif equity >= 40:
            # Marginal — mostly call, some raises as bluff
            fold_pct = 15.0
            raise_pct = 25.0
            call_pct = 60.0
        elif equity >= 25:
            # Weak but playable — call or fold
            fold_pct = 50.0
            raise_pct = 5.0
            call_pct = 45.0
        else:
            # Very weak — mostly fold
            fold_pct = 85.0
            raise_pct = 3.0
            call_pct = 12.0

        return StrategyBreakdown(
            call=round(call_pct, 1),
            raise_=round(raise_pct, 1),
            fold=round(fold_pct, 1),
        )
