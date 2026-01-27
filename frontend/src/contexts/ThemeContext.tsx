import { createContext, useContext, useState, useEffect, ReactNode, useMemo } from 'react';
import { ThemeProvider as MuiThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

type ThemeMode = 'light' | 'dark';

interface ThemeContextType {
  mode: ThemeMode;
  toggleTheme: () => void;
  setThemeMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useThemeContext = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeContext must be used within ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  // Default to dark mode, check localStorage
  const [mode, setMode] = useState<ThemeMode>(() => {
    const stored = localStorage.getItem('theme-mode');
    return (stored as ThemeMode) || 'dark';
  });

  useEffect(() => {
    localStorage.setItem('theme-mode', mode);
  }, [mode]);

  const toggleTheme = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  const setThemeMode = (newMode: ThemeMode) => {
    setMode(newMode);
  };

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          ...(mode === 'dark'
            ? {
                // Dark mode palette
                primary: {
                  main: '#60a5fa', // Blue 400
                  light: '#93c5fd',
                  dark: '#3b82f6',
                  contrastText: '#000000',
                },
                secondary: {
                  main: '#a78bfa', // Purple 400
                  light: '#c4b5fd',
                  dark: '#8b5cf6',
                  contrastText: '#000000',
                },
                success: {
                  main: '#34d399',
                  light: '#6ee7b7',
                  dark: '#10b981',
                },
                warning: {
                  main: '#fbbf24',
                  light: '#fcd34d',
                  dark: '#f59e0b',
                },
                error: {
                  main: '#f87171',
                  light: '#fca5a5',
                  dark: '#ef4444',
                },
                info: {
                  main: '#60a5fa',
                  light: '#93c5fd',
                  dark: '#3b82f6',
                },
                background: {
                  default: '#0f172a', // Slate 900
                  paper: '#1e293b', // Slate 800
                },
                text: {
                  primary: '#f1f5f9', // Slate 100
                  secondary: '#cbd5e1', // Slate 300
                },
                divider: '#334155', // Slate 700
              }
            : {
                // Light mode palette
                primary: {
                  main: '#2563eb', // Blue 600
                  light: '#60a5fa',
                  dark: '#1e40af',
                  contrastText: '#ffffff',
                },
                secondary: {
                  main: '#8b5cf6', // Purple 600
                  light: '#a78bfa',
                  dark: '#6d28d9',
                  contrastText: '#ffffff',
                },
                success: {
                  main: '#10b981',
                  light: '#34d399',
                  dark: '#059669',
                },
                warning: {
                  main: '#f59e0b',
                  light: '#fbbf24',
                  dark: '#d97706',
                },
                error: {
                  main: '#ef4444',
                  light: '#f87171',
                  dark: '#dc2626',
                },
                info: {
                  main: '#3b82f6',
                  light: '#60a5fa',
                  dark: '#2563eb',
                },
                background: {
                  default: '#f9fafb', // Gray 50
                  paper: '#ffffff',
                },
                text: {
                  primary: '#111827', // Gray 900
                  secondary: '#6b7280', // Gray 500
                },
                divider: '#e5e7eb', // Gray 200
              }),
        },
        typography: {
          fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
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
            fontSize: '1.5rem',
            lineHeight: 1.4,
          },
          h4: {
            fontWeight: 600,
            fontSize: '1.25rem',
            lineHeight: 1.5,
          },
          h5: {
            fontWeight: 600,
            fontSize: '1.125rem',
            lineHeight: 1.5,
          },
          h6: {
            fontWeight: 600,
            fontSize: '1rem',
            lineHeight: 1.5,
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
                boxShadow: 'none',
                '&:hover': {
                  boxShadow: mode === 'dark'
                    ? '0 4px 12px rgba(0, 0, 0, 0.4)'
                    : '0 2px 8px rgba(0, 0, 0, 0.1)',
                },
              },
              sizeLarge: {
                padding: '12px 32px',
                fontSize: '1rem',
              },
            },
          },
          MuiCard: {
            styleOverrides: {
              root: {
                boxShadow: mode === 'dark'
                  ? '0 4px 6px rgba(0, 0, 0, 0.3)'
                  : '0 1px 3px rgba(0, 0, 0, 0.1)',
                borderRadius: 12,
                backgroundImage: 'none',
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
          MuiTextField: {
            styleOverrides: {
              root: {
                '& .MuiOutlinedInput-root': {
                  borderRadius: 8,
                },
              },
            },
          },
          MuiChip: {
            styleOverrides: {
              root: {
                fontWeight: 500,
              },
            },
          },
        },
      }),
    [mode]
  );

  const value = {
    mode,
    toggleTheme,
    setThemeMode,
  };

  return (
    <ThemeContext.Provider value={value}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
}
