import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Drawer,
  List,
  ListItem,
  ListItemText,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  AccountCircle,
  Menu as MenuIcon,
  Login,
} from '@mui/icons-material';
import { FaBuilding } from 'react-icons/fa';

const TitanHeader = () => {
  const [anchorEl, setAnchorEl] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const navItems = [
    { label: 'Loans', href: '#loans' },
    { label: 'Credit Cards', href: '#credit-cards' },
    { label: 'Savings', href: '#savings' },
    { label: 'Investments', href: '#investments' },
    { label: 'Support', href: '#support' },
  ];

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <>
      <AppBar 
        position="fixed" 
        sx={{ 
          backgroundColor: '#0A2A84',
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 1300,
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, md: 4 } }}>
          {/* Logo */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <FaBuilding size={32} color="#E1B81C" />
            <Typography
              variant="h5"
              component="div"
              sx={{
                fontWeight: 700,
                color: '#ffffff',
                display: { xs: 'none', sm: 'block' },
              }}
            >
              TITAN BANK
            </Typography>
          </Box>

          {/* Desktop Navigation */}
          {!isMobile && (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              {navItems.map((item) => (
                <Button
                  key={item.label}
                  color="inherit"
                  sx={{
                    fontWeight: 500,
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    },
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}

          {/* Right Side Actions */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isMobile ? (
              <IconButton
                color="inherit"
                onClick={() => setMobileMenuOpen(true)}
              >
                <MenuIcon />
              </IconButton>
            ) : (
              <>
                <Button
                  variant="outlined"
                  startIcon={<Login />}
                  sx={{
                    color: '#ffffff',
                    borderColor: '#E1B81C',
                    backgroundColor: 'rgba(225, 184, 28, 0.1)',
                    '&:hover': {
                      borderColor: '#E1B81C',
                      backgroundColor: 'rgba(225, 184, 28, 0.2)',
                    },
                  }}
                >
                  Login / NetBanking
                </Button>
                <IconButton
                  size="large"
                  edge="end"
                  aria-label="account"
                  onClick={handleProfileMenuOpen}
                  color="inherit"
                >
                  <AccountCircle />
                </IconButton>
              </>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* Mobile Menu Drawer */}
      <Drawer
        anchor="right"
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      >
        <Box sx={{ width: 250, pt: 8 }}>
          <List>
            {navItems.map((item) => (
              <ListItem key={item.label} button>
                <ListItemText primary={item.label} />
              </ListItem>
            ))}
            <ListItem button>
              <ListItemText primary="Login / NetBanking" />
            </ListItem>
          </List>
        </Box>
      </Drawer>

      {/* Profile Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>My Profile</MenuItem>
        <MenuItem onClick={handleMenuClose}>Account Settings</MenuItem>
        <MenuItem onClick={handleMenuClose}>Logout</MenuItem>
      </Menu>

      {/* Spacer for fixed header */}
      <Toolbar />
    </>
  );
};

export default TitanHeader;

