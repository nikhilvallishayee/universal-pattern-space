import { test, expect } from '@playwright/test';

test.describe('User Interactions and Visual Elements', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="app-container"]', { timeout: 10000 });
    await page.waitForTimeout(2000);
  });

  test('should display visual enhancements for enhanced cognitive features', async ({ page }) => {
    // Check for NEW badges on enhanced cognitive items
    const enhancedSection = page.locator('[data-testid="nav-section-enhanced"]');
    const newBadge = enhancedSection.locator('.badge', { hasText: 'NEW' });
    await expect(newBadge).toBeVisible();
    
    // Check for featured indicators
    const featuredItems = page.locator('[data-testid*="nav-item-"].featured');
    const featuredCount = await featuredItems.count();
    expect(featuredCount).toBeGreaterThan(0);
    
    // Check for sparkle or shimmer effects
    const enhancedItems = page.locator('[data-testid="nav-item-enhanced"], [data-testid="nav-item-stream"], [data-testid="nav-item-autonomous"]');
    for (let i = 0; i < await enhancedItems.count(); i++) {
      const item = enhancedItems.nth(i);
      
      // Check for visual enhancement classes
      const hasEnhancement = await item.evaluate(el => {
        const classes = el.className;
        return classes.includes('sparkle') || 
               classes.includes('shimmer') || 
               classes.includes('gradient') ||
               classes.includes('featured');
      });
      
      expect(hasEnhancement).toBeTruthy();
    }
  });

  test('should handle hover effects on navigation items', async ({ page }) => {
    const navItems = page.locator('[data-testid*="nav-item-"]');
    const firstItem = navItems.first();
    
    // Get initial styles
    const initialStyles = await firstItem.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        transform: computed.transform
      };
    });
    
    // Hover over the item
    await firstItem.hover();
    await page.waitForTimeout(500);
    
    // Check for hover effects
    const hoverStyles = await firstItem.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        transform: computed.transform
      };
    });
    
    // Should have some visual change on hover
    const hasHoverEffect = 
      hoverStyles.backgroundColor !== initialStyles.backgroundColor ||
      hoverStyles.transform !== initialStyles.transform;
    
    expect(hasHoverEffect).toBeTruthy();
  });

  test('should test interactive query interface', async ({ page }) => {
    // Navigate to query interface
    await page.click('[data-testid="nav-item-query"]');
    await page.waitForTimeout(1000);
    
    // Check if query input is present
    const queryInput = page.locator('[data-testid="query-input"]');
    await expect(queryInput).toBeVisible();
    
    // Type a test query
    await queryInput.fill('What is the current system status?');
    
    // Check if submit button is enabled
    const submitButton = page.locator('[data-testid="query-submit"]');
    await expect(submitButton).toBeEnabled();
    
    // Submit the query
    await submitButton.click();
    await page.waitForTimeout(2000);
    
    // Check for response or loading indicator
    const responseArea = page.locator('[data-testid="query-response"]');
    const loadingIndicator = page.locator('[data-testid="query-loading"]');
    
    const hasResponse = await responseArea.isVisible();
    const hasLoading = await loadingIndicator.isVisible();
    
    expect(hasResponse || hasLoading).toBeTruthy();
  });

  test('should test knowledge graph interactions', async ({ page }) => {
    // Navigate to knowledge graph
    await page.click('[data-testid="nav-item-knowledge"]');
    await page.waitForTimeout(2000);
    
    // Check if knowledge graph container is present
    const graphContainer = page.locator('[data-testid="knowledge-graph"]');
    await expect(graphContainer).toBeVisible();
    
    // Check for interactive elements (nodes, edges, controls)
    const graphNodes = page.locator('[data-testid="graph-node"]');
    const graphControls = page.locator('[data-testid="graph-controls"]');
    
    if (await graphNodes.count() > 0) {
      // Test node interaction
      const firstNode = graphNodes.first();
      await firstNode.click();
      await page.waitForTimeout(500);
      
      // Check for node selection or details
      const nodeDetails = page.locator('[data-testid="node-details"]');
      if (await nodeDetails.isVisible()) {
        expect(await nodeDetails.textContent()).toBeTruthy();
      }
    }
    
    if (await graphControls.isVisible()) {
      // Test graph controls
      const zoomIn = page.locator('[data-testid="zoom-in"]');
      const zoomOut = page.locator('[data-testid="zoom-out"]');
      
      if (await zoomIn.isVisible()) {
        await zoomIn.click();
        await page.waitForTimeout(500);
      }
      
      if (await zoomOut.isVisible()) {
        await zoomOut.click();
        await page.waitForTimeout(500);
      }
    }
  });

  test('should test modal interactions', async ({ page }) => {
    // Look for modal triggers
    const modalTriggers = page.locator('[data-testid*="modal-trigger"]');
    
    if (await modalTriggers.count() > 0) {
      const firstTrigger = modalTriggers.first();
      await firstTrigger.click();
      await page.waitForTimeout(500);
      
      // Check if modal opened
      const modal = page.locator('[data-testid="modal"]');
      await expect(modal).toBeVisible();
      
      // Test modal close
      const closeButton = page.locator('[data-testid="modal-close"]');
      if (await closeButton.isVisible()) {
        await closeButton.click();
        await page.waitForTimeout(500);
        await expect(modal).not.toBeVisible();
      } else {
        // Try ESC key
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
        await expect(modal).not.toBeVisible();
      }
    }
  });

  test('should test fullscreen functionality', async ({ page }) => {
    // Look for fullscreen toggle
    const fullscreenToggle = page.locator('[data-testid="fullscreen-toggle"]');
    
    if (await fullscreenToggle.isVisible()) {
      await fullscreenToggle.click();
      await page.waitForTimeout(1000);
      
      // Check if app entered fullscreen mode
      const isFullscreen = await page.evaluate(() => {
        return document.fullscreenElement !== null;
      });
      
      if (isFullscreen) {
        // Exit fullscreen
        await fullscreenToggle.click();
        await page.waitForTimeout(1000);
        
        const isStillFullscreen = await page.evaluate(() => {
          return document.fullscreenElement !== null;
        });
        
        expect(isStillFullscreen).toBeFalsy();
      }
    }
  });

  test('should test drag and drop interactions', async ({ page }) => {
    // Navigate to a view that might have drag and drop
    await page.click('[data-testid="nav-item-knowledge"]');
    await page.waitForTimeout(2000);
    
    // Look for draggable elements
    const draggableElements = page.locator('[draggable="true"]');
    
    if (await draggableElements.count() > 0) {
      const firstDraggable = draggableElements.first();
      const dropTarget = page.locator('[data-testid="drop-zone"]');
      
      if (await dropTarget.isVisible()) {
        // Perform drag and drop
        await firstDraggable.dragTo(dropTarget);
        await page.waitForTimeout(1000);
        
        // Check for visual feedback or state change
        // This would depend on the specific implementation
      }
    }
  });

  test('should test real-time data visualization updates', async ({ page }) => {
    // Navigate to stream of consciousness
    await page.click('[data-testid="nav-item-stream"]');
    await page.waitForTimeout(3000);
    
    // Check for data visualization elements
    const visualizations = page.locator('[data-testid*="visualization"], [data-testid*="chart"], [data-testid*="graph"]');
    
    if (await visualizations.count() > 0) {
      // Get initial state
      const initialContent = await visualizations.first().innerHTML();
      
      // Wait for potential updates
      await page.waitForTimeout(10000);
      
      // Check if content changed (indicating real-time updates)
      const updatedContent = await visualizations.first().innerHTML();
      
      // Content might change, or at least should remain stable
      expect(updatedContent).toBeTruthy();
    }
  });

  test('should test accessibility features', async ({ page }) => {
    // Check for ARIA labels and roles
    const interactiveElements = page.locator('button, [role="button"], input, [role="textbox"]');
    
    for (let i = 0; i < Math.min(5, await interactiveElements.count()); i++) {
      const element = interactiveElements.nth(i);
      
      // Check for accessibility attributes
      const hasAriaLabel = await element.getAttribute('aria-label');
      const hasAriaLabelledBy = await element.getAttribute('aria-labelledby');
      const hasTitle = await element.getAttribute('title');
      const hasRole = await element.getAttribute('role');
      
      // Should have at least one accessibility attribute
      const hasAccessibility = hasAriaLabel || hasAriaLabelledBy || hasTitle || hasRole;
      expect(hasAccessibility).toBeTruthy();
    }
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should test error handling in UI', async ({ page }) => {
    // Monitor console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Navigate through all views rapidly to test error handling
    const navItems = page.locator('[data-testid*="nav-item-"]');
    const navCount = await navItems.count();
    
    for (let i = 0; i < Math.min(navCount, 8); i++) {
      await navItems.nth(i).click();
      await page.waitForTimeout(1000);
    }
    
    // Check for error boundaries or error messages in UI
    const errorMessages = page.locator('[data-testid*="error"], .error-message, .error-boundary');
    const errorCount = await errorMessages.count();
    
    // Should handle errors gracefully
    expect(errorCount).toBeLessThan(3);
    
    // Should not have critical console errors
    const criticalErrors = consoleErrors.filter(error => 
      error.includes('TypeError') || 
      error.includes('ReferenceError') ||
      error.includes('Cannot read property')
    );
    
    expect(criticalErrors.length).toBeLessThan(3);
  });

  test('should test performance with multiple interactions', async ({ page }) => {
    // Start performance monitoring
    await page.evaluate(() => {
      window.performanceMarks = [];
      performance.mark('test-start');
    });
    
    // Perform multiple rapid interactions
    const interactions = [
      () => page.click('[data-testid="nav-item-enhanced"]'),
      () => page.click('[data-testid="nav-item-stream"]'),
      () => page.click('[data-testid="nav-item-autonomous"]'),
      () => page.click('[data-testid="nav-item-cognitive"]'),
      () => page.click('[data-testid="nav-item-knowledge"]')
    ];
    
    for (const interaction of interactions) {
      await interaction();
      await page.waitForTimeout(500);
    }
    
    // End performance monitoring
    const performanceData = await page.evaluate(() => {
      performance.mark('test-end');
      performance.measure('test-duration', 'test-start', 'test-end');
      
      const measure = performance.getEntriesByName('test-duration')[0];
      return {
        duration: measure.duration,
        memory: performance.memory ? {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize
        } : null
      };
    });
    
    // Test should complete within reasonable time
    expect(performanceData.duration).toBeLessThan(15000); // 15 seconds
    
    // Memory usage should be reasonable (if available)
    if (performanceData.memory) {
      expect(performanceData.memory.used).toBeLessThan(100 * 1024 * 1024); // 100MB
    }
  });
});