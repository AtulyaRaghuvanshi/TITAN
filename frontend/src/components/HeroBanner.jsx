import React from 'react';
import { Box, Typography, Container, Button } from '@mui/material';
import { ArrowForward } from '@mui/icons-material';

const HeroBanner = () => {
  return (
    <Box
      sx={{
        background: 'linear-gradient(135deg, #0A2A84 0%, #1E4BD1 100%)',
        color: '#ffffff',
        py: { xs: 8, md: 12 },
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(circle at 20% 50%, rgba(225, 184, 28, 0.1) 0%, transparent 50%)',
        },
      }}
    >
      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
        <Box sx={{ textAlign: 'center', maxWidth: '800px', mx: 'auto' }}>
          <Typography
            variant="h2"
            component="h1"
            sx={{
              fontWeight: 700,
              mb: 2,
              fontSize: { xs: '2rem', md: '3rem' },
            }}
          >
            Welcome to Titan Bank
          </Typography>
          <Typography
            variant="h4"
            component="h2"
            sx={{
              fontWeight: 600,
              mb: 3,
              color: '#E1B81C',
              fontSize: { xs: '1.5rem', md: '2rem' },
            }}
          >
            Financial Services You Can Trust
          </Typography>
          <Typography
            variant="h6"
            sx={{
              mb: 4,
              opacity: 0.9,
              fontWeight: 400,
              fontSize: { xs: '1rem', md: '1.25rem' },
            }}
          >
            Providing secure and instant financial solutions.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="large"
              endIcon={<ArrowForward />}
              sx={{
                backgroundColor: '#E1B81C',
                color: '#0A2A84',
                fontWeight: 600,
                px: 4,
                py: 1.5,
                '&:hover': {
                  backgroundColor: '#F0D04A',
                },
              }}
            >
              Apply for Loan
            </Button>
            <Button
              variant="outlined"
              size="large"
              sx={{
                borderColor: '#ffffff',
                color: '#ffffff',
                px: 4,
                py: 1.5,
                '&:hover': {
                  borderColor: '#E1B81C',
                  backgroundColor: 'rgba(225, 184, 28, 0.1)',
                },
              }}
            >
              Learn More
            </Button>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default HeroBanner;

