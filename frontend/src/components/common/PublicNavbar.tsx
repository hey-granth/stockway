import { AppBar, Toolbar, Typography, Button, Container, Box, Link } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';

export default function PublicNavbar() {
  return (
    <AppBar
      position="sticky"
      color="default"
      elevation={0}
      sx={{
        backgroundColor: 'background.default',
        borderBottom: '1px solid',
        borderColor: 'divider',
        color: 'text.primary',
      }}
    >
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ justifyContent: 'space-between', height: 64 }}>
          {/* Logo Section */}
          <Box display="flex" alignItems="center" gap={4}>
            <Typography
              variant="h6"
              component={RouterLink}
              to="/"
              sx={{
                fontWeight: 700,
                color: 'text.primary',
                textDecoration: 'none',
                letterSpacing: '-0.02em',
                fontSize: '1.25rem',
              }}
            >
              Stockway
            </Typography>

            {/* Desktop Nav Links */}
            <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 3 }}>
              <Link
                component={RouterLink}
                to="/docs"
                underline="none"
                sx={{
                  fontSize: '0.9rem',
                  fontWeight: 500,
                  color: 'text.secondary',
                  '&:hover': { color: 'text.primary' },
                  transition: 'color 0.2s',
                }}
              >
                Docs
              </Link>
              <Link
                component={RouterLink}
                to="/contact"
                underline="none"
                sx={{
                  fontSize: '0.9rem',
                  fontWeight: 500,
                  color: 'text.secondary',
                  '&:hover': { color: 'text.primary' },
                  transition: 'color 0.2s',
                }}
              >
                Contact
              </Link>
            </Box>
          </Box>

          {/* Right Action Section */}
          <Box display="flex" alignItems="center" gap={2}>
            <ThemeToggle />
            <Button
              component={RouterLink}
              to="/login"
              variant="text"
              sx={{
                display: { xs: 'none', sm: 'inline-flex' },
                color: 'text.primary',
                fontWeight: 500,
              }}
            >
              Sign In
            </Button>
            <Button
              component={RouterLink}
              to="/signup"
              variant="contained"
              sx={{
                fontWeight: 600,
                px: 2.5,
              }}
            >
              Get Started
            </Button>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
