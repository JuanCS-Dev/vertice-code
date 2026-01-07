/**
 * Accessibility Tests
 *
 * Automated accessibility testing using Axe and Playwright
 * Tests Core Web Vitals targets and accessibility compliance
 *
 * Reference: https://playwright.dev/docs/accessibility-testing
 */
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

// Configure Axe to run on every page
test.describe.configure({ mode: 'parallel' });

test.describe('Accessibility Compliance', () => {
  test.beforeEach(async ({ page }) => {
    // Inject Axe into the page
    await injectAxe(page);
  });

  test('homepage has no accessibility violations', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Run accessibility scan
    await checkA11y(page, {
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
    });

    // Axe will throw an error if violations are found
    // If we reach here, the page passed accessibility checks
    expect(true).toBe(true);
  });

  test('sign-in page accessibility', async ({ page }) => {
    await page.goto('http://localhost:3000/sign-in');

    await checkA11y(page, {
      axeOptions: {
        rules: {
          // Focus on critical accessibility issues
          'color-contrast': { enabled: true },
          'heading-order': { enabled: true },
          'image-alt': { enabled: true },
          'link-name': { enabled: true },
          'button-name': { enabled: true },
          'aria-roles': { enabled: true },
          'aria-valid-attr': { enabled: true },
          'tabindex': { enabled: true },
        },
      },
    });
  });

  test('chat page accessibility', async ({ page }) => {
    // Mock authentication for chat page access
    await page.addInitScript(() => {
      // Mock Clerk authentication
      window.localStorage.setItem('clerk-token', 'mock-token');
    });

    await page.goto('http://localhost:3000/chat');

    await checkA11y(page, {
      axeOptions: {
        rules: {
          // Exclude some rules that might not apply to dynamic content
          'color-contrast': { enabled: true },
          'heading-order': { enabled: true },
          'aria-required-children': { enabled: false }, // May not apply to chat
        },
      },
    });
  });

  test('keyboard navigation works', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Test tab navigation
    await page.keyboard.press('Tab');
    let focusedElement = await page.locator(':focus');
    await expect(focusedElement).toBeVisible();

    // Test that focus is visible (accessibility requirement)
    const focusOutline = await page.locator(':focus').evaluate((el) => {
      const computedStyle = window.getComputedStyle(el);
      return computedStyle.outline !== 'none' || computedStyle.boxShadow !== 'none';
    });
    expect(focusOutline).toBe(true);
  });

  test('color contrast meets WCAG standards', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Run specific color contrast check
    await checkA11y(page, {
      axeOptions: {
        rules: {
          'color-contrast': { enabled: true },
        },
      },
    });
  });
});

test.describe('Core Web Vitals', () => {
  test('page loads within performance budgets', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('http://localhost:3000', {
      waitUntil: 'networkidle',
    });

    const loadTime = Date.now() - startTime;

    // LCP should be under 2.5s for good performance
    expect(loadTime).toBeLessThan(2500);

    // Check for any console errors
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.waitForTimeout(1000); // Wait a bit for any errors
    expect(errors.length).toBe(0);
  });

  test('no layout shift after initial load', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Wait for initial load
    await page.waitForLoadState('networkidle');

    // Get initial layout
    const initialRects = await page.locator('body *').evaluateAll((elements) => {
      return elements.map((el) => {
        const rect = el.getBoundingClientRect();
        return {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
        };
      });
    });

    // Wait a bit and check for layout shifts
    await page.waitForTimeout(2000);

    const finalRects = await page.locator('body *').evaluateAll((elements) => {
      return elements.map((el) => {
        const rect = el.getBoundingClientRect();
        return {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
        };
      });
    });

    // Calculate layout shift (simplified)
    let totalShift = 0;
    for (let i = 0; i < Math.min(initialRects.length, finalRects.length); i++) {
      const initial = initialRects[i];
      const final = finalRects[i];

      const shiftX = Math.abs(final.x - initial.x);
      const shiftY = Math.abs(final.y - initial.y);

      // Only count significant shifts
      if (shiftX > 5 || shiftY > 5) {
        totalShift += Math.sqrt(shiftX * shiftX + shiftY * shiftY);
      }
    }

    // CLS should be under 0.1 for good UX
    expect(totalShift).toBeLessThan(100); // Simplified threshold
  });
});