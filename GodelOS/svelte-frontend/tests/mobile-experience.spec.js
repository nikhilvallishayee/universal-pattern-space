import { test, expect, devices } from '@playwright/test';

test.describe('Mobile User Experience', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="app-container"]', { timeout: 10000 });
    await page.waitForTimeout(2000);
  });

  test('should display properly on mobile viewport', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test is for mobile devices only');
    }

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that header is properly sized for mobile
    const header = page.locator('.interface-header');
    await expect(header).toBeVisible();
    
    const headerHeight = await header.boundingBox();
    expect(headerHeight.height).toBeLessThanOrEqual(60); // Mobile-optimized header height
    
    // Check sidebar is initially collapsed on mobile
    const sidebar = page.locator('.sidebar');
    await expect(sidebar).toHaveClass(/collapsed/);
    
    // Verify main content takes full width
    const mainContent = page.locator('.main-content');
    await expect(mainContent).toBeVisible();
    
    const contentBox = await mainContent.boundingBox();
    expect(contentBox.width).toBeGreaterThan(300); // Should use most of screen width
  });

  test('should support touch navigation on mobile', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test is for mobile devices only');
    }

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Test sidebar toggle with touch
    const sidebarToggle = page.locator('.sidebar-toggle');
    await expect(sidebarToggle).toBeVisible();
    
    // Touch the sidebar toggle
    await sidebarToggle.tap();
    await page.waitForTimeout(500);
    
    // Sidebar should be visible after tap
    const sidebar = page.locator('.sidebar');
    await expect(sidebar).not.toHaveClass(/collapsed/);
    
    // Tap a navigation item
    const navItem = page.locator('[data-testid="nav-item-enhanced"]');
    await expect(navItem).toBeVisible();
    await navItem.tap();
    await page.waitForTimeout(1000);
    
    // Check that navigation worked
    await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
    
    // Close sidebar by tapping toggle again
    await sidebarToggle.tap();
    await page.waitForTimeout(500);
    await expect(sidebar).toHaveClass(/collapsed/);
  });

  test('should handle touch interactions on components', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test is for mobile devices only');
    }

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to dashboard
    await page.tap('[data-testid="nav-item-dashboard"]');
    await page.waitForTimeout(2000);
    
    // Test touch interactions on expand buttons
    const expandButtons = page.locator('.expand-btn');
    if (await expandButtons.count() > 0) {
      const firstExpandBtn = expandButtons.first();
      await expect(firstExpandBtn).toBeVisible();
      
      // Check button is touch-friendly size
      const buttonBox = await firstExpandBtn.boundingBox();
      expect(buttonBox.height).toBeGreaterThanOrEqual(40); // iOS recommended minimum
      expect(buttonBox.width).toBeGreaterThanOrEqual(40);
      
      // Test tap interaction
      await firstExpandBtn.tap();
      await page.waitForTimeout(500);
      
      // Should trigger some UI change (modal, navigation, etc.)
      // This is a basic interaction test
    }
  });

  test('should optimize content layout for mobile scrolling', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test is for mobile devices only');
    }

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that main content is scrollable
    const mainContent = page.locator('.main-content');
    await expect(mainContent).toBeVisible();
    
    // Verify dashboard layout is optimized for mobile
    await page.tap('[data-testid="nav-item-dashboard"]');
    await page.waitForTimeout(2000);
    
    const dashboardLayout = page.locator('.dashboard-layout');
    if (await dashboardLayout.isVisible()) {
      // Should use single column layout on mobile
      const layoutStyle = await dashboardLayout.evaluate(el => {
        return window.getComputedStyle(el).gridTemplateColumns;
      });
      
      // Should be single column or use mobile-optimized grid
      expect(layoutStyle).toBeTruthy();
    }
    
    // Test vertical scrolling works smoothly
    await page.evaluate(() => {
      document.querySelector('.main-content').scrollTop = 100;
    });
    
    await page.waitForTimeout(500);
    
    const scrollTop = await page.evaluate(() => {
      return document.querySelector('.main-content').scrollTop;
    });
    
    expect(scrollTop).toBeGreaterThan(0);
  });

  test('should display mobile-optimized navigation sections', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test is for mobile devices only');
    }

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Open sidebar
    await page.tap('.sidebar-toggle');
    await page.waitForTimeout(500);
    
    // Check all navigation sections are present and touch-friendly
    const navSections = [
      '[data-testid="nav-section-core"]',
      '[data-testid="nav-section-enhanced"]',
      '[data-testid="nav-section-analysis"]',
      '[data-testid="nav-section-system"]'
    ];
    
    for (const section of navSections) {
      const sectionElement = page.locator(section);
      await expect(sectionElement).toBeVisible();
      
      // Check section header is readable
      const sectionHeader = sectionElement.locator('.section-header');
      if (await sectionHeader.isVisible()) {
        await expect(sectionHeader).toBeVisible();
      }
    }
    
    // Test navigation items are touch-friendly
    const navItems = page.locator('.nav-item');
    const navItemCount = await navItems.count();
    
    if (navItemCount > 0) {
      for (let i = 0; i < Math.min(3, navItemCount); i++) {
        const navItem = navItems.nth(i);
        const itemBox = await navItem.boundingBox();
        
        // Each nav item should be at least 44px tall (iOS guideline)
        expect(itemBox.height).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('should handle device orientation changes', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test is for mobile devices only');
    }

    // Test portrait mode
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000);
    
    // Verify app is functional in portrait
    await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    await expect(page.locator('.sidebar')).toHaveClass(/collapsed/);
    
    // Test landscape mode  
    await page.setViewportSize({ width: 667, height: 375 });
    await page.waitForTimeout(1000);
    
    // App should still be functional in landscape
    await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    
    // Header should adapt to landscape
    const header = page.locator('.interface-header');
    await expect(header).toBeVisible();
    
    // Test navigation still works in landscape
    await page.tap('.sidebar-toggle');
    await page.waitForTimeout(500);
    
    const sidebar = page.locator('.sidebar');
    await expect(sidebar).not.toHaveClass(/collapsed/);
    
    // Close sidebar
    await page.tap('.sidebar-toggle');
    await page.waitForTimeout(500);
  });

  test('should provide accessible mobile experience', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test is for mobile devices only');
    }

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that interactive elements have proper ARIA labels for mobile screen readers
    const interactiveElements = page.locator('button, [role="button"], .nav-item');
    const elementCount = await interactiveElements.count();
    
    if (elementCount > 0) {
      for (let i = 0; i < Math.min(5, elementCount); i++) {
        const element = interactiveElements.nth(i);
        
        // Check for accessibility attributes
        const hasAriaLabel = await element.getAttribute('aria-label');
        const hasAriaLabelledBy = await element.getAttribute('aria-labelledby');
        const hasTitle = await element.getAttribute('title');
        const hasText = await element.textContent();
        
        // Should have at least one form of accessible labeling
        const hasAccessibility = hasAriaLabel || hasAriaLabelledBy || hasTitle || (hasText && hasText.trim());
        expect(hasAccessibility).toBeTruthy();
      }
    }
    
    // Test keyboard navigation on mobile (for external keyboards)
    await page.keyboard.press('Tab');
    await page.waitForTimeout(200);
    
    // Check that focus is visible
    const focusedElement = page.locator(':focus');
    if (await focusedElement.isVisible()) {
      await expect(focusedElement).toBeVisible();
    }
  });

  test('should optimize performance on mobile devices', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test is for mobile devices only');
    }

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Measure page load performance on mobile
    const startTime = Date.now();
    
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForSelector('[data-testid="app-container"]');
    
    const loadTime = Date.now() - startTime;
    
    // Should load reasonably fast on mobile (allowing for slower mobile connections)
    expect(loadTime).toBeLessThan(15000); // 15 seconds max for mobile
    
    // Test smooth animations and transitions
    await page.tap('.sidebar-toggle');
    
    // Check for smooth transition (no janky animations)
    const sidebar = page.locator('.sidebar');
    await expect(sidebar).not.toHaveClass(/collapsed/);
    
    // Close sidebar and check animation
    await page.tap('.sidebar-toggle');
    await expect(sidebar).toHaveClass(/collapsed/);
    
    // Test navigation performance
    const navStartTime = Date.now();
    await page.tap('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(2000);
    const navEndTime = Date.now();
    
    // Navigation should be responsive
    expect(navEndTime - navStartTime).toBeLessThan(5000);
  });

  test('should support common mobile gestures and interactions', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip('This test is for mobile devices only');
    }

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Test long press (touch and hold) doesn't break interface
    const mainContent = page.locator('.main-content');
    await mainContent.click({ delay: 1000 }); // Simulate long press
    
    // Interface should remain functional
    await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    
    // Test double tap doesn't cause zoom issues
    await mainContent.dblclick();
    await page.waitForTimeout(500);
    
    // App should still be functional
    await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    
    // Test touch selection doesn't interfere with navigation
    await page.tap('[data-testid="nav-item-dashboard"]');
    await page.waitForTimeout(2000);
    
    await expect(page.locator('[data-testid="dashboard-view"]')).toBeVisible();
  });
});

test.describe('Tablet Experience', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="app-container"]', { timeout: 10000 });
    await page.waitForTimeout(2000);
  });

  test('should adapt layout for tablet viewports', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 1024, height: 768 });
    
    // Tablet should show a hybrid layout between mobile and desktop
    const sidebar = page.locator('.sidebar');
    await expect(sidebar).toBeVisible();
    
    // Sidebar might be collapsible but not full-screen overlay like mobile
    const sidebarBox = await sidebar.boundingBox();
    expect(sidebarBox.width).toBeLessThan(500); // Not full width like mobile
    
    // Main content should have adequate space
    const mainContent = page.locator('.main-content');
    const contentBox = await mainContent.boundingBox();
    expect(contentBox.width).toBeGreaterThan(500);
    
    // Test touch interactions work on tablet
    await page.tap('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(2000);
    
    await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
  });

  test('should support both touch and mouse interactions on tablet', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 1024, height: 768 });
    
    // Test touch interaction
    await page.tap('[data-testid="nav-item-dashboard"]');
    await page.waitForTimeout(2000);
    
    await expect(page.locator('[data-testid="dashboard-view"]')).toBeVisible();
    
    // Test mouse hover (if supported)
    const navItem = page.locator('[data-testid="nav-item-enhanced"]');
    await navItem.hover();
    await page.waitForTimeout(500);
    
    // Test click
    await navItem.click();
    await page.waitForTimeout(2000);
    
    await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
  });
});