/**
 * LazyImage component with Intersection Observer API for image lazy loading
 * Implements progressive image loading with WebP/AVIF support and fallbacks
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '../utils';

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
  placeholder?: string;
  blurDataURL?: string;
  priority?: boolean;
  quality?: number;
  sizes?: string;
  onLoad?: () => void;
  onError?: (error: Event) => void;
  fallbackSrc?: string;
  webpSrc?: string;
  avifSrc?: string;
  loading?: 'lazy' | 'eager';
  crossOrigin?: 'anonymous' | 'use-credentials';
  decoding?: 'async' | 'sync' | 'auto';
  referrerPolicy?: React.HTMLAttributeReferrerPolicy;
  style?: React.CSSProperties;
  threshold?: number;
  rootMargin?: string;
}

interface ImageState {
  isLoaded: boolean;
  isInView: boolean;
  hasError: boolean;
  currentSrc: string;
}

export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  className,
  width,
  height,
  placeholder,
  blurDataURL,
  priority = false,
  quality = 85,
  sizes,
  onLoad,
  onError,
  fallbackSrc,
  webpSrc,
  avifSrc,
  loading = 'lazy',
  crossOrigin,
  decoding = 'async',
  referrerPolicy,
  style,
  threshold = 0.1,
  rootMargin = '50px',
  ...props
}) => {
  const [imageState, setImageState] = useState<ImageState>({
    isLoaded: false,
    isInView: priority, // If priority, start as in view
    hasError: false,
    currentSrc: placeholder || blurDataURL || ''
  });

  const imgRef = useRef<HTMLImageElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Determine the best image source based on browser support
  const getBestImageSrc = useCallback((): string => {
    if (typeof window === 'undefined') return src;

    // Check for AVIF support
    if (avifSrc && 'createImageBitmap' in window) {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (ctx && canvas.toDataURL('image/avif').indexOf('data:image/avif') === 0) {
        return avifSrc;
      }
    }

    // Check for WebP support
    if (webpSrc) {
      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      const webpSupported = canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
      if (webpSupported) {
        return webpSrc;
      }
    }

    return src;
  }, [src, webpSrc, avifSrc]);

  // Handle image load success
  const handleImageLoad = useCallback(() => {
    setImageState(prev => ({ ...prev, isLoaded: true, hasError: false }));
    onLoad?.();
  }, [onLoad]);

  // Handle image load error with fallback
  const handleImageError = useCallback((event: Event) => {
    console.warn(`Failed to load image: ${imageState.currentSrc}`);
    
    setImageState(prev => {
      // Try fallback source if available and not already tried
      if (fallbackSrc && prev.currentSrc !== fallbackSrc) {
        return { ...prev, currentSrc: fallbackSrc, hasError: false };
      }
      
      // If no fallback or fallback also failed
      return { ...prev, hasError: true };
    });
    
    onError?.(event);
  }, [fallbackSrc, imageState.currentSrc, onError]);

  // Set up intersection observer for lazy loading
  useEffect(() => {
    if (priority || imageState.isInView) return;

    const currentImgRef = imgRef.current;
    if (!currentImgRef) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setImageState(prev => ({ ...prev, isInView: true }));
            observerRef.current?.disconnect();
          }
        });
      },
      {
        threshold,
        rootMargin
      }
    );

    observerRef.current.observe(currentImgRef);

    return () => {
      observerRef.current?.disconnect();
    };
  }, [priority, imageState.isInView, threshold, rootMargin]);

  // Update image source when in view
  useEffect(() => {
    if (imageState.isInView && !imageState.isLoaded && !imageState.hasError) {
      const bestSrc = getBestImageSrc();
      setImageState(prev => ({ ...prev, currentSrc: bestSrc }));
    }
  }, [imageState.isInView, imageState.isLoaded, imageState.hasError, getBestImageSrc]);

  // Preload image when it comes into view
  useEffect(() => {
    if (imageState.isInView && imageState.currentSrc && imageState.currentSrc !== placeholder && imageState.currentSrc !== blurDataURL) {
      const img = new Image();
      img.onload = handleImageLoad;
      img.onerror = (event) => handleImageError(event as Event);
      img.src = imageState.currentSrc;
      
      // Set additional attributes for better loading
      if (crossOrigin) img.crossOrigin = crossOrigin;
      if (decoding) img.decoding = decoding;
      if (referrerPolicy) img.referrerPolicy = referrerPolicy;
    }
  }, [imageState.isInView, imageState.currentSrc, placeholder, blurDataURL, handleImageLoad, handleImageError, crossOrigin, decoding, referrerPolicy]);

  // Generate responsive srcSet if sizes are provided
  const generateSrcSet = useCallback((baseSrc: string): string => {
    if (!sizes) return '';
    
    const widths = [320, 640, 768, 1024, 1280, 1536];
    return widths
      .map(w => `${baseSrc}?w=${w}&q=${quality} ${w}w`)
      .join(', ');
  }, [sizes, quality]);

  const imageClasses = cn(
    'transition-opacity duration-300 ease-in-out',
    {
      'opacity-0': !imageState.isLoaded && !imageState.hasError,
      'opacity-100': imageState.isLoaded || imageState.hasError,
      'blur-sm': !imageState.isLoaded && (placeholder || blurDataURL),
    },
    className
  );

  const containerStyle: React.CSSProperties = {
    ...style,
    ...(width && height ? { aspectRatio: `${width} / ${height}` } : {}),
  };

  // Show placeholder while loading
  if (!imageState.isInView && !priority) {
    return (
      <div
        ref={imgRef}
        className={cn('bg-slate-200 animate-pulse', className)}
        style={containerStyle}
        aria-label={`Loading ${alt}`}
      >
        {placeholder && (
          <img
            src={placeholder}
            alt=""
            className="w-full h-full object-cover opacity-50"
            aria-hidden="true"
          />
        )}
      </div>
    );
  }

  // Show error state
  if (imageState.hasError) {
    return (
      <div
        className={cn('bg-slate-300 flex items-center justify-center text-slate-500', className)}
        style={containerStyle}
        role="img"
        aria-label={`Failed to load ${alt}`}
      >
        <svg
          className="w-8 h-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      </div>
    );
  }

  return (
    <img
      ref={imgRef}
      src={imageState.currentSrc}
      alt={alt}
      className={imageClasses}
      width={width}
      height={height}
      loading={loading}
      decoding={decoding}
      crossOrigin={crossOrigin}
      referrerPolicy={referrerPolicy}
      sizes={sizes}
      srcSet={sizes ? generateSrcSet(imageState.currentSrc) : undefined}
      style={containerStyle}
      {...props}
    />
  );
};

// Higher-order component for lazy loading any image
export const withLazyLoading = <P extends object>(
  _Component: React.ComponentType<P & { src: string; alt: string }>
) => {
  return React.forwardRef<HTMLElement, P & LazyImageProps>((props, _ref) => {
    return <LazyImage {...props} />;
  });
};

// Hook for programmatic lazy image loading
export const useLazyImage = (src: string, options: Partial<LazyImageProps> = {}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isInView, setIsInView] = useState(options.priority || false);

  const load = useCallback(() => {
    const img = new Image();
    
    img.onload = () => {
      setIsLoaded(true);
      setHasError(false);
    };
    
    img.onerror = () => {
      setHasError(true);
      setIsLoaded(false);
    };
    
    img.src = src;
  }, [src]);

  useEffect(() => {
    if (isInView && !isLoaded && !hasError) {
      load();
    }
  }, [isInView, isLoaded, hasError, load]);

  return {
    isLoaded,
    hasError,
    isInView,
    setIsInView,
    load
  };
};

export default LazyImage;