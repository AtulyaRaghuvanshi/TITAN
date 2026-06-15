import React, { useEffect, useRef } from 'react';
import {
  Drawer,
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Divider,
  Chip,
} from '@mui/material';
import {
  CheckCircle,
  RadioButtonUnchecked,
  AccessTime,
  Close,
} from '@mui/icons-material';

const ProcessingSidebar = ({ open, onClose, events = [] }) => {
  const listRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom when new events arrive
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [events]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ color: '#28a745', fontSize: 20 }} />;
      case 'processing':
        return <AccessTime sx={{ color: '#ffc107', fontSize: 20 }} />;
      default:
        return <RadioButtonUnchecked sx={{ color: '#6c757d', fontSize: 20 }} />;
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-IN', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: '100%', sm: 380 },
          backgroundColor: '#eef0f4',
          borderLeft: '1px solid #d0d5dd',
        },
      }}
      ModalProps={{
        keepMounted: true,
      }}
    >
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box
          sx={{
            backgroundColor: '#0A2A84',
            color: '#ffffff',
            p: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Process Transparency
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.9 }}>
              Real-time loan processing status
            </Typography>
          </Box>
          <IconButton
            onClick={onClose}
            sx={{ color: '#ffffff' }}
            size="small"
          >
            <Close />
          </IconButton>
        </Box>

        <Divider />

        {/* Events List */}
        <Box
          ref={listRef}
          sx={{
            flex: 1,
            overflowY: 'auto',
            p: 2,
          }}
        >
          {events.length === 0 ? (
            <Box
              sx={{
                textAlign: 'center',
                py: 4,
                color: '#666',
              }}
            >
              <Typography variant="body2">
                Processing status will appear here
              </Typography>
            </Box>
          ) : (
            <List sx={{ p: 0 }}>
              {events.map((event, index) => (
                <ListItem
                  key={index}
                  sx={{
                    backgroundColor: '#ffffff',
                    mb: 1,
                    borderRadius: 2,
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
                    py: 1.5,
                    px: 2,
                    animation: `fadeInUp 0.4s ease-out ${Math.min(index * 0.05, 0.5)}s forwards`,
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {getStatusIcon(event.status || 'completed')}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 500,
                          color: '#1A1A1A',
                          mb: 0.5,
                        }}
                      >
                        {event.message}
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        <Typography
                          variant="caption"
                          sx={{ color: '#666', fontSize: '0.75rem' }}
                        >
                          {formatTime(event.timestamp)}
                        </Typography>
                        {event.category && (
                          <Chip
                            label={event.category}
                            size="small"
                            sx={{
                              height: 18,
                              fontSize: '0.65rem',
                              backgroundColor: '#f0f0f0',
                            }}
                          />
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>

        {/* Footer */}
        <Box
          sx={{
            backgroundColor: '#ffffff',
            p: 2,
            borderTop: '1px solid #d0d5dd',
          }}
        >
          <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
            Your loan application is being processed securely
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
};

export default ProcessingSidebar;
