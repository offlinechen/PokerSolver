"""Pydantic schemas for the GameState."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class GameMode(str, Enum):
    """Supported game modes."""
    STANDARD = "standard"
    SHORTDECK = "shortdeck"
    SNG = "sng"
    SQUID = "squid"


class Position(str, Enum):
    UTG = "UTG"
    UTG1 = "UTG1"
    UTG2 = "UTG2"
    MP = "MP"
    HJ = "HJ"
    CO = "CO"
    BTN = "BTN"
    SB = "SB"
    BB = "BB"


class Street(str, Enum):
    PREFLOP = "PREFLOP"
    FLOP = "FLOP"
    TURN = "TURN"
    RIVER = "RIVER"


class ActionType(str, Enum):
    FOLD = "FOLD"
    CHECK = "CHECK"
    CALL = "CALL"
    BET = "BET"
    RAISE = "RAISE"
    ALL_IN = "ALL_IN"


class ActorType(str, Enum):
    HERO = "Hero"
    VILLAIN = "Villain"


class ActionRecord(BaseModel):
    """A single action taken during a hand."""
    street: Street
    actor: ActorType
    action: ActionType
    amount: float | None = None  # in BB, null for Check/Fold


class CardInput(BaseModel):
    """Card input format, e.g. 'Ah' or 'Td'."""
    value: str = Field(..., min_length=2, max_length=2, pattern=r"^[AKQJT98765432][hdsc]$")


class GameStateRequest(BaseModel):
    """Request body for hand analysis.

    M1: mode, hero_cards, board_cards, hero_position, stack_size_bb, pot_size_bb
    M2: + villain_profile, action_history analysis, table_size
    """
    mode: GameMode = GameMode.STANDARD
    hero_cards: list[str] = Field(..., min_length=2, max_length=2)
    board_cards: list[str] = Field(
        default_factory=list, min_length=0, max_length=5
    )
    hero_position: Position
    stack_size_bb: float = Field(..., gt=0)
    pot_size_bb: float = Field(..., ge=0)
    actions: list[ActionRecord] = Field(default_factory=list)

    @field_validator("hero_cards")
    @classmethod
    def validate_hero_cards(cls, v: list[str]) -> list[str]:
        if len(v) != 2:
            raise ValueError("Must contain exactly 2 cards")
        for card in v:
            if len(card) != 2:
                raise ValueError(f"Invalid card format: {card}")
        return v

    @field_validator("board_cards")
    @classmethod
    def validate_board_cards(cls, v: list[str]) -> list[str]:
        if len(v) > 5:
            raise ValueError("Board can have at most 5 cards")
        return v
