/**
 * Page Transition Component
 *
 * Uses View Transitions API for smooth page changes
 * Provides smooth transitions between routes
 *
 * Reference: https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API
 */
'use client';

import { useEffect, ReactNode } from 'react';
import { usePathname } from 'next/navigation';

interface PageTransitionProps {
  children: ReactNode;
}

export function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname();

  useEffect(() => {
    // Check browser support for View Transitions API
    if (!document.startViewTransition) {
      return;
    }

    // Add CSS for smooth transitions
    const styleId = 'page-transitions-style';
    let styleElement = document.getElementById(styleId) as HTMLStyleElement;

    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = styleId;
      document.head.appendChild(styleElement);
    }

    styleElement.textContent = `
      /* View transition styles */
      ::view-transition-old(root),
      ::view-transition-new(root) {
        animation-duration: 0.4s;
        animation-timing-function: cubic-bezier(0.4, 0.0, 0.2, 1);
      }

      ::view-transition-old(root) {
        animation-name: fade-out;
      }

      ::view-transition-new(root) {
        animation-name: fade-in;
      }

      @keyframes fade-out {
        to {
          opacity: 0;
          transform: scale(0.98);
        }
      }

      @keyframes fade-in {
        from {
          opacity: 0;
          transform: scale(1.02);
        }
      }

      /* Page-specific transitions */
      .page-enter {
        opacity: 0;
        transform: translateY(20px);
        animation: page-enter 0.3s ease-out forwards;
      }

      @keyframes page-enter {
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      /* Reduce motion for accessibility */
      @media (prefers-reduced-motion: reduce) {
        ::view-transition-old(root),
        ::view-transition-new(root) {
          animation-duration: 0.1s;
        }

        .page-enter {
          animation-duration: 0.1s;
        }
      }
    `;

    return () => {
      // Cleanup on unmount
      if (styleElement && document.head.contains(styleElement)) {
        document.head.removeChild(styleElement);
      }
    };
  }, []);

  return (
    <div
      key={pathname}
      className="page-enter"
      style={{
        minHeight: '100vh',
        width: '100%',
      }}
    >
      {children}
    </div>
  );
}
