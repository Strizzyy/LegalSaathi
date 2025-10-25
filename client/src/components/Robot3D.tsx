import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import './Robot3D.css';

// Fallback static robot component
const RobotFallback = () => (
  <div className="robot-container robot-fallback">
    <div className="speech-bubble">Hello, explorer. Team Lunatics is online.</div>
    <div className="robot-static">
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
const AnimatedRobot = () => (
  <motion.div
    className="robot-container"
    initial={{ opacity: 0, scale: 0.5 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.5, type: "spring" }}
  >
    <div className="speech-bubble">Hello, explorer. Team Lunatics is online.</div>
    <div className="robot">
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
  </motion.div>
);

export const Robot3D = () => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [showFallback, setShowFallback] = useState(false);

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

  // Show fallback if there's an error or timeout
  if (showFallback || hasError) {
    return <RobotFallback />;
  }

  // Show animated version if loaded successfully
  if (isLoaded) {
    return <AnimatedRobot />;
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