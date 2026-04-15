import { test, expect } from '@playwright/test';

test.describe('Enhanced Cognitive Features', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for the application to load
    await page.waitForSelector('[data-testid="app-container"]', { timeout: 10000 });
    
    // Wait for WebSocket connection (if any)
    await page.waitForTimeout(2000);
  });

  test('should load the application successfully', async ({ page }) => {
    // Check if the main application container is present
    await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    
    // Check if the sidebar navigation is present
    await expect(page.locator('[data-testid="sidebar-nav"]')).toBeVisible();
    
    // Check if the main content area is present
    await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
  });

  test('should display enhanced cognition section with NEW badge', async ({ page }) => {
    // Look for the Enhanced Cognition section
    const enhancedSection = page.locator('[data-testid="nav-section-enhanced"]');
    await expect(enhancedSection).toBeVisible();
    
    // Check for the NEW badge
    const newBadge = enhancedSection.locator('.badge', { hasText: 'NEW' });
    await expect(newBadge).toBeVisible();
    
    // Check for the rocket icon
    await expect(enhancedSection.locator('text=🚀')).toBeVisible();
    
    // Check for the section title
    await expect(enhancedSection.locator('text=Enhanced Cognition')).toBeVisible();
  });

  test('should navigate to Enhanced Dashboard', async ({ page }) => {
    // Click on Enhanced Dashboard
    await page.click('[data-testid="nav-item-enhanced"]');
    
    // Wait for navigation
    await page.waitForTimeout(1000);
    
    // Check if the Enhanced Dashboard component is loaded
    await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
    
    // Check for featured indicator
    const enhancedNavItem = page.locator('[data-testid="nav-item-enhanced"]');
    await expect(enhancedNavItem.locator('.featured')).toBeVisible();
  });

  test('should navigate to Stream of Consciousness', async ({ page }) => {
    // Click on Stream of Consciousness
    await page.click('[data-testid="nav-item-stream"]');
    
    // Wait for navigation
    await page.waitForTimeout(1000);
    
    // Check if the Stream of Consciousness component is loaded
    await expect(page.locator('[data-testid="stream-of-consciousness-monitor"]')).toBeVisible();
    
    // Check for the wave icon
    await expect(page.locator('[data-testid="nav-item-stream"] text=🌊')).toBeVisible();
    
    // Check for featured indicator
    const streamNavItem = page.locator('[data-testid="nav-item-stream"]');
    await expect(streamNavItem.locator('.featured')).toBeVisible();
  });

  test('should navigate to Autonomous Learning', async ({ page }) => {
    // Click on Autonomous Learning
    await page.click('[data-testid="nav-item-autonomous"]');
    
    // Wait for navigation
    await page.waitForTimeout(1000);
    
    // Check if the Autonomous Learning component is loaded
    await expect(page.locator('[data-testid="autonomous-learning-monitor"]')).toBeVisible();
    
    // Check for the robot icon
    await expect(page.locator('[data-testid="nav-item-autonomous"] text=🤖')).toBeVisible();
    
    // Check for featured indicator
    const autonomousNavItem = page.locator('[data-testid="nav-item-autonomous"]');
    await expect(autonomousNavItem.locator('.featured')).toBeVisible();
  });

  test('should display all navigation sections', async ({ page }) => {
    // Core Features section
    await expect(page.locator('[data-testid="nav-section-core"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-section-core"] text=Core Features')).toBeVisible();
    
    // Enhanced Cognition section
    await expect(page.locator('[data-testid="nav-section-enhanced"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-section-enhanced"] text=Enhanced Cognition')).toBeVisible();
    
    // Analysis & Tools section
    await expect(page.locator('[data-testid="nav-section-analysis"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-section-analysis"] text=Analysis & Tools')).toBeVisible();
    
    // System Management section
    await expect(page.locator('[data-testid="nav-section-system"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-section-system"] text=System Management')).toBeVisible();
  });

  test('should navigate through core features', async ({ page }) => {
    // Test Dashboard navigation
    await page.click('[data-testid="nav-item-dashboard"]');
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="dashboard-view"]')).toBeVisible();
    
    // Test Cognitive State navigation
    await page.click('[data-testid="nav-item-cognitive"]');
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="cognitive-state-monitor"]')).toBeVisible();
    
    // Test Knowledge Graph navigation
    await page.click('[data-testid="nav-item-knowledge"]');
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="knowledge-graph"]')).toBeVisible();
    
    // Test Query Interface navigation
    await page.click('[data-testid="nav-item-query"]');
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="query-interface"]')).toBeVisible();
  });

  test('should test sidebar collapse functionality', async ({ page }) => {
    // Check if sidebar toggle button exists
    const sidebarToggle = page.locator('[data-testid="sidebar-toggle"]');
    await expect(sidebarToggle).toBeVisible();
    
    // Click to collapse sidebar
    await sidebarToggle.click();
    await page.waitForTimeout(500);
    
    // Check if sidebar is collapsed (should have collapsed class or reduced width)
    const sidebar = page.locator('[data-testid="sidebar-nav"]');
    await expect(sidebar).toHaveClass(/collapsed/);
    
    // Click to expand sidebar
    await sidebarToggle.click();
    await page.waitForTimeout(500);
    
    // Check if sidebar is expanded
    await expect(sidebar).not.toHaveClass(/collapsed/);
  });

  test('should display system health indicators', async ({ page }) => {
    // Check for system health display
    const healthIndicator = page.locator('[data-testid="system-health"]');
    await expect(healthIndicator).toBeVisible();
    
    // Check for WebSocket connection status
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    await expect(connectionStatus).toBeVisible();
  });

  test('should handle responsive design', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    
    // Check if mobile navigation works
    await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    
    // Check if tablet navigation works
    await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    
    // Reset to desktop
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.waitForTimeout(500);
  });

  test('should test keyboard navigation', async ({ page }) => {
    // Focus on the first navigation item
    await page.keyboard.press('Tab');
    
    // Navigate through items with arrow keys
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowDown');
    
    // Press Enter to activate
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);
    
    // Check if navigation worked
    // This will depend on which item was selected
  });

  test('should verify enhanced cognitive API connectivity', async ({ page }) => {
    // Navigate to Enhanced Dashboard
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(2000);
    
    // Check for API data loading indicators
    const loadingIndicators = page.locator('[data-testid*="loading"]');
    
    // Wait for data to load (loading indicators should disappear)
    await expect(loadingIndicators).toHaveCount(0, { timeout: 10000 });
    
    // Check for error messages
    const errorMessages = page.locator('[data-testid*="error"]');
    await expect(errorMessages).toHaveCount(0);
  });
});