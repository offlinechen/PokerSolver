// ============================================================
// PokerCoachAI — Frontend Type Definitions
// ============================================================

// --- Card Types ---
export type Suit = 'h' | 'd' | 'c' | 's';
export type Rank = 'A' | 'K' | 'Q' | 'J' | 'T' | '9' | '8' | '7' | '6' | '5' | '4' | '3' | '2';

export interface Card {
  rank: Rank;
  suit: Suit;
}

// --- Position Types ---
export type Position = 'UTG' | 'UTG1' | 'UTG2' | 'MP' | 'HJ' | 'CO' | 'BTN' | 'SB' | 'BB';

export const POSITIONS: Position[] = ['UTG', 'UTG1', 'UTG2', 'MP', 'HJ', 'CO', 'BTN', 'SB', 'BB'];

// 按人数返回可用位置
export function getPositionsForTable(playerCount: number): Position[] {
  if (playerCount <= 2) return ['BTN', 'BB'];
  if (playerCount <= 6) return ['UTG', 'MP', 'HJ', 'CO', 'BTN', 'BB'];
  return ['UTG', 'UTG1', 'UTG2', 'MP', 'HJ', 'CO', 'BTN', 'SB', 'BB'];
}

// --- Street Types ---
export type Street = 'PREFLOP' | 'FLOP' | 'TURN' | 'RIVER';

export const STREETS: Street[] = ['PREFLOP', 'FLOP', 'TURN', 'RIVER'];

// --- Action Types ---
export type ActionType = 'FOLD' | 'CHECK' | 'CALL' | 'BET' | 'RAISE' | 'ALL_IN';

export interface ActionRecord {
  street: Street;
  actor: string; // 'Hero' or villain position label like 'UTG', 'BB', etc.
  action: ActionType;
  amount: number | null;
}

// --- Villain / Other Player ---
export interface Villain {
  id: string;
  position: Position;
  stackSizeBB: number;
}

// --- Card Utility ---
export const SUITS: Suit[] = ['s', 'h', 'd', 'c']; // spades, hearts, diamonds, clubs
export const RANKS: Rank[] = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];

export function cardToString(card: Card): string {
  return `${card.rank}${card.suit}`;
}

export function stringToCard(str: string): Card {
  return { rank: str[0] as Rank, suit: str[1] as Suit };
}

export function cardsToString(cards: Card[]): string {
  return cards.map(cardToString).join('');
}

export function formatCardsDisplay(cards: Card[]): string {
  const suitSymbols: Record<Suit, string> = { s: '♠', h: '♥', d: '♦', c: '♣' };
  return cards.map(c => `${c.rank}${suitSymbols[c.suit]}`).join(' ');
}

export const SUIT_COLORS: Record<Suit, string> = {
  s: '#1a1a1a', // black
  h: '#d32f2f', // red
  d: '#1976d2', // blue
  c: '#2e7d32', // green
};

export const SUIT_SYMBOLS: Record<Suit, string> = {
  s: '♠',
  h: '♥',
  d: '♦',
  c: '♣',
};
