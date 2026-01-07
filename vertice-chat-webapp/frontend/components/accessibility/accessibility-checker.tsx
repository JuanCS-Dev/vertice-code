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
          rules: {
            // Enable specific rules
            'color-contrast': { enabled: true },
            'heading-order': { enabled: true },
            'image-alt': { enabled: true },
            'link-name': { enabled: true },
            'button-name': { enabled: true },
            'aria-roles': { enabled: true },
            'aria-valid-attr': { enabled: true },
            'tabindex': { enabled: true },
          },
          // Disable noisy rules in development
          disableOtherRules: false,
        },
        (violations: any[]) => {
          // Log violations to console
          if (violations.length > 0) {
            console.group('🚨 Accessibility Violations Found');
            violations.forEach((violation, index) => {
              console.log(`${index + 1}. ${violation.help}`);
              console.log(`   Impact: ${violation.impact}`);
              console.log(`   Element: ${violation.target}`);
              console.log(`   Help: ${violation.helpUrl}`);
              console.log('---');
            });
            console.groupEnd();
          }
        }
      );

      console.log('🛡️ Accessibility checker enabled in development mode');
    }).catch((error) => {
      console.warn('Failed to load Axe accessibility checker:', error);
    });
  }, []);

  return null; // This component doesn't render anything
}