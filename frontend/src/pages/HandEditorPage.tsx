import { useState, useMemo, useCallback } from 'react';
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
  ToggleButton,
  Tabs,
  Tab,
  Paper,
  IconButton,
  LinearProgress,
  Alert,
  MenuItem,
  Select,
  FormControl,
  Tooltip,
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { useHandEditorStore, STREETS, BOARD_CARDS_PER_STREET } from '@/stores/handEditorStore';
import { useAnalysisStore } from '@/stores/analysisStore';
import { analyzeHand } from '@/services/api';
import type { Card, Position, Suit, Villain, ActionType, Street } from '@/types/poker';
import {
  getPositionsForTable,
  RANKS,
  SUITS,
  SUIT_SYMBOLS,
  SUIT_COLORS,
  cardToString,
} from '@/types/poker';

// ===================================================================
// 街段信息
// ===================================================================

const STREET_LABELS: Record<Street, string> = {
  PREFLOP: '翻前',
  FLOP: '翻牌',
  TURN: '转牌',
  RIVER: '河牌',
};

// ===================================================================
// 行动顺序计算
// ===================================================================

/** 返回当前街段的行动顺序（位置列表），按规则从第一个行动者开始 */
function buildTurnOrder(
  positions: Position[],
  heroPos: Position | null,
  street: Street,
): Position[] {
  if (positions.length === 0 || !heroPos) return [];
  const beforeHero = positions.filter((p) => p !== heroPos);

  if (street === 'PREFLOP') {
    const heroIdx = positions.indexOf(heroPos);
    if (heroIdx === -1) return beforeHero;
    return beforeHero.filter((p) => positions.indexOf(p) < heroIdx);
  } else {
    const heroIdx = positions.indexOf(heroPos);
    if (heroIdx === -1) return beforeHero;
    const after = positions.slice(heroIdx + 1);
    const before = positions.slice(0, heroIdx);
    return [...after, ...before];
  }
}

// ===================================================================
// SVG 牌桌组件
// ===================================================================

const SEAT_COORDS_9: [number, number][] = [
  [50, 5], [80, 10], [95, 30], [97, 55], [88, 78], [65, 88], [35, 88], [15, 72], [7, 42],
];
const SEAT_COORDS_6: [number, number][] = [
  [50, 8], [92, 32], [92, 68], [65, 90], [35, 90], [8, 50],
];
const SEAT_COORDS_2: [number, number][] = [
  [50, 92], [50, 8],
];

function getSeatCoords(tableSize: number): [number, number][] {
  if (tableSize <= 2) return SEAT_COORDS_2;
  if (tableSize <= 6) return SEAT_COORDS_6;
  return SEAT_COORDS_9;
}

function PositionBadge({
  pos,
  isHero,
  stackBB,
  isTurn,
  folded,
}: {
  pos: string;
  isHero: boolean;
  stackBB: number;
  isTurn: boolean;
  folded: boolean;
}) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.2, opacity: folded ? 0.35 : 1 }}>
      <Chip
        label={pos}
        size="small"
        color={isHero ? 'error' : 'default'}
        variant={isHero ? 'filled' : 'outlined'}
        sx={{ fontWeight: 700, fontSize: '0.7rem', height: 20 }}
      />
      <Typography variant="caption" sx={{ fontSize: '0.6rem', color: folded ? 'text.disabled' : 'text.secondary' }}>
        {folded ? 'FOLD' : `${stackBB}BB`}
      </Typography>
    </Box>
  );
}

function PokerTable({
  tableSize,
  heroPosition,
  villains,
  onSelectPlayer,
  selectedPlayer,
  currentTurn,
  foldedPositions,
}: {
  tableSize: number;
  heroPosition: Position | null;
  villains: Villain[];
  onSelectPlayer: (actor: string) => void;
  selectedPlayer: string;
  currentTurn: string;
  foldedPositions: Set<string>;
}) {
  const coords = useMemo(() => getSeatCoords(tableSize), [tableSize]);
  const positions = useMemo(() => getPositionsForTable(tableSize), [tableSize]);

  return (
    <Box sx={{ position: 'relative', width: '100%', aspectRatio: '1.3 / 1', minHeight: 220 }}>
      <svg viewBox="0 0 100 100" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
        <ellipse cx="50" cy="50" rx="42" ry="30" fill="#1b5e20" stroke="#4caf50" strokeWidth="1.5" />
        <ellipse cx="50" cy="50" rx="34" ry="22" fill="#2e7d32" stroke="none" />
        <text x="50" y="53" textAnchor="middle" fill="#a5d6a7" fontSize="4">POKER TABLE</text>
      </svg>

      {positions.map((pos, i) => {
        const [cx, cy] = coords[i] || [50, 50];
        const isHero = pos === heroPosition;
        const isTurn = currentTurn === pos || (currentTurn === 'Hero' && isHero);
        const isSelected = selectedPlayer === pos || (selectedPlayer === 'Hero' && isHero);
        const folded = isHero ? false : foldedPositions.has(pos);
        const villain = villains.find((v) => v.position === pos);
        const stack = isHero ? 0 : (villain?.stackSizeBB ?? 100);

        return (
          <Box
            key={pos}
            onClick={() => onSelectPlayer(isHero ? 'Hero' : pos)}
            sx={{
              position: 'absolute',
              left: `${cx}%`,
              top: `${cy}%`,
              transform: 'translate(-50%, -50%)',
              cursor: 'pointer',
              transition: 'all 0.15s',
              p: 0.3,
              borderRadius: 1,
              border: isTurn ? '2px solid #ff9800' : isSelected ? '2px solid #4fc3f7' : '2px solid transparent',
              bgcolor: isTurn ? 'rgba(255,152,0,0.15)' : isSelected ? 'rgba(79,195,247,0.08)' : 'transparent',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' },
            }}
          >
            <PositionBadge pos={pos} isHero={isHero} stackBB={stack} isTurn={isTurn} folded={folded} />
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

  // ------------------------------------------------------------------
  // 当前街道与牌桌
  // ------------------------------------------------------------------
  const maxBoardCards = BOARD_CARDS_PER_STREET[store.currentStreet];
  const positions = useMemo(() => getPositionsForTable(store.tableSize), [store.tableSize]);

  // 已弃牌的玩家（本街道）
  const foldedPositions = useMemo(() => {
    const folded = new Set<string>();
    store.actions
      .filter((a) => a.street === store.currentStreet && a.action === 'FOLD')
      .forEach((a) => folded.add(a.actor));
    return folded;
  }, [store.actions, store.currentStreet]);

  // ------------------------------------------------------------------
  // 计算行动顺序 & 当前轮到谁
  // ------------------------------------------------------------------
  const turnOrder = useMemo(
    () => buildTurnOrder(positions, store.heroPosition, store.currentStreet),
    [positions, store.heroPosition, store.currentStreet],
  );

  // 已在本街道行动过的玩家
  const actedThisStreet = useMemo(() => {
    const acted = new Set<string>();
    store.actions
      .filter((a) => a.street === store.currentStreet)
      .forEach((a) => acted.add(a.actor));
    return acted;
  }, [store.actions, store.currentStreet]);

  // 当前该谁行动
  const currentTurnPlayer = useMemo(() => {
    // 找到第一个还没在本街道行动过的玩家（且未弃牌）
    for (const pos of turnOrder) {
      if (!actedThisStreet.has(pos) && !foldedPositions.has(pos)) {
        return pos;
      }
    }
    // 所有非 Hero 玩家都行动过了 → Hero 的回合
    return 'Hero';
  }, [turnOrder, actedThisStreet, foldedPositions]);

  const isHeroTurn = currentTurnPlayer === 'Hero';

  // ------------------------------------------------------------------
  // 卡牌选择
  // ------------------------------------------------------------------
  const handleCardClick = (rank: string, suit: Suit) => {
    const card: Card = { rank: rank as Card['rank'], suit };
    if (store.heroCards.length < 2) {
      store.setHeroCards([...store.heroCards, card]);
    } else if (store.boardCards.length < maxBoardCards) {
      store.setBoardCards([...store.boardCards, card]);
    }
  };

  const isCardSelected = (rank: string, suit: Suit): boolean => {
    const allSelected = [...store.heroCards, ...store.boardCards];
    return allSelected.some((c) => c.rank === rank && c.suit === suit);
  };

  // ------------------------------------------------------------------
  // 行动
  // ------------------------------------------------------------------
  const handleAddAction = (action: ActionType) => {
    const needsAmt = ['BET', 'RAISE', 'CALL', 'ALL_IN'].includes(action);
    const amount = needsAmt && typeof betAmount === 'number' && betAmount > 0 ? betAmount : null;

    store.addAction({
      street: store.currentStreet,
      actor: currentTurnPlayer,
      action,
      amount,
    });
    setBetAmount('');
  };

  // ------------------------------------------------------------------
  // 提交分析（仅 Hero 回合可用）
  // ------------------------------------------------------------------
  const handleSubmit = async () => {
    if (store.heroCards.length < 2 || !store.heroPosition) return;
    analysis.setLoading(true);
    analysis.setError(null);
    try {
      const result = await analyzeHand({
        hero_cards: store.heroCards.map(cardToString) as [string, string],
        board_cards: store.boardCards.map(cardToString),
        hero_position: store.heroPosition,
        stack_size_bb: store.stackSizeBB,
        pot_size_bb: store.potSizeBB,
        actions: store.actions.map((a) => ({
          street: a.street,
          actor: a.actor === 'Hero' ? 'Hero' : 'Villain',
          action: a.action,
          amount: a.amount,
        })),
      });
      analysis.setResult(result);
      navigate(`/hand/${result.hand_id}`);
    } catch (err) {
      analysis.setError(err instanceof Error ? err.message : '分析失败');
    }
  };

  const canSubmit =
    store.heroCards.length >= 2 &&
    store.heroPosition !== null &&
    store.stackSizeBB > 0 &&
    isHeroTurn;

  const progress =
    (store.heroCards.length >= 2 ? 25 : store.heroCards.length * 12) +
    (store.heroPosition ? 25 : 0) +
    (store.potSizeBB > 0 ? 25 : 0) +
    (store.actions.length > 0 ? 25 : 0);

  const streetActions = store.actions.filter((a) => a.street === store.currentStreet);

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight={700}>
        新建手牌分析
      </Typography>

      {/* ============================================================ */}
      {/* 回合提示条 */}
      {/* ============================================================ */}
      {store.heroPosition && (
        <Paper
          sx={{
            mb: 2,
            p: 1.5,
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            bgcolor: isHeroTurn ? 'rgba(76,175,80,0.12)' : 'rgba(255,152,0,0.08)',
            border: isHeroTurn ? '1px solid #4caf50' : '1px solid #ff9800',
          }}
        >
          {isHeroTurn ? (
            <>
              <Chip label="你的回合!" color="success" size="medium" />
              <Typography variant="body1" fontWeight={600} color="success.main">
                轮到 Hero ({store.heroPosition}) 行动 — 可进行分析
              </Typography>
            </>
          ) : (
            <>
              <Chip label="等待中" color="warning" size="medium" />
              <Typography variant="body1" color="warning.main">
                当前行动者: {currentTurnPlayer}
                {turnOrder.length > 0 && (
                  <Typography component="span" variant="body2" sx={{ ml: 1 }}>
                    （顺序: {turnOrder.join(' → ')} → 你）
                  </Typography>
                )}
              </Typography>
            </>
          )}
        </Paper>
      )}

      {/* ============================================================ */}
      {/* 街段 Tabs */}
      {/* ============================================================ */}
      <Paper sx={{ mb: 2, overflow: 'hidden' }}>
        <Tabs
          value={STREETS.indexOf(store.currentStreet)}
          onChange={(_, i) => store.setCurrentStreet(STREETS[i])}
          variant="fullWidth"
          sx={{ '& .MuiTab-root': { py: 1.5, fontWeight: 600 } }}
        >
          {STREETS.map((s, i) => (
            <Tooltip
              key={s}
              title={i === 0 ? '无需公共牌' : `需要 ${BOARD_CARDS_PER_STREET[s]} 张公共牌`}
            >
              <Tab
                label={`${STREET_LABELS[s]} (${s})`}
                disabled={i > 0 && store.boardCards.length < BOARD_CARDS_PER_STREET[s]}
                sx={
                  store.currentStreet === s
                    ? { bgcolor: 'rgba(76,175,80,0.1)', color: '#4caf50 !important' }
                    : undefined
                }
              />
            </Tooltip>
          ))}
        </Tabs>
      </Paper>

      <LinearProgress
        variant="determinate"
        value={Math.min(progress, 100)}
        sx={{ mb: 2, height: 4, borderRadius: 2 }}
      />

      {analysis.error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => analysis.setError(null)}>
          {analysis.error}
        </Alert>
      )}

      <Grid container spacing={2}>
        {/* ================================================================ */}
        {/* 左：卡牌选择 */}
        {/* ================================================================ */}
        <Grid size={{ xs: 12, lg: 5 }}>
          <MuiCard sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                {store.heroCards.length < 2
                  ? '选择 Hero 手牌 (需 2 张)'
                  : store.boardCards.length < maxBoardCards
                    ? `${STREET_LABELS[store.currentStreet]}阶段 — 可选 ${maxBoardCards} 张公共牌（已选 ${store.boardCards.length}）`
                    : maxBoardCards === 0
                      ? '翻前已就绪'
                      : '公共牌已就绪'}
              </Typography>

              <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Hero</Typography>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    {[0, 1].map((i) => {
                      const card = store.heroCards[i];
                      return (
                        <Paper
                          key={i}
                          variant="outlined"
                          sx={{
                            width: 40, height: 56, display: 'flex', alignItems: 'center',
                            justifyContent: 'center', fontSize: '1.2rem', fontWeight: 700,
                            color: card ? SUIT_COLORS[card.suit] : '#555',
                            bgcolor: card ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.02)',
                            cursor: card ? 'pointer' : 'default',
                          }}
                          onClick={() => { if (card) store.setHeroCards(store.heroCards.filter((_, j) => j !== i)); }}
                        >
                          {card ? `${card.rank}${SUIT_SYMBOLS[card.suit]}` : '?'}
                        </Paper>
                      );
                    })}
                  </Box>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Board ({store.boardCards.length}/{maxBoardCards})
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    {Array.from({ length: maxBoardCards }).map((_, i) => {
                      const card = store.boardCards[i];
                      return (
                        <Paper
                          key={i}
                          variant="outlined"
                          sx={{
                            width: 36, height: 52, display: 'flex', alignItems: 'center',
                            justifyContent: 'center', fontSize: '1rem', fontWeight: 700,
                            color: card ? SUIT_COLORS[card.suit] : '#444',
                            bgcolor: card ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.01)',
                            cursor: card ? 'pointer' : 'default',
                          }}
                          onClick={() => { if (card) store.setBoardCards(store.boardCards.filter((_, j) => j !== i)); }}
                        >
                          {card ? `${card.rank}${SUIT_SYMBOLS[card.suit]}` : '·'}
                        </Paper>
                      );
                    })}
                    {maxBoardCards === 0 && (
                      <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>翻前无公共牌</Typography>
                    )}
                  </Box>
                </Box>
              </Box>

              {/* 52 张牌网格 */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.3 }}>
                {RANKS.map((rank) => (
                  <Box key={rank} sx={{ display: 'flex', gap: 0.3 }}>
                    {SUITS.map((suit) => {
                      const selected = isCardSelected(rank, suit);
                      return (
                        <Button
                          key={`${rank}${suit}`}
                          variant={selected ? 'contained' : 'outlined'}
                          onClick={() => handleCardClick(rank, suit)}
                          disabled={
                            (store.heroCards.length >= 2 && store.boardCards.length >= maxBoardCards) ||
                            (store.heroCards.length < 2 && store.boardCards.length > 0)
                          }
                          sx={{
                            minWidth: 40, height: 40, p: 0, fontSize: '0.85rem', fontWeight: 700,
                            color: selected ? '#fff' : SUIT_COLORS[suit],
                            borderColor: 'rgba(255,255,255,0.08)', opacity: selected ? 1 : 0.7,
                          }}
                        >
                          {rank}{SUIT_SYMBOLS[suit]}
                        </Button>
                      );
                    })}
                  </Box>
                ))}
              </Box>

              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button size="small" variant="text" onClick={() => { store.setHeroCards([]); store.setBoardCards([]); }}>
                  清空选牌
                </Button>
              </Box>
            </CardContent>
          </MuiCard>
        </Grid>

        {/* ================================================================ */}
        {/* 中：牌桌 + 设置 */}
        {/* ================================================================ */}
        <Grid size={{ xs: 12, lg: 4 }}>
          <MuiCard sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1" fontWeight={600}>
                  牌桌 ({store.tableSize}人)
                </Typography>
                <FormControl size="small" sx={{ minWidth: 80 }}>
                  <Select
                    value={store.tableSize}
                    onChange={(e) => store.setTableSize(Number(e.target.value))}
                  >
                    <MenuItem value={2}>2人 (HU)</MenuItem>
                    <MenuItem value={6}>6人</MenuItem>
                    <MenuItem value={9}>9人</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              <PokerTable
                tableSize={store.tableSize}
                heroPosition={store.heroPosition}
                villains={store.villains}
                onSelectPlayer={() => {}} // 行动者由顺序决定，不可手动选
                selectedPlayer={currentTurnPlayer}
                currentTurn={currentTurnPlayer}
                foldedPositions={foldedPositions}
              />

              {/* 当前行动者 */}
              <Box sx={{ mt: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
                <Typography variant="body2" color="text.secondary">当前行动者:</Typography>
                <Chip
                  label={currentTurnPlayer === 'Hero' ? `Hero (${store.heroPosition})` : currentTurnPlayer}
                  color={isHeroTurn ? 'success' : 'warning'}
                  size="small"
                />
              </Box>

              {/* 行动顺序指引 */}
              {turnOrder.length > 0 && (
                <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary">顺序:</Typography>
                  {turnOrder.map((pos, i) => {
                    const done = actedThisStreet.has(pos) || foldedPositions.has(pos);
                    const isCurrent = currentTurnPlayer === pos;
                    return (
                      <Chip
                        key={pos}
                        label={`${i + 1}. ${pos}`}
                        size="small"
                        variant={isCurrent ? 'filled' : done ? 'outlined' : 'outlined'}
                        color={isCurrent ? 'warning' : done ? 'default' : 'default'}
                        sx={{
                          height: 20, fontSize: '0.65rem',
                          opacity: done && !isCurrent ? 0.4 : 1,
                          borderColor: isCurrent ? '#ff9800' : undefined,
                        }}
                      />
                    );
                  })}
                  <Chip
                    label="你"
                    size="small"
                    variant="filled"
                    color={isHeroTurn ? 'success' : 'default'}
                    sx={{ height: 20, fontSize: '0.65rem', opacity: isHeroTurn ? 1 : 0.4 }}
                  />
                </Box>
              )}
            </CardContent>
          </MuiCard>

          {/* 玩家筹码 */}
          <MuiCard sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>玩家堆叠</Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 1.5 }}>
                <TextField label="Hero 筹码" type="number" value={store.stackSizeBB}
                  onChange={(e) => store.setStackSize(Number(e.target.value))}
                  size="small" sx={{ flex: 1 }} inputProps={{ min: 1 }} />
                <TextField label="底池" type="number" value={store.potSizeBB}
                  onChange={(e) => store.setPotSize(Number(e.target.value))}
                  size="small" sx={{ flex: 1 }} inputProps={{ min: 0, step: 0.5 }} />
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {store.villains.map((v) => (
                  <TextField key={v.position} label={v.position} type="number" value={v.stackSizeBB}
                    onChange={(e) => store.setVillainStack(v.position, Number(e.target.value))}
                    size="small" sx={{ width: 90 }}
                    inputProps={{ min: 0, style: { fontSize: '0.85rem' } }} />
                ))}
              </Box>
            </CardContent>
          </MuiCard>
        </Grid>

        {/* ================================================================ */}
        {/* 右：行动面板 */}
        {/* ================================================================ */}
        <Grid size={{ xs: 12, lg: 3 }}>
          <MuiCard sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                {STREET_LABELS[store.currentStreet]} 行动
              </Typography>

              {/* 操作按钮（仅当前行动者的回合可用） */}
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
                    disabled={analysis.isLoading || isHeroTurn}
                    sx={{ minWidth: 56, fontSize: '0.75rem' }}
                  >
                    {a.replace('_', '')}
                  </Button>
                ))}
              </Box>

              <TextField label="金额 (BB)" type="number" value={betAmount}
                onChange={(e) => setBetAmount(e.target.value ? Number(e.target.value) : '')}
                size="small" fullWidth sx={{ mb: 1 }}
                disabled={isHeroTurn}
                inputProps={{ min: 0.5, step: 0.5 }} />

              {/* 当前街道行动历史 — 带位置标签 */}
              <Paper variant="outlined" sx={{ p: 1, maxHeight: 200, overflow: 'auto', bgcolor: 'rgba(0,0,0,0.15)' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  {STREET_LABELS[store.currentStreet]} 行动记录
                </Typography>
                {streetActions.length === 0 ? (
                  <Typography variant="body2" color="text.disabled" sx={{ p: 1 }}>暂无</Typography>
                ) : (
                  streetActions.map((action, i) => {
                    const globalIdx = store.actions.indexOf(action);
                    const isVillain = action.actor !== 'Hero';
                    return (
                      <Box
                        key={globalIdx}
                        sx={{
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          py: 0.3, px: 0.5, borderRadius: 1,
                          '&:hover': { bgcolor: 'rgba(255,255,255,0.03)' },
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {/* 位置标签 */}
                          <Chip
                            label={isVillain ? action.actor : `Hero(${store.heroPosition})`}
                            size="small"
                            color={isVillain ? 'primary' : 'error'}
                            variant="outlined"
                            sx={{ height: 18, fontSize: '0.6rem', fontWeight: 700 }}
                          />
                          <Typography variant="body2" component="span">
                            {action.action}
                            {action.amount ? ` ${action.amount}BB` : ''}
                          </Typography>
                        </Box>
                        <IconButton size="small" onClick={() => store.removeAction(globalIdx)} sx={{ p: 0.2 }}>
                          <DeleteIcon sx={{ fontSize: 14 }} />
                        </IconButton>
                      </Box>
                    );
                  })
                )}
              </Paper>
            </CardContent>
          </MuiCard>

          {/* 全局行动记录 — 带位置 */}
          <MuiCard>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>全局行动记录</Typography>
              <Paper variant="outlined" sx={{ p: 1, maxHeight: 220, overflow: 'auto', bgcolor: 'rgba(0,0,0,0.1)' }}>
                {store.actions.length === 0 ? (
                  <Typography variant="body2" color="text.disabled" sx={{ p: 1 }}>暂无</Typography>
                ) : (
                  STREETS.map((street) => {
                    const acts = store.actions.filter((a) => a.street === street);
                    if (acts.length === 0) return null;
                    return (
                      <Box key={street} sx={{ mb: 1 }}>
                        <Chip label={STREET_LABELS[street]} size="small"
                          sx={{ mb: 0.3, fontSize: '0.65rem', height: 18 }} />
                        {acts.map((a, j) => (
                          <Typography key={j} variant="body2" sx={{ pl: 1, fontSize: '0.8rem' }}>
                            <Chip
                              label={a.actor === 'Hero' ? `Hero(${store.heroPosition})` : a.actor}
                              size="small"
                              color={a.actor === 'Hero' ? 'error' : 'primary'}
                              variant="outlined"
                              sx={{ mr: 0.5, height: 16, fontSize: '0.6rem' }}
                            />
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

      {/* ================================================================ */}
      {/* 底部提交 */}
      {/* ================================================================ */}
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 2 }}>
        {!isHeroTurn && store.heroPosition && (
          <Typography variant="body2" color="text.secondary">
            请先完成 {turnOrder.filter((p) => !actedThisStreet.has(p) && !foldedPositions.has(p)).join(', ')} 的行动，再进行分析
          </Typography>
        )}
        <Button
          variant="contained"
          size="large"
          onClick={handleSubmit}
          disabled={!canSubmit || analysis.isLoading}
          sx={{ px: 6 }}
          color={isHeroTurn ? 'success' : 'primary'}
        >
          {analysis.isLoading ? '分析中...' : isHeroTurn ? '🔍 分析这手牌' : '等待你的回合...'}
        </Button>
      </Box>
    </Box>
  );
}
