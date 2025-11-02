import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import './Robot3D.css';
import { AIChat } from './AIChat';
import type { DocumentContext } from '../types/chat';

// Fallback static robot component
const RobotFallback = ({ onClick }: { onClick: () => void }) => (
  <div className="robot-container robot-fallback">
    <div className="speech-bubble">Hi! Click me to chat with AI assistant.</div>
    <div 
      className="robot-static cursor-pointer hover:scale-105 transition-transform duration-200" 
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      aria-label="Click to open AI assistant chat"
    >
      <div className="head">
        <div className="antenna"></div>
        <div className="ear left"></div>
        <div className="ear right"></div>
        <div className="screen">
          <div className="eyes">
            <div className="eye left"></div>
            <div className="eye right"></div>
          </div>
          <div className="smile"></div>
        </div>
      </div>
      <div className="body">
        <div className="arm left">
          <div className="hand"></div>
        </div>
        <div className="arm right">
          <div className="hand"></div>
        </div>
        <div className="legs">
          <div className="leg">
            <div className="foot"></div>
          </div>
          <div className="leg">
            <div className="foot"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Animated robot component
const AnimatedRobot = ({ onClick }: { onClick: () => void }) => (
  <motion.div
    className="robot-container"
    initial={{ opacity: 0, scale: 0.5 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.5, type: "spring" }}
  >
    <div className="speech-bubble">Hi! Click me to chat with AI assistant.</div>
    <motion.div 
      className="robot cursor-pointer"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      aria-label="Click to open AI assistant chat"
    >
      <div className="head">
        <div className="antenna"></div>
        <div className="ear left"></div>
        <div className="ear right"></div>
        <div className="screen">
          <div className="eyes">
            <div className="eye left"></div>
            <div className="eye right"></div>
          </div>
          <div className="smile"></div>
        </div>
      </div>
      <div className="body">
        <div className="arm left">
          <div className="hand"></div>
        </div>
        <div className="arm right">
          <div className="hand"></div>
        </div>
        <div className="legs">
          <div className="leg">
            <div className="foot"></div>
          </div>
          <div className="leg">
            <div className="foot"></div>
          </div>
        </div>
      </div>
    </motion.div>
  </motion.div>
);

export const Robot3D = () => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [showFallback, setShowFallback] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Create a basic document context for the AI chat
  const documentContext: DocumentContext = {
    documentType: 'general',
    overallRisk: 'GREEN',
    summary: 'Welcome to Legal Saathi - AI-powered legal document analysis platform',
    totalClauses: 0
  };

  useEffect(() => {
    // Simulate component loading and timeout detection
    const loadingTimer = setTimeout(() => {
      try {
        // Check if framer-motion is available and working
        if (typeof motion !== 'undefined') {
          setIsLoaded(true);
        } else {
          throw new Error('Framer Motion not available');
        }
      } catch (error) {
        console.warn('Robot3D: Animation failed, using fallback', error);
        setHasError(true);
        setShowFallback(true);
      }
    }, 100);

    // Timeout detection - fallback after 2.5 seconds
    const timeoutTimer = setTimeout(() => {
      if (!isLoaded && !hasError) {
        console.warn('Robot3D: Loading timeout, switching to fallback');
        setShowFallback(true);
      }
    }, 2500);

    return () => {
      clearTimeout(loadingTimer);
      clearTimeout(timeoutTimer);
    };
  }, [isLoaded, hasError]);

  const handleRobotClick = () => {
    setIsChatOpen(true);
  };

  const handleChatClose = () => {
    setIsChatOpen(false);
  };

  // Show fallback if there's an error or timeout
  if (showFallback || hasError) {
    return (
      <>
        <RobotFallback onClick={handleRobotClick} />
        <AIChat 
          isOpen={isChatOpen} 
          onClose={handleChatClose} 
          documentContext={documentContext}
        />
      </>
    );
  }

  // Show animated version if loaded successfully
  if (isLoaded) {
    return (
      <>
        <AnimatedRobot onClick={handleRobotClick} />
        <AIChat 
          isOpen={isChatOpen} 
          onClose={handleChatClose} 
          documentContext={documentContext}
        />
      </>
    );
  }

  // Show loading state (minimal placeholder)
  return (
    <div className="robot-container robot-loading">
      <div className="robot-placeholder">
        <div className="loading-spinner"></div>
      </div>
    </div>
  );
};