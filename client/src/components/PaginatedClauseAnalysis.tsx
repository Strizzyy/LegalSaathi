import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, 
  ChevronRight, 
  Filter, 
  Search, 
  SortAsc,
  Loader2,
  AlertTriangle,
  FileText,
  Info,
  MessageCircle,
  Users,
  Activity
} from 'lucide-react';
import { cn, formatPercentage } from '../utils';
import { ClauseTranslationButton } from './ClauseTranslationButton';
import { ClauseSummary } from './ClauseSummary';
import { DetailedClauseAnalysis } from './DetailedClauseAnalysis';
import type { ClauseContext } from '../types/chat';

interface PaginatedClauseAnalysisProps {
  analysisId: string;
  onOpenChat: (clauseContext?: ClauseContext) => void;
  onOpenHumanSupport: (clauseContext?: ClauseContext) => void;
  className?: string;
}

interface ClauseData {
  clause_id: string;
  clause_text: string;
  risk_level: string;
  risk_score: number;
  severity: string;
  confidence_percentage: number;
  reasons: string[];
  plain_explanation: string;
  legal_implications: string[];
  recommendations: string[];
  risk_categories: Record<string, number>;
}

interface PaginationResponse {
  clauses: ClauseData[];
  total_clauses: number;
  filtered_clauses: number;
  current_page: number;
  page_size: number;
  total_pages: number;
  has_more: boolean;
  has_previous: boolean;
  filters_applied: Record<string, any>;
  sort_criteria: string;
  analysis_id: string;
  pagination_info: {
    showing_start: number;
    showing_end: number;
    showing_total: number;
  };
}

interface SearchResult extends ClauseData {
  matches: Array<{
    field: string;
    match_count: number;
    snippet: string;
  }>;
  total_matches: number;
  relevance_score: number;
}

interface SearchResponse {
  search_query: string;
  search_fields: string[];
  results: SearchResult[];
  total_matches: number;
  total_clauses_searched: number;
  analysis_id: string;
  search_summary: {
    high_risk_matches: number;
    medium_risk_matches: number;
    low_risk_matches: number;
    avg_relevance_score: number;
  };
}

export function PaginatedClauseAnalysis({ 
  analysisId, 
  onOpenChat, 
  onOpenHumanSupport, 
  className = '' 
}: PaginatedClauseAnalysisProps) {
  const [clauses, setClauses] = useState<ClauseData[]>([]);
  const [pagination, setPagination] = useState<PaginationResponse | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // UI State
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [riskFilter, setRiskFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState('risk_score');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [expandedClauses, setExpandedClauses] = useState<Set<string>>(new Set());

  // Load clauses with pagination
  const loadClauses = async (page: number = currentPage) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy
      });
      
      if (riskFilter) {
        params.append('risk_filter', riskFilter.toLowerCase());
      }
      
      const response = await fetch(`/api/analysis/${analysisId}/clauses?${params}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load clauses: ${response.statusText}`);
      }
      
      const data: PaginationResponse = await response.json();
      setPagination(data);
      setClauses(data.clauses);
      setCurrentPage(data.current_page);
      
    } catch (err) {
      console.error('Error loading clauses:', err);
      setError(err instanceof Error ? err.message : 'Failed to load clauses');
    } finally {
      setIsLoading(false);
    }
  };

  // Search clauses
  const searchClauses = async (query: string) => {
    if (!query.trim()) {
      setIsSearchMode(false);
      setSearchResults(null);
      loadClauses(1);
      return;
    }

    setIsSearching(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        q: query.trim()
      });
      
      const response = await fetch(`/api/analysis/${analysisId}/search?${params}`);
      
      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }
      
      const data: SearchResponse = await response.json();
      setSearchResults(data);
      setIsSearchMode(true);
      
    } catch (err) {
      console.error('Error searching clauses:', err);
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadClauses(1);
  }, [analysisId, pageSize, riskFilter, sortBy]);

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    loadClauses(newPage);
  };

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    searchClauses(searchQuery);
  };

  // Clear search
  const clearSearch = () => {
    setSearchQuery('');
    setIsSearchMode(false);
    setSearchResults(null);
    loadClauses(1);
  };

  // Toggle clause expansion
  const toggleClause = (clauseId: string) => {
    const newExpanded = new Set(expandedClauses);
    if (newExpanded.has(clauseId)) {
      newExpanded.delete(clauseId);
    } else {
      newExpanded.add(clauseId);
    }
    setExpandedClauses(newExpanded);
  };

  // Helper to get severity from clause
  const getClauseSeverity = (clause: ClauseData | SearchResult): string => {
    if ('severity' in clause && clause.severity) {
      return clause.severity;
    }
    // Fallback based on risk level
    const riskLevel = clause.risk_level;
    if (riskLevel === 'RED') return 'high';
    if (riskLevel === 'YELLOW') return 'moderate';
    return 'low';
  };

  // Helper to safely get clause properties
  const getClauseProperty = (clause: ClauseData | SearchResult, property: keyof ClauseData, fallback: any): any => {
    if (property in clause) {
      return (clause as any)[property] || fallback;
    }
    return fallback;
  };

  // Create clause context for chat
  const createClauseContext = (clause: ClauseData | SearchResult): ClauseContext => ({
    clauseId: clause.clause_id,
    text: clause.clause_text,
    riskLevel: clause.risk_level as 'RED' | 'YELLOW' | 'GREEN',
    riskScore: clause.risk_score,
    confidencePercentage: clause.confidence_percentage,
    explanation: clause.plain_explanation,
    implications: getClauseProperty(clause, 'legal_implications', []),
    recommendations: getClauseProperty(clause, 'recommendations', []),
    riskCategories: getClauseProperty(clause, 'risk_categories', {})
  });

  // Get display data (search results or paginated clauses)
  const displayData: (ClauseData | SearchResult)[] = isSearchMode ? searchResults?.results || [] : clauses;
  const isDisplayingSearchResults = isSearchMode && searchResults;

  if (error) {
    return (
      <div className={`bg-red-500/10 border border-red-500/30 rounded-2xl p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <h3 className="text-lg font-semibold text-red-400">Error Loading Clauses</h3>
        </div>
        <p className="text-red-300 mb-4">{error}</p>
        <button
          onClick={() => loadClauses(1)}
          className="px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/50 rounded-lg hover:bg-red-500/30 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl p-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-6 space-y-4 lg:space-y-0">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            {isDisplayingSearchResults ? 'Search Results' : 'Detailed Clause Analysis'}
          </h2>
          <p className="text-slate-400">
            {isDisplayingSearchResults 
              ? `${searchResults.total_matches} matches found for "${searchResults.search_query}"`
              : `Each clause analyzed for risk level and plain language explanation`
            }
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex items-center space-x-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search clauses..."
                className="pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:border-cyan-500 focus:outline-none w-48"
              />
            </div>
            <button
              type="submit"
              disabled={isSearching}
              className="px-3 py-2 bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 rounded-lg hover:bg-cyan-500/30 transition-colors disabled:opacity-50"
            >
              {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </button>
            {isSearchMode && (
              <button
                onClick={clearSearch}
                className="px-3 py-2 bg-slate-600 text-slate-300 border border-slate-600 rounded-lg hover:bg-slate-500 transition-colors"
              >
                Clear
              </button>
            )}
          </form>

          {/* Filters (only show when not in search mode) */}
          {!isSearchMode && (
            <>
              {/* Risk Filter */}
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-slate-400" />
                <select
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                  className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:border-cyan-500 focus:outline-none"
                >
                  <option value="">All Risk Levels</option>
                  <option value="red">High Risk</option>
                  <option value="yellow">Medium Risk</option>
                  <option value="green">Low Risk</option>
                </select>
              </div>

              {/* Sort */}
              <div className="flex items-center space-x-2">
                <SortAsc className="w-4 h-4 text-slate-400" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:border-cyan-500 focus:outline-none"
                >
                  <option value="risk_score">Risk Score</option>
                  <option value="risk_level">Risk Level</option>
                  <option value="confidence">Confidence</option>
                  <option value="clause_id">Clause Order</option>
                </select>
              </div>

              {/* Page Size */}
              <div className="flex items-center space-x-2">
                <span className="text-sm text-slate-400">Show:</span>
                <select
                  value={pageSize}
                  onChange={(e) => setPageSize(Number(e.target.value))}
                  className="px-2 py-1 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:border-cyan-500 focus:outline-none"
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Stats */}
      {!isSearchMode && pagination && (
        <div className="flex items-center justify-between mb-6 p-4 bg-slate-700/30 rounded-lg">
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full" />
              <span className="text-slate-300">High Risk: {pagination.total_clauses - pagination.filtered_clauses + displayData.filter(c => c.risk_level === 'RED').length}</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full" />
              <span className="text-slate-300">Medium: {displayData.filter(c => c.risk_level === 'YELLOW').length}</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-slate-300">Low Risk: {displayData.filter(c => c.risk_level === 'GREEN').length}</span>
            </div>
          </div>
          <div className="text-sm text-slate-400">
            Showing {pagination.pagination_info.showing_start}-{pagination.pagination_info.showing_end} of {pagination.pagination_info.showing_total}
          </div>
        </div>
      )}

      {/* Search Stats */}
      {isDisplayingSearchResults && (
        <div className="flex items-center justify-between mb-6 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full" />
              <span className="text-slate-300">High Risk: {searchResults.search_summary.high_risk_matches}</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full" />
              <span className="text-slate-300">Medium: {searchResults.search_summary.medium_risk_matches}</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-slate-300">Low Risk: {searchResults.search_summary.low_risk_matches}</span>
            </div>
          </div>
          <div className="text-sm text-slate-400">
            Avg Relevance: {searchResults.search_summary.avg_relevance_score.toFixed(1)}
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
            <span className="text-slate-300">Loading clauses...</span>
          </div>
        </div>
      )}

      {/* Clauses */}
      {!isLoading && (
        <div className="space-y-6">
          <AnimatePresence>
            {displayData.map((clause, index) => (
              <motion.div
                key={`${clause.clause_id}_${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className={cn(
                  "clause-analysis-item border-2 rounded-xl p-6",
                  clause.risk_level === 'RED' ? "border-red-500/50 bg-red-500/5" :
                  clause.risk_level === 'YELLOW' ? "border-yellow-500/50 bg-yellow-500/5" :
                  "border-green-500/50 bg-green-500/5"
                )}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className={cn(
                      "w-4 h-4 rounded-full",
                      clause.risk_level === 'RED' ? "bg-red-500" :
                      clause.risk_level === 'YELLOW' ? "bg-yellow-500" :
                      "bg-green-500"
                    )} />
                    <div>
                      <h3 className="text-lg font-bold text-white">Clause {clause.clause_id}</h3>
                      <p className="text-slate-400 text-sm">
                        {getClauseSeverity(clause).charAt(0).toUpperCase() + getClauseSeverity(clause).slice(1)} Risk
                        {isDisplayingSearchResults && 'total_matches' in clause && (
                          <span className="ml-2 px-2 py-1 bg-cyan-500/20 text-cyan-400 rounded text-xs">
                            {clause.total_matches} matches
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className={cn(
                      "px-4 py-2 rounded-lg border text-sm font-bold mb-1",
                      clause.risk_level === 'RED' ? "bg-red-500/20 border-red-500/50 text-red-400" :
                      clause.risk_level === 'YELLOW' ? "bg-yellow-500/20 border-yellow-500/50 text-yellow-400" :
                      "bg-green-500/20 border-green-500/50 text-green-400"
                    )}>
                      {clause.risk_level} RISK
                    </div>
                    <div className="text-xs text-slate-400">
                      Score: {formatPercentage(clause.risk_score)} | Confidence: {clause.confidence_percentage}%
                    </div>
                  </div>
                </div>

                {/* Confidence Bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-300 flex items-center">
                      <Activity className="w-4 h-4 mr-1" />
                      AI Confidence:
                    </span>
                    <span className="text-sm text-slate-400">{clause.confidence_percentage}%</span>
                  </div>
                  <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                    <div 
                      className={cn(
                        "h-full rounded-full transition-all duration-500",
                        clause.confidence_percentage >= 80 ? "bg-green-400" :
                        clause.confidence_percentage >= 60 ? "bg-yellow-400" : "bg-red-400"
                      )}
                      style={{ width: `${clause.confidence_percentage}%` }}
                    />
                  </div>
                </div>

                {/* Search Matches (if in search mode) */}
                {isDisplayingSearchResults && 'matches' in clause && (
                  <div className="mb-4 p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                    <h4 className="text-sm font-semibold text-cyan-400 mb-2">Search Matches:</h4>
                    {clause.matches.map((match, idx) => (
                      <div key={idx} className="text-xs text-slate-300 mb-1">
                        <span className="text-cyan-400 capitalize">{match.field.replace('_', ' ')}:</span> {match.snippet}
                      </div>
                    ))}
                  </div>
                )}

                {/* Clause Text */}
                <div className="bg-slate-700/50 rounded-xl p-4 mb-4 border border-slate-600">
                  <h4 className="font-semibold text-white mb-2 flex items-center">
                    <FileText className="w-4 h-4 mr-2" />
                    Original Clause Text:
                  </h4>
                  <p className="text-slate-300 text-sm leading-relaxed font-mono bg-slate-800/50 p-3 rounded border border-slate-600">
                    {clause.clause_text}
                  </p>
                </div>

                {/* Explanation */}
                <div className={cn(
                  "rounded-xl p-4 mb-4 border",
                  clause.risk_level === 'RED' ? "bg-red-500/10 border-red-500/30" :
                  clause.risk_level === 'YELLOW' ? "bg-yellow-500/10 border-yellow-500/30" :
                  "bg-green-500/10 border-green-500/30"
                )}>
                  <h4 className="font-semibold text-white mb-2 flex items-center">
                    <Info className="w-4 h-4 mr-2" />
                    What This Means:
                  </h4>
                  <p className="text-slate-200">{clause.plain_explanation}</p>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap items-center gap-3 mb-4">
                  <ClauseTranslationButton 
                    clauseData={{
                      id: clause.clause_id,
                      text: clause.clause_text,
                      index: index
                    }}
                  />
                  <ClauseSummary 
                    clauseId={`${clause.clause_id}_${index}`}
                    clauseData={{
                      risk_level: {
                        level: clause.risk_level as 'RED' | 'YELLOW' | 'GREEN',
                        severity: getClauseSeverity(clause)
                      }
                    }}
                  />
                  
                  <button
                    onClick={() => onOpenChat(createClauseContext(clause))}
                    className="inline-flex items-center px-3 py-1.5 bg-purple-500/20 text-purple-400 border border-purple-500/50 rounded-lg hover:bg-purple-500/30 transition-colors text-sm"
                  >
                    <MessageCircle className="w-3 h-3 mr-1.5" />
                    Ask AI
                  </button>
                  
                  <button
                    onClick={() => onOpenHumanSupport(createClauseContext(clause))}
                    className="inline-flex items-center px-3 py-1.5 bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 rounded-lg hover:bg-cyan-500/30 transition-colors text-sm"
                  >
                    <Users className="w-3 h-3 mr-1.5" />
                    Expert Help
                  </button>
                </div>

                {/* Detailed Analysis */}
                <DetailedClauseAnalysis 
                  clause={{
                    clause_text: clause.clause_text,
                    risk_level: {
                      level: clause.risk_level as 'RED' | 'YELLOW' | 'GREEN',
                      severity: getClauseSeverity(clause),
                      confidence_percentage: clause.confidence_percentage,
                    },
                    plain_explanation: clause.plain_explanation,
                    legal_implications: getClauseProperty(clause, 'legal_implications', []),
                    recommendations: getClauseProperty(clause, 'recommendations', [])
                  }}
                  isExpanded={expandedClauses.has(clause.clause_id)}
                  onToggle={() => toggleClause(clause.clause_id)}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Pagination (only show when not in search mode) */}
      {!isSearchMode && pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-700">
          <div className="text-sm text-slate-400">
            Page {pagination.current_page} of {pagination.total_pages}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handlePageChange(pagination.current_page - 1)}
              disabled={!pagination.has_previous}
              className="inline-flex items-center px-3 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </button>
            
            {/* Page Numbers */}
            <div className="flex items-center space-x-1">
              {Array.from({ length: Math.min(5, pagination.total_pages) }, (_, i) => {
                const pageNum = Math.max(1, pagination.current_page - 2) + i;
                if (pageNum > pagination.total_pages) return null;
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    className={cn(
                      "px-3 py-2 rounded-lg transition-colors",
                      pageNum === pagination.current_page
                        ? "bg-cyan-500 text-white"
                        : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                    )}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={() => handlePageChange(pagination.current_page + 1)}
              disabled={!pagination.has_more}
              className="inline-flex items-center px-3 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && displayData.length === 0 && (
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">
            {isSearchMode ? 'No Search Results' : 'No Clauses Found'}
          </h3>
          <p className="text-slate-400">
            {isSearchMode 
              ? `No clauses match your search for "${searchQuery}"`
              : 'No clauses match the current filters'
            }
          </p>
          {isSearchMode && (
            <button
              onClick={clearSearch}
              className="mt-4 px-4 py-2 bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 rounded-lg hover:bg-cyan-500/30 transition-colors"
            >
              Clear Search
            </button>
          )}
        </div>
      )}
    </div>
  );
}