/**
 * Accessibility Checker for Development
 *
 * Integrates Axe accessibility testing in development mode
 * Automatically scans for accessibility violations
 *
 * Reference: https://github.com/dequelabs/axe-core-npm/tree/develop/packages/react
 */
'use client';

import { useEffect } from 'react';

declare global {
  interface Window {
    React: typeof import('react');
    ReactDOM: typeof import('react-dom');
  }
}

export function AccessibilityChecker() {
  useEffect(() => {
    // Only run in development
    if (process.env.NODE_ENV !== 'development') {
      return;
    }

    // Dynamically import Axe to avoid SSR issues
    import('@axe-core/react').then((axe) => {
      // Initialize Axe with React and ReactDOM
      axe.default(
        window.React,
        window.ReactDOM,
        1000, // Check every 1 second
        {
          // Axe configuration
          rules: [
            // Enable specific rules
            { id: 'color-contrast', enabled: true },
            { id: 'heading-order', enabled: true },
            { id: 'image-alt', enabled: true },
            { id: 'link-name', enabled: true },
            { id: 'button-name', enabled: true },
            { id: 'aria-roles', enabled: true },
            { id: 'aria-valid-attr', enabled: true },
            { id: 'tabindex', enabled: true },
          ],
          // Disable noisy rules in development
          disableOtherRules: false,
        }
      );

      console.log('🛡️ Accessibility checker enabled in development mode');
    }).catch((error) => {
      console.warn('Failed to load Axe accessibility checker:', error);
    });
  }, []);

  return null; // This component doesn't render anything
}