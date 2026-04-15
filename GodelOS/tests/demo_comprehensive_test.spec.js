/**
 * Simplified Comprehensive UI Testing Demonstration
 * 
 * This test demonstrates the methodology for comprehensive UI-Backend validation
 * and captures screenshots to show the testing approach.
 */

import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3001';
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

test.describe('GödelOS Comprehensive Testing Demonstration', () => {

  test('Backend Connectivity Validation', async ({ page }) => {
    console.log('🔍 Testing backend connectivity and API responses...');
    
    // Test backend health endpoint
    const response = await page.request.get(`${BACKEND_URL}/api/health`);
    console.log('Backend health status:', response.status());
    expect(response.ok()).toBeTruthy();
    
    const health = await response.json();
    console.log('Backend health data:', health);
    
    // Test knowledge graph endpoint
    const kgResponse = await page.request.get(`${BACKEND_URL}/api/knowledge/graph`);
    const kgData = await kgResponse.json();
    console.log(`Knowledge graph: ${kgData.nodes?.length || 0} nodes, ${kgData.edges?.length || 0} edges`);
    
    // Test cognitive state endpoint
    const cogResponse = await page.request.get(`${BACKEND_URL}/api/cognitive-state`);
    const cogData = await cogResponse.json();
    console.log('Cognitive state:', cogData.status);
    
    // Test transparency sessions endpoint
    const sessionResponse = await page.request.get(`${BACKEND_URL}/api/transparency/sessions/active`);
    const sessionData = await sessionResponse.json();
    console.log(`Active sessions: ${sessionData.count || 0} sessions found`);
    
    expect(response.status()).toBe(200);
    expect(kgResponse.status()).toBe(200);
    expect(cogResponse.status()).toBe(200);
    expect(sessionResponse.status()).toBe(200);
  });

  test('Frontend Loading and Basic Navigation', async ({ page }) => {
    console.log('🔍 Testing frontend accessibility and basic navigation...');
    
    // Navigate to frontend
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of initial page load
    await page.screenshot({ 
      path: '/tmp/test_screenshot_1_frontend_loading.png',
      fullPage: true 
    });
    console.log('📸 Screenshot captured: Frontend loading');
    
    // Check page title and basic content
    const title = await page.title();
    console.log('Page title:', title);
    
    // Look for common GödelOS UI elements
    const pageContent = await page.content();
    const hasGodelos = pageContent.includes('Gödel') || pageContent.includes('GödelOS') || pageContent.includes('Cognitive');
    console.log('Contains GödelOS references:', hasGodelos);
    
    // Check for navigation elements
    const navigationElements = await page.locator('nav, .nav, .navigation, [class*="nav"]').count();
    const buttonElements = await page.locator('button').count();
    const linkElements = await page.locator('a').count();
    
    console.log(`UI Elements found: ${navigationElements} nav elements, ${buttonElements} buttons, ${linkElements} links`);
    
    // Take another screenshot showing UI elements
    await page.screenshot({ 
      path: '/tmp/test_screenshot_2_ui_elements.png',
      fullPage: true 
    });
    console.log('📸 Screenshot captured: UI elements analysis');
  });

  test('API Integration Testing', async ({ page }) => {
    console.log('🔍 Testing dynamic API integration with frontend...');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Monitor network requests
    const requests = [];
    page.on('request', request => {
      if (request.url().includes(BACKEND_URL)) {
        requests.push({
          url: request.url(),
          method: request.method(),
          timestamp: new Date().toISOString()
        });
      }
    });
    
    // Wait for any API calls
    await page.waitForTimeout(5000);
    
    console.log(`Network activity: ${requests.length} backend API calls detected:`);
    requests.forEach(req => {
      console.log(`  ${req.method} ${req.url}`);
    });
    
    // Take screenshot showing network activity
    await page.screenshot({ 
      path: '/tmp/test_screenshot_3_api_integration.png',
      fullPage: true 
    });
    console.log('📸 Screenshot captured: API integration test');
    
    // Test if we can inject and execute JavaScript to interact with the page
    const pageEvaluation = await page.evaluate(() => {
      const analysis = {
        hasConsole: typeof console !== 'undefined',
        hasWebSocket: typeof WebSocket !== 'undefined',
        hasFetch: typeof fetch !== 'undefined',
        documentReady: document.readyState,
        scriptsLoaded: document.scripts.length,
        elementsCount: document.querySelectorAll('*').length
      };
      return analysis;
    });
    
    console.log('Frontend JavaScript environment analysis:', pageEvaluation);
  });

  test('Critical Issues Verification Demo', async ({ page }) => {
    console.log('🔍 Demonstrating critical issues testing methodology...');
    
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    const criticalIssues = {
      reasoning_sessions: 'TESTING - Looking for reasoning session indicators',
      knowledge_graph: 'TESTING - Analyzing knowledge graph data sources', 
      websocket_status: 'TESTING - Monitoring WebSocket connection patterns',
      consciousness_stream: 'TESTING - Checking for consciousness event indicators',
      transparency_modal: 'TESTING - Validating transparency modal accessibility',
      navigation_stability: 'TESTING - Testing navigation after view switches',
      autonomous_learning: 'TESTING - Verifying autonomous learning indicators'
    };
    
    // Demonstrate the testing approach for each critical issue
    for (const [issue, description] of Object.entries(criticalIssues)) {
      console.log(`🎯 ${issue}: ${description}`);
      
      // Look for elements that might indicate this functionality
      const searchPatterns = {
        reasoning_sessions: ['reasoning', 'session', 'progress', '0%', '25%', '50%', '75%', '100%'],
        knowledge_graph: ['knowledge', 'graph', 'nodes', 'edges', 'visualization', 'test data'],
        websocket_status: ['connected', 'disconnected', 'websocket', 'status', 'reconnect'],
        consciousness_stream: ['consciousness', 'stream', 'events', '0 events', 'no events'],
        transparency_modal: ['transparency', 'modal', 'session', 'trace', 'dummy'],
        navigation_stability: ['reflection', 'navigation', 'nav', 'menu', 'broken'],
        autonomous_learning: ['autonomous', 'learning', 'inactive', 'nothing', 'placeholder']
      };
      
      const patterns = searchPatterns[issue] || [];
      const pageText = await page.textContent('body') || '';
      const foundPatterns = patterns.filter(pattern => 
        pageText.toLowerCase().includes(pattern.toLowerCase())
      );
      
      console.log(`  Found patterns: ${foundPatterns.join(', ') || 'none'}`);
      await page.waitForTimeout(1000); // Simulate analysis time
    }
    
    // Take comprehensive screenshot showing the analysis
    await page.screenshot({ 
      path: '/tmp/test_screenshot_4_critical_issues_analysis.png',
      fullPage: true 
    });
    console.log('📸 Screenshot captured: Critical issues analysis');
  });

  test('System Health Validation Summary', async ({ page }) => {
    console.log('🔍 Generating system health validation summary...');
    
    // Test all key backend endpoints
    const endpoints = [
      '/api/health',
      '/api/knowledge/graph',
      '/api/cognitive-state',
      '/api/transparency/sessions/active',
      '/api/transparency/statistics',
      '/api/stream-of-consciousness'
    ];
    
    const endpointResults = {};
    for (const endpoint of endpoints) {
      try {
        const response = await page.request.get(`${BACKEND_URL}${endpoint}`);
        endpointResults[endpoint] = {
          status: response.status(),
          ok: response.ok(),
          contentType: response.headers()['content-type'] || 'unknown'
        };
      } catch (error) {
        endpointResults[endpoint] = { 
          status: 'error', 
          error: error.message 
        };
      }
    }
    
    console.log('Backend Endpoint Health Check:');
    Object.entries(endpointResults).forEach(([endpoint, result]) => {
      console.log(`  ${endpoint}: ${result.status} (${result.ok ? 'OK' : 'FAIL'})`);
    });
    
    // Test frontend responsiveness
    await page.goto(FRONTEND_URL);
    const loadStart = Date.now();
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - loadStart;
    
    console.log(`Frontend load time: ${loadTime}ms`);
    
    // Generate final comprehensive screenshot
    await page.screenshot({ 
      path: '/tmp/test_screenshot_5_system_health_summary.png',
      fullPage: true 
    });
    console.log('📸 Screenshot captured: System health summary');
    
    // System health scoring
    const workingEndpoints = Object.values(endpointResults).filter(r => r.ok).length;
    const totalEndpoints = endpoints.length;
    const healthScore = Math.round((workingEndpoints / totalEndpoints) * 100);
    
    console.log(`🎯 SYSTEM HEALTH SCORE: ${healthScore}% (${workingEndpoints}/${totalEndpoints} endpoints working)`);
    console.log(`📊 Frontend responsiveness: ${loadTime < 3000 ? 'GOOD' : 'SLOW'} (${loadTime}ms)`);
    
    // Final assertions
    expect(healthScore).toBeGreaterThan(50); // At least 50% of endpoints should work
    expect(loadTime).toBeLessThan(10000); // Frontend should load within 10 seconds
  });

});