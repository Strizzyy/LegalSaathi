/**
 * Skeleton loading components for better perceived performance
 * Provides various skeleton patterns for different UI components
 */

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../utils';

interface SkeletonProps {
  className?: string;
  animate?: boolean;
  variant?: 'pulse' | 'wave' | 'shimmer';
}

// Base skeleton component
export const Skeleton: React.FC<SkeletonProps> = ({ 
  className, 
  animate = true, 
  variant = 'pulse' 
}) => {
  const baseClasses = 'bg-slate-700 rounded';
  
  const animationClasses = {
    pulse: animate ? 'animate-pulse' : '',
    wave: animate ? 'animate-wave' : '',
    shimmer: animate ? 'animate-shimmer' : ''
  };

  return (
    <div 
      className={cn(baseClasses, animationClasses[variant], className)}
      aria-hidden="true"
    />
  );
};

// Text skeleton with multiple lines
interface TextSkeletonProps extends SkeletonProps {
  lines?: number;
  lineHeight?: string;
  lastLineWidth?: string;
}

export const TextSkeleton: React.FC<TextSkeletonProps> = ({
  lines = 3,
  lineHeight = 'h-4',
  lastLineWidth = 'w-3/4',
  className,
  animate = true,
  variant = 'pulse'
}) => {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton
          key={i}
          className={cn(
            lineHeight,
            i === lines - 1 ? lastLineWidth : 'w-full'
          )}
          animate={animate}
          variant={variant}
        />
      ))}
    </div>
  );
};

// Card skeleton for document analysis results
export const DocumentAnalysisSkeleton: React.FC<SkeletonProps> = ({ 
  className, 
  animate = true 
}) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn('bg-slate-800 rounded-lg p-6 space-y-4', className)}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-32" animate={animate} />
        <Skeleton className="h-8 w-20 rounded-full" animate={animate} />
      </div>
      
      {/* Content */}
      <div className="space-y-3">
        <TextSkeleton lines={2} animate={animate} />
        <div className="flex space-x-2">
          <Skeleton className="h-6 w-16 rounded-full" animate={animate} />
          <Skeleton className="h-6 w-20 rounded-full" animate={animate} />
        </div>
      </div>
      
      {/* Actions */}
      <div className="flex space-x-2 pt-4">
        <Skeleton className="h-8 w-24 rounded-lg" animate={animate} />
        <Skeleton className="h-8 w-20 rounded-lg" animate={animate} />
      </div>
    </motion.div>
  );
};

// Table skeleton for admin dashboard
export const TableSkeleton: React.FC<SkeletonProps & { rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4,
  className,
  animate = true
}) => {
  return (
    <div className={cn('space-y-3', className)}>
      {/* Header */}
      <div className="flex space-x-4">
        {Array.from({ length: columns }, (_, i) => (
          <Skeleton key={i} className="h-4 flex-1" animate={animate} />
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }, (_, rowIndex) => (
        <div key={rowIndex} className="flex space-x-4">
          {Array.from({ length: columns }, (_, colIndex) => (
            <Skeleton 
              key={colIndex} 
              className={cn(
                'h-8 flex-1',
                colIndex === 0 ? 'w-1/4' : colIndex === columns - 1 ? 'w-1/6' : ''
              )} 
              animate={animate} 
            />
          ))}
        </div>
      ))}
    </div>
  );
};

// Chart skeleton for analytics
export const ChartSkeleton: React.FC<SkeletonProps> = ({ 
  className, 
  animate = true 
}) => {
  return (
    <div className={cn('space-y-4', className)}>
      {/* Chart title */}
      <Skeleton className="h-6 w-48" animate={animate} />
      
      {/* Chart area */}
      <div className="relative h-64 bg-slate-800 rounded-lg p-4">
        {/* Y-axis labels */}
        <div className="absolute left-2 top-4 bottom-4 flex flex-col justify-between">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-3 w-8" animate={animate} />
          ))}
        </div>
        
        {/* Chart bars */}
        <div className="ml-12 h-full flex items-end justify-between space-x-2">
          {Array.from({ length: 7 }, (_, i) => (
            <Skeleton 
              key={i} 
              className="w-8 rounded-t"
              style={{ height: `${Math.random() * 80 + 20}%` }}
              animate={animate} 
            />
          ))}
        </div>
        
        {/* X-axis labels */}
        <div className="ml-12 mt-2 flex justify-between">
          {Array.from({ length: 7 }, (_, i) => (
            <Skeleton key={i} className="h-3 w-8" animate={animate} />
          ))}
        </div>
      </div>
    </div>
  );
};

// Navigation skeleton
export const NavigationSkeleton: React.FC<SkeletonProps> = ({ 
  className, 
  animate = true 
}) => {
  return (
    <div className={cn('flex items-center justify-between p-4', className)}>
      {/* Logo */}
      <Skeleton className="h-8 w-32" animate={animate} />
      
      {/* Navigation items */}
      <div className="flex space-x-6">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-4 w-16" animate={animate} />
        ))}
      </div>
      
      {/* User menu */}
      <Skeleton className="h-8 w-8 rounded-full" animate={animate} />
    </div>
  );
};

// Form skeleton
export const FormSkeleton: React.FC<SkeletonProps & { fields?: number }> = ({
  fields = 4,
  className,
  animate = true
}) => {
  return (
    <div className={cn('space-y-6', className)}>
      {Array.from({ length: fields }, (_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" animate={animate} />
          <Skeleton className="h-10 w-full rounded-lg" animate={animate} />
        </div>
      ))}
      
      {/* Submit button */}
      <Skeleton className="h-10 w-32 rounded-lg" animate={animate} />
    </div>
  );
};

// Image gallery skeleton
export const ImageGallerySkeleton: React.FC<SkeletonProps & { images?: number }> = ({
  images = 6,
  className,
  animate = true
}) => {
  return (
    <div className={cn('grid grid-cols-2 md:grid-cols-3 gap-4', className)}>
      {Array.from({ length: images }, (_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="aspect-square w-full rounded-lg" animate={animate} />
          <Skeleton className="h-4 w-3/4" animate={animate} />
        </div>
      ))}
    </div>
  );
};

// Dashboard widget skeleton
export const DashboardWidgetSkeleton: React.FC<SkeletonProps> = ({
  className,
  animate = true
}) => {
  return (
    <div className={cn('bg-slate-800 rounded-lg p-6 space-y-4', className)}>
      {/* Widget header */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-32" animate={animate} />
        <Skeleton className="h-4 w-4 rounded" animate={animate} />
      </div>
      
      {/* Main metric */}
      <Skeleton className="h-8 w-20" animate={animate} />
      
      {/* Trend indicator */}
      <div className="flex items-center space-x-2">
        <Skeleton className="h-4 w-4 rounded" animate={animate} />
        <Skeleton className="h-4 w-16" animate={animate} />
      </div>
      
      {/* Mini chart */}
      <div className="flex items-end space-x-1 h-8">
        {Array.from({ length: 8 }, (_, i) => (
          <Skeleton 
            key={i} 
            className="w-2 rounded-t"
            style={{ height: `${Math.random() * 100}%` }}
            animate={animate} 
          />
        ))}
      </div>
    </div>
  );
};

// Loading screen skeleton
export const LoadingScreenSkeleton: React.FC<SkeletonProps> = ({
  className,
  animate = true
}) => {
  return (
    <div className={cn('min-h-screen bg-slate-900 p-4', className)}>
      <NavigationSkeleton animate={animate} />
      
      <div className="max-w-6xl mx-auto mt-8 space-y-8">
        {/* Hero section */}
        <div className="text-center space-y-4">
          <Skeleton className="h-12 w-96 mx-auto" animate={animate} />
          <Skeleton className="h-6 w-128 mx-auto" animate={animate} />
        </div>
        
        {/* Content grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }, (_, i) => (
            <DashboardWidgetSkeleton key={i} animate={animate} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Skeleton;