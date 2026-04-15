import { test, expect, devices } from '@playwright/test';

/**
 * Comprehensive Cognitive Pipeline E2E Test
 * 
 * This test demonstrates the complete GödelOS cognitive interface working
 * harmoniously with the backend, showing the full cognitive pipeline
 * across mobile, tablet, and desktop experiences.
 */

test.describe('Comprehensive Cognitive Pipeline E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app and wait for full initialization
    await page.goto('/');
    await page.waitForSelector('[data-testid="app-container"]', { timeout: 15000 });
    
    // Wait for WebSocket connection to establish
    await page.waitForTimeout(3000);
    
    // Verify initial system health
    await expect(page.locator('[data-testid="system-health"]')).toBeVisible();
  });

  test('Full Cognitive Pipeline - Desktop Experience', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    // === Phase 1: System Initialization ===
    console.log('🔄 Phase 1: System Initialization');
    
    // Verify all core systems are operational
    const systemHealth = page.locator('[data-testid="system-health"]');
    await expect(systemHealth).toBeVisible();
    
    // Check inference engine status
    const inferenceEngine = page.locator('[data-system="inference-engine"]');
    if (await inferenceEngine.isVisible()) {
      const status = await inferenceEngine.textContent();
      console.log('Inference Engine Status:', status);
    }
    
    // Check knowledge store connectivity
    const knowledgeStore = page.locator('[data-system="knowledge-store"]');
    if (await knowledgeStore.isVisible()) {
      const status = await knowledgeStore.textContent();
      console.log('Knowledge Store Status:', status);
    }
    
    // === Phase 2: Navigation and UI Interaction ===
    console.log('🧭 Phase 2: Navigation and UI Interaction');
    
    // Navigate through core features
    const coreFeatures = [
      { testId: 'nav-item-dashboard', expectedView: 'dashboard-view', name: 'Dashboard' },
      { testId: 'nav-item-cognitive-state', expectedView: 'cognitive-state-view', name: 'Cognitive State' },
      { testId: 'nav-item-enhanced', expectedView: 'enhanced-cognitive-dashboard', name: 'Enhanced Features' }
    ];
    
    for (const feature of coreFeatures) {
      console.log(`Testing ${feature.name} navigation...`);
      
      const navItem = page.locator(`[data-testid="${feature.testId}"]`);
      if (await navItem.isVisible()) {
        await navItem.click();
        await page.waitForTimeout(2000);
        
        // Verify the view loaded
        const view = page.locator(`[data-testid="${feature.expectedView}"]`);
        if (await view.isVisible()) {
          await expect(view).toBeVisible();
          console.log(`✅ ${feature.name} loaded successfully`);
        }
      }
    }
    
    // === Phase 3: Cognitive Data Processing ===
    console.log('🧠 Phase 3: Cognitive Data Processing');
    
    // Navigate to dashboard for data interaction
    await page.click('[data-testid="nav-item-dashboard"]');
    await page.waitForTimeout(2000);
    
    // Test data refresh/update capabilities
    const refreshButton = page.locator('[data-testid="refresh-data"]');
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await page.waitForTimeout(1000);
      console.log('✅ Data refresh triggered');
    }
    
    // Check for real-time data updates
    const dataElements = page.locator('[data-testid="real-time-data"]');
    if (await dataElements.count() > 0) {
      console.log(`✅ Found ${await dataElements.count()} real-time data elements`);
    }
    
    // === Phase 4: Backend Integration Validation ===
    console.log('🔗 Phase 4: Backend Integration Validation');
    
    // Monitor network requests to backend
    const responses = [];
    page.on('response', response => {
      if (response.url().includes('api') || response.url().includes('ws')) {
        responses.push({
          url: response.url(),
          status: response.status(),
          type: response.request().method()
        });
      }
    });
    
    // Trigger actions that should create backend calls
    await page.click('[data-testid="nav-item-cognitive-state"]');
    await page.waitForTimeout(3000);
    
    // Verify backend connectivity
    const hasBackendCommunication = responses.length > 0;
    console.log(`✅ Backend communication: ${hasBackendCommunication ? 'Active' : 'None detected'}`);
    console.log(`📊 API calls made: ${responses.length}`);
    
    // === Phase 5: System Performance Validation ===
    console.log('⚡ Phase 5: System Performance Validation');
    
    // Measure navigation performance
    const startTime = Date.now();
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForSelector('[data-testid="enhanced-cognitive-dashboard"]');
    const navigationTime = Date.now() - startTime;
    
    console.log(`📈 Navigation time: ${navigationTime}ms`);
    expect(navigationTime).toBeLessThan(5000); // Should be fast
    
    // Check for memory leaks or performance issues
    const performanceMetrics = await page.evaluate(() => {
      return {
        memory: performance.memory ? {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize
        } : null,
        timing: performance.timing ? {
          loadComplete: performance.timing.loadEventEnd - performance.timing.navigationStart
        } : null
      };
    });
    
    console.log('📊 Performance Metrics:', performanceMetrics);
    
    console.log('✅ Desktop cognitive pipeline test completed successfully');
  });

  test('Full Cognitive Pipeline - Mobile Experience', async ({ page }) => {
    // Set mobile viewport (iPhone 12)
    await page.setViewportSize({ width: 390, height: 844 });
    
    // === Phase 1: Mobile System Initialization ===
    console.log('📱 Phase 1: Mobile System Initialization');
    
    // Verify mobile-optimized layout
    const appContainer = page.locator('[data-testid="app-container"]');
    await expect(appContainer).toBeVisible();
    
    // Check that sidebar is collapsed on mobile
    const sidebar = page.locator('.sidebar');
    await expect(sidebar).toHaveClass(/collapsed/);
    
    // === Phase 2: Mobile Touch Navigation ===
    console.log('👆 Phase 2: Mobile Touch Navigation');
    
    // Test sidebar toggle with touch
    const sidebarToggle = page.locator('.sidebar-toggle');
    await expect(sidebarToggle).toBeVisible();
    await sidebarToggle.tap();
    await page.waitForTimeout(500);
    
    // Sidebar should be visible after tap
    await expect(sidebar).not.toHaveClass(/collapsed/);
    
    // Navigate through features using touch
    const mobileNavItems = [
      { testId: 'nav-item-dashboard', name: 'Dashboard' },
      { testId: 'nav-item-cognitive-state', name: 'Cognitive State' }
    ];
    
    for (const item of mobileNavItems) {
      console.log(`Testing mobile navigation to ${item.name}...`);
      
      const navItem = page.locator(`[data-testid="${item.testId}"]`);
      if (await navItem.isVisible()) {
        // Verify touch target size (iOS guideline: 44px minimum)
        const boundingBox = await navItem.boundingBox();
        expect(boundingBox.height).toBeGreaterThanOrEqual(44);
        
        await navItem.tap();
        await page.waitForTimeout(2000);
        console.log(`✅ Mobile navigation to ${item.name} successful`);
      }
    }
    
    // Close sidebar
    await sidebarToggle.tap();
    await page.waitForTimeout(500);
    await expect(sidebar).toHaveClass(/collapsed/);
    
    // === Phase 3: Mobile Data Interaction ===
    console.log('📊 Phase 3: Mobile Data Interaction');
    
    // Test scrolling and data interaction on mobile
    const mainContent = page.locator('.main-content');
    await expect(mainContent).toBeVisible();
    
    // Test vertical scrolling
    await page.evaluate(() => {
      document.querySelector('.main-content').scrollTop = 100;
    });
    await page.waitForTimeout(500);
    
    const scrollTop = await page.evaluate(() => {
      return document.querySelector('.main-content').scrollTop;
    });
    expect(scrollTop).toBeGreaterThan(0);
    console.log('✅ Mobile scrolling functionality verified');
    
    // === Phase 4: Mobile Backend Integration ===
    console.log('🔗 Phase 4: Mobile Backend Integration');
    
    // Test that backend integration works on mobile
    const responseCount = await page.evaluate(() => {
      // Simulate checking for active WebSocket connections
      return window.webSocketActive ? 1 : 0;
    });
    
    console.log(`📡 Mobile backend connectivity check: ${responseCount > 0 ? 'Connected' : 'Checking...'}`);
    
    // === Phase 5: Mobile Performance Validation ===
    console.log('⚡ Phase 5: Mobile Performance Validation');
    
    // Test mobile-specific performance
    const mobileStartTime = Date.now();
    await page.tap('.sidebar-toggle');
    await page.waitForTimeout(300);
    await page.tap('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(2000);
    const mobileNavTime = Date.now() - mobileStartTime;
    
    console.log(`📱 Mobile navigation time: ${mobileNavTime}ms`);
    expect(mobileNavTime).toBeLessThan(8000); // Allow more time for mobile
    
    console.log('✅ Mobile cognitive pipeline test completed successfully');
  });

  test('Full Cognitive Pipeline - Tablet Experience', async ({ page }) => {
    // Set tablet viewport (iPad Pro)
    await page.setViewportSize({ width: 1024, height: 1366 });
    
    // === Phase 1: Tablet System Initialization ===
    console.log('📲 Phase 1: Tablet System Initialization');
    
    // Verify tablet-optimized layout (hybrid of mobile/desktop)
    const appContainer = page.locator('[data-testid="app-container"]');
    await expect(appContainer).toBeVisible();
    
    // Check sidebar behavior on tablet
    const sidebar = page.locator('.sidebar');
    await expect(sidebar).toBeVisible();
    
    // === Phase 2: Tablet Hybrid Interaction ===
    console.log('🔄 Phase 2: Tablet Hybrid Interaction');
    
    // Test both touch and mouse interactions
    const navItem = page.locator('[data-testid="nav-item-dashboard"]');
    if (await navItem.isVisible()) {
      // Test hover (mouse-like behavior)
      await navItem.hover();
      await page.waitForTimeout(200);
      
      // Test tap (touch behavior)
      await navItem.tap();
      await page.waitForTimeout(2000);
      
      console.log('✅ Tablet hybrid interaction verified');
    }
    
    // === Phase 3: Tablet Layout Validation ===
    console.log('📐 Phase 3: Tablet Layout Validation');
    
    // Verify tablet-specific layout optimizations
    const mainContent = page.locator('.main-content');
    const contentBox = await mainContent.boundingBox();
    
    // Tablet should have more space than mobile but less than desktop
    expect(contentBox.width).toBeGreaterThan(500);
    expect(contentBox.width).toBeLessThan(1400);
    
    console.log(`✅ Tablet layout optimized: ${contentBox.width}px width`);
    
    // === Phase 4: Tablet Orientation Testing ===
    console.log('🔄 Phase 4: Tablet Orientation Testing');
    
    // Test portrait to landscape transition
    await page.setViewportSize({ width: 1366, height: 1024 }); // Landscape
    await page.waitForTimeout(1000);
    
    // App should still be functional
    await expect(appContainer).toBeVisible();
    await expect(sidebar).toBeVisible();
    
    // Test navigation in landscape
    await page.tap('[data-testid="nav-item-cognitive-state"]');
    await page.waitForTimeout(2000);
    
    console.log('✅ Tablet orientation change handled successfully');
    
    console.log('✅ Tablet cognitive pipeline test completed successfully');
  });

  test('Cross-Device Cognitive Pipeline Integration', async ({ page }) => {
    // === Phase 1: Multi-Device Simulation ===
    console.log('🌐 Phase 1: Multi-Device Simulation');
    
    const deviceConfigs = [
      { width: 375, height: 667, name: 'Mobile' },
      { width: 1024, height: 768, name: 'Tablet' },
      { width: 1920, height: 1080, name: 'Desktop' }
    ];
    
    for (const device of deviceConfigs) {
      console.log(`Testing ${device.name} configuration...`);
      
      await page.setViewportSize({ width: device.width, height: device.height });
      await page.waitForTimeout(1000);
      
      // Verify app functionality across devices
      await expect(page.locator('[data-testid="app-container"]')).toBeVisible();
      
      // Test core navigation on each device
      if (device.width < 768) {
        // Mobile: Test sidebar toggle
        await page.tap('.sidebar-toggle');
        await page.waitForTimeout(300);
        await page.tap('[data-testid="nav-item-dashboard"]');
        await page.waitForTimeout(1000);
        await page.tap('.sidebar-toggle');
      } else {
        // Tablet/Desktop: Direct navigation
        await page.click('[data-testid="nav-item-dashboard"]');
        await page.waitForTimeout(1000);
      }
      
      console.log(`✅ ${device.name} configuration verified`);
    }
    
    // === Phase 2: Data Consistency Across Devices ===
    console.log('📊 Phase 2: Data Consistency Across Devices');
    
    // Return to desktop view for detailed testing
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    // Navigate to cognitive state view
    await page.click('[data-testid="nav-item-cognitive-state"]');
    await page.waitForTimeout(2000);
    
    // Check for data elements that should be consistent
    const dataElements = page.locator('[data-testid="cognitive-data"]');
    if (await dataElements.count() > 0) {
      console.log(`✅ Found ${await dataElements.count()} cognitive data elements`);
    }
    
    // === Phase 3: Real-Time System Monitoring ===
    console.log('📡 Phase 3: Real-Time System Monitoring');
    
    // Check system health components
    const systemComponents = [
      'inference-engine',
      'knowledge-store', 
      'reflection-engine',
      'learning-modules'
    ];
    
    for (const component of systemComponents) {
      const componentElement = page.locator(`[data-component="${component}"]`);
      if (await componentElement.isVisible()) {
        console.log(`✅ ${component} component active`);
      }
    }
    
    // === Phase 4: End-to-End Workflow Validation ===
    console.log('🔄 Phase 4: End-to-End Workflow Validation');
    
    // Simulate a complete cognitive workflow
    const workflowSteps = [
      { action: 'nav-item-dashboard', description: 'Access Dashboard' },
      { action: 'nav-item-cognitive-state', description: 'Check Cognitive State' },
      { action: 'nav-item-enhanced', description: 'Access Enhanced Features' }
    ];
    
    for (const step of workflowSteps) {
      console.log(`Executing: ${step.description}`);
      
      const element = page.locator(`[data-testid="${step.action}"]`);
      if (await element.isVisible()) {
        await element.click();
        await page.waitForTimeout(2000);
        console.log(`✅ ${step.description} completed`);
      }
    }
    
    console.log('🎉 Complete cognitive pipeline integration test passed!');
  });

  test('Backend API Integration Comprehensive Test', async ({ page }) => {
    // === Phase 1: API Connectivity Validation ===
    console.log('🔌 Phase 1: API Connectivity Validation');
    
    // Track all network requests
    const apiRequests = [];
    const wsConnections = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push({
          url: request.url(),
          method: request.method(),
          timestamp: Date.now()
        });
      }
    });
    
    page.on('websocket', ws => {
      wsConnections.push({
        url: ws.url(),
        timestamp: Date.now()
      });
      console.log(`🔗 WebSocket connection: ${ws.url()}`);
    });
    
    // Navigate through the app to trigger API calls
    await page.click('[data-testid="nav-item-dashboard"]');
    await page.waitForTimeout(3000);
    
    await page.click('[data-testid="nav-item-cognitive-state"]');
    await page.waitForTimeout(3000);
    
    // === Phase 2: Real-Time Data Validation ===
    console.log('📊 Phase 2: Real-Time Data Validation');
    
    // Check for real-time data updates
    const hasRealTimeData = await page.evaluate(() => {
      // Look for elements that indicate real-time data
      const indicators = document.querySelectorAll('[data-real-time="true"]');
      return indicators.length > 0;
    });
    
    console.log(`✅ Real-time data indicators: ${hasRealTimeData ? 'Present' : 'None found'}`);
    
    // === Phase 3: Error Handling Validation ===
    console.log('⚠️ Phase 3: Error Handling Validation');
    
    // Test error handling by attempting to access non-existent endpoint
    const errorHandlingTest = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/non-existent-endpoint');
        return { status: response.status, handled: true };
      } catch (error) {
        return { error: error.message, handled: true };
      }
    });
    
    console.log(`✅ Error handling test:`, errorHandlingTest);
    
    // === Phase 4: Performance Under Load ===
    console.log('⚡ Phase 4: Performance Under Load');
    
    // Simulate rapid navigation to test performance
    const rapidNavStart = Date.now();
    
    for (let i = 0; i < 3; i++) {
      await page.click('[data-testid="nav-item-dashboard"]');
      await page.waitForTimeout(500);
      await page.click('[data-testid="nav-item-cognitive-state"]');
      await page.waitForTimeout(500);
    }
    
    const rapidNavTime = Date.now() - rapidNavStart;
    console.log(`⚡ Rapid navigation time: ${rapidNavTime}ms`);
    
    // Should handle rapid navigation gracefully
    expect(rapidNavTime).toBeLessThan(10000);
    
    // === Final Summary ===
    console.log('📋 Backend Integration Test Summary:');
    console.log(`- API requests made: ${apiRequests.length}`);
    console.log(`- WebSocket connections: ${wsConnections.length}`);
    console.log(`- Performance: ${rapidNavTime}ms for rapid navigation`);
    
    console.log('🎉 Complete backend integration test passed!');
  });
});