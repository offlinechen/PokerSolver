import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Pagination,
  Skeleton,
  Typography,
} from '@mui/material';
import { getHands } from '@/services/api';
import type { HandListItem } from '@/types/analysis';
import { SUIT_SYMBOLS } from '@/types/poker';
import type { Suit } from '@/types/poker';

function formatCards(cards: string): string {
  const result: string[] = [];
  for (let i = 0; i < cards.length; i += 2) {
    const rank = cards[i];
    const suit = cards[i + 1] as Suit;
    result.push(`${rank}${SUIT_SYMBOLS[suit] || suit}`);
  }
  return result.join(' ');
}

function HandCard({ hand }: { hand: HandListItem }) {
  const navigate = useNavigate();

  return (
    <Card sx={{ mb: 1 }}>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 2 }}>
        <Chip
          label={hand.hero_position}
          size="small"
          color="primary"
          variant="outlined"
        />
        <Box sx={{ flexGrow: 1, cursor: 'pointer' }} onClick={() => navigate(`/hand/${hand.id}`)}>
          <Typography variant="body1" fontFamily="monospace">
            {formatCards(hand.hero_cards)}
          </Typography>
          {hand.board_cards && (
            <Typography variant="body2" color="text.secondary" fontFamily="monospace">
              {formatCards(hand.board_cards)}
            </Typography>
          )}
        </Box>
        {hand.result_bb !== null && (
          <Chip
            label={`${hand.result_bb > 0 ? '+' : ''}${hand.result_bb.toFixed(1)}BB`}
            size="small"
            color={hand.result_bb > 0 ? 'success' : 'error'}
          />
        )}
        <Chip
          label="回放"
          size="small"
          color="secondary"
          variant="outlined"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/hand/${hand.id}/replay`);
          }}
          sx={{ cursor: 'pointer' }}
        />
        <Typography variant="caption" color="text.secondary">
          {new Date(hand.created_at).toLocaleDateString('zh-CN')}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading } = useQuery({
    queryKey: ['hands', page],
    queryFn: () => getHands(page, pageSize),
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight={700}>
        历史记录
      </Typography>

      {isLoading ? (
        Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} variant="rounded" height={72} sx={{ mb: 1 }} />
        ))
      ) : data && data.items.length > 0 ? (
        <>
          {data.items.map((hand) => (
            <HandCard key={hand.id} hand={hand} />
          ))}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Pagination
              count={Math.ceil(data.total / pageSize)}
              page={page}
              onChange={(_, p) => setPage(p)}
              color="primary"
            />
          </Box>
        </>
      ) : (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            暂无历史记录
          </Typography>
          <Typography variant="body2" color="text.secondary">
            开始分析一手牌，记录会自动出现在这里
          </Typography>
        </Box>
      )}
    </Box>
  );
}
