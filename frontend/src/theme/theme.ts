// ============================================================
// PokerCoachAI — MUI Theme Configuration
// ============================================================

import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#4CAF50', // Green — poker table felt
      light: '#81C784',
      dark: '#388E3C',
    },
    secondary: {
      main: '#FF9800', // Orange — chips / accent
      light: '#FFB74D',
      dark: '#F57C00',
    },
    background: {
      default: '#0D1B2A',
      paper: '#1B2838',
    },
    error: {
      main: '#EF5350',
    },
    warning: {
      main: '#FFB300',
    },
    success: {
      main: '#66BB6A',
    },
    text: {
      primary: '#ECEFF1',
      secondary: '#90A4AE',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica Neue", Arial, sans-serif',
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 500 },
    h6: { fontWeight: 500 },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

export default theme;
