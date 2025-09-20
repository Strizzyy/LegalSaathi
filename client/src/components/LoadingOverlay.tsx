import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const loadingStages = [
  { text: 'Analyzing Your Document', subtext: 'Our AI is carefully reviewing your legal document...', duration: 1000 },
  { text: 'Identifying Clauses', subtext: 'Breaking down the document into key sections...', duration: 800 },
  { text: 'Assessing Risk Levels', subtext: 'Evaluating each clause for potential concerns...', duration: 1200 },
  { text: 'Generating Explanations', subtext: 'Creating plain-language explanations...', duration: 900 },
  { text: 'Finalizing Results', subtext: 'Preparing your comprehensive analysis...', duration: 600 }
];

export function LoadingOverlay() {
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    // Progress simulation
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const increment = Math.random() * 8 + 3; // 3-11% increments
        return Math.min(prev + increment, 92); // Cap at 92% until completion
      });
    }, 600);

    // Stage progression
    let stageTimeout: NodeJS.Timeout;
    const progressStages = () => {
      if (currentStage < loadingStages.length - 1) {
        stageTimeout = setTimeout(() => {
          setCurrentStage(prev => prev + 1);
          progressStages();
        }, loadingStages[currentStage].duration);
      }
    };

    progressStages();

    return () => {
      clearInterval(progressInterval);
      clearTimeout(stageTimeout);
    };
  }, [currentStage]);

  const stage = loadingStages[currentStage];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="loading-overlay"
      >
        <div className="loading-content">
          {/* Animated Spinner */}
          <motion.div
            className="spinner"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
          
          {/* Loading Text with Animation */}
          <motion.div
            key={currentStage}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <h2 className="text-2xl font-bold text-white mb-2">{stage.text}</h2>
            <p className="text-slate-300 mb-6">{stage.subtext}</p>
          </motion.div>
          
          {/* Progress Bar */}
          <div className="w-80 max-w-full">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-400">Progress</span>
              <span className="text-sm text-slate-400">{Math.round(progress)}%</span>
            </div>
            <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
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
              <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
            </svg>
            <span>Powered by Google Cloud AI</span>
          </motion.div>
          
          {/* Community Impact Message */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1, duration: 0.5 }}
            className="text-center mt-8 space-y-2"
          >
            <div className="text-lg font-semibold text-cyan-400">
              Protecting 10,000+ Users Daily
            </div>
            <div className="text-slate-400">
              Join thousands who've avoided unfavorable legal terms
            </div>
          </motion.div>
          
          {/* Floating Animation Elements */}
          <div className="absolute top-10 left-10 w-20 h-20 bg-cyan-500/20 rounded-full blur-xl animate-float" />
          <div className="absolute bottom-10 right-10 w-32 h-32 bg-blue-500/20 rounded-full blur-xl animate-float" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 left-20 w-16 h-16 bg-purple-500/20 rounded-full blur-xl animate-float" style={{ animationDelay: '2s' }} />
        </div>
      </motion.div>
    </AnimatePresence>
  );
}