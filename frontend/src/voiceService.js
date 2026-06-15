/**
 * Voice Service for Speech-to-Text and Text-to-Speech
 * Supports Hindi and English languages
 */

class VoiceService {
  constructor() {
    this.recognition = null;
    this.synthesis = window.speechSynthesis;
    this.isListening = false;
    this.currentLanguage = 'en-IN'; // Default: English (India)
    this.initSpeechRecognition();
  }

  /**
   * Initialize Speech Recognition API
   */
  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('Speech Recognition not supported in this browser');
      return null;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = this.currentLanguage;
    
    return this.recognition;
  }

  /**
   * Set language for speech recognition
   * @param {string} lang - Language code ('en-IN' for English, 'hi-IN' for Hindi)
   */
  setLanguage(lang) {
    this.currentLanguage = lang;
    if (this.recognition) {
      this.recognition.lang = lang;
    }
  }

  /**
   * Start listening for voice input
   * @param {function} onResult - Callback when speech is recognized
   * @param {function} onError - Callback for errors
   */
  startListening(onResult, onError) {
    if (!this.recognition) {
      if (onError) onError('Speech recognition not supported in this browser');
      return false;
    }

    if (this.isListening) {
      this.stopListening();
    }

    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (onResult) onResult(transcript);
      this.isListening = false;
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      if (onError) onError(event.error);
      this.isListening = false;
    };

    this.recognition.onend = () => {
      this.isListening = false;
    };

    try {
      this.recognition.start();
      this.isListening = true;
      return true;
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      if (onError) onError(error.message);
      return false;
    }
  }

  /**
   * Stop listening for voice input
   */
  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }

  /**
   * Speak text using Text-to-Speech
   * @param {string} text - Text to speak
   * @param {string} lang - Language code ('en-IN' or 'hi-IN')
   * @param {function} onEnd - Callback when speech ends
   */
  speak(text, lang = 'en-IN', onEnd = null) {
    // Stop any ongoing speech
    this.synthesis.cancel();

    if (!text) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 1.0; // Normal speed
    utterance.pitch = 1.0; // Normal pitch
    utterance.volume = 1.0; // Full volume

    // Set voice based on language
    utterance.onstart = () => {
      console.log('Speech started');
    };

    utterance.onend = () => {
      if (onEnd) onEnd();
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
    };

    // Try to find appropriate voice for the language
    const voices = this.synthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.lang.startsWith(lang.split('-')[0])
    );
    
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    this.synthesis.speak(utterance);
  }

  /**
   * Stop speaking
   */
  stopSpeaking() {
    this.synthesis.cancel();
  }

  /**
   * Check if speech recognition is available
   */
  isSpeechRecognitionAvailable() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  /**
   * Check if speech synthesis is available
   */
  isSpeechSynthesisAvailable() {
    return !!window.speechSynthesis;
  }

  /**
   * Get available voices for a language
   */
  getAvailableVoices(lang = 'en') {
    const voices = this.synthesis.getVoices();
    return voices.filter(voice => voice.lang.startsWith(lang));
  }
}

export default VoiceService;

