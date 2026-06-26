import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Chip,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  CircularProgress,
  Alert,
  Button,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  SkipNext as SkipNextIcon,
  SkipPrevious as SkipPreviousIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { getReplay } from '@/services/api';
import type { ReplayResponse, StreetSnapshot, EquityPoint } from '@/types/analysis';

const STREET_COLORS: Record<string, string> = {
  PREFLOP: '#ff9800',
  FLOP: '#4caf50',
  TURN: '#2196f3',
  RIVER: '#9c27b0',
};

const STREET_LABELS: Record<string, string> = {
  PREFLOP: 'Preflop',
  FLOP: 'Flop',
  TURN: 'Turn',
  RIVER: 'River',
};

const ACTION_LABELS: Record<string, string> = {
  FOLD: 'Fold',
  CHECK: 'Check',
  CALL: 'Call',
  BET: 'Bet',
  RAISE: 'Raise',
  ALL_IN: 'All In',
};

function formatCards(cards: string | null): string {
  if (!cards) return '—';
  if (cards.length <= 4) return cards;
  return cards.match(/.{1,2}/g)?.join(' ') || cards;
}

function ActionChip({ actionType, amount, playerType }: {
  actionType: string;
  amount: number | null;
  playerType: string;
}) {
  const isAggressive = ['BET', 'RAISE', 'ALL_IN'].includes(actionType);
  return (
    <Chip
      size="small"
      label={
        amount != null
          ? `${ACTION_LABELS[actionType] || actionType} ${amount}BB`
          : ACTION_LABELS[actionType] || actionType
      }
      color={
        actionType === 'FOLD' ? 'default' :
        isAggressive ? 'error' :
        actionType === 'CHECK' ? 'default' : 'primary'
      }
      variant={playerType === 'Hero' ? 'filled' : 'outlined'}
      sx={{ mr: 0.5, mb: 0.5 }}
    />
  );
}

export default function ReplayPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [autoPlay, setAutoPlay] = useState(false);

  const { data: replay, isLoading, error } = useQuery<ReplayResponse>({
    queryKey: ['replay', id],
    queryFn: () => getReplay(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" py={10}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error || !replay) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error instanceof Error ? error.message : 'Failed to load replay data'}
        <Button
          size="small"
          onClick={() => navigate('/history')}
          sx={{ ml: 2 }}
        >
          Back to History
        </Button>
      </Alert>
    );
  }

  const allActions = replay.streets.flatMap(s => s.actions);
  const maxStep = allActions.length;

  const handleNext = () => {
    setActiveStep(prev => Math.min(prev + 1, maxStep));
  };

  const handlePrev = () => {
    setActiveStep(prev => Math.max(prev - 1, 0));
  };

  const toggleAutoPlay = () => {
    setAutoPlay(prev => !prev);
  };

  const getStreetForStep = (step: number): string => {
    let count = 0;
    for (const street of replay.streets) {
      count += street.actions.length;
      if (step < count) return street.street;
    }
    return 'RIVER';
  };

  const currentStreet = getStreetForStep(activeStep);

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/history')}
            sx={{ mb: 1 }}
          >
            Back
          </Button>
          <Typography variant="h4" fontWeight={700}>
            Hand Replay
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
            Position: {replay.hero_position} &nbsp;|&nbsp;
            Cards: {formatCards(replay.hero_cards)} &nbsp;|&nbsp;
            Board: {formatCards(replay.board_cards)}
            {replay.result_bb != null && (
              <> &nbsp;|&nbsp; Result: {replay.result_bb > 0 ? '+' : ''}{replay.result_bb}BB</>
            )}
          </Typography>
        </Box>
      </Box>

      <Box display="flex" gap={3} flexWrap="wrap">
        {/* Left: Action Timeline */}
        <Box flex={1} minWidth={400}>
          {/* Playback controls */}
          <Paper sx={{ p: 2, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Button
              size="small"
              onClick={handlePrev}
              disabled={activeStep === 0}
              startIcon={<SkipPreviousIcon />}
            >
              Prev
            </Button>
            <Button
              size="small"
              variant={autoPlay ? 'contained' : 'outlined'}
              onClick={toggleAutoPlay}
              startIcon={autoPlay ? <PauseIcon /> : <PlayArrowIcon />}
            >
              {autoPlay ? 'Pause' : 'AutoPlay'}
            </Button>
            <Button
              size="small"
              onClick={handleNext}
              disabled={activeStep >= maxStep}
              startIcon={<SkipNextIcon />}
            >
              Next
            </Button>
            <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
              Step {activeStep}/{maxStep}
            </Typography>
          </Paper>

          {/* Streets as stepper groups */}
          {replay.streets.map((street) => {
            const streetIndex = replay.streets.indexOf(street);
            if (street.actions.length === 0) return null;

            return (
              <Paper key={street.street} sx={{ mb: 2, overflow: 'hidden' }}>
                <Box
                  sx={{
                    px: 2,
                    py: 1,
                    bgcolor: STREET_COLORS[street.street] || '#666',
                    color: '#fff',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Typography fontWeight={600}>
                    {STREET_LABELS[street.street] || street.street}
                  </Typography>
                  <Typography variant="body2">
                    Pot: {street.pot_size_bb}BB &nbsp;|&nbsp;
                    Stack: {street.hero_stack_bb}BB
                  </Typography>
                </Box>

                <Box sx={{ p: 1 }}>
                  {street.actions.map((action, i) => {
                    const globalStep =
                      replay.streets
                        .slice(0, streetIndex)
                        .reduce((sum, s) => sum + s.actions.length, 0) + i;

                    const isActive = globalStep <= activeStep;
                    const isPast = globalStep < activeStep;
                    const isLastActive = globalStep === activeStep;

                    return (
                      <Box
                        key={`${street.street}-${i}`}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          py: 0.75,
                          px: 1,
                          opacity: isPast ? 0.5 : isActive ? 1 : 0.2,
                          bgcolor: isLastActive ? 'action.selected' : 'transparent',
                          borderRadius: 1,
                          transition: 'opacity 0.3s',
                        }}
                      >
                        <Box
                          sx={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            bgcolor: action.player_type === 'Hero' ? '#ff5252' : '#448aff',
                            flexShrink: 0,
                          }}
                        />
                        <Typography variant="body2" sx={{ minWidth: 100, fontWeight: 500 }}>
                          {action.player_type} ({action.player_position})
                        </Typography>
                        <ActionChip
                          actionType={action.action_type}
                          amount={action.amount}
                          playerType={action.player_type}
                        />
                      </Box>
                    );
                  })}
                </Box>
              </Paper>
            );
          })}
        </Box>

        {/* Right: Equity Chart + Info */}
        <Box flex={1} minWidth={350}>
          {/* Equity Curve Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Equity Curve
              </Typography>
              <Box sx={{ width: '100%', height: 200 }}>
                <ResponsiveContainer>
                  <LineChart
                    data={replay.equity_curve}
                    margin={{ top: 5, right: 20, left: -20, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="label" stroke="#888" fontSize={12} />
                    <YAxis
                      domain={[0, 100]}
                      stroke="#888"
                      fontSize={12}
                      tickFormatter={(v: number) => `${v}%`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e1e1e', border: '1px solid #444' }}
                      formatter={(value: number) => [`${value}%`, 'Equity']}
                    />
                    <ReferenceLine y={50} stroke="#666" strokeDasharray="3 3" />
                    <Line
                      type="monotone"
                      dataKey="equity"
                      stroke="#4caf50"
                      strokeWidth={2}
                      dot={{ fill: '#4caf50', r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>

          {/* Pot Progression Card */}
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Pot Progression
              </Typography>
              <Box sx={{ width: '100%', height: 180 }}>
                <ResponsiveContainer>
                  <LineChart
                    data={replay.equity_curve}
                    margin={{ top: 5, right: 20, left: -20, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="label" stroke="#888" fontSize={12} />
                    <YAxis stroke="#888" fontSize={12} tickFormatter={(v: number) => `${v}BB`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e1e1e', border: '1px solid #444' }}
                      formatter={(value: number) => [`${value}BB`, 'Pot']}
                    />
                    <Line
                      type="monotone"
                      dataKey="pot_size_bb"
                      stroke="#ff9800"
                      strokeWidth={2}
                      dot={{ fill: '#ff9800', r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>

          {/* Quick stats */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Summary
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">Total Actions</Typography>
                  <Typography variant="h6">{replay.total_actions}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Final Pot</Typography>
                  <Typography variant="h6">{replay.final_pot_bb}BB</Typography>
                </Box>
                {replay.result_bb != null && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">Result</Typography>
                    <Typography
                      variant="h6"
                      color={replay.result_bb > 0 ? 'success.main' : replay.result_bb < 0 ? 'error.main' : 'text.primary'}
                    >
                      {replay.result_bb > 0 ? '+' : ''}{replay.result_bb}BB
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
}
