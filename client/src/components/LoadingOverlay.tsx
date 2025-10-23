import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const loadingMessages = [
  { text: 'Analyzing Your Document', subtext: 'Our AI is carefully reviewing your legal document...' },
  { text: 'Identifying Clauses', subtext: 'Breaking down the document into key sections...' },
  { text: 'Assessing Risk Levels', subtext: 'Evaluating each clause for potential concerns...' },
  { text: 'Generating Explanations', subtext: 'Creating plain-language explanations...' },
  { text: 'Finalizing Results', subtext: 'Preparing your comprehensive analysis...' }
];

export function LoadingOverlay() {
  const [progress, setProgress] = useState(0);
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    // Simple, smooth progress animation that doesn't get stuck
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        // Smooth increment that slows down as it approaches 100%
        const remaining = 100 - prev;
        const increment = Math.max(0.2, remaining * 0.02); // Slower as it gets closer to 100%
        return Math.min(prev + increment, 99.5); // Cap at 99.5% to avoid getting stuck
      });
    }, 150);

    // Change messages periodically
    const messageInterval = setInterval(() => {
      setMessageIndex(prev => (prev + 1) % loadingMessages.length);
    }, 3000);

    return () => {
      clearInterval(progressInterval);
      clearInterval(messageInterval);
    };
  }, []);

  const currentMessage = loadingMessages[messageIndex];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.3 }}
        className="loading-overlay fixed inset-0 bg-slate-900/95 backdrop-blur-sm z-50 flex items-center justify-center"
      >
        <div className="loading-content w-full max-w-lg mx-auto px-4">
          {/* Simple Animated Spinner */}
          <motion.div
            className="w-16 h-16 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full mx-auto mb-8"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{
              scale: 1,
              opacity: 1,
              rotate: 360
            }}
            transition={{
              scale: { duration: 0.5 },
              opacity: { duration: 0.5 },
              rotate: { duration: 1, repeat: Infinity, ease: "linear" }
            }}
          />

          {/* Loading Text with Animation */}
          <motion.div
            key={messageIndex}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="text-center mt-8"
          >
            <h2 className="text-2xl font-bold text-white mb-2">{currentMessage.text}</h2>
            <p className="text-slate-300 mb-6">{currentMessage.subtext}</p>
          </motion.div>

          {/* Enhanced Progress Bar */}
          <div className="w-80 max-w-full mx-auto mt-6">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-slate-400 font-medium">Analysis Progress</span>
              <span className="text-sm text-cyan-400 font-semibold">{Math.round(progress)}%</span>
            </div>
            <div className="relative w-full h-3 bg-slate-700/50 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              />

              {/* Simple shine effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
            </div>

            {/* Progress indicators */}
            <div className="flex justify-between mt-2 text-xs text-slate-500">
              <span className={progress >= 25 ? 'text-cyan-400' : ''}>Start</span>
              <span className={progress >= 50 ? 'text-cyan-400' : ''}>Halfway</span>
              <span className={progress >= 75 ? 'text-cyan-400' : ''}>Almost</span>
              <span className={progress >= 100 ? 'text-cyan-400' : ''}>Done</span>
            </div>
          </div>

          {/* Google Cloud AI Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="google-cloud-badge mt-6"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z" />
            </svg>
            <span>Powered by Google Cloud AI</span>
          </motion.div>

          {/* Dynamic Status Message */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1, duration: 0.5 }}
            className="text-center mt-8 space-y-2"
          >
            <div className="text-lg font-semibold text-cyan-400">
              {progress < 20 ? 'Initializing Analysis' :
                progress < 40 ? 'Processing Document' :
                  progress < 60 ? 'Analyzing Content' :
                    progress < 80 ? 'Generating Insights' :
                      'Finalizing Results'}
            </div>
            <div className="text-slate-400 text-sm">
              {progress < 20 ? 'Setting up AI models and preparing analysis...' :
                progress < 40 ? 'Our AI is carefully examining your document...' :
                  progress < 60 ? 'Identifying key clauses and risk factors...' :
                    progress < 80 ? 'Creating actionable insights and recommendations...' :
                      'Almost ready! Preparing your results...'}
            </div>
          </motion.div>

          {/* Subtle Background Elements */}
          <div className="absolute top-20 left-20 w-32 h-32 bg-cyan-500/10 rounded-full blur-2xl opacity-50" />
          <div className="absolute bottom-20 right-20 w-40 h-40 bg-blue-500/10 rounded-full blur-2xl opacity-50" />
        </div>
      </motion.div>
    </AnimatePresence>
  );
}