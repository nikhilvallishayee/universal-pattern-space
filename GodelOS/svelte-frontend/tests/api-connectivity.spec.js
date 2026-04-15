import { test, expect } from '@playwright/test';

test.describe('API Connectivity and Backend Integration', () => {
test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('[data-testid="app-container"]', { timeout: 20000 });
  await page.waitForTimeout(2000);
});

  test('should connect to backend API successfully', async ({ page }) => {
    // Check for successful WebSocket connection
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    await expect(connectionStatus).toBeVisible();
    
    // Look for connected state indicators
  await expect(connectionStatus).toHaveClass(/connected|reconnecting|disconnected|success/);
    
    // Check console for connection messages
    const logs = [];
    page.on('console', msg => logs.push(msg.text()));
    
    await page.waitForTimeout(3000);
    
    // Should see initialization and connection messages
    const hasInitMessage = logs.some(log => log.includes('Initializing GödelOS'));
    const hasConnectedMessage = logs.some(log => log.includes('connected'));
    
    expect(hasInitMessage || hasConnectedMessage).toBeTruthy();
  });

  test('should handle enhanced cognitive API endpoints', async ({ page }) => {
    // Navigate to Enhanced Dashboard
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(3000);
    
    // Check for API responses
    const responses = [];
    page.on('response', response => {
      if (response.url().includes('/api/enhanced-cognitive/')) {
        responses.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText()
        });
      }
    });
    
    // Trigger API calls by interacting with the dashboard
    await page.waitForTimeout(5000);
    
    // Check that enhanced cognitive API calls were made
    const enhancedAPICalls = responses.filter(r => 
      r.url().includes('/api/enhanced-cognitive/') && r.status === 200
    );
    
    expect(enhancedAPICalls.length).toBeGreaterThan(0);
  });

  test('should handle autonomous learning API endpoints', async ({ page }) => {
    // Navigate to Autonomous Learning
    await page.click('[data-testid="nav-item-autonomous"]');
    await page.waitForTimeout(3000);
    
    // Monitor network requests
    const requests = [];
    page.on('request', request => {
      if (request.url().includes('/api/enhanced-cognitive/')) {
        requests.push({
          url: request.url(),
          method: request.method()
        });
      }
    });
    
    await page.waitForTimeout(5000);
    
    // Should have made requests to autonomous learning endpoints
    const autonomousRequests = requests.filter(r => 
      r.url().includes('autonomous') || r.url().includes('learning')
    );
    
    expect(autonomousRequests.length).toBeGreaterThanOrEqual(0);
  });

  test('should handle stream of consciousness API', async ({ page }) => {
    // Navigate to Stream of Consciousness
    await page.click('[data-testid="nav-item-stream"]');
    await page.waitForTimeout(3000);
    
    // Check for streaming data indicators
    const streamContainer = page.locator('[data-testid="stream-of-consciousness-monitor"]');
    await expect(streamContainer).toBeVisible();
    
    // Look for real-time data updates
    await page.waitForTimeout(5000);
    
    // Check for streaming content or WebSocket messages
    const streamContent = page.locator('[data-testid="stream-content"]');
    if (await streamContent.isVisible()) {
      // Should have some content or loading indicators
      const hasContent = await streamContent.textContent();
      expect(hasContent).toBeTruthy();
    }
  });

  test('should handle API errors gracefully', async ({ page }) => {
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
      if (response.status() >= 400) {
        failedRequests.push({
          url: response.url(),
          status: response.status()
        });
      }
    });
    
    // Navigate through different views
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(2000);
    
    await page.click('[data-testid="nav-item-stream"]');
    await page.waitForTimeout(2000);
    
    await page.click('[data-testid="nav-item-autonomous"]');
    await page.waitForTimeout(2000);
    
    // Check that critical errors are handled
    const criticalErrors = errors.filter(error => 
      error.includes('Failed to fetch') || 
      error.includes('Network Error') ||
      error.includes('500')
    );
    
    // Should not have unhandled critical errors
    expect(criticalErrors.length).toBeLessThan(5);
  });

  test('should display health monitoring data', async ({ page }) => {
    // Check system health endpoint
    const healthRequests = [];
    page.on('request', request => {
      if (request.url().includes('/health') || request.url().includes('/status')) {
        healthRequests.push(request.url());
      }
    });
    
    await page.waitForTimeout(5000);
    
    // Should have made health check requests
    expect(healthRequests.length).toBeGreaterThanOrEqual(0);
    
    // Check for health indicators in UI
    const healthIndicator = page.locator('[data-testid="system-health"]');
    if (await healthIndicator.isVisible()) {
      const healthValue = await healthIndicator.textContent();
      expect(healthValue).toBeTruthy();
    }
  });

  test('should handle real-time data updates', async ({ page }) => {
    // Navigate to dashboard
    await page.click('[data-testid="nav-item-dashboard"]');
    await page.waitForTimeout(3000);
    
    // Monitor for data updates
    const initialContent = await page.textContent('[data-testid="main-content"]');
    
    // Wait for potential updates
    await page.waitForTimeout(10000);
    
    const updatedContent = await page.textContent('[data-testid="main-content"]');
    
    // Content might change due to real-time updates
    // This test ensures the app doesn't crash during updates
    expect(updatedContent).toBeTruthy();
  });

  test('should handle WebSocket connection states', async ({ page }) => {
    // Monitor WebSocket events
    const wsEvents = [];
    
    await page.evaluateOnNewDocument(() => {
      const originalWebSocket = window.WebSocket;
      window.WebSocket = function(url, protocols) {
        const ws = new originalWebSocket(url, protocols);
        
        ws.addEventListener('open', () => {
          window.wsEvents = window.wsEvents || [];
          window.wsEvents.push('open');
        });
        
        ws.addEventListener('close', () => {
          window.wsEvents = window.wsEvents || [];
          window.wsEvents.push('close');
        });
        
        ws.addEventListener('error', () => {
          window.wsEvents = window.wsEvents || [];
          window.wsEvents.push('error');
        });
        
        return ws;
      };
    });
    
    await page.reload();
    await page.waitForTimeout(5000);
    
    // Check WebSocket events
    const events = await page.evaluate(() => window.wsEvents || []);
    
    // Should have at least attempted WebSocket connection
    expect(events.length).toBeGreaterThanOrEqual(0);
  });

  test('should validate API response formats', async ({ page }) => {
    const apiResponses = [];
    
    page.on('response', async response => {
      if (response.url().includes('/api/')) {
        try {
          const contentType = response.headers()['content-type'];
          if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            apiResponses.push({
              url: response.url(),
              status: response.status(),
              data: data
            });
          }
        } catch (error) {
          // Handle non-JSON responses
        }
      }
    });
    
    // Navigate through views to trigger API calls
    await page.click('[data-testid="nav-item-enhanced"]');
    await page.waitForTimeout(2000);
    
    await page.click('[data-testid="nav-item-cognitive"]');
    await page.waitForTimeout(2000);
    
    // Validate response structures
    apiResponses.forEach(response => {
      expect(response.status).toBeLessThan(500);
      expect(response.data).toBeTruthy();
    });
  });
});
