import { motion } from 'framer-motion';
import { 
  FileText,
  Shield,
  Target,
  MessageCircle,
  CheckCircle,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { cn } from '../utils';

interface DetailedClauseAnalysisProps {
  clause: {
    risk_level: {
      level: 'RED' | 'YELLOW' | 'GREEN';
      severity: string;
      confidence_percentage: number;
    };
    clause_text: string;
    plain_explanation: string;
    legal_implications: string[];
    recommendations: string[];
  };
  isExpanded: boolean;
  onToggle: () => void;
}

export function DetailedClauseAnalysis({ clause, isExpanded, onToggle }: DetailedClauseAnalysisProps) {
  return (
    <div className="mt-4">
      <button
        onClick={onToggle}
        className={cn(
          "w-full flex items-center justify-between p-3 rounded-lg border transition-colors",
          clause.risk_level.level === 'RED' ? "border-red-500/30 bg-red-500/10 hover:bg-red-500/20" :
          clause.risk_level.level === 'YELLOW' ? "border-yellow-500/30 bg-yellow-500/10 hover:bg-yellow-500/20" :
          "border-green-500/30 bg-green-500/10 hover:bg-green-500/20"
        )}
      >
        <span className="flex items-center">
          <FileText className="w-4 h-4 mr-2" />
          <strong>View Detailed Analysis</strong>
        </span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>
      
      {isExpanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.2 }}
          className={cn(
            "mt-3 p-4 rounded-lg border space-y-6",
            clause.risk_level.level === 'RED' ? "border-red-500/30 bg-red-500/5" :
            clause.risk_level.level === 'YELLOW' ? "border-yellow-500/30 bg-yellow-500/5" :
            "border-green-500/30 bg-green-500/5"
          )}
        >
          {/* Risk Level Indicator */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={cn(
                "px-3 py-1.5 rounded-lg flex items-center space-x-2 text-sm border",
                clause.risk_level.level === 'RED' ? "bg-red-500/10 text-red-400 border-red-500/30" :
                clause.risk_level.level === 'YELLOW' ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/30" :
                "bg-green-500/10 text-green-400 border-green-500/30"
              )}>
                <Shield className="w-4 h-4" />
                <span>{clause.risk_level.level} Risk Level</span>
              </div>
              <span className="text-slate-400">
                {clause.risk_level.severity} severity
              </span>
            </div>
            <div className="text-sm text-slate-400">
              Confidence: {clause.risk_level.confidence_percentage}%
            </div>
          </div>

          {/* Clause Text */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-2 flex items-center">
              <FileText className="w-4 h-4 mr-2" />
              Original Text
            </h4>
            <div className={cn(
              "p-3 rounded-lg border font-mono text-sm",
              clause.risk_level.level === 'RED' ? "bg-red-500/5 border-red-500/20 text-red-100" :
              clause.risk_level.level === 'YELLOW' ? "bg-yellow-500/5 border-yellow-500/20 text-yellow-100" :
              "bg-green-500/5 border-green-500/20 text-green-100"
            )}>
              {clause.clause_text}
            </div>
          </div>

          {/* Plain Language Explanation */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-2 flex items-center">
              <MessageCircle className={cn(
                "w-4 h-4 mr-2",
                clause.risk_level.level === 'RED' ? "text-red-400" :
                clause.risk_level.level === 'YELLOW' ? "text-yellow-400" :
                "text-green-400"
              )} />
              In Simple Terms
            </h4>
            <p className="text-slate-300">
              {clause.plain_explanation}
            </p>
          </div>

          {/* Legal Implications */}
          {clause.legal_implications.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                <AlertTriangle className={cn(
                  "w-4 h-4 mr-2",
                  clause.risk_level.level === 'RED' ? "text-red-400" :
                  clause.risk_level.level === 'YELLOW' ? "text-yellow-400" :
                  "text-green-400"
                )} />
                Legal Implications
              </h4>
              <ul className="space-y-2">
                {clause.legal_implications.map((implication, i) => (
                  <li key={i} className="flex items-start">
                    <Shield className={cn(
                      "w-4 h-4 mt-0.5 mr-3 flex-shrink-0",
                      clause.risk_level.level === 'RED' ? "text-red-400" :
                      clause.risk_level.level === 'YELLOW' ? "text-yellow-400" :
                      "text-green-400"
                    )} />
                    <span className="text-slate-300">{implication}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {clause.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-white mb-3 flex items-center">
                <Target className={cn(
                  "w-4 h-4 mr-2",
                  clause.risk_level.level === 'RED' ? "text-red-400" :
                  clause.risk_level.level === 'YELLOW' ? "text-yellow-400" :
                  "text-green-400"
                )} />
                Recommended Actions
              </h4>
              <ul className="space-y-2">
                {clause.recommendations.map((recommendation, i) => (
                  <li key={i} className="flex items-start">
                    <CheckCircle className={cn(
                      "w-4 h-4 mt-0.5 mr-3 flex-shrink-0",
                      clause.risk_level.level === 'RED' ? "text-red-400" :
                      clause.risk_level.level === 'YELLOW' ? "text-yellow-400" :
                      "text-green-400"
                    )} />
                    <span className="text-slate-300">{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Analysis Note */}
          <div className={cn(
            "p-3 rounded-lg border text-sm flex items-start space-x-2",
            clause.risk_level.level === 'RED' ? "bg-red-500/5 border-red-500/20" :
            clause.risk_level.level === 'YELLOW' ? "bg-yellow-500/5 border-yellow-500/20" :
            "bg-green-500/5 border-green-500/20"
          )}>
            <Info className="w-4 h-4 mt-0.5 flex-shrink-0 text-slate-400" />
            <p className="text-slate-400">
              This analysis is provided by our AI system with a confidence level of {clause.risk_level.confidence_percentage}%. 
              For critical decisions, we recommend consulting with a legal professional.
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
}