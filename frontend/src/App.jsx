import React, { useState, useEffect } from 'react';
import { Box, Container } from '@mui/material';
import TitanHeader from './components/TitanHeader';
import HeroBanner from './components/HeroBanner';
import TitanChatbot from './components/TitanChatbot';
import ProcessingSidebar from './components/ProcessingSidebar';
import FooterCorporate from './components/FooterCorporate';
import ProcessEventService from './services/processEventService';

function App() {
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [processEvents, setProcessEvents] = useState([]);
  const [chatContext, setChatContext] = useState(null);
  const processEventService = new ProcessEventService();

  // Open sidebar when chatbot is active
  useEffect(() => {
    if (chatbotOpen) {
      setSidebarOpen(true);
    }
  }, [chatbotOpen]);

  const handleProcessEvent = (event) => {
    const processedEvent = processEventService.convertEvent(event);
    setProcessEvents((prev) => [...prev, processedEvent]);
  };

  const handleChatbotMessage = (context) => {
    setChatContext(context);
    
    // Generate process steps from context
    const steps = processEventService.generateStepsFromContext(context);
    if (steps.length > 0) {
      setProcessEvents((prev) => {
        // Avoid duplicates
        const existingMessages = prev.map(e => e.message);
        const newSteps = steps.filter(step => !existingMessages.includes(step.message));
        return [...prev, ...newSteps];
      });
    }
  };

  const handleChatbotToggle = () => {
    setChatbotOpen(!chatbotOpen);
    if (!chatbotOpen) {
      // Reset events when opening chatbot
      setProcessEvents([]);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <TitanHeader />
      
      <Box
        component="main"
        sx={{
          flex: 1,
          position: 'relative',
          backgroundColor: '#F2F4F7',
        }}
      >
        <HeroBanner />
        
        {/* Main Content Sections */}
        <Container maxWidth="lg" sx={{ py: 6 }}>
          {/* Add more sections here for Loans, Credit Cards, etc. */}
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Box
              sx={{
                backgroundColor: '#ffffff',
                borderRadius: 3,
                p: 4,
                boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
              }}
            >
              <h2 style={{ color: '#0A2A84', marginBottom: '1rem' }}>
                Start Your Loan Application
              </h2>
              <p style={{ color: '#666', marginBottom: '2rem' }}>
                Click the chatbot icon in the bottom-right corner to begin your loan application journey.
                Our AI-powered assistant will guide you through the entire process.
              </p>
            </Box>
          </Box>
        </Container>
      </Box>

      <FooterCorporate />

      {/* Chatbot */}
      <TitanChatbot
        isOpen={chatbotOpen}
        onToggle={handleChatbotToggle}
        onProcessEvent={handleProcessEvent}
        onContextUpdate={handleChatbotMessage}
      />

      {/* Process Transparency Sidebar */}
      <ProcessingSidebar
        open={sidebarOpen && chatbotOpen}
        onClose={() => setSidebarOpen(false)}
        events={processEvents}
      />
    </Box>
  );
}

export default App;
