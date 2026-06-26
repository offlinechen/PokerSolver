import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid2 as Grid,
  Typography,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Psychology as PsychologyIcon,
  Timeline as TimelineIcon,
  Casino as CasinoIcon,
} from '@mui/icons-material';

const features = [
  {
    icon: <AnalyticsIcon sx={{ fontSize: 40 }} />,
    title: 'GTO 分析',
    description: '基于 Solver 的精确 GTO 计算，EV、Equity、策略频率一目了然',
  },
  {
    icon: <PsychologyIcon sx={{ fontSize: 40 }} />,
    title: 'AI 教练',
    description: '大语言模型将冰冷的数字转化为易懂的策略讲解',
  },
  {
    icon: <TimelineIcon sx={{ fontSize: 40 }} />,
    title: '牌局回放',
    description: '逐步回放每一手牌，追踪 EV 变化，发现决策漏洞',
  },
];

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          textAlign: 'center',
          py: { xs: 6, md: 10 },
          px: 2,
        }}
      >
        <CasinoIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        <Typography variant="h2" fontWeight={800} gutterBottom>
          PokerCoachAI
        </Typography>
        <Typography
          variant="h5"
          color="text.secondary"
          sx={{ maxWidth: 600, mx: 'auto', mb: 4 }}
        >
          将 GTO Solver 的数学精度与大语言模型的解释力结合，
          让每位玩家都拥有自己的职业扑克教练。
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate('/hand/new')}
          sx={{
            px: 6,
            py: 1.5,
            fontSize: '1.1rem',
          }}
        >
          开始分析一手牌
        </Button>
      </Box>

      {/* Features */}
      <Container maxWidth="md">
        <Grid container spacing={3}>
          {features.map((feature) => (
            <Grid size={{ xs: 12, md: 4 }} key={feature.title}>
              <Card
                sx={{
                  height: '100%',
                  backgroundColor: 'background.paper',
                  transition: 'transform 0.2s',
                  '&:hover': { transform: 'translateY(-4px)' },
                }}
              >
                <CardContent sx={{ textAlign: 'center', p: 4 }}>
                  <Box sx={{ color: 'primary.main', mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom fontWeight={600}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Bottom CTA */}
      <Box sx={{ textAlign: 'center', py: 6 }}>
        <Typography variant="body2" color="text.secondary">
          Solver负责计算 · LLM负责解释 · 玩家画像负责利用
        </Typography>
      </Box>
    </Box>
  );
}
