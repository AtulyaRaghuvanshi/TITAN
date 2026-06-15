import React, { useState, useEffect, useRef, useLayoutEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Avatar,
  Button,
} from '@mui/material';
import {
  Send,
  Close,
  AttachFile,
  PictureAsPdf,
  Download,
  HelpOutline,
} from '@mui/icons-material';
import { FaRobot } from 'react-icons/fa';
import { sendMessage, getCustomers, uploadSalarySlip, sendEmailOtp, verifyEmailOtp } from '../api';

// Simple markdown parser for formatting messages
const formatMessage = (text) => {
  if (!text) return '';
  
  // Split text into parts (text and markdown)
  const parts = [];
  let lastIndex = 0;
  const regex = /\*\*(.+?)\*\*/g;
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      const beforeText = text.substring(lastIndex, match.index);
      if (beforeText) {
        parts.push({ type: 'text', content: beforeText });
      }
    }
    // Add bold text
    parts.push({ type: 'bold', content: match[1] });
    lastIndex = regex.lastIndex;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.substring(lastIndex) });
  }
  
  // If no markdown found, return original text with line breaks
  if (parts.length === 0) {
    const lines = text.split('\n');
    return lines.map((line, idx) => (
      <React.Fragment key={idx}>
        {line}
        {idx < lines.length - 1 && <br />}
      </React.Fragment>
    ));
  }
  
  // Render parts with line breaks
  const result = [];
  parts.forEach((part, idx) => {
    const lines = part.content.split('\n');
    lines.forEach((line, lineIdx) => {
      if (lineIdx > 0) result.push(<br key={`${idx}-${lineIdx}-br`} />);
      if (part.type === 'bold') {
        result.push(<strong key={`${idx}-${lineIdx}`}>{line}</strong>);
      } else {
        result.push(<span key={`${idx}-${lineIdx}`}>{line}</span>);
      }
    });
  });
  
  return result;
};

const TitanChatbot = ({ 
  isOpen, 
  onToggle, 
  onProcessEvent,
  onContextUpdate,
  customerId = null 
}) => {
  const [messages, setMessages] = useState([]);
  const latestMessagesRef = useRef(messages);
  const [input, setInput] = useState('');
  const [context, setContext] = useState(null);
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [onboardingStage, setOnboardingStage] = useState('ASK_NAME'); // ASK_NAME | ASK_MOBILE | ASK_EMAIL | ASK_EMAIL_OTP | DONE
  const [customerName, setCustomerName] = useState('');
  const [customerMobile, setCustomerMobile] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [emailVerified, setEmailVerified] = useState(false);
  const [customerAddress, setCustomerAddress] = useState('');
  const [customerGender, setCustomerGender] = useState('');
  const [customerNationality, setCustomerNationality] = useState('');
  const [customerEducation, setCustomerEducation] = useState('');
  const [matchedCustomer, setMatchedCustomer] = useState(null);
  const [lifeInsuranceChoice, setLifeInsuranceChoice] = useState(''); // 'yes' | 'no'
  const [activeCustomerId, setActiveCustomerId] = useState(customerId || '');
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);
  const suppressFocusRef = useRef(false);

  // Robustly focus the typing box and place caret at the end
  const focusStrong = () => {
    const el = inputRef.current;
    if (!el) return;
    try {
      el.focus();
      const len = el.value ? el.value.length : 0;
      if (el.setSelectionRange) el.setSelectionRange(len, len);
    } catch (e) {}
    // Retry on next frame in case of paints/transitions
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(() => {
        const el2 = inputRef.current;
        if (!el2) return;
        try {
          el2.focus();
          const len2 = el2.value ? el2.value.length : 0;
          if (el2.setSelectionRange) el2.setSelectionRange(len2, len2);
        } catch (e) {}
      });
    }
  };

  const focusQuestionInput = () => {
    focusStrong();
    setMessages(prev => [
      ...prev,
      {
        from: 'bot',
        text: 'Please type your question about EMI, fees, eligibility, or documents. I’m here to help.',
        timestamp: new Date(),
      },
    ]);
    // Refocus after message append to ensure caret is ready for typing
    setTimeout(() => {
      focusStrong();
    }, 0);
  };

  const handleProceed = async () => {
    // Choose the appropriate keyword based on stage
    let keyword = 'confirm';
    if (context?.chosen_offer && !context?.sales_done) {
      keyword = 'yes';
    } else if (context?.stage === 'VERIFICATION') {
      keyword = 'confirm';
    } else if (context?.stage === 'UNDERWRITING') {
      // No explicit proceed keyword required; send a no-op confirmation to keep flow moving
      keyword = 'confirm';
    } else if (context?.stage === 'SANCTION') {
      // Final stage; allow a polite acknowledgement
      keyword = 'confirm';
    }
    await sendTextMessage(keyword);
  };

  useEffect(() => {
    let mounted = true;
    getCustomers().then((list) => {
      if (mounted) {
        setCustomers(list);
        // If an explicit customerId is passed from parent, honour it
        if (customerId) {
          setActiveCustomerId(customerId);
          setOnboardingStage('DONE');
        }
      }
    }).catch((error) => {
      console.error('Unable to load customers:', error);
    });
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (isOpen) {
      // Initialize with welcome message
      if (messages.length === 0) {
        setMessages([{
          from: 'bot',
          text: 'Hello! I\'m your Titan Bank Virtual Assistant. Let\'s first verify if you have a pre-approved offer.',
          timestamp: new Date(),
        }, {
          from: 'bot',
          text: 'Please tell me your full name.',
          timestamp: new Date(),
        }]);
      }
    }
  }, [isOpen, messages.length]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    latestMessagesRef.current = messages;
    // After any message change, ensure the text input is ready for typing
    setTimeout(() => {
      focusStrong();
    }, 0);
  }, [messages]);

  // When chat opens, ensure the input is focused so typing always works
  useEffect(() => {
    if (isOpen) {
      const id = setTimeout(() => {
        focusStrong();
      }, 0);
      return () => clearTimeout(id);
    }
  }, [isOpen, messages.length]);

  // On open, focus immediately with stronger guarantees (layout phase + retries)
  useLayoutEffect(() => {
    if (isOpen) {
      focusStrong();
      if (typeof requestAnimationFrame === 'function') {
        requestAnimationFrame(focusStrong);
      }
      const t = setTimeout(focusStrong, 30);
      return () => clearTimeout(t);
    }
  }, [isOpen]);

  // Route stray keystrokes into the input when the chat is open
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => {
      const t = e.target;
      const isTypingEl = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
      if (isTypingEl) return;
      // Only handle regular character keys/backspace/space/enter
      const allowed = e.key.length === 1 || e.key === 'Backspace' || e.key === 'Enter' || e.key === ' ';
      if (!allowed || e.metaKey || e.ctrlKey || e.altKey) return;
      focusStrong();
    };
    window.addEventListener('keydown', handler, true);
    return () => window.removeEventListener('keydown', handler, true);
  }, [isOpen]);

  // When returning from another browser tab/window, refocus the typing box if chat is open
  useEffect(() => {
    if (!isOpen) return;
    const focusInput = () => {
      // small delay allows the browser to settle after tab switch
      setTimeout(() => focusStrong(), 0);
    };
    const onVisibility = () => {
      if (document.visibilityState === 'visible') focusInput();
    };
    window.addEventListener('focus', focusInput);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.removeEventListener('focus', focusInput);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [isOpen]);

  // Keep-alive: periodically ensure the input remains focused while chat is open
  useEffect(() => {
    if (!isOpen) return;
    const id = setInterval(() => {
      if (suppressFocusRef.current) return;
      const el = inputRef.current;
      if (!el) return;
      if (document.activeElement !== el) {
        try { el.focus(); } catch {}
      }
    }, 800);
    return () => clearInterval(id);
  }, [isOpen]);

  const resolveCustomerId = (textFallback) => {
    // Prefer the ID we captured during onboarding
    if (activeCustomerId) return activeCustomerId;

    // Fallback: try to infer from typed name for robustness
    const lowerMsg = (textFallback || '').toLowerCase();
    const match = customers.find(c =>
      lowerMsg.includes(c.name.toLowerCase())
    );
    return match?.customer_id || 'C001';
  };

  const completeOnboardingWithCustomer = (cust) => {
    setActiveCustomerId(cust.customer_id);
    setOnboardingStage('DONE');
    
    // Preserve user-entered name (in case it differs slightly from database)
    // This ensures the sanction letter uses what the user typed
    if (customerName && customerName.trim()) {
      // Keep user-entered name for sanction letter
    } else {
      // Fallback to database name if user didn't provide one
      setCustomerName(cust.name);
    }

    const limitText = cust.preapproved_limit
      ? `₹${Number(cust.preapproved_limit).toLocaleString('en-IN')}`
      : 'a pre-approved limit';

    setMessages(prev => [
      ...prev,
      {
        from: 'bot',
        text: `Thank you, ${customerName || cust.name}. I found you in our pre-approved list.`,
        timestamp: new Date(),
      },
      {
        from: 'bot',
        text: `Your profile shows a pre-approved limit of ${limitText}. Now tell me your loan requirement, for example: "I need a 3 lakh loan for 36 months."`,
        timestamp: new Date(),
      },
    ]);
  };

  const handleOnboardingMessage = async (userMessage) => {
    const trimmed = userMessage.trim();

    // Add user message to chat
    setMessages(prev => [
      ...prev,
      {
        from: 'user',
        text: trimmed,
        timestamp: new Date(),
      },
    ]);

    if (onboardingStage === 'ASK_NAME') {
      setCustomerName(trimmed);
      setOnboardingStage('ASK_MOBILE');
      setMessages(prev => [
        ...prev,
        {
          from: 'bot',
          text: 'Thanks! Please share your 10‑digit mobile number registered with the bank.',
          timestamp: new Date(),
        },
      ]);
      return;
    }
    // Post-OTP additional onboarding
    if (onboardingStage === 'ASK_ADDRESS') {
      setCustomerAddress(trimmed);
      setOnboardingStage('ASK_GENDER');
      setMessages(prev => [
        ...prev,
        { from: 'bot', text: 'Thank you. Please select your gender:\n- Male\n- Female\n- Third gender\n\nYou can type one of the options.', timestamp: new Date() },
      ]);
      return;
    }

    if (onboardingStage === 'ASK_GENDER') {
      const lower = trimmed.toLowerCase();
      let value = '';
      if (lower.includes('male')) value = 'Male';
      else if (lower.includes('female')) value = 'Female';
      else if (lower.includes('third')) value = 'Third gender';
      if (!value) {
        setMessages(prev => [
          ...prev,
          { from: 'bot', text: 'Please choose one of the options:\n- Male\n- Female\n- Third gender', timestamp: new Date() },
        ]);
        return;
      }
      setCustomerGender(value);
      setOnboardingStage('ASK_NATIONALITY');
      setMessages(prev => [
        ...prev,
        { from: 'bot', text: 'Thanks. What is your nationality?', timestamp: new Date() },
      ]);
      return;
    }

    if (onboardingStage === 'ASK_NATIONALITY') {
      setCustomerNationality(trimmed);
      setOnboardingStage('ASK_EDUCATION');
      setMessages(prev => [
        ...prev,
        { from: 'bot', text: 'Please select your highest education level:\n- Matriculate\n- Undergraduate\n- Graduate\n- Postgraduate\n- Professional\n\nYou can type one of the options.', timestamp: new Date() },
      ]);
      return;
    }

    if (onboardingStage === 'ASK_EDUCATION') {
      const lower = trimmed.toLowerCase();
      const options = ['Matriculate','Undergraduate','Graduate','Postgraduate','Professional'];
      const matched = options.find(o => lower.includes(o.toLowerCase()));
      if (!matched) {
        setMessages(prev => [
          ...prev,
          { from: 'bot', text: 'Please choose one option:\n- Matriculate\n- Undergraduate\n- Graduate\n- Postgraduate\n- Professional', timestamp: new Date() },
        ]);
        return;
      }
      setCustomerEducation(matched);
      setOnboardingStage('ASK_LIFE_INSURANCE');
      setMessages(prev => [
        ...prev,
        { from: 'bot', text: 'Would you like to add a life insurance cover with your loan?\n- Yes\n- No\n\nPlease type Yes or No.', timestamp: new Date() },
      ]);
      return;
    }

    if (onboardingStage === 'ASK_LIFE_INSURANCE') {
      const lower = trimmed.toLowerCase();
      if (['yes','y'].includes(lower)) {
        setLifeInsuranceChoice('yes');
      } else if (['no','n'].includes(lower)) {
        setLifeInsuranceChoice('no');
      } else {
        setMessages(prev => [
          ...prev,
          { from: 'bot', text: 'Please type Yes or No for life insurance.', timestamp: new Date() },
        ]);
        return;
      }
      setOnboardingStage('DONE');
      if (matchedCustomer) {
        completeOnboardingWithCustomer(matchedCustomer);
      } else {
        setMessages(prev => [
          ...prev,
          { from: 'bot', text: 'Thank you. Your preference has been noted.', timestamp: new Date() },
          { from: 'bot', text: 'Now tell me your loan requirement, for example: "I need a 3 lakh loan for 36 months."', timestamp: new Date() },
        ]);
      }
      return;
    }

    if (onboardingStage === 'ASK_MOBILE') {
      const digitsOnly = trimmed.replace(/\D/g, '');
      if (digitsOnly.length < 8) {
        setMessages(prev => [
          ...prev,
          {
            from: 'bot',
            text: 'That doesn\'t look like a valid mobile number. Please enter the 10‑digit mobile number linked to your bank account.',
            timestamp: new Date(),
          },
        ]);
        return;
      }

      setCustomerMobile(digitsOnly);
      setOnboardingStage('ASK_EMAIL');
      setMessages(prev => [
        ...prev,
        {
          from: 'bot',
          text: 'Thanks! Could you also share your email address so we can send respectful updates and your sanction letter?',
          timestamp: new Date(),
        },
      ]);
      return;
    }

    if (onboardingStage === 'ASK_EMAIL') {
      const email = trimmed;
      const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      if (!emailOk) {
        setMessages(prev => [
          ...prev,
          {
            from: 'bot',
            text: 'That doesn\'t look like a valid email. Please enter a correct email address (e.g., name@example.com).',
            timestamp: new Date(),
          },
        ]);
        return;
      }

      setCustomerEmail(email);

      // Send OTP and move to OTP entry stage
      try {
        const resp = await sendEmailOtp(email);
        const hint = resp?.demo_otp ? ` (for demo, your OTP is ${resp.demo_otp})` : '';
        setOnboardingStage('ASK_EMAIL_OTP');
        setMessages(prev => [
          ...prev,
          {
            from: 'bot',
            text: `Thank you. I have sent a one‑time password to ${email}. Please enter the 6‑digit code to verify your email${hint}. If you didn't receive it, type "resend".`,
            timestamp: new Date(),
          },
        ]);
      } catch (e) {
        setMessages(prev => [
          ...prev,
          { from: 'bot', text: 'Sorry, I couldn\'t send the OTP right now. Please try again.', timestamp: new Date() },
        ]);
      }
      return;
    }

    if (onboardingStage === 'ASK_EMAIL_OTP') {
      const lower = trimmed.toLowerCase();
      if (lower === 'resend') {
        try {
          const resp = await sendEmailOtp(customerEmail);
          const hint = resp?.demo_otp ? ` (for demo, your OTP is ${resp.demo_otp})` : '';
          setMessages(prev => [
            ...prev,
            { from: 'bot', text: `I've sent a fresh OTP to ${customerEmail}.${hint} Please enter the 6‑digit code.`, timestamp: new Date() },
          ]);
        } catch (e) {
          setMessages(prev => [
            ...prev,
            { from: 'bot', text: 'Sorry, I couldn\'t resend the OTP. Please try again in a moment.', timestamp: new Date() },
          ]);
        }
        return;
      }

      const code = trimmed.replace(/\D/g, '').slice(0, 6);
      if (code.length !== 6) {
        setMessages(prev => [
          ...prev,
          { from: 'bot', text: 'Please enter the 6‑digit OTP sent to your email, or type "resend" to get a new code.', timestamp: new Date() },
        ]);
        return;
      }
      try {
        const result = await verifyEmailOtp(customerEmail, code);
        if (result?.verified) {
          setEmailVerified(true);

          const digitsOnly = customerMobile;
          const nameLower = customerName.toLowerCase().trim();
          const match = customers.find(c =>
            c.name.toLowerCase().trim() === nameLower &&
            String(c.mobile).replace(/\D/g, '') === digitsOnly
          );
          if (match) {
            completeOnboardingWithCustomer(match);
          } else {
            setOnboardingStage('DONE');
            setMessages(prev => [
              ...prev,
              { from: 'bot', text: 'Email verified successfully. I could not find a pre‑approved profile with that name and mobile number. For this demo, I will continue as a new customer and run the full eligibility journey for you.', timestamp: new Date() },
              { from: 'bot', text: 'Now tell me your loan requirement, for example: "I need a 3 lakh loan for 36 months."', timestamp: new Date() },
            ]);
          }
        } else {
          setMessages(prev => [
            ...prev,
            { from: 'bot', text: 'That code didn\'t match. Please try again, or type "resend" to get a new OTP.', timestamp: new Date() },
          ]);
        }
      } catch (e) {
        setMessages(prev => [
          ...prev,
          { from: 'bot', text: 'There was an issue verifying the OTP. Please try again.', timestamp: new Date() },
        ]);
      }
      return;
    }
  };

  const sendTextMessage = async (messageText, explicitCustomerId, baseMessagesOverride) => {
    if (!messageText.trim()) return;

    const activeCustomerId = explicitCustomerId || resolveCustomerId(messageText);

    const userMessage = messageText.trim();

    setLoading(true);

    // Add user message
    const baseMessages = Array.isArray(baseMessagesOverride) ? baseMessagesOverride : messages;
    const newMessages = [...baseMessages, {
      from: 'user',
      text: userMessage,
      timestamp: new Date(),
    }];
    setMessages(newMessages);

    // Emit process events
    onProcessEvent({
      message: 'Processing your request...',
      status: 'processing',
      timestamp: new Date().toISOString(),
    });

    try {
      // Include user-entered name and mobile in context so backend uses it for sanction letter
      const contextWithName = {
        ...context,
        customer_name: customerName || context?.customer_name,
        customer_mobile: customerMobile || context?.customer_mobile,
        customer_email: customerEmail || context?.customer_email,
        email_verified: emailVerified || context?.email_verified,
        customer_address: customerAddress || context?.customer_address,
        customer_gender: customerGender || context?.customer_gender,
        customer_nationality: customerNationality || context?.customer_nationality,
        customer_education: customerEducation || context?.customer_education,
        life_insurance: lifeInsuranceChoice ? (lifeInsuranceChoice === 'yes' ? 'Opted In' : 'Not opted') : (context?.life_insurance),
      };
      const response = await sendMessage(activeCustomerId, userMessage, contextWithName);

      // Update context
      const newContext = response.context;
      setContext(newContext);

      // Notify parent of context update
      if (onContextUpdate) {
        onContextUpdate(newContext);
      }

      // Add bot response with PDF if available
      const botMessage = {
        from: 'bot',
        text: response.reply,
        timestamp: new Date(),
      };
      
      // If PDF is included, attach it to the message
      if (response.pdf_base64) {
        botMessage.pdf = response.pdf_base64;
        botMessage.pdfFilename = `sanction_letter_${activeCustomerId || 'C001'}.pdf`;
      }
      
      setMessages([...newMessages, botMessage]);

      // Emit process events based on context
      if (newContext?.stage) {
        onProcessEvent({
          event_type: `STAGE_${newContext.stage}`,
          message: `Stage: ${newContext.stage}`,
          status: 'completed',
          timestamp: new Date().toISOString(),
          category: 'Stage Update',
        });
      }

    } catch (error) {
      console.error('Error:', error);
      setMessages([...newMessages, {
        from: 'bot',
        text: 'Sorry, there was an error. Please try again.',
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    const current = input;
    setInput('');
    if (inputRef.current) inputRef.current.focus();

    if (onboardingStage !== 'DONE') {
      await handleOnboardingMessage(current);
      return;
    }

    await sendTextMessage(current);
    if (inputRef.current) inputRef.current.focus();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const activeCustomerId = resolveCustomerId(input || (messages[0]?.text ?? ''));

    try {
      setUploading(true);
      // Decide which verification trigger to send based on current context flags
      const isSelfEmployed = String(context?.employment_type || '').toLowerCase().startsWith('self');
      let trigger = 'uploaded';
      if (!context?.bank_statement_uploaded) {
        trigger = 'bank uploaded';
      } else if (!context?.id_address_proof_uploaded) {
        trigger = 'id uploaded';
      } else if (isSelfEmployed && !context?.business_docs_uploaded) {
        // Prefer 'itr uploaded' as a default marker for business docs
        trigger = 'itr uploaded';
      } else if (!isSelfEmployed && !context?.salary_slip_uploaded) {
        trigger = 'uploaded';
      } else if (!context?.pan_card_uploaded) {
        trigger = 'pan uploaded';
      }

      // Show a local message with attachment preview and the trigger caption
      const isImage = file.type.startsWith('image/');
      const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
      const previewUrl = URL.createObjectURL(file);
      setMessages(prev => [
        ...prev,
        {
          from: 'user',
          text: `Uploaded file: ${file.name}`,
          timestamp: new Date(),
          attachment: {
            name: file.name,
            type: file.type,
            url: previewUrl,
            isImage,
            isPdf,
            trigger, // show the exact phrase sent to backend
          },
        },
      ]);

      // Only upload the actual file to the salary slip endpoint when we are on that step
      if (trigger === 'uploaded' && !isSelfEmployed && !context?.salary_slip_uploaded) {
        await uploadSalarySlip(activeCustomerId, file);
      }

      // Small delay so the PDF clip is visually noticeable before the bot replies
      await new Promise((resolve) => setTimeout(resolve, 400));

      // Inform backend verification flow with the correct trigger
      await sendTextMessage(trigger, activeCustomerId, latestMessagesRef.current);
    } catch (error) {
      console.error('Upload error:', error);
      setMessages(prev => [
        ...prev,
        {
          from: 'bot',
          text: 'Sorry, there was an error uploading the file. Please try again.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setUploading(false);
      // Reset file input so the same file can be re-selected if needed
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      // Keep caret in the typing box after uploads
      suppressFocusRef.current = false;
      if (inputRef.current) inputRef.current.focus();
    }
  };

  if (!isOpen) {
    // Floating button
    return (
      <Box
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          zIndex: 1200,
        }}
      >
        <Paper
          elevation={8}
          sx={{
            borderRadius: '50%',
            width: 64,
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#0A2A84',
            cursor: 'pointer',
            transition: 'all 0.3s',
            '&:hover': {
              transform: 'scale(1.1)',
              backgroundColor: '#1E4BD1',
            },
          }}
          onClick={onToggle}
        >
          <FaRobot size={32} color="#E1B81C" />
        </Paper>
      </Box>
    );
  }

  return (
    <>
      {/* Backdrop blur when open */}
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(4px)',
          zIndex: 1299,
          display: isOpen ? 'block' : 'none',
        }}
        onClick={onToggle}
      />

      {/* Chatbot Window */}
      <Paper
        elevation={24}
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          width: { xs: 'calc(100% - 48px)', sm: 420 },
          height: { xs: 'calc(100% - 48px)', sm: 600 },
          maxHeight: { xs: 'calc(100vh - 48px)', sm: 600 },
          display: 'flex',
          flexDirection: 'column',
          zIndex: 1300,
          borderRadius: 3,
          overflow: 'hidden',
        }}
      >
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
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar sx={{ backgroundColor: '#E1B81C', width: 40, height: 40 }}>
              <FaRobot size={24} color="#0A2A84" />
            </Avatar>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Titan Virtual Assistant
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.9 }}>
                Online • Ready to help
              </Typography>
            </Box>
          </Box>
          <IconButton onClick={onToggle} sx={{ color: '#ffffff' }} size="small">
            <Close />
          </IconButton>
        </Box>

        {/* Messages */}
        <Box
          sx={{
            flex: 1,
            overflowY: 'auto',
            p: 2,
            backgroundColor: '#fafafa',
          }}
        >
          {messages.map((msg, idx) => {
            // Support split marker to render a separate polite prompt bubble
            if (msg.from === 'bot' && typeof msg.text === 'string' && msg.text.includes('||SPLIT||')) {
              const [first, second] = msg.text.split('||SPLIT||');
              return (
                <Box key={idx} sx={{ mb: 2 }}>
                  {/* First bubble: offer details */}
                  <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 1 }}>
                    <Box sx={{ maxWidth: '75%', p: 1.5, borderRadius: 2, backgroundColor: '#ffffff', color: '#1A1A1A', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                      <Box component="div" sx={{ fontSize: '0.875rem', lineHeight: 1.5, '& strong': { fontWeight: 600, color: '#0A2A84' }}}>
                        {formatMessage(first)}
                      </Box>
                    </Box>
                  </Box>
                  {/* Second bubble: polite question prompt with a small button */}
                  <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <Box sx={{ maxWidth: '75%', p: 1.5, borderRadius: 2, backgroundColor: '#ffffff', color: '#1A1A1A', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                      <Box component="div" sx={{ fontSize: '0.875rem', lineHeight: 1.5, mb: 1 }}>
                        {formatMessage(second)}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Button size="small" variant="contained" onClick={handleProceed} sx={{ textTransform: 'none', backgroundColor: '#0A2A84' }}>
                          Proceed
                        </Button>
                        <Button size="small" variant="outlined" onClick={focusQuestionInput} sx={{ textTransform: 'none', borderColor: '#0A2A84', color: '#0A2A84' }}>
                          Ask another question
                        </Button>
                      </Box>
                    </Box>
                  </Box>
                </Box>
              );
            }

            return (
              <Box
                key={idx}
                sx={{
                  display: 'flex',
                  justifyContent: msg.from === 'user' ? 'flex-end' : 'flex-start',
                  mb: 2,
                }}
              >
                <Box
                  sx={{
                    maxWidth: '75%',
                    p: 1.5,
                    borderRadius: 2,
                    backgroundColor: msg.from === 'user' ? '#0A2A84' : '#ffffff',
                    color: msg.from === 'user' ? '#ffffff' : '#1A1A1A',
                    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                  }}
                >
                  <Box
                    component="div"
                    sx={{ 
                      mb: msg.pdf ? 1.5 : 0,
                      fontSize: '0.875rem',
                      lineHeight: 1.5,
                      '& strong': {
                        fontWeight: 600,
                        color: msg.from === 'user' ? '#ffffff' : '#0A2A84',
                      },
                    }}
                  >
                    {formatMessage(msg.text)}
                  </Box>
                  {/* Buttons are only shown in the split-offer bubble above */}
                {msg.pdf && (
                  <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px solid #e0e0e0' }}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        p: 1.5,
                        backgroundColor: '#f5f5f5',
                        borderRadius: 1,
                        cursor: 'pointer',
                        '&:hover': {
                          backgroundColor: '#eeeeee',
                        },
                      }}
                      onClick={() => {
                        // Create download link
                        const link = document.createElement('a');
                        link.href = `data:application/pdf;base64,${msg.pdf}`;
                        link.download = msg.pdfFilename || 'sanction_letter.pdf';
                        link.click();
                      }}
                    >
                      <PictureAsPdf sx={{ color: '#dc3545', fontSize: 24 }} />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#1A1A1A' }}>
                          Sanction Letter PDF
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#666' }}>
                          Click to download
                        </Typography>
                      </Box>
                      <Download sx={{ color: '#0A2A84' }} />
                    </Box>
                    {/* Embedded PDF Viewer */}
                    <Box sx={{ mt: 1.5, borderRadius: 1, overflow: 'hidden', border: '1px solid #e0e0e0' }}>
                      <iframe
                        src={`data:application/pdf;base64,${msg.pdf}`}
                        width="100%"
                        height="400px"
                        style={{ border: 'none' }}
                        title="Sanction Letter PDF"
                      />
                    </Box>
                  </Box>
                )}
                {msg.attachment && (
                  <Box sx={{ mt: 1.5, pt: 1.5, borderTop: msg.from === 'user' ? '1px solid #e0e0e0' : 'none' }}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        p: 1.25,
                        backgroundColor: msg.from === 'user' ? 'rgba(255,255,255,0.15)' : '#f5f5f5',
                        borderRadius: 1,
                      }}
                    >
                      {msg.attachment.isPdf ? (
                        <PictureAsPdf sx={{ color: '#dc3545', fontSize: 22 }} />
                      ) : (
                        <AttachFile sx={{ color: msg.from === 'user' ? '#ffffff' : '#0A2A84', fontSize: 22 }} />
                      )}
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography
                          variant="body2"
                          noWrap
                          title={msg.attachment.name}
                          sx={{ fontWeight: 600, color: msg.from === 'user' ? '#ffffff' : '#1A1A1A' }}
                        >
                          {msg.attachment.name}
                        </Typography>
                        <Typography variant="caption" sx={{ color: msg.from === 'user' ? 'rgba(255,255,255,0.8)' : '#666' }}>
                          {msg.attachment.isPdf ? 'PDF document' : (msg.attachment.isImage ? 'Image' : 'File')}
                        </Typography>
                        {msg.attachment.trigger && (
                          <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: msg.from === 'user' ? 'rgba(255,255,255,0.9)' : '#0A2A84', fontStyle: 'italic' }}>
                            Sent: {msg.attachment.trigger}
                          </Typography>
                        )}
                      </Box>
                      <IconButton
                        size="small"
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = msg.attachment.url;
                          link.download = msg.attachment.name;
                          link.click();
                        }}
                        sx={{ color: msg.from === 'user' ? '#ffffff' : '#0A2A84' }}
                      >
                        <Download fontSize="small" />
                      </IconButton>
                    </Box>
                    {msg.attachment.isImage && (
                      <Box sx={{ mt: 1, borderRadius: 1, overflow: 'hidden', border: '1px solid #e0e0e0' }}>
                        <img
                          src={msg.attachment.url}
                          alt={msg.attachment.name}
                          style={{ display: 'block', width: '100%', height: 'auto', maxHeight: 300, objectFit: 'contain' }}
                        />
                      </Box>
                    )}
                    {msg.attachment.isPdf && (
                      <Box sx={{ mt: 1, borderRadius: 1, overflow: 'hidden', border: '1px solid #e0e0e0' }}>
                        <iframe
                          src={msg.attachment.url}
                          width="100%"
                          height="300px"
                          style={{ border: 'none' }}
                          title={msg.attachment.name}
                        />
                      </Box>
                    )}
                  </Box>
                )}
              </Box>
            </Box>
            );
          })}
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
              <Box
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  backgroundColor: '#ffffff',
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                }}
              >
                <Typography variant="body2" sx={{ color: '#666' }}>
                  Thinking...
                </Typography>
              </Box>
            </Box>
          )}
          <div ref={messagesEndRef} />
        </Box>

        {/* Input */}
        <Box
          sx={{
            p: 2,
            borderTop: '1px solid #e0e0e0',
            backgroundColor: '#ffffff',
            display: 'flex',
            gap: 1,
            alignItems: 'center',
          }}
          onClick={() => inputRef.current && inputRef.current.focus()}
        >
          <IconButton
            onClick={() => fileInputRef.current && fileInputRef.current.click()}
            sx={{ color: '#0A2A84' }}
            size="small"
            onMouseDown={(e) => { suppressFocusRef.current = true; e.preventDefault(); }}
          >
            <AttachFile />
          </IconButton>
          <Box
            component="input"
            type="file"
            accept=".pdf,image/*"
            ref={fileInputRef}
            onChange={handleFileChange}
            sx={{ display: 'none' }}
          />
          <Box
            component="input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            ref={inputRef}
            autoFocus
            autoComplete="off"
            onBlur={() => {
              // If chat is open and we didn't deliberately suppress focus (e.g., opening file picker), keep input active
              if (isOpen && !suppressFocusRef.current) {
                setTimeout(() => inputRef.current && inputRef.current.focus(), 0);
              }
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type your message..."
            sx={{
              flex: 1,
              px: 2,
              py: 1.25,
              borderRadius: 3,
              border: '1px solid #e0e0e0',
              fontSize: '0.95rem',
              outline: 'none',
            }}
          />
          <IconButton
            onClick={focusQuestionInput}
            sx={{ color: '#0A2A84' }}
            title="Ask a question"
            onMouseDown={(e) => e.preventDefault()}
          >
            <HelpOutline />
          </IconButton>
          <IconButton
            onClick={handleSend}
            sx={{
              backgroundColor: '#0A2A84',
              color: '#ffffff',
              '&:hover': {
                backgroundColor: '#1E4BD1',
              },
              '&:disabled': {
                backgroundColor: '#ccc',
              },
            }}
            onMouseDown={(e) => e.preventDefault()}
          >
            <Send />
          </IconButton>
        </Box>
      </Paper>
    </>
  );
};

export default TitanChatbot;

