import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid2 as Grid,
  LinearProgress,
  Paper,
  Typography,
  Alert,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Replay as ReplayIcon,
} from '@mui/icons-material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { getHand } from '@/services/api';
import { useAnalysisStore } from '@/stores/analysisStore';
import type { StrategyBreakdown } from '@/types/analysis';

const PIE_COLORS = ['#66BB6A', '#FF9800', '#EF5350'];
const STRATEGY_LABELS: Record<string, string> = {
  call: 'Call',
  raise: 'Raise',
  fold: 'Fold',
};

function StrategyPie({ strategy }: { strategy: StrategyBreakdown }) {
  const data = [
    { name: 'Call', value: strategy.call },
    { name: 'Raise', value: strategy.raise },
    { name: 'Fold', value: strategy.fold },
  ];

  return (
    <Box sx={{ width: '100%', height: 250 }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={index} fill={PIE_COLORS[index]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3 }}>
        {data.map((item, i) => (
          <Box key={item.name} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: PIE_COLORS[i],
              }}
            />
            <Typography variant="caption">
              {item.name}: {item.value.toFixed(1)}%
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

function EVBar({ call, raise, fold }: { call: number; raise: number; fold: number }) {
  const data = [
    { name: 'Call', ev: call },
    { name: 'Raise', ev: raise },
    { name: 'Fold', ev: fold },
  ];

  return (
    <Box sx={{ width: '100%', height: 200 }}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis type="number" stroke="#90A4AE" />
          <YAxis type="category" dataKey="name" stroke="#90A4AE" />
          <Tooltip />
          <Bar dataKey="ev" radius={[0, 6, 6, 0]}>
            {data.map((item, i) => (
              <Cell
                key={i}
                fill={item.ev > 0 ? '#66BB6A' : item.ev < 0 ? '#EF5350' : '#90A4AE'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}

export default function AnalysisResultPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const storeResult = useAnalysisStore((s) => s.currentResult);

  const { data: hand } = useQuery({
    queryKey: ['hand', id],
    queryFn: () => getHand(id!),
    enabled: !!id,
  });

  const result = storeResult;

  if (!result) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h5" color="text.secondary" gutterBottom>
          未找到分析结果
        </Typography>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/hand/new')}
        >
          新建分析
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Button
          variant="text"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/history')}
        >
          返回历史
        </Button>
        <Chip
          label={result.recommendation}
          color={
            result.recommendation === 'Call'
              ? 'success'
              : result.recommendation === 'Raise'
                ? 'warning'
                : 'error'
          }
          sx={{ fontSize: '1.1rem', fontWeight: 700, py: 2.5, px: 2 }}
        />
      </Box>

      <Grid container spacing={3}>
        {/* Equity */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Equity (胜率)
              </Typography>
              <Typography variant="h3" fontWeight={800} color="primary.main">
                {result.equity.toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={result.equity}
                sx={{ mt: 1, height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* EV Comparison */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                EV 对比
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-around', mt: 2 }}>
                {[
                  { label: 'Call', value: result.call_ev },
                  { label: 'Raise', value: result.raise_ev },
                  { label: 'Fold', value: result.fold_ev },
                ].map(({ label, value }) => (
                  <Box key={label} sx={{ textAlign: 'center' }}>
                    <Typography
                      variant="h5"
                      fontWeight={700}
                      color={value > 0 ? 'success.main' : value < 0 ? 'error.main' : 'text.secondary'}
                    >
                      {value > 0 ? '+' : ''}
                      {value.toFixed(2)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {label} EV (BB)
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Hand Info */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                牌局信息
              </Typography>
              {hand && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2">
                    <strong>手牌:</strong> {hand.hero_cards}
                  </Typography>
                  <Typography variant="body2">
                    <strong>公共牌:</strong> {hand.board_cards || '翻前'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>位置:</strong> {hand.hero_position}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Strategy Chart */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                GTO 策略分布
              </Typography>
              <StrategyPie strategy={result.strategy} />
            </CardContent>
          </Card>
        </Grid>

        {/* EV Bar Chart */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                EV 柱状图
              </Typography>
              <EVBar
                call={result.call_ev}
                raise={result.raise_ev}
                fold={result.fold_ev}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* AI Analysis Sections */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                GTO 分析
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                {result.gto_analysis}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom color="warning.main">
                风险分析
              </Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                {result.risk_analysis}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom color="primary.main">
                学习要点
              </Typography>
              <Box component="ul" sx={{ pl: 2, mt: 0 }}>
                {result.learning_points.map((point, i) => (
                  <Typography key={i} component="li" variant="body2" sx={{ mb: 1, lineHeight: 1.6 }}>
                    {point}
                  </Typography>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
