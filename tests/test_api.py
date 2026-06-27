"""Integration tests for PokerCoachAI API and Solver.

Run with: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest


# =====================================================================
# Health & Basic
# =====================================================================

@pytest.mark.asyncio
async def test_health_check(client):
    """Verify health endpoint returns OK."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


@pytest.mark.asyncio
async def test_openapi_schema(client):
    """Verify OpenAPI schema is generated correctly."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "PokerCoachAI"
    assert "/api/v1/analyze" in str(schema["paths"])
    assert "/api/v1/hands" in str(schema["paths"])
    assert "/api/v1/analyses" in str(schema["paths"])


# =====================================================================
# Analyze Endpoint — Validation
# =====================================================================

@pytest.mark.asyncio
async def test_analyze_validation_missing_cards(client):
    """Analyze endpoint should reject invalid input."""
    response = await client.post("/api/v1/analyze", json={
        "hero_cards": [],
        "hero_position": "BTN",
        "stack_size_bb": 100,
        "pot_size_bb": 10,
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_validation_bad_position(client):
    """Analyze endpoint should reject invalid position."""
    response = await client.post("/api/v1/analyze", json={
        "hero_cards": ["Ah", "Kh"],
        "hero_position": "INVALID",
        "stack_size_bb": 100,
        "pot_size_bb": 10,
    })
    assert response.status_code == 422


# =====================================================================
# Solver Unit Tests
# =====================================================================

def test_parse_card():
    """Test card parsing."""
    from app.solver.engine.deck import DeckConfig
    card = DeckConfig.parse_card("Ah")
    assert DeckConfig.format_card(card) == "Ah"

    card = DeckConfig.parse_card("2c")
    assert DeckConfig.format_card(card) == "2c"

    card = DeckConfig.parse_card("Td")
    assert DeckConfig.format_card(card) == "Td"


def test_hand_scoring():
    """Test basic hand scoring."""
    from app.solver.engine.deck import DeckConfig
    from app.solver.engine.hand_evaluator import best_5_cards

    # Royal flush: A-K-Q-J-T all hearts
    royal = [DeckConfig.parse_card(c) for c in ["Ah", "Kh", "Qh", "Jh", "Th", "2c", "3d"]]
    score1 = best_5_cards(royal, mode="standard")

    # Ace-high (no pair, no straight): A-K-Q-J-9
    high_card = [DeckConfig.parse_card(c) for c in ["Ah", "Ks", "Qh", "Jh", "9c", "5c", "3d"]]
    score2 = best_5_cards(high_card, mode="standard")

    assert score1 > score2, f"Royal flush ({score1}) should beat ace-high ({score2})"


def test_calculate_equity_preflop():
    """Test equity calculation returns reasonable values."""
    from app.solver.equity_calculator import calculate_equity

    # AA should have very high equity preflop
    equity = calculate_equity(
        hero_cards=["Ah", "As"],
        board_cards=[],
        hero_position="BTN",
        simulations=2000,
    )
    assert 65 <= equity <= 95, f"AA equity {equity}% should be 65-95%"


def test_calculate_equity_postflop():
    """Test equity with board cards."""
    from app.solver.equity_calculator import calculate_equity

    # Top set on dry board should have very high equity
    equity = calculate_equity(
        hero_cards=["Ah", "As"],
        board_cards=["Ad", "7c", "2h"],
        hero_position="BTN",
        simulations=2000,
    )
    assert 75 <= equity <= 99, f"Top set equity {equity}% should be 75-99%"


def test_strategy_ranges():
    """Test that strategy frequencies are valid."""
    from app.schemas.game_state import GameStateRequest
    from app.solver.texas_solver import TexasSolver
    import asyncio

    async def _run():
        solver = TexasSolver()
        gs = GameStateRequest(
            hero_cards=["Ah", "Kh"],
            board_cards=[],
            hero_position="BTN",
            stack_size_bb=100,
            pot_size_bb=10,
        )
        result = await solver.solve(gs)
        assert 0 <= result.strategy.call <= 100
        assert 0 <= result.strategy.raise_ <= 100
        assert 0 <= result.strategy.fold <= 100
        total = result.strategy.call + result.strategy.raise_ + result.strategy.fold
        assert 98 <= total <= 102, f"Strategy total {total}% should be ~100%"

    asyncio.run(_run())


def test_ev_calculation():
    """Test EV calculations are sensible."""
    from app.solver.texas_solver import TexasSolver
    from app.schemas.game_state import GameStateRequest

    solver = TexasSolver()
    gs = GameStateRequest(
        hero_cards=["Ah", "As"],
        board_cards=["Ad", "7c", "2h"],
        hero_position="BTN",
        stack_size_bb=100,
        pot_size_bb=20,
    )
    face = solver._extract_face_amount(gs)
    ev = solver._calculate_ev(gs, equity=85.0, face_amount=face)

    # With 85% equity, call_ev should be positive
    assert ev["call_ev"] > 0
    # Fold EV is always 0 (post-sunk-cost)
    assert ev["fold_ev"] == 0
