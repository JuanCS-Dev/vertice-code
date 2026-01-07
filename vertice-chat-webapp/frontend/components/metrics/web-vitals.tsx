/**
 * Web Vitals Monitoring
 *
 * Monitors Core Web Vitals and sends to analytics
 * Tracks LCP, FID, CLS, FCP, TTFB
 *
 * Reference: https://web.dev/vitals/
 */
'use client';

import { useEffect } from 'react';

declare global {
  interface Window {
    va?: (event: string, data: any) => void;
  }
}

export function WebVitalsMonitor() {
  useEffect(() => {
    // Dynamic import to avoid SSR issues
    import('web-vitals').then(({ onCLS, onFID, onLCP, onFCP, onTTFB }) => {
      const sendToAnalytics = (metric: any) => {
        // Send to Vercel Analytics if available
        if (window.va) {
          window.va('event', {
            name: metric.name,
            value: metric.value,
            delta: metric.delta,
            id: metric.id,
            rating: getRating(metric.name, metric.value),
          });
        }

        // Log in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`[WebVitals] ${metric.name}:`, {
            value: metric.value,
            delta: metric.delta,
            rating: getRating(metric.name, metric.value),
          });
        }

        // Send to custom analytics endpoint
        sendToCustomAnalytics(metric);
      };

      // Monitor all Core Web Vitals
      onCLS(sendToAnalytics);      // Cumulative Layout Shift
      onFID(sendToAnalytics);      // First Input Delay
      onLCP(sendToAnalytics);      // Largest Contentful Paint
      onFCP(sendToAnalytics);      // First Contentful Paint
      onTTFB(sendToAnalytics);     // Time to First Byte
    }).catch((error) => {
      console.warn('Failed to load web-vitals:', error);
    });
  }, []);

  return null;
}

/**
 * Get performance rating based on metric values
 *
 * Based on Google's Core Web Vitals thresholds:
 * - LCP: Good < 2.5s, Needs Improvement 2.5-4s, Poor > 4s
 * - FID: Good < 100ms, Needs Improvement 100-300ms, Poor > 300ms
 * - CLS: Good < 0.1, Needs Improvement 0.1-0.25, Poor > 0.25
 */
function getRating(metricName: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  switch (metricName) {
    case 'LCP':
      return value < 2500 ? 'good' : value < 4000 ? 'needs-improvement' : 'poor';

    case 'FID':
      return value < 100 ? 'good' : value < 300 ? 'needs-improvement' : 'poor';

    case 'CLS':
      return value < 0.1 ? 'good' : value < 0.25 ? 'needs-improvement' : 'poor';

    case 'FCP':
      return value < 1800 ? 'good' : value < 3000 ? 'needs-improvement' : 'poor';

    case 'TTFB':
      return value < 800 ? 'good' : value < 1800 ? 'needs-improvement' : 'poor';

    default:
      return 'good';
  }
}

/**
 * Send metrics to custom analytics endpoint
 */
async function sendToCustomAnalytics(metric: any) {
  try {
    // Send to backend for storage/analysis
    await fetch('/api/analytics/web-vitals', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        metric: metric.name,
        value: metric.value,
        delta: metric.delta,
        rating: getRating(metric.name, metric.value),
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      }),
    });
  } catch (error) {
    // Silently fail - don't break user experience
    console.warn('Failed to send web vitals to analytics:', error);
  }
}