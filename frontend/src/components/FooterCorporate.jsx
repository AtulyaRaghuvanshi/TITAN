import React from 'react';
import { Box, Container, Typography, Grid, Link, Divider } from '@mui/material';
import { FaBuilding } from 'react-icons/fa';

const FooterCorporate = () => {
  const footerLinks = {
    'Products': [
      'Personal Loans',
      'Home Loans',
      'Credit Cards',
      'Savings Accounts',
      'Fixed Deposits',
    ],
    'Services': [
      'NetBanking',
      'Mobile Banking',
      'Investment Services',
      'Insurance',
      'Wealth Management',
    ],
    'About': [
      'About Us',
      'Careers',
      'News & Updates',
      'Investor Relations',
      'Corporate Governance',
    ],
    'Support': [
      'Contact Us',
      'FAQs',
      'Branch Locator',
      'Complaints',
      'Terms & Conditions',
    ],
  };

  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: '#0A2A84',
        color: '#ffffff',
        pt: 6,
        pb: 3,
        mt: 8,
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          {/* Brand Section */}
          <Grid item xs={12} md={3}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
              <FaBuilding size={32} color="#E1B81C" />
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                TITAN BANK
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ opacity: 0.8, mb: 2 }}>
              Financial Services You Can Trust
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              © 2024 Titan Bank. All rights reserved.
            </Typography>
          </Grid>

          {/* Links Sections */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <Grid item xs={6} md={2} key={category}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: 600, mb: 2, color: '#E1B81C' }}
              >
                {category}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {links.map((link) => (
                  <Link
                    key={link}
                    href="#"
                    sx={{
                      color: '#ffffff',
                      opacity: 0.8,
                      textDecoration: 'none',
                      fontSize: '0.875rem',
                      '&:hover': {
                        opacity: 1,
                        color: '#E1B81C',
                      },
                    }}
                  >
                    {link}
                  </Link>
                ))}
              </Box>
            </Grid>
          ))}
        </Grid>

        <Divider sx={{ my: 4, borderColor: 'rgba(255, 255, 255, 0.2)' }} />

        {/* Bottom Section */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Typography variant="caption" sx={{ opacity: 0.7 }}>
            Licensed by Reserve Bank of India | Member of DICGC
          </Typography>
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Link href="#" sx={{ color: '#ffffff', opacity: 0.8, fontSize: '0.875rem' }}>
              Privacy Policy
            </Link>
            <Link href="#" sx={{ color: '#ffffff', opacity: 0.8, fontSize: '0.875rem' }}>
              Terms of Use
            </Link>
            <Link href="#" sx={{ color: '#ffffff', opacity: 0.8, fontSize: '0.875rem' }}>
              Security
            </Link>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default FooterCorporate;

