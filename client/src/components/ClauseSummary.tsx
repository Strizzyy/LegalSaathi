import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, 
  Lightbulb, 
  AlertTriangle, 
  CheckCircle, 
  Loader2, 
  ChevronDown, 
  ChevronUp,
  Target,
  Shield
} from 'lucide-react';
import { summarizationService, type ClauseSummary } from '../services/summarizationService';

interface ClauseSummaryProps {
  clauseId: string;
  clauseData: any;
  className?: string;
}

export function ClauseSummary({ clauseId, clauseData, className = '' }: ClauseSummaryProps) {
  const [summary, setSummary] = useState<ClauseSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    const unsubscribe = summarizationService.subscribe(() => {
      setSummary(summarizationService.getClauseSummary(clauseId));
      setIsLoading(summarizationService.isLoading(clauseId));
    });

    // Initial load
    setSummary(summarizationService.getClauseSummary(clauseId));
    
    return unsubscribe;
  }, [clauseId]);

  const handleGenerateSummary = async () => {
    await summarizationService.generateClauseSummary(clauseId, clauseData);
  };

  const handleToggleExpanded = () => {
    if (!summary && !isLoading) {
      handleGenerateSummary();
    }
    setIsExpanded(!isExpanded);
  };

  return (
    <div className={`clause-summary ${className}`}>
      {/* Summary Toggle Button */}
      <button
        onClick={handleToggleExpanded}
        disabled={isLoading}
        className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-400 hover:to-pink-400 transition-all text-xs disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Lightbulb className="w-3 h-3 mr-1" />
            {summary ? 'View Summary' : 'Get Summary'}
            {summary && (
              isExpanded ? (
                <ChevronUp className="w-3 h-3 ml-1" />
              ) : (
                <ChevronDown className="w-3 h-3 ml-1" />
              )
            )}
          </>
        )}
      </button>

      {/* Summary Display */}
      <AnimatePresence>
        {isExpanded && summary && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3"
          >
            <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-lg p-4 space-y-4">
              {/* Plain Language Explanation */}
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <FileText className="w-4 h-4 text-purple-400" />
                  <h4 className="text-sm font-semibold text-white">In Simple Terms</h4>
                </div>
                <div className="bg-purple-500/10 border border-purple-500/20 rounded p-3">
                  <p className="text-sm text-purple-100 leading-relaxed">{summary.plainLanguage}</p>
                </div>
              </div>

              {/* Key Risks */}
              {summary.keyRisks.length > 0 && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <Shield className="w-4 h-4 text-orange-400" />
                    <h4 className="text-sm font-semibold text-white">Key Risks</h4>
                    <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-1 rounded-full">
                      {summary.keyRisks.length}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {summary.keyRisks.slice(0, 3).map((risk, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <AlertTriangle className="w-3 h-3 text-orange-400 mt-1 flex-shrink-0" />
                        <span className="text-xs text-slate-300">{risk}</span>
                      </div>
                    ))}
                    {summary.keyRisks.length > 3 && (
                      <div className="text-xs text-slate-400 italic">
                        +{summary.keyRisks.length - 3} more risks identified
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Action Items */}
              {summary.actionItems.length > 0 && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <Target className="w-4 h-4 text-green-400" />
                    <h4 className="text-sm font-semibold text-white">What You Should Do</h4>
                    <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">
                      {summary.actionItems.length}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {summary.actionItems.slice(0, 3).map((action, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <CheckCircle className="w-3 h-3 text-green-400 mt-1 flex-shrink-0" />
                        <span className="text-xs text-slate-300">{action}</span>
                      </div>
                    ))}
                    {summary.actionItems.length > 3 && (
                      <div className="text-xs text-slate-400 italic">
                        +{summary.actionItems.length - 3} more recommendations
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Summary Footer */}
              <div className="pt-2 border-t border-purple-500/20">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Generated: {summary.timestamp.toLocaleString()}</span>
                  <div className="flex items-center space-x-1">
                    <Lightbulb className="w-3 h-3" />
                    <span>AI Summary</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading State */}
      {isExpanded && isLoading && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-3"
        >
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-center space-x-3">
              <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
              <span className="text-sm text-slate-300">Generating clause summary...</span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}