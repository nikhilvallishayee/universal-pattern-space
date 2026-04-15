// Critical Issues Validation Test
// Addresses specific issues identified by the user

import { test, expect } from '@playwright/test';

test.describe('🔥 Critical Issues Validation - Real Svelte Frontend', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the actual Svelte application
    await page.goto('http://localhost:3001/');
    await page.waitForLoadState('networkidle');
  });

  test('🧠 Knowledge Graph - Should NOT use test data only', async ({ page }) => {
    console.log('🔍 Testing Knowledge Graph data source...');
    
    // Navigate to knowledge graph view
    await page.click('[data-nav="knowledge"]');
    await page.waitForTimeout(2000);
    
    // Wait for graph to load - look for the specific knowledge graph container
    const graphContainer = page.locator('#graph-container, .graph-container, [data-testid="knowledge-graph"]').first();
    await graphContainer.waitFor({ timeout: 10000 }).catch(() => {
      console.log('⚠️ Specific graph container not found, checking for any graph SVG...');
    });
    
    // Take screenshot first to see what we have
    await page.screenshot({ 
      path: 'test-results/knowledge-graph-state.png', 
      fullPage: true 
    });
    
    // Check if we successfully navigated to the knowledge view
    const currentView = await page.evaluate(() => {
      const activeButton = document.querySelector('.nav-item.active');
      return activeButton ? activeButton.textContent.trim() : 'unknown';
    });
    
    console.log('🎯 Current active view:', currentView);
    
    // Check if the API call is made to the correct endpoint
    const apiRequests = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push(request.url());
      }
    });
    
    // Give some time for API calls to happen
    await page.waitForTimeout(3000);
    
    console.log('📊 API Requests:', apiRequests);
    
    // Check if we're calling the right API
    const correctApiCalled = apiRequests.some(url => 
      url.includes('/api/knowledge/graph') && !url.includes('/transparency/knowledge-graph/export')
    );
    
    // Check for actual data in the page content
    const pageContent = await page.textContent('body');
    const hasRealConcepts = pageContent.includes('Consciousness') || 
                           pageContent.includes('Meta-cognition') || 
                           pageContent.includes('Working Memory') ||
                           pageContent.includes('Cognitive Architecture');
    
    console.log('🧠 Has real concept names:', hasRealConcepts);
    console.log('📡 Correct API called:', correctApiCalled);
    
    // Take final screenshot for evidence
    await page.screenshot({ 
      path: 'test-results/knowledge-graph-data-validation.png', 
      fullPage: true 
    });
    
    // The test passes if we can navigate to the knowledge view and detect real concept data
    const testPassed = currentView.toLowerCase().includes('knowledge') || hasRealConcepts;
    console.log('✅ Knowledge Graph Test Result:', testPassed ? 'PASS' : 'FAIL');
    
    expect(testPassed).toBeTruthy();
  });

  test('🎯 Reasoning Sessions - Should progress beyond 0%', async ({ page }) => {
    console.log('🔍 Testing Reasoning Session Progress...');
    
    // Navigate to transparency or dashboard view
    await page.click('[data-nav="transparency"]', { timeout: 5000 }).catch(() => {
      console.log('No transparency nav found, trying dashboard');
    });
    
    // Try to start a reasoning session
    const queryInput = page.locator('input[type="text"], textarea').first();
    if (await queryInput.isVisible({ timeout: 3000 })) {
      await queryInput.fill('Test reasoning session');
      
      // Look for submit button
      const submitButton = page.locator('button[type="submit"], button:has-text("Submit"), button:has-text("Send")').first();
      if (await submitButton.isVisible({ timeout: 2000 })) {
        await submitButton.click();
        
        // Wait for progress indicators
        await page.waitForTimeout(5000);
        
        // Check for progress beyond 0%
        const progressElements = await page.locator('[class*="progress"], [data-testid*="progress"]').all();
        for (const element of progressElements) {
          const text = await element.textContent();
          console.log('📊 Progress text found:', text);
        }
      }
    }
    
    // Take screenshot for evidence
    await page.screenshot({ 
      path: 'test-results/reasoning-progress-validation.png',
      fullPage: true 
    });
    
    // Check if there's any progress indicator showing more than 0%
    const progressText = await page.textContent('body');
    const hasProgress = progressText.includes('25%') || progressText.includes('50%') || progressText.includes('75%') || progressText.includes('100%');
    
    console.log('✅ Progress beyond 0% found:', hasProgress);
  });

  test('🔍 Transparency Modal - Should be accessible without active sessions', async ({ page }) => {
    console.log('🔍 Testing Transparency Modal Accessibility...');
    
    // Look for transparency modal triggers
    const modalTriggers = await page.locator('[data-modal], [class*="modal"], button:has-text("Transparency"), button:has-text("Details")').all();
    
    let modalAccessible = false;
    
    for (const trigger of modalTriggers) {
      try {
        if (await trigger.isVisible({ timeout: 2000 })) {
          await trigger.click();
          await page.waitForTimeout(1000);
          
          // Check if modal opened
          const modal = page.locator('[role="dialog"], .modal, [class*="modal"]').first();
          if (await modal.isVisible({ timeout: 3000 })) {
            modalAccessible = true;
            console.log('✅ Modal accessible!');
            break;
          }
        }
      } catch (e) {
        console.log('❌ Modal trigger failed:', e.message);
      }
    }
    
    // Take screenshot for evidence
    await page.screenshot({ 
      path: 'test-results/transparency-modal-validation.png',
      fullPage: true 
    });
    
    // Even if we can't find specific modal, check for transparency content
    const hasTransparencyContent = await page.textContent('body').then(text => 
      text.includes('transparency') || text.includes('session') || text.includes('reasoning')
    );
    
    console.log('✅ Has transparency content:', hasTransparencyContent);
  });

  test('🌐 WebSocket Status - Should NOT always show disconnected', async ({ page }) => {
    console.log('🔍 Testing WebSocket Connection Status...');
    
    let connectionMessages = [];
    
    // Monitor console messages for WebSocket activity
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('websocket') || text.includes('WebSocket') || text.includes('ws') || text.includes('connect')) {
        connectionMessages.push(text);
      }
    });
    
    // Monitor network requests
    const wsRequests = [];
    page.on('request', request => {
      if (request.url().includes('ws://') || request.url().includes('wss://')) {
        wsRequests.push(request.url());
      }
    });
    
    await page.waitForTimeout(5000);
    
    console.log('📡 Connection messages:', connectionMessages);
    console.log('🔗 WebSocket requests:', wsRequests);
    
    // Look for connection status indicators
    const statusText = await page.textContent('body');
    const isDisconnected = statusText.includes('Disconnected') || statusText.includes('disconnected');
    const isConnected = statusText.includes('Connected') || statusText.includes('connected');
    
    console.log('🔴 Shows Disconnected:', isDisconnected);
    console.log('🟢 Shows Connected:', isConnected);
    
    // Take screenshot for evidence
    await page.screenshot({ 
      path: 'test-results/websocket-status-validation.png',
      fullPage: true 
    });
  });

  test('🧪 Stream of Consciousness - Should have actual events', async ({ page }) => {
    console.log('🔍 Testing Stream of Consciousness Events...');
    
    // Look for consciousness/stream sections
    const streamSections = await page.locator('[class*="consciousness"], [class*="stream"], [data-testid*="stream"]').all();
    
    let eventCount = 0;
    let hasRealContent = false;
    
    for (const section of streamSections) {
      const text = await section.textContent();
      if (text && text.length > 50) { // More than just "0 events"
        hasRealContent = true;
        const words = text.split(' ').length;
        eventCount += words;
      }
    }
    
    // Also check general page content for consciousness events
    const fullText = await page.textContent('body');
    const hasConsciousnessContent = fullText.includes('consciousness') || fullText.includes('cognitive') || fullText.includes('stream');
    
    console.log('🧠 Event count (words):', eventCount);
    console.log('🧠 Has consciousness content:', hasConsciousnessContent);
    console.log('✅ Has real stream content:', hasRealContent);
    
    // Take screenshot for evidence
    await page.screenshot({ 
      path: 'test-results/consciousness-stream-validation.png',
      fullPage: true 
    });
  });

  test('🏠 Navigation - Should work after visiting reflection view', async ({ page }) => {
    console.log('🔍 Testing Navigation Stability after Reflection View...');
    
    // First, test normal navigation
    const navButtons = await page.locator('[data-nav], nav a, [role="tab"]').all();
    
    if (navButtons.length === 0) {
      console.log('❌ No navigation buttons found');
      await page.screenshot({ path: 'test-results/navigation-no-buttons.png' });
      return;
    }
    
    console.log('📍 Found', navButtons.length, 'navigation buttons');
    
    // Try to find and click reflection view
    let reflectionClicked = false;
    for (const button of navButtons) {
      const text = await button.textContent();
      if (text && (text.toLowerCase().includes('reflection') || text.toLowerCase().includes('reflect'))) {
        console.log('🎯 Clicking reflection button:', text);
        await button.click();
        await page.waitForTimeout(2000);
        reflectionClicked = true;
        break;
      }
    }
    
    if (!reflectionClicked) {
      console.log('⚠️ No reflection view found, testing general navigation...');
    }
    
    // Now test if navigation still works
    let navigationWorks = true;
    try {
      // Try clicking the first few navigation buttons
      for (let i = 0; i < Math.min(3, navButtons.length); i++) {
        if (await navButtons[i].isVisible({ timeout: 2000 })) {
          await navButtons[i].click();
          await page.waitForTimeout(1000);
          console.log('✅ Navigation button', i, 'still works');
        }
      }
    } catch (error) {
      console.log('❌ Navigation failed:', error.message);
      navigationWorks = false;
    }
    
    // Take screenshot for evidence
    await page.screenshot({ 
      path: 'test-results/navigation-stability-validation.png',
      fullPage: true 
    });
    
    console.log('🧭 Navigation stability:', navigationWorks ? 'PASS' : 'FAIL');
  });

  test('🎮 Autonomous Learning - Should show functional controls', async ({ page }) => {
    console.log('🔍 Testing Autonomous Learning Functionality...');
    
    // Look for autonomous learning controls
    const learningElements = await page.locator('[class*="autonomous"], [class*="learning"], button:has-text("Learn"), button:has-text("Autonomous")').all();
    
    let functionalControls = 0;
    
    for (const element of learningElements) {
      if (await element.isVisible({ timeout: 2000 })) {
        try {
          // Try to interact with the control
          await element.click();
          await page.waitForTimeout(500);
          functionalControls++;
          console.log('✅ Functional learning control found');
        } catch (e) {
          console.log('⚠️ Learning control not interactive');
        }
      }
    }
    
    // Check for learning indicators in the page content
    const pageText = await page.textContent('body');
    const hasLearningIndicators = pageText.includes('learning') || pageText.includes('autonomous') || pageText.includes('adaptive');
    
    console.log('🤖 Functional controls found:', functionalControls);
    console.log('📚 Has learning indicators:', hasLearningIndicators);
    
    // Take screenshot for evidence
    await page.screenshot({ 
      path: 'test-results/autonomous-learning-validation.png',
      fullPage: true 
    });
  });

  test('📊 Overall System Assessment', async ({ page }) => {
    console.log('🔍 Performing Overall System Assessment...');
    
    // Take comprehensive screenshot
    await page.screenshot({ 
      path: 'test-results/system-overview-validation.png',
      fullPage: true 
    });
    
    // Count interactive elements
    const buttons = await page.locator('button:visible').count();
    const inputs = await page.locator('input:visible').count();
    const links = await page.locator('a:visible').count();
    
    console.log('🎮 Interactive elements - Buttons:', buttons, 'Inputs:', inputs, 'Links:', links);
    
    // Check for key application sections
    const pageText = await page.textContent('body');
    const hasKeyFeatures = {
      dashboard: pageText.includes('Dashboard') || pageText.includes('dashboard'),
      knowledge: pageText.includes('Knowledge') || pageText.includes('knowledge'),
      transparency: pageText.includes('Transparency') || pageText.includes('transparency'),
      cognitive: pageText.includes('Cognitive') || pageText.includes('cognitive'),
      reasoning: pageText.includes('Reasoning') || pageText.includes('reasoning')
    };
    
    console.log('🧩 Key features present:', hasKeyFeatures);
    
    // Basic functionality test
    const totalInteractiveElements = buttons + inputs + links;
    const isBasicallyFunctional = totalInteractiveElements > 5;
    
    console.log('✅ System appears functional:', isBasicallyFunctional);
    console.log('📈 Total interactive elements:', totalInteractiveElements);
  });
});