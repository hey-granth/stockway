import { Box, Container, Typography, Button, Grid, Card, CardContent } from '@mui/material';
import {
  Store,
  Warehouse,
  DeliveryDining,
  TrendingUp,
  Speed,
  Security,
  ArrowForward,
  CheckCircleOutline,
  Inventory2,
  LocalShipping,
  ShoppingCart
} from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';
import PublicNavbar from '@/components/common/PublicNavbar';
import Footer from '@/components/common/Footer';

export default function LandingPage() {
  const ecosystem = [
    {
      icon: <Store sx={{ fontSize: 32 }} />,
      title: 'For Shopkeepers',
      description: 'Order inventory from nearby warehouses and track deliveries in real-time.',
    },
    {
      icon: <Warehouse sx={{ fontSize: 32 }} />,
      title: 'For Warehouses',
      description: 'Manage stock levels, process incoming orders, and assign riders efficiently.',
    },
    {
      icon: <DeliveryDining sx={{ fontSize: 32 }} />,
      title: 'For Riders',
      description: 'Receive delivery tasks, navigate to locations, and track earnings.',
    },
  ];

  const workflow = [
    {
      step: '01',
      title: 'Order',
      desc: 'Shopkeeper browses catalog and places order.',
      icon: <ShoppingCart color="primary" />,
    },
    {
      step: '02',
      title: 'Process',
      desc: 'Warehouse accepts order and assigns a rider.',
      icon: <Inventory2 color="warning" />,
    },
    {
      step: '03',
      title: 'Deliver',
      desc: 'Rider picks up package and delivers to shop.',
      icon: <LocalShipping color="success" />,
    },
  ];

  const capabilities = [
    {
      icon: <TrendingUp />,
      title: 'Analytics',
      description: 'Data-driven insights for better decision making.',
    },
    {
      icon: <Speed />,
      title: 'Speed',
      description: 'Optimized routing for faster delivery times.',
    },
    {
      icon: <Security />,
      title: 'Security',
      description: 'End-to-end encryption for all transaction data.',
    },
    {
      icon: <CheckCircleOutline />,
      title: 'Reliability',
      description: '99.9% uptime guarantee for business continuity.',
    },
  ];

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary', display: 'flex', flexDirection: 'column' }}>
      <PublicNavbar />

      {/* Hero Section - Full Viewport Height */}
      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          display: 'flex',
          alignItems: 'center',
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.default',
          py: { xs: 8, md: 0 } // Vertical padding only on mobile where height might overflow
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={{ xs: 8, md: 8 }} alignItems="center">
            {/* Left Column: Narrative */}
            <Grid item xs={12} md={6}>
              <Box maxWidth="600px">
                <Typography
                  variant="overline"
                  sx={{
                    fontWeight: 600,
                    color: 'primary.main',
                    letterSpacing: '0.1em',
                    mb: 2,
                    display: 'block'
                  }}
                >
                  MODULAR LOGISTICS PLATFORM
                </Typography>
                <Typography
                  variant="h1"
                  sx={{
                    fontSize: { xs: '2.5rem', md: '4.5rem' },
                    fontWeight: 700,
                    letterSpacing: '-0.03em',
                    lineHeight: 1.1,
                    mb: 3,
                    color: 'text.primary',
                  }}
                >
                  The <Box component="span" sx={{ color: 'text.secondary' }}>operating system</Box> for rural commerce.
                </Typography>

                <Typography
                  variant="body1"
                  color="text.secondary"
                  sx={{ mb: 5, fontSize: '1.25rem', lineHeight: 1.6, maxWidth: '520px' }}
                >
                  Stockway is the infrastructure connecting shopkeepers, warehouses, and logistics fleets in one seamless network.
                </Typography>

                <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
                  <Button
                    component={RouterLink}
                    to="/signup"
                    variant="contained"
                    size="large"
                    endIcon={<ArrowForward />}
                    sx={{
                      px: 4,
                      py: 1.5,
                      borderRadius: 2,
                      fontSize: '1rem',
                      textTransform: 'none',
                    }}
                  >
                    Start Free Trial
                  </Button>
                  <Button
                    component={RouterLink}
                    to="/docs"
                    variant="text"
                    size="large"
                    sx={{
                      px: 3,
                      py: 1.5,
                      fontSize: '1rem',
                      textTransform: 'none',
                      color: 'text.primary'
                    }}
                  >
                    View Documentation
                  </Button>
                </Box>
              </Box>
            </Grid>

            {/* Right Column: System Schematic */}
            <Grid item xs={12} md={6}>
              <Box
                sx={{
                  position: 'relative',
                  p: 4,
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 4,
                  bgcolor: 'background.paper',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 3,
                  maxWidth: '500px',
                  mx: 'auto',
                  boxShadow: '0px 0px 0px 1px rgba(0,0,0,0.05)'
                }}
              >
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>
                    System Architecture
                  </Typography>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'success.main', boxShadow: '0 0 8px rgba(16, 185, 129, 0.5)' }} />
                </Box>

                {/* Architecture Nodes */}
                {[
                  { label: 'Shopkeeper App', sub: 'Order Placement', icon: <Store fontSize="small" /> },
                  { label: 'Warehouse RMS', sub: 'Inventory Sync', icon: <Warehouse fontSize="small" /> },
                  { label: 'Rider Client', sub: 'Route Optimization', icon: <DeliveryDining fontSize="small" /> }
                ].map((node, i) => (
                  <Box key={i} sx={{ position: 'relative' }}>
                    {i !== 2 && (
                      <Box sx={{
                        position: 'absolute', left: 24, top: 48, bottom: -24, width: 2, bgcolor: 'divider', zIndex: 0
                      }} />
                    )}
                    <Box display="flex" alignItems="center" gap={2} sx={{ position: 'relative', zIndex: 1, bgcolor: 'background.paper', py: 1 }}>
                      <Box sx={{
                        width: 48, height: 48, borderRadius: 2, border: 1, borderColor: 'divider',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default'
                      }}>
                        {node.icon}
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" fontWeight={600}>{node.label}</Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>{node.sub}</Typography>
                      </Box>
                      <Box sx={{ ml: 'auto' }}>
                        <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'divider' }} />
                      </Box>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 2: Ecosystem (Who it's for) */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
        <Container maxWidth="lg" sx={{ py: 12 }}>
          <Box mb={8} textAlign="center">
            <Typography variant="h3" fontWeight={700} letterSpacing="-0.02em" mb={2}>
              Built for the entire chain
            </Typography>
            <Typography variant="body1" color="text.secondary" maxWidth="600px" mx="auto">
              Every stakeholder gets a dedicated interface tailored to their specific workflow needs.
            </Typography>
          </Box>
          <Grid container spacing={4}>
            {ecosystem.map((role, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Card sx={{ height: '100%', bgcolor: 'background.default' }} variant="outlined">
                  <CardContent sx={{ p: 4 }}>
                    <Box sx={{
                      width: 56, height: 56,
                      borderRadius: 2,
                      bgcolor: 'background.paper',
                      border: 1,
                      borderColor: 'divider',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      mb: 3,
                      color: 'text.primary'
                    }}>
                      {role.icon}
                    </Box>
                    <Typography variant="h5" gutterBottom fontWeight={600}>
                      {role.title}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {role.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Section 3: Workflow (How it works) */}
      <Container maxWidth="lg" sx={{ py: 16 }}>
        <Box mb={10} textAlign={{ xs: 'left', md: 'center' }}>
          <Typography variant="h3" fontWeight={700} letterSpacing="-0.02em" mb={2}>
            How Stockway Works
          </Typography>
        </Box>

        <Grid container spacing={0} sx={{
          border: 1,
          borderColor: 'divider',
          borderRadius: { xs: 4, md: 4 },
          overflow: 'hidden'
        }}>
          {workflow.map((step, index) => (
            <Grid item xs={12} md={4} key={index} sx={{
              borderBottom: { xs: 1, md: 0 },
              borderRight: { xs: 0, md: 1 },
              borderColor: 'divider',
              '&:last-child': { borderRight: 0, borderBottom: 0 }
            }}>
              <Box sx={{ p: 6, height: '100%', bgcolor: 'background.paper', transition: 'background-color 0.2s', '&:hover': { bgcolor: 'background.default' } }}>
                <Box display="flex" justifyContent="space-between" mb={4}>
                  <Typography variant="h2" fontWeight={800} sx={{ opacity: 0.1 }}>{step.step}</Typography>
                  {step.icon}
                </Box>
                <Typography variant="h5" fontWeight={600} gutterBottom>{step.title}</Typography>
                <Typography variant="body1" color="text.secondary">{step.desc}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Container>


      {/* Section 4: Capabilities (Platform) */}
      <Box sx={{ borderTop: 1, borderColor: 'divider', bgcolor: 'background.default' }}>
        <Container maxWidth="lg" sx={{ py: 16 }}>
          <Grid container spacing={8} alignItems="center">
            <Grid item xs={12} md={5}>
              <Typography variant="h3" fontWeight={700} mb={3}>
                Enterprise-grade <br /> capabilities
              </Typography>
              <Typography variant="body1" color="text.secondary" mb={4} fontSize="1.125rem">
                Scalable infrastructure designed to handle high-frequency transactions and large-scale inventory management without compromising performance.
              </Typography>
              <Button
                variant="outlined"
                size="large"
                endIcon={<ArrowForward />}
                sx={{ textTransform: 'none' }}
                component={RouterLink}
                to="/signup"
              >
                Explore Features
              </Button>
            </Grid>
            <Grid item xs={12} md={7}>
              <Grid container spacing={4}>
                {capabilities.map((cap, i) => (
                  <Grid item xs={12} sm={6} key={i}>
                    <Box sx={{ p: 3, border: 1, borderColor: 'divider', borderRadius: 2, bgcolor: 'background.paper' }}>
                      <Box sx={{ mb: 2, color: 'text.primary' }}>{cap.icon}</Box>
                      <Typography variant="h6" fontWeight={600} gutterBottom>{cap.title}</Typography>
                      <Typography variant="body2" color="text.secondary">{cap.description}</Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Section 5: Final CTA */}
      <Box sx={{ borderTop: 1, borderColor: 'divider', bgcolor: 'background.paper', py: 16 }}>
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h2" fontWeight={700} mb={3} letterSpacing="-0.03em">
            Ready to optimize your supply chain?
          </Typography>
          <Typography variant="h6" color="text.secondary" fontWeight={400} mb={6} maxWidth="600px" mx="auto">
            Join hundreds of businesses using Stockway to streamline their delivery network.
          </Typography>
          <Button
            component={RouterLink}
            to="/signup"
            variant="contained"
            size="large"
            sx={{ px: 8, py: 2, fontSize: '1.125rem', borderRadius: 2, textTransform: 'none' }}
          >
            Get Started Now
          </Button>
        </Container>
      </Box>

      <Footer />
    </Box>
  );
}
