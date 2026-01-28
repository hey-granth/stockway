import { Container, Typography, Box, Link, Paper, Stack } from '@mui/material';


export default function ContactPage() {
    return (
        <Container maxWidth="md" sx={{ py: 8 }}>
            <Paper
                elevation={0}
                sx={{
                    p: { xs: 4, md: 8 },
                    borderRadius: 4,
                    border: '1px solid',
                    borderColor: 'divider',
                    textAlign: 'center'
                }}
            >
                <Typography variant="h3" component="h1" gutterBottom fontWeight={700}>
                    Get in touch
                </Typography>

                <Typography variant="h6" color="text.secondary" sx={{ mb: 6, maxWidth: '600px', mx: 'auto' }}>
                    Have questions about Stockway? I'm always open to discussing the project, technical details, or potential collaborations.
                </Typography>

                <Stack spacing={3} alignItems="center" justifyContent="center">
                    <Link
                        href="mailto:granthcodes@gmail.com"
                        underline="hover"
                        sx={{ fontSize: '1.25rem', color: 'text.primary', fontWeight: 500 }}
                    >
                        granthcodes@gmail.com
                    </Link>

                    <Box sx={{ display: 'flex', gap: 4, mt: 2 }}>
                        <Link
                            href="https://github.com/hey-granth"
                            target="_blank"
                            rel="noopener noreferrer"
                            color="text.secondary"
                            underline="hover"
                            sx={{ '&:hover': { color: 'text.primary' } }}
                        >
                            GitHub
                        </Link>

                        <Link
                            href="https://x.com/heygranth"
                            target="_blank"
                            rel="noopener noreferrer"
                            color="text.secondary"
                            underline="hover"
                            sx={{ '&:hover': { color: 'text.primary' } }}
                        >
                            X (Twitter)
                        </Link>

                        <Link
                            href="https://linkedin.com/in/granth-agarwal"
                            target="_blank"
                            rel="noopener noreferrer"
                            color="text.secondary"
                            underline="hover"
                            sx={{ '&:hover': { color: 'text.primary' } }}
                        >
                            LinkedIn
                        </Link>
                    </Box>
                </Stack>
            </Paper>
        </Container>
    );
}
