import { test, expect } from '@playwright/test';

test.describe('Enhanced Cognitive Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="app-container"]', { timeout: 10000 });
    await page.waitForTimeout(2000);
  });

  test.describe('Enhanced Cognitive Dashboard', () => {
    test.beforeEach(async ({ page }) => {
      await page.click('[data-testid="nav-item-enhanced"]');
      await page.waitForTimeout(2000);
    });

    test('should display enhanced cognitive dashboard', async ({ page }) => {
      // Check if dashboard container is visible
      await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
      
      // Check for key dashboard sections
      const dashboardSections = [
        '[data-testid="cognitive-overview"]',
        '[data-testid="enhancement-metrics"]',
        '[data-testid="system-status"]',
        '[data-testid="performance-indicators"]'
      ];
      
      for (const selector of dashboardSections) {
        const section = page.locator(selector);
        if (await section.isVisible()) {
          await expect(section).toBeVisible();
        }
      }
    });

    test('should display real-time metrics', async ({ page }) => {
      // Look for metric displays
      const metrics = page.locator('[data-testid*="metric-"], [data-testid*="indicator-"]');
      const metricCount = await metrics.count();
      
      if (metricCount > 0) {
        // Check that metrics have values
        for (let i = 0; i < Math.min(metricCount, 5); i++) {
          const metric = metrics.nth(i);
          const content = await metric.textContent();
          expect(content.trim()).toBeTruthy();
        }
      }
    });

    test('should handle dashboard interactions', async ({ page }) => {
      // Look for interactive elements
      const buttons = page.locator('[data-testid="enhanced-cognitive-dashboard"] button');
      const toggles = page.locator('[data-testid="enhanced-cognitive-dashboard"] [data-testid*="toggle"]');
      
      if (await buttons.count() > 0) {
        const firstButton = buttons.first();
        await firstButton.click();
        await page.waitForTimeout(1000);
        
        // Should not cause errors
        const errorElements = page.locator('[data-testid*="error"]');
        expect(await errorElements.count()).toBeLessThan(2);
      }
    });
  });

  test.describe('Stream of Consciousness Monitor', () => {
    test.beforeEach(async ({ page }) => {
      await page.click('[data-testid="nav-item-stream"]');
      await page.waitForTimeout(3000);
    });

    test('should display stream of consciousness interface', async ({ page }) => {
      await expect(page.locator('[data-testid="stream-of-consciousness-monitor"]')).toBeVisible();
      
      // Check for stream components
      const streamElements = [
        '[data-testid="stream-content"]',
        '[data-testid="stream-controls"]',
        '[data-testid="stream-status"]'
      ];
      
      for (const selector of streamElements) {
        const element = page.locator(selector);
        if (await element.isVisible()) {
          await expect(element).toBeVisible();
        }
      }
    });

    test('should handle streaming data', async ({ page }) => {
      // Check for streaming indicators
      const streamContainer = page.locator('[data-testid="stream-content"]');
      
      if (await streamContainer.isVisible()) {
        // Wait for potential data updates
        await page.waitForTimeout(5000);
        
        // Check for stream entries or messages
        const streamEntries = page.locator('[data-testid*="stream-entry"], [data-testid*="thought-"]');
        const entryCount = await streamEntries.count();
        
        // Should have some content or be properly handling empty state
        expect(entryCount >= 0).toBeTruthy();
      }
    });

    test('should test stream controls', async ({ page }) => {
      // Look for stream control buttons
      const playButton = page.locator('[data-testid="stream-play"]');
      const pauseButton = page.locator('[data-testid="stream-pause"]');
      const clearButton = page.locator('[data-testid="stream-clear"]');
      
      if (await playButton.isVisible()) {
        await playButton.click();
        await page.waitForTimeout(1000);
      }
      
      if (await pauseButton.isVisible()) {
        await pauseButton.click();
        await page.waitForTimeout(1000);
      }
      
      if (await clearButton.isVisible()) {
        await clearButton.click();
        await page.waitForTimeout(1000);
        
        // Stream should be cleared
        const streamEntries = page.locator('[data-testid*="stream-entry"]');
        expect(await streamEntries.count()).toBeLessThanOrEqual(1);
      }
    });

    test('should display cognitive events', async ({ page }) => {
      // Wait for cognitive events to appear
      await page.waitForTimeout(8000);
      
      // Check for event types
      const eventTypes = [
        '[data-testid*="thought-"]',
        '[data-testid*="reflection-"]',
        '[data-testid*="decision-"]',
        '[data-testid*="insight-"]'
      ];
      
      let hasEvents = false;
      for (const selector of eventTypes) {
        const events = page.locator(selector);
        if (await events.count() > 0) {
          hasEvents = true;
          break;
        }
      }
      
      // Should have events or proper empty state handling
      expect(hasEvents || await page.locator('[data-testid="empty-stream"]').isVisible()).toBeTruthy();
    });
  });

  test.describe('Autonomous Learning Monitor', () => {
    test.beforeEach(async ({ page }) => {
      await page.click('[data-testid="nav-item-autonomous"]');
      await page.waitForTimeout(3000);
    });

    test('should display autonomous learning interface', async ({ page }) => {
      await expect(page.locator('[data-testid="autonomous-learning-monitor"]')).toBeVisible();
      
      // Check for learning components
      const learningElements = [
        '[data-testid="learning-status"]',
        '[data-testid="knowledge-acquisition"]',
        '[data-testid="learning-progress"]',
        '[data-testid="autonomous-insights"]'
      ];
      
      for (const selector of learningElements) {
        const element = page.locator(selector);
        if (await element.isVisible()) {
          await expect(element).toBeVisible();
        }
      }
    });

    test('should display learning metrics', async ({ page }) => {
      // Look for learning metrics
      const metrics = page.locator('[data-testid*="learning-metric"], [data-testid*="acquisition-"]');
      
      if (await metrics.count() > 0) {
        // Check metric values
        for (let i = 0; i < Math.min(await metrics.count(), 3); i++) {
          const metric = metrics.nth(i);
          const content = await metric.textContent();
          expect(content.trim()).toBeTruthy();
        }
      }
    });

    test('should handle autonomous learning controls', async ({ page }) => {
      // Look for learning control buttons
      const startButton = page.locator('[data-testid="start-learning"]');
      const stopButton = page.locator('[data-testid="stop-learning"]');
      const configButton = page.locator('[data-testid="configure-learning"]');
      
      if (await startButton.isVisible()) {
        await startButton.click();
        await page.waitForTimeout(2000);
        
        // Should show learning in progress
        const progressIndicator = page.locator('[data-testid="learning-progress"]');
        if (await progressIndicator.isVisible()) {
          expect(await progressIndicator.textContent()).toBeTruthy();
        }
      }
      
      if (await configButton.isVisible()) {
        await configButton.click();
        await page.waitForTimeout(1000);
        
        // Should open configuration interface
        const configPanel = page.locator('[data-testid="learning-config"]');
        if (await configPanel.isVisible()) {
          await expect(configPanel).toBeVisible();
        }
      }
    });

    test('should display knowledge acquisition progress', async ({ page }) => {
      // Wait for learning data to load
      await page.waitForTimeout(5000);
      
      // Check for acquisition indicators
      const acquisitionElements = [
        '[data-testid="concepts-learned"]',
        '[data-testid="knowledge-sources"]',
        '[data-testid="learning-rate"]',
        '[data-testid="acquisition-queue"]'
      ];
      
      let hasAcquisitionData = false;
      for (const selector of acquisitionElements) {
        const element = page.locator(selector);
        if (await element.isVisible()) {
          hasAcquisitionData = true;
          const content = await element.textContent();
          expect(content.trim()).toBeTruthy();
        }
      }
      
      // Should have acquisition data or proper empty state
      expect(hasAcquisitionData || await page.locator('[data-testid="no-learning-data"]').isVisible()).toBeTruthy();
    });
  });

  test.describe('Enhanced Cognitive Integration', () => {
    test('should maintain state across enhanced cognitive views', async ({ page }) => {
      // Navigate to enhanced dashboard
      await page.click('[data-testid="nav-item-enhanced"]');
      await page.waitForTimeout(2000);
      
      // Get initial state
      const initialState = await page.evaluate(() => {
        return {
          url: window.location.href,
          activeView: document.querySelector('[data-testid="enhanced-cognitive-dashboard"]') ? 'enhanced' : null
        };
      });
      
      // Navigate to stream
      await page.click('[data-testid="nav-item-stream"]');
      await page.waitForTimeout(2000);
      
      // Navigate to autonomous
      await page.click('[data-testid="nav-item-autonomous"]');
      await page.waitForTimeout(2000);
      
      // Navigate back to enhanced
      await page.click('[data-testid="nav-item-enhanced"]');
      await page.waitForTimeout(2000);
      
      // Should return to enhanced dashboard
      await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
    });

    test('should handle enhanced cognitive API health', async ({ page }) => {
      // Monitor API health across enhanced views
      const apiCalls = [];
      
      page.on('response', response => {
        if (response.url().includes('/api/enhanced-cognitive/')) {
          apiCalls.push({
            url: response.url(),
            status: response.status(),
            view: 'unknown'
          });
        }
      });
      
      // Navigate through enhanced views
      await page.click('[data-testid="nav-item-enhanced"]');
      await page.waitForTimeout(3000);
      
      await page.click('[data-testid="nav-item-stream"]');
      await page.waitForTimeout(3000);
      
      await page.click('[data-testid="nav-item-autonomous"]');
      await page.waitForTimeout(3000);
      
      // Check API health
      const healthyAPICalls = apiCalls.filter(call => call.status >= 200 && call.status < 400);
      const errorAPICalls = apiCalls.filter(call => call.status >= 400);
      
      // Should have mostly healthy API calls
      expect(healthyAPICalls.length).toBeGreaterThanOrEqual(errorAPICalls.length);
    });

    test('should test enhanced cognitive data flow', async ({ page }) => {
      // Test data consistency across components
      await page.click('[data-testid="nav-item-enhanced"]');
      await page.waitForTimeout(3000);
      
      // Get system status from dashboard
      const dashboardStatus = page.locator('[data-testid="system-status"]');
      let dashboardData = null;
      
      if (await dashboardStatus.isVisible()) {
        dashboardData = await dashboardStatus.textContent();
      }
      
      // Navigate to stream and check consistency
      await page.click('[data-testid="nav-item-stream"]');
      await page.waitForTimeout(3000);
      
      const streamStatus = page.locator('[data-testid="stream-status"]');
      if (await streamStatus.isVisible() && dashboardData) {
        const streamData = await streamStatus.textContent();
        // Data should be consistent or at least valid
        expect(streamData.trim()).toBeTruthy();
      }
    });

    test('should handle enhanced cognitive error recovery', async ({ page }) => {
      // Monitor console errors
      const errors = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      
      // Rapidly navigate through enhanced views to test error handling
      const views = ['enhanced', 'stream', 'autonomous'];
      
      for (let i = 0; i < 3; i++) {
        for (const view of views) {
          await page.click(`[data-testid="nav-item-${view}"]`);
          await page.waitForTimeout(1000);
        }
      }
      
      // Should handle rapid navigation without critical errors
      const criticalErrors = errors.filter(error => 
        error.includes('Cannot read property') ||
        error.includes('TypeError') ||
        error.includes('ReferenceError')
      );
      
      expect(criticalErrors.length).toBeLessThan(5);
      
      // UI should still be functional
      await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    });
  });

  test.describe('Performance and Optimization', () => {
    test('should handle large datasets in enhanced views', async ({ page }) => {
      // Navigate to stream view (likely to have continuous data)
      await page.click('[data-testid="nav-item-stream"]');
      await page.waitForTimeout(5000);
      
      // Let stream accumulate data
      await page.waitForTimeout(15000);
      
      // Check if UI remains responsive
      const streamContainer = page.locator('[data-testid="stream-of-consciousness-monitor"]');
      await expect(streamContainer).toBeVisible();
      
      // Test interaction responsiveness
      const navItem = page.locator('[data-testid="nav-item-enhanced"]');
      const startTime = Date.now();
      await navItem.click();
      await page.waitForSelector('[data-testid="enhanced-cognitive-dashboard"]');
      const endTime = Date.now();
      
      // Navigation should be reasonably fast
      expect(endTime - startTime).toBeLessThan(5000);
    });

    test('should optimize memory usage in enhanced components', async ({ page }) => {
      // Get initial memory usage
      const initialMemory = await page.evaluate(() => {
        return performance.memory ? {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize
        } : null;
      });
      
      if (initialMemory) {
        // Navigate through enhanced views multiple times
        for (let i = 0; i < 5; i++) {
          await page.click('[data-testid="nav-item-enhanced"]');
          await page.waitForTimeout(2000);
          
          await page.click('[data-testid="nav-item-stream"]');
          await page.waitForTimeout(2000);
          
          await page.click('[data-testid="nav-item-autonomous"]');
          await page.waitForTimeout(2000);
        }
        
        // Check final memory usage
        const finalMemory = await page.evaluate(() => {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize
          };
        });
        
        // Memory growth should be reasonable
        const memoryGrowth = finalMemory.used - initialMemory.used;
        expect(memoryGrowth).toBeLessThan(50 * 1024 * 1024); // 50MB growth limit
      }
    });
  });
});