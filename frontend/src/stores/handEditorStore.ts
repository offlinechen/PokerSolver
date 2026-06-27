// ============================================================
// PokerCoachAI — Hand Editor Store (Zustand)
// ============================================================

import { create } from 'zustand';
import type { ActionRecord, Card, GameMode, Position, Street, Villain } from '@/types/poker';
import { getPositionsForTable } from '@/types/poker';

export const STREETS: Street[] = ['PREFLOP', 'FLOP', 'TURN', 'RIVER'];

// 每条街允许的公共牌数量
export const BOARD_CARDS_PER_STREET: Record<Street, number> = {
  PREFLOP: 0,
  FLOP: 3,
  TURN: 4,
  RIVER: 5,
};

interface HandEditorState {
  // Game mode
  mode: GameMode;

  // Hand State
  heroCards: Card[];
  boardCards: Card[];
  heroPosition: Position | null;
  stackSizeBB: number;
  potSizeBB: number;
  actions: ActionRecord[];

  // Table settings
  tableSize: number;          // 2, 6, or 9
  villains: Villain[];        // other players at the table
  currentStreet: Street;      // active street dimension
  currentTurnIndex: number;   // whose turn in the action order (0-based)

  // Actions
  setMode: (mode: GameMode) => void;
  setHeroCards: (cards: Card[]) => void;
  setBoardCards: (cards: Card[]) => void;
  setHeroPosition: (pos: Position) => void;
  setStackSize: (bb: number) => void;
  setPotSize: (bb: number) => void;
  addAction: (action: ActionRecord) => void;
  removeAction: (index: number) => void;
  clearActions: () => void;

  // Table actions
  setTableSize: (size: number) => void;
  setVillainStack: (pos: Position, stackBB: number) => void;
  setCurrentStreet: (street: Street) => void;
  setCurrentTurnIndex: (idx: number) => void;
  reset: () => void;
}

// Build initial villains from table size
function buildVillains(tableSize: number, heroPos?: Position | null): Villain[] {
  const all = getPositionsForTable(tableSize);
  return all
    .filter((p) => p !== (heroPos ?? ''))
    .map((p) => ({ id: p, position: p, stackSizeBB: 100 }));
}

const initialState = {
  mode: 'standard' as GameMode,
  heroCards: [] as Card[],
  boardCards: [] as Card[],
  heroPosition: null as Position | null,
  stackSizeBB: 100,
  potSizeBB: 1.5,  // 默认盲注 1.5BB（SB+BB），避免 EV 为 0
  actions: [] as ActionRecord[],
  tableSize: 6,
  villains: buildVillains(6),
  currentStreet: 'PREFLOP' as Street,
  currentTurnIndex: 0,
};

export const useHandEditorStore = create<HandEditorState>((set) => ({
  ...initialState,

  setMode: (mode) => set({ mode }),
  setHeroCards: (cards) => set({ heroCards: cards }),
  setBoardCards: (cards) => set({ boardCards: cards }),
  setStackSize: (bb) => set({ stackSizeBB: bb }),
  setPotSize: (bb) => set({ potSizeBB: bb }),

  setHeroPosition: (pos) =>
    set((state) => ({
      heroPosition: pos,
      villains: buildVillains(state.tableSize, pos),
    })),

  setTableSize: (size) =>
    set((state) => ({
      tableSize: size,
      villains: buildVillains(size, state.heroPosition),
    })),

  setVillainStack: (pos, stackBB) =>
    set((state) => ({
      villains: state.villains.map((v) =>
        v.position === pos ? { ...v, stackSizeBB: stackBB } : v,
      ),
    })),

  setCurrentStreet: (street) => set({ currentStreet: street }),

  setCurrentTurnIndex: (idx) => set({ currentTurnIndex: idx }),

  addAction: (action) =>
    set((state) => ({ actions: [...state.actions, action] })),

  removeAction: (index) =>
    set((state) => ({
      actions: state.actions.filter((_, i) => i !== index),
    })),

  clearActions: () => set({ actions: [] }),

  reset: () => set(initialState),
}));
