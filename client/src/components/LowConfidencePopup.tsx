import { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Brain, Shield, Clock, CheckCircle, XCircle, Info } from 'lucide-react';
import { Modal } from './Modal';
import type { ConfidenceBreakdown } from '../types/chat';

interface LowConfidencePopupProps {
  isVisible: boolean;
  confidence: number;
  confidenceBreakdown?: ConfidenceBreakdown;
  onAccept: (userEmail: string) => void;
  onDecline: () => void;
  onClose: () => void;
}

export function LowConfidencePopup({
  isVisible,
  confidence,
  confidenceBreakdown,
  onAccept,
  onDecline,
  onClose
}: LowConfidencePopupProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [emailError, setEmailError] = useState('');

  const confidencePercentage = Math.round(confidence * 100);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleAccept = () => {
    if (!userEmail.trim()) {
      setEmailError('Email is required for expert review');
      return;
    }
    
    if (!validateEmail(userEmail)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    setEmailError('');
    onAccept(userEmail);
  };

  const handleDecline = () => {
    onDecline();
    onClose();
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 80) return 'text-green-400';
    if (conf >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceIcon = (conf: number) => {
    if (conf >= 80) return <CheckCircle className="w-5 h-5 text-green-400" />;
    if (conf >= 60) return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
    return <XCircle className="w-5 h-5 text-red-400" />;
  };

  return (
    <Modal
      isOpen={isVisible}
      onClose={onClose}
      title="AI Confidence Assessment"
      maxWidth="lg"
    >
      <div className="space-y-6">
        {/* Main Alert */}
        <div className="flex items-start space-x-4 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
          <AlertTriangle className="w-6 h-6 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white mb-2">
              Low AI Confidence Detected
            </h3>
            <p className="text-slate-300 mb-3">
              Our AI analysis has <span className={`font-semibold ${getConfidenceColor(confidencePercentage)}`}>
                {confidencePercentage}% confidence
              </span> in the results for your document. 
              For more accurate analysis, we recommend having a human legal expert review your document.
            </p>
          </div>
        </div>

        {/* Confidence Breakdown */}
        {confidenceBreakdown && (
          <div className="space-y-4">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center space-x-2 text-blue-400 hover:text-blue-300 transition-colors"
            >
              <Info className="w-4 h-4" />
              <span>{showDetails ? 'Hide' : 'Show'} Confidence Details</span>
            </button>

            {showDetails && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="bg-slate-700/50 rounded-lg p-4 space-y-3"
              >
                <h4 className="font-semibold text-white mb-3">Analysis Breakdown</h4>
                
                {/* Component Confidences */}
                <div className="space-y-2">
                  {Object.entries(confidenceBreakdown.component_weights).map(([component, _weight]) => {
                    const componentConf = confidenceBreakdown.clause_confidences[component] || 0;
                    const confPercentage = Math.round(componentConf * 100);
                    
                    return (
                      <div key={component} className="flex items-center justify-between">
                        <span className="text-slate-300 capitalize">
                          {component.replace('_', ' ')}
                        </span>
                        <div className="flex items-center space-x-2">
                          {getConfidenceIcon(confPercentage)}
                          <span className={`font-medium ${getConfidenceColor(confPercentage)}`}>
                            {confPercentage}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Factors Affecting Confidence */}
                {confidenceBreakdown.factors_affecting_confidence.length > 0 && (
                  <div className="mt-4">
                    <h5 className="font-medium text-white mb-2">Issues Identified:</h5>
                    <ul className="space-y-1">
                      {confidenceBreakdown.factors_affecting_confidence.map((factor, index) => (
                        <li key={index} className="text-slate-300 text-sm flex items-start space-x-2">
                          <span className="text-yellow-400 mt-1">•</span>
                          <span>{factor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            )}
          </div>
        )}

        {/* Expert Review Benefits */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="font-semibold text-white mb-3 flex items-center space-x-2">
            <Brain className="w-5 h-5 text-blue-400" />
            <span>Expert Review Benefits</span>
          </h4>
          <ul className="space-y-2 text-slate-300">
            <li className="flex items-start space-x-2">
              <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              <span>Human legal expert will review complex clauses</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              <span>More accurate risk assessment and recommendations</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              <span>Detailed explanations tailored to your situation</span>
            </li>
            <li className="flex items-start space-x-2">
              <Clock className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
              <span>Results delivered via email within 24-48 hours</span>
            </li>
          </ul>
        </div>

        {/* Privacy Information */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <h4 className="font-semibold text-white mb-2 flex items-center space-x-2">
            <Shield className="w-5 h-5 text-blue-400" />
            <span>Privacy & Data Sharing</span>
          </h4>
          <div className="text-slate-300 text-sm space-y-2">
            <p>If you choose expert review, we will share:</p>
            <ul className="ml-4 space-y-1">
              <li>• Your document content (with sensitive data masked)</li>
              <li>• AI analysis results for expert reference</li>
              <li>• Your email address for result delivery</li>
            </ul>
            <p className="mt-2 text-xs text-slate-400">
              All data is handled according to our privacy policy and deleted after review completion.
            </p>
          </div>
        </div>

        {/* Email Input */}
        <div className="space-y-2">
          <label htmlFor="userEmail" className="block text-sm font-medium text-white">
            Email Address (for receiving expert analysis)
          </label>
          <input
            type="email"
            id="userEmail"
            value={userEmail}
            onChange={(e) => {
              setUserEmail(e.target.value);
              if (emailError) setEmailError('');
            }}
            placeholder="your.email@example.com"
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {emailError && (
            <p className="text-red-400 text-sm">{emailError}</p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3 pt-4">
          <button
            onClick={handleAccept}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-800"
          >
            Yes, Get Expert Review
          </button>
          <button
            onClick={handleDecline}
            className="flex-1 bg-slate-600 hover:bg-slate-700 text-white font-medium py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-slate-800"
          >
            No, Use AI Results
          </button>
        </div>

        {/* Timeline Information */}
        <div className="text-center text-sm text-slate-400 pt-2 border-t border-slate-700">
          <p>Expert review typically takes 24-48 hours • Results sent via email</p>
        </div>
      </div>
    </Modal>
  );
}