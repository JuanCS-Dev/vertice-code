/**
 * E2E tests for Chat functionality
 *
 * Testing framework: Playwright
 * Reference: https://playwright.dev/
 */
import { test, expect } from '@playwright/test';

test.describe('Chat Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication for testing
    await page.addInitScript(() => {
      // Mock Clerk authentication
      window.localStorage.setItem('clerk-token', 'mock-token');
    });

    await page.goto('http://localhost:3000/chat');
  });

  test('sends a message and receives response', async ({ page }) => {
    // Type message
    await page.fill('input[placeholder="Digite sua mensagem..."]', 'Hello!');

    // Send
    await page.click('button:has-text("Send")');

    // Wait for assistant response
    await page.waitForSelector('text=/Olá|Hello/', { timeout: 10000 });

    // Verify message appears
    const messages = await page.locator('[data-testid="message"]').count();
    expect(messages).toBeGreaterThanOrEqual(2); // User + Assistant
  });

  test('creates an artifact', async ({ page }) => {
    // Send code request
    await page.fill('input[placeholder="Digite sua mensagem..."]', 'Write a function that adds two numbers');
    await page.click('button:has-text("Send")');

    // Wait for artifact
    await page.waitForSelector('[data-testid="artifact"]', { timeout: 15000 });

    // Verify artifact content
    const artifact = page.locator('[data-testid="artifact"]');
    expect(await artifact.textContent()).toContain('function');
  });

  test('uses slash commands', async ({ page }) => {
    // Type help command
    await page.fill('input[placeholder="Digite sua mensagem..."]', '/help');

    // Send
    await page.click('button:has-text("Send")');

    // Wait for help response
    await page.waitForSelector('text=/Available commands|Comandos disponíveis/', { timeout: 5000 });

    // Verify help content
    const messages = await page.locator('[data-testid="message"]').count();
    expect(messages).toBeGreaterThanOrEqual(2);
  });

  test('switches between chat and artifacts view', async ({ page }) => {
    // Start in chat view
    await expect(page.locator('h1')).toContainText('Vertice Chat');

    // Switch to artifacts
    await page.click('button:has-text("Artifacts")');

    // Verify artifacts view
    await expect(page.locator('h1')).toContainText('Artifacts');

    // Switch back to chat
    await page.click('button:has-text("Chat")');

    // Verify chat view
    await expect(page.locator('h1')).toContainText('Vertice Chat');
  });

  test('voice input button is present', async ({ page }) => {
    // Check voice input button exists
    const voiceButton = page.locator('button:has-text("Record")');
    await expect(voiceButton).toBeVisible();
  });

  test('keyboard shortcuts work', async ({ page }) => {
    // Focus input
    await page.focus('input[placeholder="Digite sua mensagem..."]');

    // Type message
    await page.fill('input[placeholder="Digite sua mensagem..."]', 'Test message');

    // Send with Ctrl+Enter (or Cmd+Enter on Mac)
    await page.keyboard.press('Control+Enter');

    // Wait for response
    await page.waitForSelector('text=/Test message/', { timeout: 5000 });
  });

  test('handles long messages', async ({ page }) => {
    const longMessage = 'A'.repeat(1000);

    // Type long message
    await page.fill('input[placeholder="Digite sua mensagem..."]', longMessage);

    // Send
    await page.click('button:has-text("Send")');

    // Wait for response
    await page.waitForSelector(`text=/${longMessage.slice(0, 50)}/`, { timeout: 10000 });
  });
});

test.describe('GitHub Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('clerk-token', 'mock-token');
    });

    await page.goto('http://localhost:3000/chat');
  });

  test('can access GitHub browser', async ({ page }) => {
    // Switch to GitHub view
    await page.click('button:has-text("GitHub")');

    // Verify GitHub browser loads
    await expect(page.locator('h1')).toContainText('GitHub Explorer');

    // Check for search input
    const searchInput = page.locator('input[placeholder*="search"]');
    await expect(searchInput).toBeVisible();
  });

  test('GitHub search works', async ({ page }) => {
    // Switch to GitHub view
    await page.click('button:has-text("GitHub")');

    // Type search query
    await page.fill('input[placeholder*="search"]', 'react');

    // Click search
    await page.click('button:has-text("Search")');

    // Wait for results (mocked in tests)
    await page.waitForSelector('text=/No repositories found|Found/', { timeout: 5000 });
  });
});

test.describe('Authentication Flow', () => {
  test('redirects to sign-in when not authenticated', async ({ page }) => {
    // Clear any mock authentication
    await page.evaluate(() => {
      window.localStorage.clear();
    });

    await page.goto('http://localhost:3000/chat');

    // Should redirect to sign-in
    await page.waitForURL('**/sign-in', { timeout: 5000 });
    expect(page.url()).toContain('/sign-in');
  });

  test('shows landing page for unauthenticated users', async ({ page }) => {
    await page.evaluate(() => {
      window.localStorage.clear();
    });

    await page.goto('http://localhost:3000');

    // Should show landing page
    await expect(page.locator('h1')).toContainText('Code with AI Agents');
    await expect(page.locator('button:has-text("Get Started")')).toBeVisible();
  });
});