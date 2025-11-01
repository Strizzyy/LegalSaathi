/**
 * Progressive loading component for document analysis results with pagination and virtual scrolling
 * Implements progressive enhancement for large datasets
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Loader2, RefreshCw } from 'lucide-react';
import { cn } from '../utils';

interface ProgressiveLoaderProps<T> {
  data: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  itemHeight?: number;
  containerHeight?: number;
  pageSize?: number;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  className?: string;
  onLoadMore?: (page: number) => Promise<T[]>;
  hasMore?: boolean;
  loading?: boolean;
  error?: string | null;
  enableVirtualScrolling?: boolean;
  enablePagination?: boolean;
  searchQuery?: string;
  filterFn?: (item: T, query: string) => boolean;
  sortFn?: (a: T, b: T) => number;
}

interface VirtualScrollState {
  startIndex: number;
  endIndex: number;
  scrollTop: number;
}

export function ProgressiveLoader<T>({
  data,
  renderItem,
  itemHeight = 100,
  containerHeight = 400,
  pageSize = 10,
  loadingComponent,
  errorComponent,
  emptyComponent,
  className,
  onLoadMore,
  hasMore = false,
  loading = false,
  error = null,
  enableVirtualScrolling = true,
  enablePagination = true,
  searchQuery = '',
  filterFn,
  sortFn,
}: ProgressiveLoaderProps<T>) {
  const [currentPage, setCurrentPage] = useState(0);
  const [virtualState, setVirtualState] = useState<VirtualScrollState>({
    startIndex: 0,
    endIndex: Math.ceil(containerHeight / itemHeight),
    scrollTop: 0,
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  // Process data with filtering and sorting
  const processedData = useMemo(() => {
    let result = [...data];

    // Apply filtering
    if (searchQuery && filterFn) {
      result = result.filter(item => filterFn(item, searchQuery));
    }

    // Apply sorting
    if (sortFn) {
      result = result.sort(sortFn);
    }

    return result;
  }, [data, searchQuery, filterFn, sortFn]);

  // Calculate pagination
  const totalPages = Math.ceil(processedData.length / pageSize);
  const paginatedData = enablePagination
    ? processedData.slice(currentPage * pageSize, (currentPage + 1) * pageSize)
    : processedData;

  // Calculate virtual scrolling
  const visibleData = useMemo(() => {
    if (!enableVirtualScrolling) return paginatedData;

    const { startIndex, endIndex } = virtualState;
    return paginatedData.slice(startIndex, Math.min(endIndex, paginatedData.length));
  }, [paginatedData, virtualState, enableVirtualScrolling]);

  // Handle scroll for virtual scrolling
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    if (!enableVirtualScrolling) return;

    const scrollTop = e.currentTarget.scrollTop;
    const startIndex = Math.floor(scrollTop / itemHeight);
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    const endIndex = startIndex + visibleCount + 5; // Buffer for smooth scrolling

    setVirtualState({
      startIndex,
      endIndex,
      scrollTop,
    });
  }, [itemHeight, containerHeight, enableVirtualScrolling]);

  // Load more data when reaching the end
  const handleLoadMore = useCallback(async () => {
    if (onLoadMore && hasMore && !loading) {
      try {
        await onLoadMore(currentPage + 1);
      } catch (error) {
        console.error('Failed to load more data:', error);
      }
    }
  }, [onLoadMore, hasMore, loading, currentPage]);

  // Auto-load more when scrolling near the end
  useEffect(() => {
    if (!enableVirtualScrolling || !hasMore || loading) return;

    const { scrollTop } = virtualState;
    const totalHeight = paginatedData.length * itemHeight;
    const scrollPercentage = (scrollTop + containerHeight) / totalHeight;

    if (scrollPercentage > 0.8) {
      handleLoadMore();
    }
  }, [virtualState, paginatedData.length, itemHeight, containerHeight, hasMore, loading, handleLoadMore, enableVirtualScrolling]);

  // Pagination handlers
  const handlePreviousPage = useCallback(() => {
    if (currentPage > 0) {
      setCurrentPage(prev => prev - 1);
      setVirtualState({ startIndex: 0, endIndex: Math.ceil(containerHeight / itemHeight), scrollTop: 0 });
    }
  }, [currentPage, containerHeight, itemHeight]);

  const handleNextPage = useCallback(() => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(prev => prev + 1);
      setVirtualState({ startIndex: 0, endIndex: Math.ceil(containerHeight / itemHeight), scrollTop: 0 });
    }
  }, [currentPage, totalPages, containerHeight, itemHeight]);

  const handlePageSelect = useCallback((page: number) => {
    setCurrentPage(page);
    setVirtualState({ startIndex: 0, endIndex: Math.ceil(containerHeight / itemHeight), scrollTop: 0 });
  }, [containerHeight, itemHeight]);

  // Loading state
  if (loading && processedData.length === 0) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        {loadingComponent || (
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-cyan-400 mx-auto mb-2" />
            <p className="text-slate-300">Loading data...</p>
          </div>
        )}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        {errorComponent || (
          <div className="text-center">
            <div className="text-red-400 mb-2">⚠️ Error loading data</div>
            <p className="text-slate-300 text-sm">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              <RefreshCw className="w-4 h-4 inline mr-2" />
              Retry
            </button>
          </div>
        )}
      </div>
    );
  }

  // Empty state
  if (processedData.length === 0) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        {emptyComponent || (
          <div className="text-center text-slate-400">
            <p>No data available</p>
            {searchQuery && <p className="text-sm mt-1">Try adjusting your search criteria</p>}
          </div>
        )}
      </div>
    );
  }

  const totalHeight = enableVirtualScrolling ? paginatedData.length * itemHeight : 'auto';
  const offsetY = enableVirtualScrolling ? virtualState.startIndex * itemHeight : 0;

  return (
    <div className={cn('relative', className)}>
      {/* Virtual scroll container */}
      <div
        ref={containerRef}
        className="overflow-auto"
        style={{ height: containerHeight }}
        onScroll={handleScroll}
      >
        <div
          ref={scrollElementRef}
          style={{
            height: totalHeight,
            position: 'relative',
          }}
        >
          <div
            style={{
              transform: `translateY(${offsetY}px)`,
              position: enableVirtualScrolling ? 'absolute' : 'relative',
              top: 0,
              left: 0,
              right: 0,
            }}
          >
            <AnimatePresence mode="popLayout">
              {visibleData.map((item, index) => {
                const actualIndex = enableVirtualScrolling
                  ? virtualState.startIndex + index
                  : currentPage * pageSize + index;

                return (
                  <motion.div
                    key={actualIndex}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.2, delay: index * 0.05 }}
                    style={{
                      height: enableVirtualScrolling ? itemHeight : 'auto',
                      minHeight: enableVirtualScrolling ? itemHeight : undefined,
                    }}
                  >
                    {renderItem(item, actualIndex)}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Loading more indicator */}
      {loading && processedData.length > 0 && (
        <div className="flex items-center justify-center p-4 border-t border-slate-700">
          <Loader2 className="w-4 h-4 animate-spin text-cyan-400 mr-2" />
          <span className="text-slate-300 text-sm">Loading more...</span>
        </div>
      )}

      {/* Pagination controls */}
      {enablePagination && totalPages > 1 && (
        <div className="flex items-center justify-between p-4 border-t border-slate-700">
          <div className="flex items-center space-x-2">
            <button
              onClick={handlePreviousPage}
              disabled={currentPage === 0}
              className={cn(
                'p-2 rounded-lg transition-colors',
                currentPage === 0
                  ? 'text-slate-500 cursor-not-allowed'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700'
              )}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <div className="flex items-center space-x-1">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i;
                } else if (currentPage < 3) {
                  pageNum = i;
                } else if (currentPage > totalPages - 4) {
                  pageNum = totalPages - 5 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageSelect(pageNum)}
                    className={cn(
                      'px-3 py-1 rounded text-sm transition-colors',
                      pageNum === currentPage
                        ? 'bg-cyan-500 text-white'
                        : 'text-slate-300 hover:text-white hover:bg-slate-700'
                    )}
                  >
                    {pageNum + 1}
                  </button>
                );
              })}
            </div>

            <button
              onClick={handleNextPage}
              disabled={currentPage === totalPages - 1}
              className={cn(
                'p-2 rounded-lg transition-colors',
                currentPage === totalPages - 1
                  ? 'text-slate-500 cursor-not-allowed'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700'
              )}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="text-sm text-slate-400">
            Page {currentPage + 1} of {totalPages} ({processedData.length} items)
          </div>
        </div>
      )}
    </div>
  );
}

export default ProgressiveLoader;