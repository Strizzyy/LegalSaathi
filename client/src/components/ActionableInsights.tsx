import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Brain,
    AlertTriangle,
    Users,
    MessageSquare,
    Shield,
    Target,
    TrendingUp,
    CheckCircle,
    Info,
    Loader2,
    RefreshCw,
    Eye,
    Zap,
    BarChart3
} from 'lucide-react';
import { cn } from '../utils';

interface ActionableInsightsProps {
    analysisId: string;
    className?: string;
}

interface InsightsSummary {
    intelligence_score: number;
    risk_distribution: {
        critical: number;
        high: number;
        medium: number;
        total: number;
    };
    key_metrics: {
        negotiation_opportunities: number;
        compliance_concerns: number;
        document_conflicts: number;
        bias_indicators: number;
        entity_relationships: number;
    };
    recommendations: string[];
}

interface ConflictAnalysis {
    conflict_id: string;
    clause_ids: string[];
    conflict_type: string;
    description: string;
    severity: string;
    resolution_suggestions: string[];
    confidence: number;
}

interface BiasIndicator {
    bias_type: string;
    clause_id: string;
    biased_language: string;
    explanation: string;
    suggested_alternative: string;
    severity: string;
    confidence: number;
}

interface NegotiationPoint {
    clause_id: string;
    negotiation_type: string;
    current_language: string;
    suggested_language: string;
    rationale: string;
    priority: string;
    potential_impact: string;
    confidence: number;
}

interface EntityRelationship {
    entity1: string;
    entity2: string;
    relationship_type: string;
    description: string;
    legal_significance: string;
    confidence: number;
}

interface ComplianceFlag {
    regulation_type: string;
    clause_id: string;
    issue_description: string;
    compliance_risk: string;
    recommended_action: string;
    severity: string;
    confidence: number;
}

export function ActionableInsights({ analysisId, className = '' }: ActionableInsightsProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [summary, setSummary] = useState<InsightsSummary | null>(null);
    const [conflicts, setConflicts] = useState<ConflictAnalysis[]>([]);
    const [biasIndicators, setBiasIndicators] = useState<BiasIndicator[]>([]);
    const [negotiationPoints, setNegotiationPoints] = useState<NegotiationPoint[]>([]);
    const [entityRelationships, setEntityRelationships] = useState<EntityRelationship[]>([]);
    const [complianceFlags, setComplianceFlags] = useState<ComplianceFlag[]>([]);
    const [activeTab, setActiveTab] = useState<string>('summary');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (analysisId) {
            // Add a small delay to ensure analysis is fully stored
            const timer = setTimeout(() => {
                loadInsights();
            }, 500); // 500ms delay (reduced since backend issue is fixed)

            return () => clearTimeout(timer);
        }

        // Return empty cleanup function for the else case
        return () => { };
    }, [analysisId]);

    const loadInsights = async (retryCount: number = 0) => {
        setIsLoading(true);
        setError(null);

        try {
            // Load summary first
            const summaryResponse = await fetch(`/api/insights/summary/${analysisId}`);
            if (!summaryResponse.ok) {
                const errorText = await summaryResponse.text();
                console.error('Summary API error:', errorText);

                // Retry on 500 errors (up to 2 times)
                if (summaryResponse.status === 500 && retryCount < 2) {
                    console.log(`Retrying insights load (attempt ${retryCount + 1}/2)...`);
                    setIsLoading(false); // Stop loading indicator during retry delay
                    setTimeout(() => loadInsights(retryCount + 1), 2000); // 2 second delay
                    return;
                }

                throw new Error(`Failed to load insights summary: ${summaryResponse.status}`);
            }
            const summaryData = await summaryResponse.json();

            // Check if the response indicates an error
            if (!summaryData.success) {
                throw new Error(summaryData.message || 'Insights summary generation failed');
            }

            setSummary(summaryData);

            // Load detailed insights in parallel
            const [conflictsRes, biasRes, negotiationRes, entitiesRes, complianceRes] = await Promise.all([
                fetch(`/api/insights/conflicts/${analysisId}`),
                fetch(`/api/insights/bias/${analysisId}`),
                fetch(`/api/insights/negotiation/${analysisId}`),
                fetch(`/api/insights/entities/${analysisId}`),
                fetch(`/api/insights/compliance/${analysisId}`)
            ]);

            if (conflictsRes.ok) {
                const conflictsData = await conflictsRes.json();
                setConflicts(conflictsData.conflicts || []);
            }

            if (biasRes.ok) {
                const biasData = await biasRes.json();
                setBiasIndicators(biasData.bias_indicators || []);
            }

            if (negotiationRes.ok) {
                const negotiationData = await negotiationRes.json();
                setNegotiationPoints(negotiationData.negotiation_points || []);
            }

            if (entitiesRes.ok) {
                const entitiesData = await entitiesRes.json();
                setEntityRelationships(entitiesData.entity_relationships || []);
            }

            if (complianceRes.ok) {
                const complianceData = await complianceRes.json();
                setComplianceFlags(complianceData.compliance_flags || []);
            }

        } catch (error) {
            console.error('Failed to load actionable insights:', error);
            setError(error instanceof Error ? error.message : 'Failed to load insights');

            // Set empty summary as fallback
            setSummary({
                intelligence_score: 0,
                risk_distribution: { critical: 0, high: 0, medium: 0, total: 0 },
                key_metrics: {
                    negotiation_opportunities: 0,
                    compliance_concerns: 0,
                    document_conflicts: 0,
                    bias_indicators: 0,
                    entity_relationships: 0
                },
                recommendations: ['Insights generation failed - please try again later']
            });
        } finally {
            setIsLoading(false);
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity.toLowerCase()) {
            case 'critical':
                return 'text-red-400 bg-red-500/20 border-red-500/50';
            case 'high':
                return 'text-orange-400 bg-orange-500/20 border-orange-500/50';
            case 'medium':
                return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
            case 'low':
                return 'text-green-400 bg-green-500/20 border-green-500/50';
            default:
                return 'text-slate-400 bg-slate-500/20 border-slate-500/50';
        }
    };

    const getIntelligenceScoreColor = (score: number) => {
        if (score >= 80) return 'text-green-400';
        if (score >= 60) return 'text-yellow-400';
        if (score >= 40) return 'text-orange-400';
        return 'text-red-400';
    };

    if (isLoading) {
        return (
            <div className={`actionable-insights-loading ${className}`}>
                <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
                    <div className="flex items-center justify-center space-x-3">
                        <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
                        <span className="text-white">Generating actionable insights...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`actionable-insights-error ${className}`}>
                <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
                    <div className="text-center">
                        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-white mb-2">Insights Generation Failed</h3>
                        <p className="text-slate-400 mb-4">{error}</p>
                        <button
                            onClick={() => loadInsights(0)}
                            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-lg hover:from-cyan-400 hover:to-blue-400 transition-all"
                        >
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (!summary) {
        return null;
    }

    const tabs = [
        { id: 'summary', label: 'Overview', icon: BarChart3, count: null },
        { id: 'conflicts', label: 'Conflicts', icon: AlertTriangle, count: conflicts.length },
        { id: 'bias', label: 'Bias Analysis', icon: Eye, count: biasIndicators.length },
        { id: 'negotiation', label: 'Negotiation', icon: MessageSquare, count: negotiationPoints.length },
        { id: 'entities', label: 'Relationships', icon: Users, count: entityRelationships.length },
        { id: 'compliance', label: 'Compliance', icon: Shield, count: complianceFlags.length }
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`actionable-insights ${className}`}
        >
            <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-2xl p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                        <div className="p-2 bg-purple-500/20 rounded-lg">
                            <Brain className="w-6 h-6 text-purple-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">Actionable Insights</h2>
                            <p className="text-slate-400 text-sm">Advanced AI-powered document intelligence</p>
                            <div className="flex items-center mt-1">
                                <Zap className="w-3 h-3 text-yellow-400 mr-1" />
                                <span className="text-xs text-yellow-400 font-medium">Powered by Google Cloud AI</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center space-x-4">
                        <div className="text-center">
                            <div className={cn("text-2xl font-bold", getIntelligenceScoreColor(summary.intelligence_score))}>
                                {summary.intelligence_score.toFixed(0)}
                            </div>
                            <div className="text-xs text-slate-400">Intelligence Score</div>
                        </div>
                        <button
                            onClick={() => loadInsights(0)}
                            className="inline-flex items-center px-3 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors text-sm"
                        >
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Refresh
                        </button>
                    </div>
                </div>

                {/* Tab Navigation */}
                <div className="flex flex-wrap gap-2 mb-6 border-b border-slate-700 pb-4">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={cn(
                                "inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                                activeTab === tab.id
                                    ? "bg-purple-500/20 text-purple-400 border border-purple-500/50"
                                    : "text-slate-400 hover:text-white hover:bg-slate-700"
                            )}
                        >
                            <tab.icon className="w-4 h-4 mr-2" />
                            {tab.label}
                            {tab.count !== null && tab.count > 0 && (
                                <span className="ml-2 px-2 py-0.5 bg-slate-600 text-slate-200 rounded-full text-xs">
                                    {tab.count}
                                </span>
                            )}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="tab-content">
                    {activeTab === 'summary' && (
                        <div className="space-y-6">
                            {/* Risk Distribution */}
                            <div className="grid md:grid-cols-2 gap-6">
                                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                                    <h3 className="font-semibold text-white mb-3 flex items-center">
                                        <TrendingUp className="w-5 h-5 mr-2" />
                                        Risk Distribution
                                    </h3>
                                    <div className="space-y-3">
                                        {[
                                            { label: 'Critical', count: summary.risk_distribution.critical, color: 'bg-red-500' },
                                            { label: 'High', count: summary.risk_distribution.high, color: 'bg-orange-500' },
                                            { label: 'Medium', count: summary.risk_distribution.medium, color: 'bg-yellow-500' }
                                        ].map((risk) => (
                                            <div key={risk.label} className="flex items-center justify-between">
                                                <div className="flex items-center space-x-2">
                                                    <div className={cn("w-3 h-3 rounded-full", risk.color)} />
                                                    <span className="text-slate-300">{risk.label}</span>
                                                </div>
                                                <span className="text-white font-medium">{risk.count}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                                    <h3 className="font-semibold text-white mb-3 flex items-center">
                                        <Target className="w-5 h-5 mr-2" />
                                        Key Metrics
                                    </h3>
                                    <div className="space-y-3">
                                        {[
                                            { label: 'Negotiation Opportunities', count: summary.key_metrics.negotiation_opportunities, icon: MessageSquare },
                                            { label: 'Compliance Concerns', count: summary.key_metrics.compliance_concerns, icon: Shield },
                                            { label: 'Document Conflicts', count: summary.key_metrics.document_conflicts, icon: AlertTriangle },
                                            { label: 'Entity Relationships', count: summary.key_metrics.entity_relationships, icon: Users }
                                        ].map((metric) => (
                                            <div key={metric.label} className="flex items-center justify-between">
                                                <div className="flex items-center space-x-2">
                                                    <metric.icon className="w-4 h-4 text-slate-400" />
                                                    <span className="text-slate-300 text-sm">{metric.label}</span>
                                                </div>
                                                <span className="text-white font-medium">{metric.count}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Priority Actions */}
                            <div className="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/30 rounded-lg p-4">
                                <h3 className="font-semibold text-white mb-3 flex items-center">
                                    <AlertTriangle className="w-5 h-5 mr-2 text-red-400" />
                                    Immediate Actions Required
                                </h3>
                                <div className="space-y-3">
                                    {summary.risk_distribution.critical > 0 && (
                                        <div className="flex items-start space-x-3 p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                                            <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0" />
                                            <div>
                                                <p className="text-red-300 font-medium">Critical Risk Alert</p>
                                                <p className="text-slate-300 text-sm">
                                                    {summary.risk_distribution.critical} critical issue{summary.risk_distribution.critical > 1 ? 's' : ''} detected. 
                                                    Review immediately before proceeding.
                                                </p>
                                            </div>
                                        </div>
                                    )}
                                    {summary.key_metrics.negotiation_opportunities > 0 && (
                                        <div className="flex items-start space-x-3 p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                                            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                                            <div>
                                                <p className="text-blue-300 font-medium">Negotiation Opportunities</p>
                                                <p className="text-slate-300 text-sm">
                                                    {summary.key_metrics.negotiation_opportunities} clause{summary.key_metrics.negotiation_opportunities > 1 ? 's' : ''} can be improved through negotiation.
                                                </p>
                                            </div>
                                        </div>
                                    )}
                                    {summary.key_metrics.compliance_concerns > 0 && (
                                        <div className="flex items-start space-x-3 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                                            <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0" />
                                            <div>
                                                <p className="text-yellow-300 font-medium">Compliance Review Needed</p>
                                                <p className="text-slate-300 text-sm">
                                                    {summary.key_metrics.compliance_concerns} potential compliance issue{summary.key_metrics.compliance_concerns > 1 ? 's' : ''} identified.
                                                </p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Recommendations */}
                            {summary.recommendations.filter(Boolean).length > 0 && (
                                <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
                                    <h3 className="font-semibold text-white mb-3 flex items-center">
                                        <Zap className="w-5 h-5 mr-2" />
                                        AI-Powered Recommendations
                                    </h3>
                                    <ul className="space-y-3">
                                        {summary.recommendations.filter(Boolean).map((recommendation, index) => (
                                            <li key={index} className="flex items-start space-x-3 p-3 bg-slate-800/50 rounded-lg">
                                                <CheckCircle className="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" />
                                                <div>
                                                    <span className="text-slate-200 font-medium">Action {index + 1}</span>
                                                    <p className="text-slate-300 text-sm mt-1">{recommendation}</p>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Quick Stats */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-center">
                                    <BarChart3 className="w-6 h-6 text-purple-400 mx-auto mb-2" />
                                    <div className="text-2xl font-bold text-white">{summary.intelligence_score.toFixed(0)}</div>
                                    <div className="text-xs text-slate-400">Intelligence Score</div>
                                </div>
                                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-center">
                                    <Target className="w-6 h-6 text-green-400 mx-auto mb-2" />
                                    <div className="text-2xl font-bold text-white">{summary.risk_distribution.total}</div>
                                    <div className="text-xs text-slate-400">Total Issues</div>
                                </div>
                                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-center">
                                    <MessageSquare className="w-6 h-6 text-blue-400 mx-auto mb-2" />
                                    <div className="text-2xl font-bold text-white">{summary.key_metrics.negotiation_opportunities}</div>
                                    <div className="text-xs text-slate-400">Negotiable</div>
                                </div>
                                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-center">
                                    <Shield className="w-6 h-6 text-orange-400 mx-auto mb-2" />
                                    <div className="text-2xl font-bold text-white">{summary.key_metrics.compliance_concerns}</div>
                                    <div className="text-xs text-slate-400">Compliance</div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'conflicts' && (
                        <div className="space-y-4">
                            {conflicts.length === 0 ? (
                                <div className="text-center py-8">
                                    <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-white mb-2">No Conflicts Detected</h3>
                                    <p className="text-slate-400">The document appears to be internally consistent.</p>
                                </div>
                            ) : (
                                conflicts.map((conflict) => (
                                    <div key={conflict.conflict_id} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                                        <div className="flex items-start justify-between mb-3">
                                            <div className="flex items-center space-x-2">
                                                <AlertTriangle className="w-5 h-5 text-orange-400" />
                                                <h4 className="font-semibold text-white">{conflict.conflict_type.replace('_', ' ').toUpperCase()}</h4>
                                            </div>
                                            <span className={cn("px-2 py-1 rounded-full text-xs border", getSeverityColor(conflict.severity))}>
                                                {conflict.severity}
                                            </span>
                                        </div>
                                        <p className="text-slate-300 mb-3">{conflict.description}</p>
                                        <div className="mb-3">
                                            <span className="text-sm text-slate-400">Affected Clauses: </span>
                                            <span className="text-sm text-slate-200">{conflict.clause_ids.join(', ')}</span>
                                        </div>
                                        {conflict.resolution_suggestions.length > 0 && (
                                            <div>
                                                <h5 className="text-sm font-medium text-white mb-2">Resolution Suggestions:</h5>
                                                <ul className="space-y-1">
                                                    {conflict.resolution_suggestions.map((suggestion, idx) => (
                                                        <li key={idx} className="text-sm text-slate-300 flex items-start space-x-2">
                                                            <span className="text-cyan-400">•</span>
                                                            <span>{suggestion}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === 'bias' && (
                        <div className="space-y-4">
                            {biasIndicators.length === 0 ? (
                                <div className="text-center py-8">
                                    <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-white mb-2">No Bias Detected</h3>
                                    <p className="text-slate-400">The document language appears to be fair and balanced.</p>
                                </div>
                            ) : (
                                biasIndicators.map((bias, index) => (
                                    <div key={index} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                                        <div className="flex items-start justify-between mb-3">
                                            <div className="flex items-center space-x-2">
                                                <Eye className="w-5 h-5 text-yellow-400" />
                                                <h4 className="font-semibold text-white">{bias.bias_type.replace('_', ' ').toUpperCase()}</h4>
                                            </div>
                                            <span className={cn("px-2 py-1 rounded-full text-xs border", getSeverityColor(bias.severity))}>
                                                {bias.severity}
                                            </span>
                                        </div>
                                        <div className="space-y-3">
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Biased Language: </span>
                                                <span className="text-sm text-red-300 bg-red-500/20 px-2 py-1 rounded">{bias.biased_language}</span>
                                            </div>
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Suggested Alternative: </span>
                                                <span className="text-sm text-green-300 bg-green-500/20 px-2 py-1 rounded">{bias.suggested_alternative}</span>
                                            </div>
                                            <p className="text-sm text-slate-300">{bias.explanation}</p>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === 'negotiation' && (
                        <div className="space-y-4">
                            {negotiationPoints.length === 0 ? (
                                <div className="text-center py-8">
                                    <Info className="w-12 h-12 text-blue-400 mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-white mb-2">No Negotiation Points Identified</h3>
                                    <p className="text-slate-400">The document terms appear to be well-balanced.</p>
                                </div>
                            ) : (
                                negotiationPoints.map((point, index) => (
                                    <div key={index} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                                        <div className="flex items-start justify-between mb-3">
                                            <div className="flex items-center space-x-2">
                                                <MessageSquare className="w-5 h-5 text-blue-400" />
                                                <h4 className="font-semibold text-white">{point.negotiation_type.replace('_', ' ').toUpperCase()}</h4>
                                            </div>
                                            <span className={cn("px-2 py-1 rounded-full text-xs border", getSeverityColor(point.priority))}>
                                                {point.priority} priority
                                            </span>
                                        </div>
                                        <div className="space-y-3">
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Current Language: </span>
                                                <span className="text-sm text-orange-300 bg-orange-500/20 px-2 py-1 rounded">{point.current_language}</span>
                                            </div>
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Suggested Language: </span>
                                                <span className="text-sm text-green-300 bg-green-500/20 px-2 py-1 rounded">{point.suggested_language}</span>
                                            </div>
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Rationale: </span>
                                                <span className="text-sm text-slate-300">{point.rationale}</span>
                                            </div>
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Potential Impact: </span>
                                                <span className="text-sm text-slate-300">{point.potential_impact}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === 'entities' && (
                        <div className="space-y-4">
                            {entityRelationships.length === 0 ? (
                                <div className="text-center py-8">
                                    <Users className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-white mb-2">No Entity Relationships Found</h3>
                                    <p className="text-slate-400">Unable to identify significant entity relationships in this document.</p>
                                </div>
                            ) : (
                                entityRelationships.map((relationship) => (
                                    <div key={`${relationship.entity1}-${relationship.entity2}`} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                                        <div className="flex items-center space-x-2 mb-3">
                                            <Users className="w-5 h-5 text-green-400" />
                                            <h4 className="font-semibold text-white">{relationship.relationship_type.replace('_', ' ').toUpperCase()}</h4>
                                        </div>
                                        <div className="space-y-2">
                                            <div className="flex items-center space-x-2">
                                                <span className="text-sm font-medium text-slate-400">Entities: </span>
                                                <span className="text-sm text-blue-300">{relationship.entity1}</span>
                                                <span className="text-slate-400">↔</span>
                                                <span className="text-sm text-blue-300">{relationship.entity2}</span>
                                            </div>
                                            <p className="text-sm text-slate-300">{relationship.description}</p>
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Legal Significance: </span>
                                                <span className="text-sm text-slate-300">{relationship.legal_significance}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === 'compliance' && (
                        <div className="space-y-4">
                            {complianceFlags.length === 0 ? (
                                <div className="text-center py-8">
                                    <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-white mb-2">No Compliance Issues Detected</h3>
                                    <p className="text-slate-400">The document appears to comply with standard regulations.</p>
                                </div>
                            ) : (
                                complianceFlags.map((flag, index) => (
                                    <div key={index} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                                        <div className="flex items-start justify-between mb-3">
                                            <div className="flex items-center space-x-2">
                                                <Shield className="w-5 h-5 text-red-400" />
                                                <h4 className="font-semibold text-white">{flag.regulation_type.replace('_', ' ').toUpperCase()}</h4>
                                            </div>
                                            <span className={cn("px-2 py-1 rounded-full text-xs border", getSeverityColor(flag.severity))}>
                                                {flag.severity}
                                            </span>
                                        </div>
                                        <div className="space-y-3">
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Issue: </span>
                                                <span className="text-sm text-slate-300">{flag.issue_description}</span>
                                            </div>
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Compliance Risk: </span>
                                                <span className="text-sm text-red-300">{flag.compliance_risk}</span>
                                            </div>
                                            <div>
                                                <span className="text-sm font-medium text-slate-400">Recommended Action: </span>
                                                <span className="text-sm text-green-300">{flag.recommended_action}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}