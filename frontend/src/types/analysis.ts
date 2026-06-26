// ============================================================
// PokerCoachAI — Analysis Type Definitions
// ============================================================

export interface StrategyBreakdown {
  call: number;
  raise: number;
  fold: number;
}

export interface AnalysisResponse {
  hand_id: string;
  analysis_id: string;
  recommendation: string;
  equity: number;
  call_ev: number;
  raise_ev: number;
  fold_ev: number;
  strategy: StrategyBreakdown;
  gto_analysis: string;
  exploit_analysis: string;
  risk_analysis: string;
  learning_points: string[];
  created_at: string;
}

export interface HandActionResponse {
  street: string;
  player_position: string;
  player_type: string;
  action_type: string;
  amount: number | null;
  action_order: number;
}

export interface HandResponse {
  id: string;
  hero_cards: string;
  board_cards: string | null;
  hero_position: string;
  stack_size_bb: number;
  pot_size_bb: number;
  result_bb: number | null;
  actions: HandActionResponse[];
  created_at: string;
}

export interface HandListItem {
  id: string;
  hero_cards: string;
  board_cards: string | null;
  hero_position: string;
  result_bb: number | null;
  created_at: string;
}

export interface HandListResponse {
  items: HandListItem[];
  total: number;
  page: number;
  page_size: number;
}

// --- Replay Types ---

export interface StreetSnapshot {
  street: string;
  actions: HandActionResponse[];
  hero_cards: string;
  board_cards: string | null;
  pot_size_bb: number;
  hero_stack_bb: number;
}

export interface EquityPoint {
  label: string;
  equity: number;
  pot_size_bb: number;
}

export interface ReplayResponse {
  hand_id: string;
  hero_cards: string;
  hero_position: string;
  board_cards: string | null;
  final_pot_bb: number;
  result_bb: number | null;
  streets: StreetSnapshot[];
  equity_curve: EquityPoint[];
  total_actions: number;
}
