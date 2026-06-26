// ============================================================
// PokerCoachAI — API Service
// ============================================================

import type {
  AnalysisResponse,
  HandListResponse,
  HandResponse,
  ReplayResponse,
} from '@/types/analysis';
import type { ActionRecord, Position, Street } from '@/types/poker';

const API_BASE = '/api/v1';

// --- Analyze ---

export interface AnalyzeRequest {
  hero_cards: [string, string];
  board_cards: string[];
  hero_position: Position;
  stack_size_bb: number;
  pot_size_bb: number;
  actions: {
    street: Street;
    actor: 'Hero' | 'Villain';
    action: string;
    amount: number | null;
  }[];
}

export async function analyzeHand(request: AnalyzeRequest): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// --- Hands ---

export async function getHands(
  page: number = 1,
  pageSize: number = 20
): Promise<HandListResponse> {
  const response = await fetch(
    `${API_BASE}/hands?page=${page}&pageSize=${pageSize}`
  );

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export async function getHand(handId: string): Promise<HandResponse> {
  const response = await fetch(`${API_BASE}/hands/${handId}`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

// --- Replay ---

export async function getReplay(handId: string): Promise<ReplayResponse> {
  const response = await fetch(`${API_BASE}/hands/${handId}/replay`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
