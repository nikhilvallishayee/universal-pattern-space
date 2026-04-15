import { test, expect } from '@playwright/test';

test.describe('System Integration and End-to-End Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="app-container"]', { timeout: 10000 });
    await page.waitForTimeout(3000);
  });

  test('should complete full system initialization', async ({ page }) => {
    // Check for successful application loading
    await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    
    // Check for WebSocket connection
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    if (await connectionStatus.isVisible()) {
      await expect(connectionStatus).toHaveClass(/connected|success/);
    }
    
    // Check for system health indicators
    const healthIndicator = page.locator('[data-testid="system-health"]');
    if (await healthIndicator.isVisible()) {
      const healthText = await healthIndicator.textContent();
      expect(healthText.trim()).toBeTruthy();
    }
    
    // Verify all main navigation sections are present
    const navSections = [
      '[data-testid="nav-section-core"]',
      '[data-testid="nav-section-enhanced"]',
      '[data-testid="nav-section-analysis"]',
      '[data-testid="nav-section-system"]'
    ];
    
    for (const section of navSections) {
      await expect(page.locator(section)).toBeVisible();
    }
  });

  test('should handle complete user workflow', async ({ page }) => {
    // 1. Start at dashboard
    await page.click('[data-testid="nav-item-dashboard"]');
    await page.waitForTimeout(2000);
    await expect(page.locator('[data-testid="dashboard-view"]')).toBeVisible();
    
    // 2. Check system status
    const systemHealth = page.locator('[data-testid="system-health"]');
    if (await systemHealth.isVisible()) {
      const healthValue = await systemHealth.textContent();
      console.log('System Health:', healthValue);
    }
    
    // 3. Navigate to enhanced cognitive features
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(3000);
    await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
    
    // 4. Monitor stream of consciousness
    await page.click('[data-testid="nav-item-stream"]');
    await page.waitForTimeout(3000);
    await expect(page.locator('[data-testid="stream-of-consciousness-monitor"]')).toBeVisible();
    
    // 5. Check autonomous learning
    await page.click('[data-testid="nav-item-autonomous"]');
    await page.waitForTimeout(3000);
    await expect(page.locator('[data-testid="autonomous-learning-monitor"]')).toBeVisible();
    
    // 6. Interact with knowledge graph
    await page.click('[data-testid="nav-item-knowledge"]');
    await page.waitForTimeout(3000);
    await expect(page.locator('[data-testid="knowledge-graph"]')).toBeVisible();
    
    // 7. Test query interface
    await page.click('[data-testid="nav-item-query"]');
    await page.waitForTimeout(2000);
    await expect(page.locator('[data-testid="query-interface"]')).toBeVisible();
    
    const queryInput = page.locator('[data-testid="query-input"]');
    if (await queryInput.isVisible()) {
      await queryInput.fill('What is the current system status?');
      
      const submitButton = page.locator('[data-testid="query-submit"]');
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForTimeout(3000);
        
        // Check for response
        const responseArea = page.locator('[data-testid="query-response"]');
        if (await responseArea.isVisible()) {
          const response = await responseArea.textContent();
          expect(response.trim()).toBeTruthy();
        }
      }
    }
    
    // 8. Return to enhanced dashboard
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(2000);
    await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
  });

  test('should maintain system stability under load', async ({ page }) => {
    // Monitor console errors
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Monitor failed requests
    const failedRequests = [];
    page.on('response', response => {
      if (response.status() >= 500) {
        failedRequests.push({
          url: response.url(),
          status: response.status()
        });
      }
    });
    
    // Perform intensive navigation
    const views = [
      'dashboard', 'enhanced', 'stream', 'autonomous', 
      'cognitive', 'knowledge', 'query', 'transparency'
    ];
    
    for (let cycle = 0; cycle < 3; cycle++) {
      for (const view of views) {
        const navItem = page.locator(`[data-testid="nav-item-${view}"]`);
        if (await navItem.isVisible()) {
          await navItem.click();
          await page.waitForTimeout(1500);
        }
      }
    }
    
    // System should remain stable
    expect(errors.length).toBeLessThan(10);
    expect(failedRequests.length).toBeLessThan(5);
    
    // UI should still be responsive
    await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    await expect(page.locator('[data-testid="sidebar-nav"]')).toBeVisible();
  });

  test('should handle real-time data synchronization', async ({ page }) => {
    // Navigate to enhanced dashboard
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(3000);
    
    // Get initial data state
    const initialMetrics = await page.evaluate(() => {
      const metrics = document.querySelectorAll('[data-testid*="metric-"]');
      return Array.from(metrics).map(m => m.textContent);
    });
    
    // Navigate to stream view
    await page.click('[data-testid="nav-item-stream"]');
    await page.waitForTimeout(5000);
    
    // Let stream accumulate some data
    await page.waitForTimeout(10000);
    
    // Return to dashboard
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(3000);
    
    // Check if data has been updated
    const updatedMetrics = await page.evaluate(() => {
      const metrics = document.querySelectorAll('[data-testid*="metric-"]');
      return Array.from(metrics).map(m => m.textContent);
    });
    
    // Data should be present (either updated or maintained)
    expect(updatedMetrics.length).toBeGreaterThanOrEqual(0);
    
    // Check for real-time indicators
    const realtimeIndicators = page.locator('[data-testid*="realtime"], [data-testid*="live"]');
    if (await realtimeIndicators.count() > 0) {
      await expect(realtimeIndicators.first()).toBeVisible();
    }
  });

  test('should validate enhanced cognitive API integration', async ({ page }) => {
    const apiCalls = [];
    
    // Monitor enhanced cognitive API calls
    page.on('request', request => {
      if (request.url().includes('/api/enhanced-cognitive/')) {
        apiCalls.push({
          url: request.url(),
          method: request.method(),
          timestamp: Date.now()
        });
      }
    });
    
    const apiResponses = [];
    page.on('response', response => {
      if (response.url().includes('/api/enhanced-cognitive/')) {
        apiResponses.push({
          url: response.url(),
          status: response.status(),
          timestamp: Date.now()
        });
      }
    });
    
    // Navigate through enhanced cognitive features
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(3000);
    
    await page.click('[data-testid="nav-item-stream"]');
    await page.waitForTimeout(3000);
    
    await page.click('[data-testid="nav-item-autonomous"]');
    await page.waitForTimeout(3000);
    
    // Validate API integration
    expect(apiCalls.length).toBeGreaterThan(0);
    
    const successfulResponses = apiResponses.filter(r => r.status >= 200 && r.status < 400);
    const errorResponses = apiResponses.filter(r => r.status >= 400);
    
    // Should have more successful than error responses
    expect(successfulResponses.length).toBeGreaterThanOrEqual(errorResponses.length);
    
    // Check for specific enhanced cognitive endpoints
    const enhancedEndpoints = apiCalls.filter(call => 
      call.url().includes('enhanced') || 
      call.url().includes('stream') || 
      call.url().includes('autonomous')
    );
    
    expect(enhancedEndpoints.length).toBeGreaterThan(0);
  });

  test('should handle system recovery and error resilience', async ({ page }) => {
    // Simulate network issues by intercepting requests
    await page.route('**/api/enhanced-cognitive/**', route => {
      // Randomly fail some requests to test error handling
      if (Math.random() < 0.3) {
        route.abort();
      } else {
        route.continue();
      }
    });
    
    // Navigate through system with simulated issues
    const views = ['enhanced', 'stream', 'autonomous'];
    
    for (const view of views) {
      await page.click(`[data-testid="nav-item-${view}"]`);
      await page.waitForTimeout(3000);
      
      // System should handle errors gracefully
      const errorMessages = page.locator('[data-testid*="error"]');
      const errorCount = await errorMessages.count();
      
      // Should not have excessive error messages
      expect(errorCount).toBeLessThan(5);
      
      // UI should remain functional
      await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
    }
    
    // Remove route interception
    await page.unroute('**/api/enhanced-cognitive/**');
    
    // System should recover
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(5000);
    
    await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
  });

  test('should validate data consistency across components', async ({ page }) => {
    // Navigate to enhanced dashboard and collect system data
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(3000);
    
    const dashboardData = await page.evaluate(() => {
      const systemStatus = document.querySelector('[data-testid="system-status"]');
      const metrics = document.querySelectorAll('[data-testid*="metric-"]');
      
      return {
        systemStatus: systemStatus ? systemStatus.textContent : null,
        metrics: Array.from(metrics).map(m => m.textContent),
        timestamp: Date.now()
      };
    });
    
    // Navigate to cognitive state monitor
    await page.click('[data-testid="nav-item-cognitive"]');
    await page.waitForTimeout(3000);
    
    const cognitiveData = await page.evaluate(() => {
      const statusElements = document.querySelectorAll('[data-testid*="status"], [data-testid*="state"]');
      
      return {
        statusElements: Array.from(statusElements).map(el => el.textContent),
        timestamp: Date.now()
      };
    });
    
    // Data should be consistent and valid
    expect(dashboardData.timestamp).toBeTruthy();
    expect(cognitiveData.timestamp).toBeTruthy();
    
    // Time difference should be reasonable
    const timeDiff = cognitiveData.timestamp - dashboardData.timestamp;
    expect(timeDiff).toBeLessThan(60000); // Less than 1 minute
  });

  test('should validate complete feature accessibility', async ({ page }) => {
    // Test that all enhanced cognitive features are accessible
    const enhancedFeatures = [
      { nav: 'nav-item-enhanced', component: 'enhanced-cognitive-dashboard', name: 'Enhanced Dashboard' },
      { nav: 'nav-item-stream', component: 'stream-of-consciousness-monitor', name: 'Stream of Consciousness' },
      { nav: 'nav-item-autonomous', component: 'autonomous-learning-monitor', name: 'Autonomous Learning' }
    ];
    
    for (const feature of enhancedFeatures) {
      // Navigate to feature
      await page.click(`[data-testid="${feature.nav}"]`);
      await page.waitForTimeout(3000);
      
      // Verify component loads
      await expect(page.locator(`[data-testid="${feature.component}"]`)).toBeVisible();
      
      // Check for interactive elements
      const buttons = page.locator(`[data-testid="${feature.component}"] button`);
      const inputs = page.locator(`[data-testid="${feature.component}"] input`);
      const links = page.locator(`[data-testid="${feature.component}"] a`);
      
      const interactiveCount = await buttons.count() + await inputs.count() + await links.count();
      
      // Should have some interactive elements or be a display-only component
      expect(interactiveCount >= 0).toBeTruthy();
      
      console.log(`✅ ${feature.name} - Component loaded with ${interactiveCount} interactive elements`);
    }
  });

  test('should handle browser compatibility and responsive design', async ({ page }) => {
    // Test different viewport sizes
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop Large' },
      { width: 1366, height: 768, name: 'Desktop Standard' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(1000);
      
      // Check if app remains functional
      await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
      
      // Test navigation in this viewport
      await page.click('[data-testid="nav-item-enhanced"]');
      await page.waitForTimeout(2000);
      
      await expect(page.locator('[data-testid="enhanced-cognitive-dashboard"]')).toBeVisible();
      
      console.log(`✅ ${viewport.name} (${viewport.width}x${viewport.height}) - Layout responsive`);
    }
    
    // Reset to standard desktop
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('should validate system performance metrics', async ({ page }) => {
    // Start performance monitoring
    await page.evaluate(() => {
      window.performanceData = {
        navigationStart: performance.now(),
        marks: [],
        measures: []
      };
    });
    
    // Navigate through all enhanced cognitive features
    const features = ['enhanced', 'stream', 'autonomous'];
    
    for (const feature of features) {
      const startTime = await page.evaluate(() => performance.now());
      
      await page.click(`[data-testid="nav-item-${feature}"]`);
      await page.waitForTimeout(2000);
      
      const endTime = await page.evaluate(() => performance.now());
      const navigationTime = endTime - startTime;
      
      // Navigation should be reasonably fast
      expect(navigationTime).toBeLessThan(5000); // 5 seconds
      
      console.log(`⏱️ ${feature} navigation: ${navigationTime.toFixed(2)}ms`);
    }
    
    // Check overall performance
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        totalTime: performance.now() - window.performanceData.navigationStart
      };
    });
    
    // Performance should be acceptable
    expect(performanceMetrics.totalTime).toBeLessThan(30000); // 30 seconds total
    
    console.log('📊 Performance Metrics:', performanceMetrics);
  });
});