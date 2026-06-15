import { createTheme } from '@mui/material/styles';

// Titan Bank Brand Colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#0A2A84', // Deep Royal Blue
      light: '#1E4BD1', // Sapphire Blue
      dark: '#061A5A',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#1E4BD1', // Sapphire Blue
      light: '#4A6FD8',
      dark: '#0F2A7A',
      contrastText: '#ffffff',
    },
    accent: {
      main: '#E1B81C', // Titan Gold
      light: '#F0D04A',
      dark: '#B8940E',
      contrastText: '#0A2A84',
    },
    background: {
      default: '#F2F4F7', // Light Background
      paper: '#ffffff',
    },
    text: {
      primary: '#1A1A1A',
      secondary: '#666666',
    },
    success: {
      main: '#28a745',
      light: '#5cb85c',
    },
    warning: {
      main: '#ffc107',
    },
    error: {
      main: '#dc3545',
    },
  },
  typography: {
    fontFamily: '"Inter", "Source Sans Pro", "Open Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
    },
    h2: {
      fontWeight: 700,
      fontSize: '2rem',
      lineHeight: 1.3,
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
      lineHeight: 1.4,
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.4,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.5,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 24px',
          fontWeight: 600,
        },
        contained: {
          boxShadow: '0 2px 8px rgba(10, 42, 132, 0.2)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(10, 42, 132, 0.3)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
          borderRadius: 12,
        },
      },
    },
  },
});

export default theme;

