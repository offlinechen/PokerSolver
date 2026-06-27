import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card as MuiCard,
  CardContent,
  Chip,
  Grid2 as Grid,
  TextField,
  Typography,
  Tabs,
  Tab,
  Paper,
  IconButton,
  Alert,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  ToggleButtonGroup,
  ToggleButton,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  RadioButtonUnchecked as UncheckIcon,
} from '@mui/icons-material';
import { useHandEditorStore, STREETS, BOARD_CARDS_PER_STREET } from '@/stores/handEditorStore';
import { useAnalysisStore } from '@/stores/analysisStore';
import { analyzeHand } from '@/services/api';
import type { Card, Position, Suit, Villain, ActionType, Street } from '@/types/poker';
import {
  getPositionsForTable,
  RANKS,
  SHORTDECK_RANKS,
  SUITS,
  SUIT_SYMBOLS,
  SUIT_COLORS,
  cardToString,
  GAME_MODES,
} from '@/types/poker';

// ===================================================================
// 常量
// ===================================================================

const STREET_LABELS: Record<Street, string> = {
  PREFLOP: '翻前', FLOP: '翻牌', TURN: '转牌', RIVER: '河牌',
};

// ===================================================================
// 行动顺序计算
// ===================================================================

function buildTurnOrder(positions: Position[], heroPos: Position | null, street: Street): Position[] {
  if (positions.length === 0 || !heroPos) return [];
  const beforeHero = positions.filter((p) => p !== heroPos);
  if (street === 'PREFLOP') {
    const heroIdx = positions.indexOf(heroPos);
    if (heroIdx === -1) return beforeHero;
    return beforeHero.filter((p) => positions.indexOf(p) < heroIdx);
  }
  const heroIdx = positions.indexOf(heroPos);
  if (heroIdx === -1) return beforeHero;
  return [...positions.slice(heroIdx + 1), ...positions.slice(0, heroIdx)];
}

// ===================================================================
// SVG 牌桌
// ===================================================================

const SEAT_COORDS_9: [number, number][] = [
  [50, 5], [80, 10], [95, 30], [97, 55], [88, 78], [65, 88], [35, 88], [15, 72], [7, 42],
];
const SEAT_COORDS_6: [number, number][] = [
  [50, 8], [92, 32], [92, 68], [65, 90], [35, 90], [8, 50],
];
const SEAT_COORDS_2: [number, number][] = [[50, 92], [50, 8]];

function getSeatCoords(tableSize: number) {
  if (tableSize <= 2) return SEAT_COORDS_2;
  if (tableSize <= 6) return SEAT_COORDS_6;
  return SEAT_COORDS_9;
}

function PokerTable({
  tableSize, heroPosition, villains, currentTurn, foldedPositions,
}: {
  tableSize: number;
  heroPosition: Position | null;
  villains: Villain[];
  currentTurn: string;
  foldedPositions: Set<string>;
}) {
  const coords = useMemo(() => getSeatCoords(tableSize), [tableSize]);
  const positions = useMemo(() => getPositionsForTable(tableSize), [tableSize]);

  return (
    <Box sx={{ position: 'relative', width: '100%', aspectRatio: '1.25/1', minHeight: 180 }}>
      <svg viewBox="0 0 100 100" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
        <ellipse cx="50" cy="50" rx="43" ry="31" fill="#0d2e0d" stroke="#2e7d32" strokeWidth="1.5" />
        <ellipse cx="50" cy="50" rx="33" ry="22" fill="#143d14" stroke="none" />
        <text x="50" y="53" textAnchor="middle" fill="#3e8e41" fontSize="3.5">TABLE</text>
      </svg>
      {positions.map((pos, i) => {
        const [cx, cy] = coords[i] || [50, 50];
        const isHero = pos === heroPosition;
        const isTurn = currentTurn === pos || (currentTurn === 'Hero' && isHero);
        const folded = isHero ? false : foldedPositions.has(pos);
        const villain = villains.find((v) => v.position === pos);
        const stack = isHero ? 0 : (villain?.stackSizeBB ?? 100);
        return (
          <Box
            key={pos}
            sx={{
              position: 'absolute', left: `${cx}%`, top: `${cy}%`,
              transform: 'translate(-50%, -50%)', p: 0.3, borderRadius: 1,
              transition: 'all 0.15s',
              border: isTurn ? '2px solid #ff9800' : '2px solid transparent',
              bgcolor: isTurn ? 'rgba(255,152,0,0.18)' : isHero ? 'rgba(244,67,54,0.12)' : 'transparent',
            }}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.15, opacity: folded ? 0.35 : 1 }}>
              <Chip
                label={pos}
                size="small"
                color={isHero ? 'error' : 'default'}
                variant={isHero ? 'filled' : 'outlined'}
                sx={{ fontWeight: 700, fontSize: '0.65rem', height: 18 }}
              />
              <Typography variant="caption" sx={{ fontSize: '0.55rem', color: 'text.secondary' }}>
                {folded ? 'FOLD' : `${stack}BB`}
              </Typography>
            </Box>
          </Box>
        );
      })}
    </Box>
  );
}

// ===================================================================
// 主页面
// ===================================================================

export default function HandEditorPage() {
  const navigate = useNavigate();
  const store = useHandEditorStore();
  const analysis = useAnalysisStore();
  const [betAmount, setBetAmount] = useState<number | ''>('');

  const maxBoardCards = BOARD_CARDS_PER_STREET[store.currentStreet];
  const positions = useMemo(() => getPositionsForTable(store.tableSize), [store.tableSize]);

  const foldedPositions = useMemo(() => {
    const s = new Set<string>();
    store.actions.filter((a) => a.street === store.currentStreet && a.action === 'FOLD')
      .forEach((a) => s.add(a.actor));
    return s;
  }, [store.actions, store.currentStreet]);

  const turnOrder = useMemo(
    () => buildTurnOrder(positions, store.heroPosition, store.currentStreet),
    [positions, store.heroPosition, store.currentStreet],
  );

  const actedThisStreet = useMemo(() => {
    const s = new Set<string>();
    store.actions.filter((a) => a.street === store.currentStreet).forEach((a) => s.add(a.actor));
    return s;
  }, [store.actions, store.currentStreet]);

  const currentTurnPlayer = useMemo(() => {
    for (const pos of turnOrder) {
      if (!actedThisStreet.has(pos) && !foldedPositions.has(pos)) return pos;
    }
    return 'Hero';
  }, [turnOrder, actedThisStreet, foldedPositions]);

  const isHeroTurn = currentTurnPlayer === 'Hero';
  const streetActions = store.actions.filter((a) => a.street === store.currentStreet);
  const pendingPlayers = turnOrder.filter((p) => !actedThisStreet.has(p) && !foldedPositions.has(p));
  const availableRanks = store.mode === 'shortdeck' ? SHORTDECK_RANKS : RANKS;

  const canSubmit = store.heroCards.length >= 2 && store.heroPosition !== null && store.stackSizeBB > 0 && isHeroTurn;

  // ── 卡牌点击（不允许重复选同张牌）──
  const handleCardClick = (rank: string, suit: Suit) => {
    if (isCardSelected(rank, suit)) return;  // 不允许选同花同张
    const card: Card = { rank: rank as Card['rank'], suit };
    if (store.heroCards.length < 2) {
      store.setHeroCards([...store.heroCards, card]);
    } else if (store.boardCards.length < maxBoardCards) {
      store.setBoardCards([...store.boardCards, card]);
    }
  };
  const isCardSelected = (rank: string, suit: Suit) =>
    [...store.heroCards, ...store.boardCards].some((c) => c.rank === rank && c.suit === suit);

  // ── 行动 ──
  const handleAddAction = (action: ActionType) => {
    const needsAmt = ['BET', 'RAISE', 'CALL', 'ALL_IN'].includes(action);
    const amount = needsAmt && typeof betAmount === 'number' && betAmount > 0 ? betAmount : null;
    store.addAction({ street: store.currentStreet, actor: currentTurnPlayer, action, amount });
    setBetAmount('');
  };

  // ── 提交 ──
  const handleSubmit = async () => {
    if (store.heroCards.length < 2 || !store.heroPosition) return;
    analysis.setLoading(true);
    analysis.setError(null);
    try {
      const result = await analyzeHand({
        mode: store.mode,
        hero_cards: store.heroCards.map(cardToString) as [string, string],
        board_cards: store.boardCards.map(cardToString),
        hero_position: store.heroPosition,
        stack_size_bb: store.stackSizeBB,
        pot_size_bb: store.potSizeBB,
        actions: store.actions.map((a) => ({
          street: a.street, actor: a.actor === 'Hero' ? 'Hero' : 'Villain',
          action: a.action, amount: a.amount,
        })),
      });
      analysis.setResult(result);
      navigate(`/hand/${result.hand_id}`);
    } catch (err) {
      analysis.setError(err instanceof Error ? err.message : '分析失败');
    }
  };

  // ── checklist: what's done / missing ──
  const checks = [
    { done: store.heroCards.length >= 2, label: store.heroCards.length >= 2 ? `手牌 ${store.heroCards.map(c => `${c.rank}${SUIT_SYMBOLS[c.suit]}`).join(' ')}` : '选 2 张手牌' },
    { done: !!store.heroPosition, label: store.heroPosition ? `位置 ${store.heroPosition}` : '选 Hero 位置' },
    { done: true, label: `${store.stackSizeBB}BB` },
    { done: isHeroTurn, label: isHeroTurn ? '你的回合' : pendingPlayers.length ? `等待 ${pendingPlayers.map(p => p).join(' ')} 行动` : '…' },
  ];

  return (
    <Box>
      {/* ============================================================ */}
      {/* 标题 */}
      {/* ============================================================ */}
      <Typography variant="h5" fontWeight={700} sx={{ mb: 1.5 }}>
        新建手牌分析
      </Typography>

      {/* ============================================================ */}
      {/* 模式 + 人数（街道 Tabs 上方） */}
      {/* ============================================================ */}
      <Paper sx={{ mb: 1.5, p: 1, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <ToggleButtonGroup
          size="small"
          value={store.mode}
          exclusive
          onChange={(_, v) => { if (v) { store.setMode(v); store.setHeroCards([]); store.setBoardCards([]); } }}
        >
          {GAME_MODES.map((m) => (
            <ToggleButton key={m.id} value={m.id} sx={{ px: 1.5, py: 0.5, fontSize: '0.78rem' }}>{m.name}</ToggleButton>
          ))}
        </ToggleButtonGroup>
        <Divider orientation="vertical" flexItem />
        <FormControl size="small" sx={{ minWidth: 72 }}>
          <InputLabel>人数</InputLabel>
          <Select value={store.tableSize} label="人数" onChange={(e) => store.setTableSize(Number(e.target.value))}>
            <MenuItem value={2}>2</MenuItem><MenuItem value={6}>6</MenuItem><MenuItem value={9}>9</MenuItem>
          </Select>
        </FormControl>
      </Paper>

      {/* ============================================================ */}
      {/* 街道 Tabs */}
      {/* ============================================================ */}
      <Tabs
        value={STREETS.indexOf(store.currentStreet)}
        onChange={(_, i) => store.setCurrentStreet(STREETS[i])}
        sx={{ mb: 1.5, minHeight: 36, '& .MuiTab-root': { minHeight: 36, py: 0.5, fontWeight: 600, fontSize: '0.8rem' } }}
      >
        {STREETS.map((s) => (
          <Tab
            key={s}
            label={`${STREET_LABELS[s]}${store.boardCards.length > 0 && BOARD_CARDS_PER_STREET[s] > 0 ? ` (${store.boardCards.length}/${BOARD_CARDS_PER_STREET[s]})` : ''}`}
          />
        ))}
      </Tabs>

      {analysis.error && (
        <Alert severity="error" sx={{ mb: 1.5 }} onClose={() => analysis.setError(null)}>{analysis.error}</Alert>
      )}

      {analysis.isLoading && (
        <LinearProgress sx={{ mb: 1.5, height: 4, borderRadius: 2 }} />
      )}

      {/* ============================================================ */}
      {/* 三栏内容 */}
      {/* ============================================================ */}
      <Grid container spacing={1.5}>
        {/* 左：选牌 */}
        <Grid size={{ xs: 12, md: 4 }}>
          <MuiCard>
            <CardContent sx={{ pb: '12px !important' }}>
              {/* 已选手牌 */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 32 }}>Hero</Typography>
                {[0, 1].map((i) => {
                  const c = store.heroCards[i];
                  return (
                    <Paper
                      key={i} variant="outlined"
                      onClick={() => { if (c) store.setHeroCards(store.heroCards.filter((_, j) => j !== i)); }}
                      sx={{
                        width: 38, height: 52, display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '1.1rem', fontWeight: 700, cursor: c ? 'pointer' : 'default',
                        color: c ? SUIT_COLORS[c.suit] : '#555',
                        bgcolor: c ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.01)',
                        borderStyle: c ? 'solid' : 'dashed',
                      }}
                    >
                      {c ? `${c.rank}${SUIT_SYMBOLS[c.suit]}` : '?'}
                    </Paper>
                  );
                })}
                <Divider orientation="vertical" flexItem />
                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 28 }}>Board</Typography>
                {Array.from({ length: Math.max(maxBoardCards, 1) }).map((_, i) => {
                  const c = store.boardCards[i];
                  if (maxBoardCards === 0) return <Typography key={i} variant="caption" color="text.disabled">—</Typography>;
                  return (
                    <Paper
                      key={i} variant="outlined"
                      onClick={() => { if (c) store.setBoardCards(store.boardCards.filter((_, j) => j !== i)); }}
                      sx={{
                        width: 32, height: 44, display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.85rem', fontWeight: 700, cursor: c ? 'pointer' : 'default',
                        color: c ? SUIT_COLORS[c.suit] : '#444',
                        bgcolor: c ? 'rgba(255,255,255,0.05)' : 'transparent',
                        borderStyle: 'dashed',
                      }}
                    >
                      {c ? `${c.rank}${SUIT_SYMBOLS[c.suit]}` : '·'}
                    </Paper>
                  );
                })}
                <Chip size="small" label={`${store.boardCards.length}/${maxBoardCards}`} variant="outlined" sx={{ height: 20, fontSize: '0.65rem' }} />
              </Box>

              {/* 牌网格 */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
                {availableRanks.map((rank) => (
                  <Box key={rank} sx={{ display: 'flex', gap: 0.25 }}>
                    {SUITS.map((suit) => {
                      const sel = isCardSelected(rank, suit);
                      const full = store.heroCards.length >= 2 && store.boardCards.length >= maxBoardCards;
                      const blocked = store.heroCards.length < 2 && store.boardCards.length > 0;
                      return (
                        <Button
                          key={`${rank}${suit}`}
                          variant={sel ? 'contained' : 'text'}
                          onClick={() => handleCardClick(rank, suit)}
                          disabled={full || blocked}
                          sx={{
                            minWidth: 32, height: 32, p: 0, fontSize: '0.75rem', fontWeight: 600,
                            color: sel ? '#fff' : SUIT_COLORS[suit],
                            bgcolor: sel ? undefined : 'transparent',
                            opacity: full || blocked ? 0.25 : 0.75,
                            '&:hover': { opacity: 1 },
                          }}
                        >
                          {rank}{SUIT_SYMBOLS[suit]}
                        </Button>
                      );
                    })}
                  </Box>
                ))}
              </Box>
              <Button size="small" sx={{ mt: 1, fontSize: '0.7rem' }} onClick={() => { store.setHeroCards([]); store.setBoardCards([]); }}>
                清空选牌
              </Button>
            </CardContent>
          </MuiCard>
        </Grid>

        {/* 中：牌桌 */}
        <Grid size={{ xs: 12, md: 4 }}>
          <MuiCard>
            <CardContent sx={{ pb: '12px !important' }}>
              {/* 位置选择 + 牌桌设置 */}
              <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                <FormControl size="small" sx={{ flex: 1, minWidth: 100 }}>
                  <InputLabel>Hero位置</InputLabel>
                  <Select
                    value={store.heroPosition || ''} label="Hero位置"
                    onChange={(e) => store.setHeroPosition(e.target.value as Position)}
                  >
                    {getPositionsForTable(store.tableSize).map((p) => (
                      <MenuItem key={p} value={p}>{p}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              <PokerTable
                tableSize={store.tableSize} heroPosition={store.heroPosition}
                villains={store.villains} currentTurn={currentTurnPlayer}
                foldedPositions={foldedPositions}
              />
              {/* 当前行动者 + 行动顺序 */}
              <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
                <Typography variant="caption" color="text.secondary">当前:</Typography>
                <Chip
                  size="small"
                  label={currentTurnPlayer === 'Hero' ? `Hero (${store.heroPosition})` : currentTurnPlayer}
                  color={isHeroTurn ? 'success' : 'warning'}
                />
                {turnOrder.length > 0 && (
                  <>
                    <Typography variant="caption" color="text.disabled" sx={{ mx: 0.3 }}>→</Typography>
                    {turnOrder.map((pos) => {
                      const done = actedThisStreet.has(pos) || foldedPositions.has(pos);
                      return (
                        <Chip
                          key={pos}
                          label={pos}
                          size="small"
                          variant={done ? 'outlined' : 'filled'}
                          color={pos === currentTurnPlayer ? 'warning' : 'default'}
                          sx={{ height: 18, fontSize: '0.6rem', opacity: done && pos !== currentTurnPlayer ? 0.35 : 1 }}
                        />
                      );
                    })}
                    <Typography variant="caption" color="text.disabled">→</Typography>
                    <Chip label="你" size="small" variant="filled" color={isHeroTurn ? 'success' : 'default'}
                      sx={{ height: 18, fontSize: '0.6rem', opacity: isHeroTurn ? 1 : 0.35 }} />
                  </>
                )}
              </Box>
              {/* 筹码设置 */}
              <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <TextField label="Hero筹码" type="number" size="small"
                  value={store.stackSizeBB}
                  onChange={(e) => store.setStackSize(Number(e.target.value))}
                  sx={{ width: 85 }} slotProps={{ htmlInput: { min: 1 } }}
                />
                <TextField label="底池" type="number" size="small"
                  value={store.potSizeBB}
                  onChange={(e) => store.setPotSize(Number(e.target.value))}
                  sx={{ width: 80 }} slotProps={{ htmlInput: { min: 0, step: 0.5 } }}
                />
                {store.villains.map((v) => (
                  <TextField key={v.position} label={v.position} type="number" size="small"
                    value={v.stackSizeBB}
                    onChange={(e) => store.setVillainStack(v.position, Number(e.target.value))}
                    sx={{ width: 72 }}
                    slotProps={{ htmlInput: { min: 0, style: { fontSize: '0.8rem' } } }}
                  />
                ))}
              </Box>
            </CardContent>
          </MuiCard>
        </Grid>

        {/* 右：行动面板 */}
        <Grid size={{ xs: 12, md: 4 }}>
          <MuiCard>
            <CardContent sx={{ pb: '12px !important' }}>
              {isHeroTurn ? (
                /* Hero 回合：简化显示，引导用户提交 */
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Chip label={`轮到你了 (${store.heroPosition})`} color="success" size="medium" sx={{ mb: 2 }} />
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    所有对手已完成行动，点击下方按钮让 AI 分析当前局面。
                  </Typography>
                  <Typography variant="caption" color="text.disabled" display="block">
                    你的决策将由 Solver 计算 GTO 建议，AI 教练会给出详细讲解。
                  </Typography>
                </Box>
              ) : (
                <>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {currentTurnPlayer} 的行动
                    </Typography>
                  </Box>

                  {/* 行动按钮 */}
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
                    {(store.currentStreet === 'PREFLOP'
                      ? ['FOLD', 'CALL', 'RAISE', 'ALL_IN']
                      : ['FOLD', 'CHECK', 'CALL', 'BET', 'RAISE', 'ALL_IN']
                    ).map((a) => (
                      <Button
                        key={a}
                        variant="outlined"
                        size="small"
                        onClick={() => handleAddAction(a as ActionType)}
                        disabled={analysis.isLoading || store.heroPosition === null}
                        sx={{ minWidth: 52, fontSize: '0.72rem' }}
                      >
                        {a.replace('_', '')}
                      </Button>
                    ))}
                  </Box>

                  <TextField label="金额 (BB)" type="number" size="small" fullWidth
                    value={betAmount}
                    onChange={(e) => setBetAmount(e.target.value ? Number(e.target.value) : '')}
                    slotProps={{ htmlInput: { min: 0.5, step: 0.5 } }}
                    sx={{ mb: 1 }}
                  />
                </>
              )}

              {/* 本街行动记录 */}
              <Typography variant="caption" color="text.secondary">{STREET_LABELS[store.currentStreet]} 记录</Typography>
              <Paper variant="outlined" sx={{ p: 0.8, maxHeight: 160, overflow: 'auto', mb: 1, bgcolor: 'rgba(0,0,0,0.15)' }}>
                {streetActions.length === 0 ? (
                  <Typography variant="body2" color="text.disabled" sx={{ p: 0.5, fontSize: '0.75rem' }}>暂无</Typography>
                ) : (
                  streetActions.map((action) => {
                    const globalIdx = store.actions.indexOf(action);
                    return (
                      <Box key={globalIdx} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 0.2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Chip
                            label={action.actor} size="small"
                            color={action.actor === 'Hero' ? 'error' : 'primary'} variant="outlined"
                            sx={{ height: 16, fontSize: '0.55rem' }}
                          />
                          <Typography variant="body2" fontSize="0.72rem">
                            {action.action}{action.amount ? ` ${action.amount}BB` : ''}
                          </Typography>
                        </Box>
                        <IconButton size="small" onClick={() => store.removeAction(globalIdx)} sx={{ p: 0 }}>
                          <DeleteIcon sx={{ fontSize: 12 }} />
                        </IconButton>
                      </Box>
                    );
                  })
                )}
              </Paper>

              {/* 全局记录 */}
              <Typography variant="caption" color="text.secondary">全局记录</Typography>
              <Paper variant="outlined" sx={{ p: 0.8, maxHeight: 140, overflow: 'auto', bgcolor: 'rgba(0,0,0,0.1)' }}>
                {store.actions.length === 0 ? (
                  <Typography variant="body2" color="text.disabled" sx={{ p: 0.5, fontSize: '0.75rem' }}>暂无</Typography>
                ) : (
                  STREETS.map((st) => {
                    const acts = store.actions.filter((a) => a.street === st);
                    if (acts.length === 0) return null;
                    return (
                      <Box key={st} sx={{ mb: 0.5 }}>
                        <Chip label={STREET_LABELS[st]} size="small" sx={{ height: 14, fontSize: '0.55rem', mb: 0.2 }} />
                        {acts.map((a, j) => (
                          <Typography key={j} variant="body2" sx={{ pl: 0.5, fontSize: '0.7rem' }}>
                            <Chip label={a.actor} size="small" color={a.actor === 'Hero' ? 'error' : 'primary'} variant="outlined"
                              sx={{ mr: 0.3, height: 14, fontSize: '0.55rem' }} />
                            {a.action}{a.amount ? ` ${a.amount}BB` : ''}
                          </Typography>
                        ))}
                      </Box>
                    );
                  })
                )}
              </Paper>
            </CardContent>
          </MuiCard>
        </Grid>
      </Grid>

      {/* ============================================================ */}
      {/* 底部状态栏 */}
      {/* ============================================================ */}
      {analysis.isLoading && (
        <LinearProgress sx={{ mt: 2, height: 4, borderRadius: 2 }} />
      )}
      <Paper sx={{ mt: 2, p: 1.5, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        {analysis.isLoading ? (
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip label="AI 分析中..." color="info" size="small" />
            <Typography variant="body2" color="text.secondary">
              正在调用 Solver 计算 + DeepSeek AI 生成分析报告，预计 5-15 秒...
            </Typography>
          </Box>
        ) : (
          <>
            {/* 准备状态 */}
            <Box sx={{ display: 'flex', gap: 1, flex: 1, flexWrap: 'wrap', alignItems: 'center' }}>
              {checks.map((chk, i) => (
                <Chip
                  key={i}
                  size="small"
                  icon={chk.done ? <CheckIcon sx={{ fontSize: 14 }} /> : <UncheckIcon sx={{ fontSize: 14 }} />}
                  label={chk.label}
                  color={chk.done ? 'success' : 'default'}
                  variant={chk.done ? 'filled' : 'outlined'}
                  sx={{ fontSize: '0.72rem' }}
                />
              ))}
            </Box>

            {/* 操作提示 */}
            {!canSubmit && (
              <Typography variant="caption" color="text.secondary" sx={{ flex: '0 1 auto' }}>
                {!store.heroPosition ? '↑ 在牌桌卡片选择 Hero 位置' :
                 store.heroCards.length < 2 ? '↑ 左侧牌网格选 2 张手牌' :
                 !isHeroTurn ? '↑ 右侧为对手添加行动' : '检查筹码和底池设置'}
              </Typography>
            )}

            {/* 提交按钮 */}
            <Button
              variant="contained" size="large"
              onClick={handleSubmit}
              disabled={!canSubmit}
              color={canSubmit ? 'success' : 'primary'}
              sx={{ px: 4, ml: 'auto' }}
            >
              {canSubmit ? '分析这手牌' : '等待准备就绪'}
            </Button>
          </>
        )}
      </Paper>
    </Box>
  );
}
