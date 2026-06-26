#!/usr/bin/env python3
"""Seed development database with sample data.

Usage:
  python scripts/seed.py    # create sample data (idempotent)
  python scripts/seed.py --clean  # wipe and re-create
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.database import Base
from app.models.user import User
from app.models.session import Session
from app.models.hand import Hand
from app.models.player import Player
from app.models.action import Action
from app.models.analysis import Analysis

SEED_USER_ID = "00000000-0000-0000-0000-000000000001"
SEED_SESSION_ID = "00000000-0000-0000-0000-000000000010"


async def seed(clean: bool = False):
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    # Create tables if not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        # Clean if requested
        if clean:
            await db.execute(delete(Analysis))
            await db.execute(delete(Action))
            await db.execute(delete(Player))
            await db.execute(delete(Hand))
            await db.execute(delete(Session))
            await db.execute(delete(User))
            await db.commit()
            print("Cleaned all data.")

        # Check if already seeded
        result = await db.execute(select(User).where(User.id == SEED_USER_ID))
        if result.scalar_one_or_none():
            print("Seed data already exists (use --clean to reset).")
            return

        # User
        user = User(
            id=SEED_USER_ID,
            username="DemoPlayer",
            email="demo@pokercoach.ai",
        )
        db.add(user)

        # Session
        session = Session(
            id=SEED_SESSION_ID,
            user_id=SEED_USER_ID,
            platform="Online",
            game_type="NLHE",
            stake="1/2",
            buy_in=200.0,
            cash_out=350.0,
        )
        db.add(session)

        # ── Hand 1: AA preflop all-in ──
        h1 = Hand(
            id="10000000-0000-0000-0000-000000000001",
            session_id=SEED_SESSION_ID,
            user_id=SEED_USER_ID,
            hero_position="BTN",
            hero_cards="AhAs",
            board_cards="Kd7c2h9s3c",
            stack_size_bb=100.0,
            pot_size_bb=24.0,
            result_bb=24.0,
        )
        db.add(h1)

        p1_hero = Player(
            id="20000000-0000-0000-0000-000000000001",
            hand_id=h1.id,
            seat_number=0,
            nickname="DemoPlayer",
            player_type="Hero",
            position="BTN",
            stack_size_bb=100.0,
        )
        p1_villain = Player(
            id="20000000-0000-0000-0000-000000000002",
            hand_id=h1.id,
            seat_number=1,
            nickname="Fish99",
            player_type="Villain",
            position="BB",
            stack_size_bb=80.0,
        )
        db.add_all([p1_hero, p1_villain])

        actions_h1 = [
            Action(hand_id=h1.id, player_id=p1_hero.id, street="PREFLOP", action_type="RAISE", amount=3.0, action_order=0),
            Action(hand_id=h1.id, player_id=p1_villain.id, street="PREFLOP", action_type="RAISE", amount=12.0, action_order=1),
            Action(hand_id=h1.id, player_id=p1_hero.id, street="PREFLOP", action_type="RAISE", amount=36.0, action_order=2),
            Action(hand_id=h1.id, player_id=p1_villain.id, street="PREFLOP", action_type="ALL_IN", amount=80.0, action_order=3),
            Action(hand_id=h1.id, player_id=p1_hero.id, street="PREFLOP", action_type="CALL", amount=44.0, action_order=4),
        ]
        db.add_all(actions_h1)

        # ── Hand 2: AKs missed board ──
        h2 = Hand(
            id="10000000-0000-0000-0000-000000000002",
            session_id=SEED_SESSION_ID,
            user_id=SEED_USER_ID,
            hero_position="CO",
            hero_cards="AhKh",
            board_cards="QdJc5s",
            stack_size_bb=100.0,
            pot_size_bb=18.0,
            result_bb=-12.0,
        )
        db.add(h2)

        p2_hero = Player(
            id="20000000-0000-0000-0000-000000000003",
            hand_id=h2.id,
            seat_number=0,
            nickname="DemoPlayer",
            player_type="Hero",
            position="CO",
            stack_size_bb=100.0,
        )
        p2_villain = Player(
            id="20000000-0000-0000-0000-000000000004",
            hand_id=h2.id,
            seat_number=1,
            nickname="NitPlayer",
            player_type="Villain",
            position="BTN",
            stack_size_bb=120.0,
        )
        db.add_all([p2_hero, p2_villain])

        actions_h2 = [
            Action(hand_id=h2.id, player_id=p2_hero.id, street="PREFLOP", action_type="RAISE", amount=3.0, action_order=0),
            Action(hand_id=h2.id, player_id=p2_villain.id, street="PREFLOP", action_type="CALL", amount=3.0, action_order=1),
            Action(hand_id=h2.id, player_id=p2_hero.id, street="FLOP", action_type="BET", amount=6.0, action_order=2),
            Action(hand_id=h2.id, player_id=p2_villain.id, street="FLOP", action_type="RAISE", amount=18.0, action_order=3),
            Action(hand_id=h2.id, player_id=p2_hero.id, street="FLOP", action_type="FOLD", amount=None, action_order=4),
        ]
        db.add_all(actions_h2)

        # ── Hand 3: 88 set-mining success ──
        h3 = Hand(
            id="10000000-0000-0000-0000-000000000003",
            session_id=SEED_SESSION_ID,
            user_id=SEED_USER_ID,
            hero_position="MP",
            hero_cards="8h8d",
            board_cards="8sTh2c4dQh",
            stack_size_bb=100.0,
            pot_size_bb=45.0,
            result_bb=45.0,
        )
        db.add(h3)

        p3_hero = Player(
            id="20000000-0000-0000-0000-000000000005",
            hand_id=h3.id,
            seat_number=0,
            nickname="DemoPlayer",
            player_type="Hero",
            position="MP",
            stack_size_bb=100.0,
        )
        p3_villain = Player(
            id="20000000-0000-0000-0000-000000000006",
            hand_id=h3.id,
            seat_number=1,
            nickname="LAGMonster",
            player_type="Villain",
            position="BB",
            stack_size_bb=95.0,
        )
        db.add_all([p3_hero, p3_villain])

        actions_h3 = [
            Action(hand_id=h3.id, player_id=p3_hero.id, street="PREFLOP", action_type="RAISE", amount=3.0, action_order=0),
            Action(hand_id=h3.id, player_id=p3_villain.id, street="PREFLOP", action_type="CALL", amount=3.0, action_order=1),
            Action(hand_id=h3.id, player_id=p3_villain.id, street="FLOP", action_type="CHECK", amount=None, action_order=2),
            Action(hand_id=h3.id, player_id=p3_hero.id, street="FLOP", action_type="BET", amount=5.0, action_order=3),
            Action(hand_id=h3.id, player_id=p3_villain.id, street="FLOP", action_type="CALL", amount=5.0, action_order=4),
            Action(hand_id=h3.id, player_id=p3_villain.id, street="TURN", action_type="CHECK", amount=None, action_order=5),
            Action(hand_id=h3.id, player_id=p3_hero.id, street="TURN", action_type="BET", amount=15.0, action_order=6),
            Action(hand_id=h3.id, player_id=p3_villain.id, street="TURN", action_type="FOLD", amount=None, action_order=7),
        ]
        db.add_all(actions_h3)

        await db.commit()
        print("Seed data created: 1 user, 1 session, 3 hands with actions.")
        print("Demo user ID:", SEED_USER_ID)
        print("Hand IDs: h1 (AA), h2 (AKs), h3 (88)")

    await engine.dispose()


if __name__ == "__main__":
    clean = "--clean" in sys.argv
    asyncio.run(seed(clean=clean))
