// ============================================================
// PokerCoachAI — Analysis Store (Zustand)
// ============================================================

import { create } from 'zustand';
import type { AnalysisResponse } from '@/types/analysis';

interface AnalysisState {
  currentResult: AnalysisResponse | null;
  isLoading: boolean;
  error: string | null;

  setResult: (result: AnalysisResponse) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearResult: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  currentResult: null,
  isLoading: false,
  error: null,

  setResult: (result) => set({ currentResult: result, error: null }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error, isLoading: false }),
  clearResult: () => set({ currentResult: null, error: null }),
}));
