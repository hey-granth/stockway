import { Box, Container, Typography, Link, Grid } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

export default function Footer() {
    return (
        <Box
            component="footer"
            sx={{
                py: 6,
                px: 2,
                mt: 'auto',
                backgroundColor: 'background.default',
                borderTop: '1px solid',
                borderColor: 'divider',
            }}
        >
            <Container maxWidth="lg">
                <Grid container spacing={4} justifyContent="space-between">
                    <Grid item xs={12} sm={4}>
                        <Typography variant="h6" color="text.primary" gutterBottom fontWeight={600}>
                            Stockway
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Stockway is a role-based supply chain operations platform that connects shopkeepers, warehouses, and delivery riders through a single, geospatially aware system for inventory, ordering, and fulfillment.
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={8}>
                        <Grid container spacing={4} justifyContent={{ sm: 'flex-end' }}>
                            <Grid item xs={6} sm={3}>
                                <Typography variant="subtitle2" color="text.primary" gutterBottom fontWeight={600}>
                                    Creator
                                </Typography>
                                <Link
                                    href="https://github.com/hey-granth/stockway"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    color="text.secondary"
                                    display="block"
                                    sx={{ mb: 1, textDecoration: 'none', '&:hover': { color: 'text.primary' } }}
                                >
                                    GitHub
                                </Link>
                                <Link
                                    href="https://x.com/heygranth"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    color="text.secondary"
                                    display="block"
                                    sx={{ mb: 1, textDecoration: 'none', '&:hover': { color: 'text.primary' } }}
                                >
                                    X (Twitter)
                                </Link>
                                <Link
                                    href="https://linkedin.com/in/granth-agarwal"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    color="text.secondary"
                                    display="block"
                                    sx={{ mb: 1, textDecoration: 'none', '&:hover': { color: 'text.primary' } }}
                                >
                                    LinkedIn
                                </Link>
                            </Grid>
                            <Grid item xs={6} sm={3}>
                                <Typography variant="subtitle2" color="text.primary" gutterBottom fontWeight={600}>
                                    Links
                                </Typography>
                                <Link component={RouterLink} to="/contact" color="text.secondary" display="block" sx={{ mb: 1, textDecoration: 'none', '&:hover': { color: 'text.primary' } }}>
                                    Contact
                                </Link>
                                <Link component={RouterLink} to="/login" color="text.secondary" display="block" sx={{ mb: 1, textDecoration: 'none', '&:hover': { color: 'text.primary' } }}>
                                    Login
                                </Link>
                            </Grid>
                        </Grid>
                    </Grid>
                </Grid>
                <Box sx={{ mt: 8, pt: 4, borderTop: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="body2" color="text.secondary" align="center">
                        {'© '}
                        {new Date().getFullYear()}
                        {' Stockway. Built by Granth Agarwal.'}
                    </Typography>
                </Box>
            </Container>
        </Box>
    );
}
