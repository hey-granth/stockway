import { Box, Container, Typography, Button, Grid, Card, CardContent, alpha } from '@mui/material';
import {
  Store,
  Warehouse,
  DeliveryDining,
  AdminPanelSettings,
  TrendingUp,
  Speed,
  Security
} from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';
import PublicNavbar from '@/components/common/PublicNavbar';

export default function LandingPage() {
  const features = [
    {
      icon: <Store sx={{ fontSize: 48 }} />,
      title: 'For Shopkeepers',
      description: 'Browse inventory, place orders, and track deliveries in real-time from nearby warehouses.',
    },
    {
      icon: <Warehouse sx={{ fontSize: 48 }} />,
      title: 'For Warehouses',
      description: 'Manage inventory, fulfill orders, coordinate with riders, and optimize your operations.',
    },
    {
      icon: <DeliveryDining sx={{ fontSize: 48 }} />,
      title: 'For Riders',
      description: 'Accept deliveries, navigate routes, track earnings, and deliver with efficiency.',
    },
    {
      icon: <AdminPanelSettings sx={{ fontSize: 48 }} />,
      title: 'Admin Control',
      description: 'Full platform oversight with analytics, user management, and system monitoring.',
    },
  ];

  const benefits = [
    {
      icon: <TrendingUp />,
      title: 'Real-time Analytics',
      description: 'Track orders, inventory, and performance metrics live.',
    },
    {
      icon: <Speed />,
      title: 'Lightning Fast',
      description: 'Optimized for speed with instant updates and notifications.',
    },
    {
      icon: <Security />,
      title: 'Secure & Reliable',
      description: 'Enterprise-grade security with role-based access control.',
    },
  ];

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <PublicNavbar />

      {/* Hero Section */}
      <Box
        sx={{
          position: 'relative',
          overflow: 'hidden',
          pt: { xs: 8, md: 12 },
          pb: { xs: 8, md: 12 },
          background: (theme) =>
            theme.palette.mode === 'dark'
              ? `linear-gradient(180deg, ${alpha(theme.palette.primary.dark, 0.1)} 0%, ${alpha(
                  theme.palette.background.default,
                  1
                )} 100%)`
              : `linear-gradient(180deg, ${alpha(theme.palette.primary.light, 0.1)} 0%, ${alpha(
                  theme.palette.background.default,
                  1
                )} 100%)`,
        }}
      >
        {/* Animated background pattern */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            opacity: 0.03,
            backgroundImage: 'radial-gradient(circle, currentColor 1px, transparent 1px)',
            backgroundSize: '40px 40px',
            pointerEvents: 'none',
          }}
        />

        <Container maxWidth="lg" sx={{ position: 'relative' }}>
          <Box textAlign="center" maxWidth="800px" mx="auto">
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: '2.5rem', sm: '3.5rem', md: '4.5rem' },
                fontWeight: 800,
                mb: 3,
                background: (theme) =>
                  theme.palette.mode === 'dark'
                    ? 'linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%)'
                    : 'linear-gradient(135deg, #2563eb 0%, #8b5cf6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '-0.02em',
              }}
            >
              Seamless Supply Chain Management
            </Typography>

            <Typography
              variant="h5"
              color="text.secondary"
              sx={{ mb: 5, lineHeight: 1.6, fontWeight: 400 }}
            >
              Connect shopkeepers, warehouses, and riders in one powerful platform.
              Real-time inventory tracking, order management, and delivery coordination.
            </Typography>

            <Box display="flex" gap={2} justifyContent="center" flexWrap="wrap">
              <Button
                component={RouterLink}
                to="/signup"
                variant="contained"
                size="large"
                sx={{
                  px: 5,
                  py: 1.5,
                  fontSize: '1.1rem',
                  background: 'linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 24px rgba(96, 165, 250, 0.3)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                Get Started Free
              </Button>
              <Button
                component={RouterLink}
                to="/login"
                variant="outlined"
                size="large"
                sx={{
                  px: 5,
                  py: 1.5,
                  fontSize: '1.1rem',
                  borderWidth: 2,
                  '&:hover': {
                    borderWidth: 2,
                    transform: 'translateY(-2px)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                Sign In
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 12 } }}>
        <Box textAlign="center" mb={8}>
          <Typography
            variant="h2"
            sx={{
              fontSize: { xs: '2rem', md: '2.5rem' },
              fontWeight: 700,
              mb: 2,
            }}
          >
            Built for Everyone in the Supply Chain
          </Typography>
          <Typography variant="h6" color="text.secondary" maxWidth="600px" mx="auto">
            Whether you're a shopkeeper, warehouse manager, rider, or admin,
            Stockway has the tools you need.
          </Typography>
        </Box>

        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card
                sx={{
                  height: '100%',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: (theme) =>
                      theme.palette.mode === 'dark'
                        ? '0 12px 32px rgba(0, 0, 0, 0.5)'
                        : '0 12px 32px rgba(0, 0, 0, 0.15)',
                  },
                }}
              >
                <CardContent sx={{ p: 4, textAlign: 'center' }}>
                  <Box
                    sx={{
                      display: 'inline-flex',
                      p: 2,
                      borderRadius: 3,
                      bgcolor: (theme) =>
                        alpha(theme.palette.primary.main, 0.1),
                      color: 'primary.main',
                      mb: 3,
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography variant="h5" fontWeight={600} gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" lineHeight={1.7}>
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Benefits Section */}
      <Box sx={{ bgcolor: 'background.paper', py: { xs: 8, md: 12 } }}>
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="center">
            {benefits.map((benefit, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Box display="flex" flexDirection="column" alignItems="center" textAlign="center">
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 80,
                      height: 80,
                      borderRadius: '50%',
                      bgcolor: (theme) => alpha(theme.palette.primary.main, 0.1),
                      color: 'primary.main',
                      mb: 3,
                    }}
                  >
                    {benefit.icon}
                  </Box>
                  <Typography variant="h5" fontWeight={600} gutterBottom>
                    {benefit.title}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    {benefit.description}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Container maxWidth="md" sx={{ py: { xs: 8, md: 12 } }}>
        <Card
          sx={{
            p: { xs: 4, md: 6 },
            textAlign: 'center',
            background: (theme) =>
              theme.palette.mode === 'dark'
                ? `linear-gradient(135deg, ${alpha(theme.palette.primary.dark, 0.2)} 0%, ${alpha(
                    theme.palette.secondary.dark,
                    0.2
                  )} 100%)`
                : `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.15)} 0%, ${alpha(
                    theme.palette.secondary.light,
                    0.15
                  )} 100%)`,
            borderRadius: 4,
          }}
        >
          <Typography
            variant="h3"
            sx={{
              fontSize: { xs: '1.75rem', md: '2.5rem' },
              fontWeight: 700,
              mb: 2,
            }}
          >
            Ready to Transform Your Supply Chain?
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
            Join Stockway today and experience seamless logistics management.
          </Typography>
          <Button
            component={RouterLink}
            to="/signup"
            variant="contained"
            size="large"
            sx={{
              px: 6,
              py: 2,
              fontSize: '1.1rem',
              background: 'linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                transform: 'translateY(-2px)',
                boxShadow: '0 8px 24px rgba(96, 165, 250, 0.3)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            Create Your Account
          </Button>
        </Card>
      </Container>

      {/* Footer */}
      <Box
        sx={{
          borderTop: '1px solid',
          borderColor: 'divider',
          py: 4,
          textAlign: 'center',
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary">
            © {new Date().getFullYear()} Stockway. All rights reserved.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}
