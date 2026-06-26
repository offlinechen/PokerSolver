"""Initial schema — core tables for Phase 1 MVP.

Revision ID: 001
Revises: None
Create Date: 2026-06-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ users
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --------------------------------------------------------------- sessions
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("platform", sa.String(64), nullable=True),
        sa.Column("game_type", sa.String(32), nullable=True),
        sa.Column("stake", sa.String(32), nullable=True),
        sa.Column("buy_in", sa.Numeric(10, 2), nullable=True),
        sa.Column("cash_out", sa.Numeric(10, 2), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    # ------------------------------------------------------------------ hands
    op.create_table(
        "hands",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("hero_position", sa.String(16), nullable=False),
        sa.Column("hero_cards", sa.String(16), nullable=False),
        sa.Column("board_cards", sa.String(32), nullable=True),
        sa.Column("stack_size_bb", sa.Numeric(10, 2), nullable=False),
        sa.Column("pot_size_bb", sa.Numeric(10, 2), nullable=False),
        sa.Column("result_bb", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_hands_session_id", "hands", ["session_id"])
    op.create_index("ix_hands_user_id", "hands", ["user_id"])
    op.create_index("ix_hands_created_at", "hands", ["created_at"])

    # ---------------------------------------------------------------- players
    op.create_table(
        "players",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column(
            "hand_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("hands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seat_number", sa.Integer, nullable=False),
        sa.Column("nickname", sa.String(128), nullable=True),
        sa.Column(
            "player_type",
            sa.String(16),
            nullable=False,
            server_default="Villain",
        ),
        sa.Column("position", sa.String(16), nullable=False),
        sa.Column("stack_size_bb", sa.Numeric(10, 2), nullable=False),
    )
    op.create_index("ix_players_hand_id", "players", ["hand_id"])

    # ---------------------------------------------------------------- actions
    op.create_table(
        "actions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column(
            "hand_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("hands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("street", sa.String(16), nullable=False),
        sa.Column("action_type", sa.String(16), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("action_order", sa.Integer, nullable=False),
    )
    op.create_index("ix_actions_hand_id", "actions", ["hand_id"])
    op.create_index("ix_actions_player_id", "actions", ["player_id"])

    # -------------------------------------------------------------- analyses
    op.create_table(
        "analyses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column(
            "hand_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("hands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("recommendation", sa.String(32), nullable=True),
        sa.Column("equity", sa.Numeric(6, 2), nullable=True),
        sa.Column("call_ev", sa.Numeric(8, 4), nullable=True),
        sa.Column("raise_ev", sa.Numeric(8, 4), nullable=True),
        sa.Column("fold_ev", sa.Numeric(8, 4), nullable=True),
        sa.Column("strategy", sa.String(256), nullable=True),
        sa.Column("gto_analysis", sa.Text, nullable=True),
        sa.Column("exploit_analysis", sa.Text, nullable=True),
        sa.Column("risk_analysis", sa.Text, nullable=True),
        sa.Column("learning_points", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_analyses_hand_id", "analyses", ["hand_id"])


def downgrade() -> None:
    op.drop_table("analyses")
    op.drop_table("actions")
    op.drop_table("players")
    op.drop_table("hands")
    op.drop_table("sessions")
    op.drop_table("users")
