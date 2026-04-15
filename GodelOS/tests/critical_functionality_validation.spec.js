/**
 * Critical Functionality Validation Tests
 * 
 * These tests specifically target the critical issues identified:
 * - Reasoning sessions stuck at 0%
 * - Knowledge graph test data only
 * - WebSocket constantly disconnected  
 * - Stream of consciousness 0 events
 * - Transparency modal dummy data
 * - Navigation breaking after reflection view
 * - Autonomous learning non-functional
 * - Provenance being useless
 */

import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3001';
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

test.describe('Critical Functionality Issues Validation', () => {
  
  test('Issue 1: Reasoning Sessions Stuck at 0% - Deep Validation', async ({ page }) => {
    console.log('🔍 Deep testing reasoning session progression...');
    
    // Navigate to transparency view
    await page.goto(`${FRONTEND_URL}/#/transparency`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Take initial screenshot
    await page.screenshot({ 
      path: '/tmp/reasoning_sessions_initial.png',
      fullPage: true 
    });
    
    // Look for any way to start a reasoning session
    const sessionStartMethods = [
      { selector: 'text=Start Session', description: 'Start Session button' },
      { selector: 'text=New Session', description: 'New Session button' },
      { selector: 'text=Begin Reasoning', description: 'Begin Reasoning button' },
      { selector: 'input[placeholder*="query"], input[placeholder*="question"]', description: 'Query input field' },
      { selector: 'button:has-text("Query")', description: 'Query button' },
      { selector: 'button:has-text("Ask")', description: 'Ask button' }
    ];
    
    let sessionStarted = false;
    let startMethod = 'none';
    
    for (const method of sessionStartMethods) {
      try {
        const element = page.locator(method.selector);
        if (await element.count() > 0 && await element.first().isVisible()) {
          console.log(`Found session start method: ${method.description}`);
          
          if (method.selector.includes('input')) {
            // It's an input field
            await element.first().fill('Test reasoning session: What is consciousness?');
            
            // Look for associated submit button
            const submitButtons = [
              'button:has-text("Submit")',
              'button:has-text("Send")',
              'button:has-text("Start")',
              'button[type="submit"]'
            ];
            
            for (const submitSelector of submitButtons) {
              const submitBtn = page.locator(submitSelector);
              if (await submitBtn.count() > 0 && await submitBtn.first().isVisible()) {
                await submitBtn.first().click();
                startMethod = `${method.description} + ${submitSelector}`;
                sessionStarted = true;
                break;
              }
            }
          } else {
            // It's a button
            await element.first().click();
            startMethod = method.description;
            sessionStarted = true;
          }
          
          if (sessionStarted) break;
        }
      } catch (error) {
        console.log(`Failed to use ${method.description}:`, error.message);
      }
    }
    
    console.log(`Session started: ${sessionStarted} via ${startMethod}`);
    
    if (!sessionStarted) {
      // Try alternative: navigate to query interface and start from there
      await page.goto(`${FRONTEND_URL}/#/query`);
      await page.waitForTimeout(2000);
      
      const queryInput = page.locator('input, textarea').first();
      if (await queryInput.count() > 0) {
        await queryInput.fill('Test query for reasoning session');
        
        const submitBtn = page.locator('button').first();
        if (await submitBtn.count() > 0) {
          await submitBtn.click();
          sessionStarted = true;
          startMethod = 'Query interface';
          
          // Navigate back to transparency to check progress
          await page.waitForTimeout(2000);
          await page.goto(`${FRONTEND_URL}/#/transparency`);
          await page.waitForTimeout(2000);
        }
      }
    }
    
    if (sessionStarted) {
      // Wait for processing and monitor progress
      console.log('Monitoring reasoning session progress...');
      
      let progressChecks = [];
      for (let i = 0; i < 10; i++) {
        await page.waitForTimeout(2000);
        
        const pageContent = await page.textContent('body');
        
        // Extract all percentage values
        const percentageMatches = pageContent.match(/(\d+(?:\.\d+)?)%/g) || [];
        const percentages = percentageMatches.map(match => 
          parseFloat(match.replace('%', ''))
        );
        
        // Look for progress indicators
        const progressIndicators = {
          percentages: percentages,
          hasActiveSession: /active|processing|reasoning|working/i.test(pageContent),
          hasSteps: /step\s*\d+|phase\s*\d+/i.test(pageContent),
          hasTimestamp: /\d{2}:\d{2}|\d+\s*(?:second|minute)s?\s*ago/i.test(pageContent),
          stuckAtZero: pageContent.includes('0%') && !percentages.some(p => p > 0)
        };
        
        progressChecks.push({
          time: i * 2,
          indicators: progressIndicators,
          contentSample: pageContent.substring(0, 200)
        });
        
        // Early exit if we see clear progress
        if (percentages.some(p => p > 0 && p < 100)) {
          console.log(`Progress detected at check ${i}: ${percentages}`);
          break;
        }
      }
      
      // Take final screenshot
      await page.screenshot({ 
        path: '/tmp/reasoning_sessions_final.png',
        fullPage: true 
      });
      
      // Analyze progress
      const finalCheck = progressChecks[progressChecks.length - 1];
      const hasRealProgress = finalCheck.indicators.percentages.some(p => p > 0 && p <= 100);
      const sessionActive = finalCheck.indicators.hasActiveSession;
      const stuckAtZero = finalCheck.indicators.stuckAtZero;
      
      console.log('Progress analysis:', {
        hasRealProgress,
        sessionActive,
        stuckAtZero,
        finalPercentages: finalCheck.indicators.percentages
      });
      
      // Test expectations
      expect(sessionStarted, 'Should be able to start a reasoning session').toBeTruthy();
      expect(stuckAtZero, 'Session should not be stuck at 0%').toBeFalsy();
      expect(hasRealProgress || sessionActive, 'Should show progress or active processing').toBeTruthy();
      
    } else {
      console.error('❌ Cannot find any way to start a reasoning session');
      expect(sessionStarted, 'Should be able to start reasoning session').toBeTruthy();
    }
  });

  test('Issue 2: Knowledge Graph Test Data Only - Validation', async ({ page }) => {
    console.log('🔍 Validating knowledge graph data source...');
    
    await page.goto(`${FRONTEND_URL}/#/knowledge-graph`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    await page.screenshot({ 
      path: '/tmp/knowledge_graph_analysis.png',
      fullPage: true 
    });
    
    const pageContent = await page.textContent('body');
    
    // Check for explicit test data indicators
    const testDataMarkers = [
      'test data',
      'sample data',
      'mock data',
      'dummy data',
      'placeholder',
      'Test Node',
      'Sample Node', 
      'Example',
      'Lorem ipsum',
      'using sample data',
      'no backend data available'
    ];
    
    const foundTestMarkers = testDataMarkers.filter(marker => 
      pageContent.toLowerCase().includes(marker.toLowerCase())
    );
    
    // Check for real data indicators
    const realDataMarkers = [
      'document processed',
      'extracted from',
      'knowledge base',
      'imported document',
      'processed text',
      'last updated',
      'source:'
    ];
    
    const foundRealMarkers = realDataMarkers.filter(marker =>
      pageContent.toLowerCase().includes(marker.toLowerCase())  
    );
    
    // Check for graph statistics that would indicate real usage
    const statsPattern = /(\d+)\s+(nodes?|vertices?|items?)/i;
    const relationPattern = /(\d+)\s+(edges?|relationships?|connections?)/i;
    
    const nodeStats = pageContent.match(statsPattern);
    const relationStats = pageContent.match(relationPattern);
    
    // Test import functionality
    let importExists = false;
    const importSelectors = [
      'text=Import',
      'text=Upload',
      'text=Add Document',
      'input[type="file"]',
      'text=Add Knowledge'
    ];
    
    for (const selector of importSelectors) {
      if (await page.locator(selector).count() > 0) {
        importExists = true;
        break;
      }
    }
    
    console.log('Knowledge graph analysis:', {
      testDataMarkers: foundTestMarkers,
      realDataMarkers: foundRealMarkers,
      nodeStats: nodeStats ? nodeStats[0] : 'none',
      relationStats: relationStats ? relationStats[0] : 'none',
      importExists
    });
    
    // Test expectations
    expect(foundTestMarkers.length, 'Should not show test data markers').toBeLessThan(2);
    expect(foundRealMarkers.length > 0 || (nodeStats && parseInt(nodeStats[1]) > 10), 
           'Should show real data or substantial content').toBeTruthy();
    expect(importExists, 'Should have import functionality').toBeTruthy();
  });

  test('Issue 3: WebSocket Connection Status - Deep Analysis', async ({ page }) => {
    console.log('🔍 Analyzing WebSocket connection behavior...');
    
    // Monitor WebSocket activity
    let wsConnections = 0;
    let wsErrors = 0;
    let wsMessages = 0;
    
    // Intercept WebSocket creation
    await page.addInitScript(() => {
      const originalWebSocket = window.WebSocket;
      window.WebSocket = function(url, protocols) {
        const ws = new originalWebSocket(url, protocols);
        
        window.wsActivity = window.wsActivity || [];
        
        ws.addEventListener('open', () => {
          window.wsActivity.push({ type: 'open', url, timestamp: Date.now() });
        });
        
        ws.addEventListener('message', (event) => {
          window.wsActivity.push({ type: 'message', timestamp: Date.now() });
        });
        
        ws.addEventListener('close', (event) => {
          window.wsActivity.push({ type: 'close', code: event.code, timestamp: Date.now() });
        });
        
        ws.addEventListener('error', () => {
          window.wsActivity.push({ type: 'error', timestamp: Date.now() });
        });
        
        return ws;
      };
    });
    
    // Navigate to enhanced dashboard where WebSocket should be active
    await page.goto(`${FRONTEND_URL}/#/enhanced`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    // Check connection status in UI
    const pageContent = await page.textContent('body');
    
    const connectionPatterns = {
      showsConnected: /connected(?!\s*false)|connection.*?(?:ok|good|active|established)/i.test(pageContent),
      showsDisconnected: /disconnected|connection.*?(?:lost|failed|error)|websocket.*?(?:error|fail)/i.test(pageContent),
      showsReconnecting: /reconnecting|connection.*?(?:retry|attempt)|websocket.*?reconnect/i.test(pageContent),
      hasStatusIndicator: /(?:connection|websocket).*?(?:status|state)/i.test(pageContent)
    };
    
    // Get WebSocket activity from page
    const initialWsActivity = await page.evaluate(() => window.wsActivity || []);
    
    // Monitor for a longer period
    console.log('Monitoring WebSocket for 15 seconds...');
    await page.waitForTimeout(15000);
    
    const finalWsActivity = await page.evaluate(() => window.wsActivity || []);
    const finalPageContent = await page.textContent('body');
    
    await page.screenshot({ 
      path: '/tmp/websocket_connection_analysis.png',
      fullPage: true 
    });
    
    // Analyze WebSocket behavior
    const openEvents = finalWsActivity.filter(a => a.type === 'open').length;
    const closeEvents = finalWsActivity.filter(a => a.type === 'close').length;
    const errorEvents = finalWsActivity.filter(a => a.type === 'error').length;
    const messageEvents = finalWsActivity.filter(a => a.type === 'message').length;
    
    const connectionStable = openEvents > 0 && errorEvents === 0 && messageEvents > 0;
    const connectionProblematic = errorEvents > 0 || closeEvents > openEvents;
    
    console.log('WebSocket analysis:', {
      totalActivity: finalWsActivity.length,
      openEvents,
      closeEvents,
      errorEvents,
      messageEvents,
      connectionStable,
      connectionProblematic,
      uiPatterns: connectionPatterns
    });
    
    // Test expectations
    expect(openEvents, 'Should establish WebSocket connections').toBeGreaterThan(0);
    expect(messageEvents, 'Should receive WebSocket messages').toBeGreaterThan(0);
    expect(connectionProblematic, 'Should not have connection problems').toBeFalsy();
    expect(connectionPatterns.showsDisconnected && !connectionPatterns.showsConnected, 
           'Should not constantly show disconnected').toBeFalsy();
  });

  test('Issue 4: Stream of Consciousness 0 Events - Deep Check', async ({ page }) => {
    console.log('🔍 Deep analysis of stream of consciousness...');
    
    await page.goto(`${FRONTEND_URL}/#/stream`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    await page.screenshot({ 
      path: '/tmp/stream_consciousness_analysis.png',
      fullPage: true 
    });
    
    const initialContent = await page.textContent('body');
    
    // Look for explicit "0 events" or empty state messages
    const emptyStateIndicators = [
      '0 events',
      'no events',
      'no consciousness events',
      'empty stream',
      'no activity',
      'no thoughts',
      'stream is empty'
    ];
    
    const foundEmptyIndicators = emptyStateIndicators.filter(indicator =>
      initialContent.toLowerCase().includes(indicator.toLowerCase())
    );
    
    // Look for event indicators
    const eventIndicators = [
      /\d+\s+events?/i,
      /\d+\s+thoughts?/i,
      /\d+\s+consciousness\s+events?/i,
      /event\s+\d+/i,
      /thought\s+\d+/i,
      /\d{2}:\d{2}:\d{2}/,  // Timestamps
      /\d+\s+(?:seconds?|minutes?|hours?)\s+ago/i
    ];
    
    const hasEventIndicators = eventIndicators.some(pattern => 
      pattern.test(initialContent)
    );
    
    // Wait longer and check for real-time updates
    console.log('Monitoring stream for real-time updates...');
    await page.waitForTimeout(10000);
    
    const updatedContent = await page.textContent('body');
    const contentChanged = updatedContent !== initialContent;
    
    // Look for live update indicators
    const liveIndicators = [
      /live|real.?time|streaming/i.test(updatedContent),
      /last\s+update/i.test(updatedContent),
      /connected|active\s+stream/i.test(updatedContent)
    ];
    
    const hasLiveIndicators = liveIndicators.some(Boolean);
    
    // Check for consciousness-related content
    const consciousnessContent = [
      /consciousness/i,
      /cognitive/i,
      /reasoning/i,
      /thought\s+process/i,
      /mental\s+activity/i,
      /awareness/i
    ];
    
    const hasConsciousnessContent = consciousnessContent.some(pattern =>
      pattern.test(updatedContent)
    );
    
    console.log('Stream of consciousness analysis:', {
      foundEmptyIndicators,
      hasEventIndicators,
      contentChanged,
      hasLiveIndicators,
      hasConsciousnessContent,
      contentLength: updatedContent.length
    });
    
    // Test expectations
    expect(foundEmptyIndicators.length, 'Should not show explicit "0 events" messages').toBeLessThan(2);
    expect(hasEventIndicators || hasLiveIndicators || hasConsciousnessContent, 
           'Should show event indicators, live updates, or consciousness content').toBeTruthy();
    expect(updatedContent.length, 'Should have substantial content').toBeGreaterThan(200);
  });

  test('Issue 5: Autonomous Learning Non-functional - Validation', async ({ page }) => {
    console.log('🔍 Testing autonomous learning functionality...');
    
    await page.goto(`${FRONTEND_URL}/#/autonomous`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    await page.screenshot({ 
      path: '/tmp/autonomous_learning_analysis.png',
      fullPage: true 
    });
    
    const pageContent = await page.textContent('body');
    
    // Check for autonomous learning indicators
    const learningIndicators = [
      /autonomous.*learning/i,
      /self.*learning/i,
      /adaptive.*learning/i,
      /learning.*progress/i,
      /knowledge.*acquisition/i,
      /learning.*session/i
    ];
    
    const hasLearningIndicators = learningIndicators.some(pattern =>
      pattern.test(pageContent)
    );
    
    // Check for activity indicators
    const activityIndicators = [
      /learning.*active/i,
      /processing.*learning/i,
      /acquired.*knowledge/i,
      /\d+\s+(?:concepts?|patterns?|insights?)\s+learned/i,
      /last.*learned/i,
      /learning.*rate/i
    ];
    
    const hasActivityIndicators = activityIndicators.some(pattern =>
      pattern.test(pageContent)
    );
    
    // Check for controls or settings
    const controlIndicators = [
      /start.*learning/i,
      /enable.*learning/i,
      /learning.*settings/i,
      /configure.*learning/i
    ];
    
    const hasControls = controlIndicators.some(pattern =>
      pattern.test(pageContent)
    ) || await page.locator('button, input, select').count() > 0;
    
    // Check for "does nothing" indicators
    const inactiveIndicators = [
      'not implemented',
      'coming soon',
      'placeholder',
      'disabled',
      'inactive',
      'no learning'
    ];
    
    const showsInactive = inactiveIndicators.some(indicator =>
      pageContent.toLowerCase().includes(indicator.toLowerCase())
    );
    
    console.log('Autonomous learning analysis:', {
      hasLearningIndicators,
      hasActivityIndicators,
      hasControls,
      showsInactive,
      contentLength: pageContent.length
    });
    
    // Test expectations
    expect(hasLearningIndicators, 'Should show learning-related content').toBeTruthy();
    expect(showsInactive, 'Should not show inactive/placeholder messages').toBeFalsy();
    expect(hasActivityIndicators || hasControls, 'Should show activity or controls').toBeTruthy();
    expect(pageContent.length, 'Should have substantial content').toBeGreaterThan(100);
  });

  test('Issue 6: Navigation Breaking After Reflection View', async ({ page }) => {
    console.log('🔍 Testing navigation stability with reflection view...');
    
    // Start with a known working view
    await page.goto(`${FRONTEND_URL}/#/dashboard`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Verify navigation works initially
    await page.click('text=Enhanced');
    await page.waitForTimeout(2000);
    const enhancedContent = await page.textContent('body');
    const enhancedWorking = enhancedContent && enhancedContent.length > 100;
    
    // Navigate back to dashboard
    await page.click('text=Dashboard');
    await page.waitForTimeout(2000);
    
    await page.screenshot({ 
      path: '/tmp/navigation_before_reflection.png',
      fullPage: true 
    });
    
    // Now navigate to reflection view
    console.log('Navigating to reflection view...');
    
    try {
      await page.click('text=Reflection');
      await page.waitForTimeout(3000);
      
      await page.screenshot({ 
        path: '/tmp/navigation_reflection_view.png',
        fullPage: true 
      });
      
      const reflectionContent = await page.textContent('body');
      const reflectionLoaded = reflectionContent && reflectionContent.length > 100;
      
      // Test navigation after reflection view
      console.log('Testing navigation after reflection view...');
      
      const navigationTests = [
        { view: 'Dashboard', selector: 'text=Dashboard' },
        { view: 'Enhanced', selector: 'text=Enhanced' },
        { view: 'Cognitive', selector: 'text=Cognitive' }
      ];
      
      let navigationBroken = false;
      const failedNavigations = [];
      
      for (const test of navigationTests) {
        try {
          console.log(`Testing navigation to ${test.view}...`);
          await page.click(test.selector);
          await page.waitForTimeout(2000);
          
          const testContent = await page.textContent('body');
          const testWorking = testContent && testContent.length > 100 && 
                             testContent !== reflectionContent;
          
          if (!testWorking) {
            navigationBroken = true;
            failedNavigations.push(test.view);
          }
          
          console.log(`Navigation to ${test.view}: ${testWorking ? 'WORKS' : 'BROKEN'}`);
          
        } catch (error) {
          navigationBroken = true;
          failedNavigations.push(`${test.view} (error: ${error.message})`);
        }
      }
      
      await page.screenshot({ 
        path: '/tmp/navigation_after_reflection.png',
        fullPage: true 
      });
      
      console.log('Navigation stability analysis:', {
        enhancedWorking,
        reflectionLoaded,
        navigationBroken,
        failedNavigations
      });
      
      // Test expectations
      expect(enhancedWorking, 'Initial navigation should work').toBeTruthy();
      expect(reflectionLoaded, 'Reflection view should load').toBeTruthy();
      expect(navigationBroken, 'Navigation should not break after reflection view').toBeFalsy();
      expect(failedNavigations.length, 'Should have no failed navigations').toBe(0);
      
    } catch (error) {
      console.error('Failed to access reflection view:', error.message);
      expect(true, 'Should be able to access reflection view').toBeFalsy();
    }
  });

  test('Issue 7: Provenance System Validation', async ({ page }) => {
    console.log('🔍 Testing provenance system functionality...');
    
    await page.goto(`${FRONTEND_URL}/#/provenance`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    
    await page.screenshot({ 
      path: '/tmp/provenance_analysis.png',
      fullPage: true 
    });
    
    const pageContent = await page.textContent('body');
    
    // Check for provenance-related functionality
    const provenanceIndicators = [
      /provenance/i,
      /data.*lineage/i,
      /source.*tracking/i,
      /origin.*data/i,
      /audit.*trail/i,
      /data.*history/i,
      /trace.*source/i
    ];
    
    const hasProvenanceFeatures = provenanceIndicators.some(pattern =>
      pattern.test(pageContent)
    );
    
    // Check for data visualization or useful information
    const usefulnessIndicators = [
      /\d+\s+(?:sources?|documents?|items?)/i,
      /last.*(?:updated|modified|accessed)/i,
      /confidence.*\d+/i,
      /quality.*score/i,
      /source.*verified/i
    ];
    
    const hasUsefulContent = usefulnessIndicators.some(pattern =>
      pattern.test(pageContent)
    );
    
    // Check for "useless and ugly" indicators
    const problemIndicators = [
      'not implemented',
      'placeholder',
      'coming soon',
      'under construction',
      'no data available'
    ];
    
    const hasProblems = problemIndicators.some(indicator =>
      pageContent.toLowerCase().includes(indicator.toLowerCase())
    );
    
    // Check for interactive elements
    const hasInteractiveElements = await page.locator('button, input, select, a').count() > 0;
    
    // Check for visual elements (charts, graphs, etc.)
    const hasVisualElements = await page.locator('svg, canvas, .chart, .graph, .visualization').count() > 0;
    
    console.log('Provenance system analysis:', {
      hasProvenanceFeatures,
      hasUsefulContent,
      hasProblems,
      hasInteractiveElements,
      hasVisualElements,
      contentLength: pageContent.length
    });
    
    // Test expectations
    expect(hasProvenanceFeatures, 'Should have provenance-related features').toBeTruthy();
    expect(hasProblems, 'Should not show placeholder/not implemented messages').toBeFalsy();
    expect(hasUsefulContent || hasInteractiveElements || hasVisualElements, 
           'Should have useful content, interactions, or visualizations').toBeTruthy();
    expect(pageContent.length, 'Should have substantial content').toBeGreaterThan(200);
  });

  test('Critical Issues Summary Report', async ({ page }) => {
    console.log('📊 Generating critical issues summary...');
    
    // This test runs after all others and provides a comprehensive summary
    const criticalIssues = [];
    const functioningFeatures = [];
    
    // We'll check key endpoints and views one final time
    const viewsToCheck = [
      { name: 'Enhanced Dashboard', path: '#/enhanced' },
      { name: 'Reasoning/Transparency', path: '#/transparency' },
      { name: 'Knowledge Graph', path: '#/knowledge-graph' },
      { name: 'Stream of Consciousness', path: '#/stream' },
      { name: 'Autonomous Learning', path: '#/autonomous' },
      { name: 'Reflection', path: '#/reflection' },
      { name: 'Provenance', path: '#/provenance' }
    ];
    
    for (const view of viewsToCheck) {
      try {
        await page.goto(`${FRONTEND_URL}/${view.path}`);
        await page.waitForTimeout(3000);
        
        const content = await page.textContent('body');
        const hasSubstantialContent = content && content.length > 200;
        const hasErrorIndicators = /error|fail|broken|not.*(?:found|available|implemented)/i.test(content);
        const hasTestData = /test.*data|dummy.*data|sample.*data|mock.*data/i.test(content);
        const hasUndefinedValues = content.includes('undefined') || content.includes('NaN');
        
        if (hasSubstantialContent && !hasErrorIndicators && !hasTestData && !hasUndefinedValues) {
          functioningFeatures.push(view.name);
        } else {
          const issues = [];
          if (!hasSubstantialContent) issues.push('minimal content');
          if (hasErrorIndicators) issues.push('error indicators');
          if (hasTestData) issues.push('test data');
          if (hasUndefinedValues) issues.push('undefined/NaN values');
          
          criticalIssues.push(`${view.name}: ${issues.join(', ')}`);
        }
        
      } catch (error) {
        criticalIssues.push(`${view.name}: navigation failed (${error.message})`);
      }
    }
    
    // Final screenshot
    await page.screenshot({ 
      path: '/tmp/critical_issues_summary.png',
      fullPage: true 
    });
    
    const report = {
      timestamp: new Date().toISOString(),
      criticalIssues: criticalIssues,
      functioningFeatures: functioningFeatures,
      overallHealth: functioningFeatures.length / viewsToCheck.length,
      recommendations: [
        'Fix data validation to eliminate undefined/NaN values',
        'Replace test data with real dynamic data',
        'Ensure all features have substantial functionality',
        'Fix navigation stability issues',
        'Implement real-time data streaming properly'
      ]
    };
    
    console.log('\n=== CRITICAL ISSUES SUMMARY ===');
    console.log(`Overall Health: ${(report.overallHealth * 100).toFixed(1)}%`);
    console.log(`Functioning Features (${functioningFeatures.length}):`, functioningFeatures);
    console.log(`Critical Issues (${criticalIssues.length}):`, criticalIssues);
    
    // Save detailed report
    await page.evaluate((reportData) => {
      const reportElement = document.createElement('div');
      reportElement.id = 'critical-issues-report';
      reportElement.innerHTML = `<pre>${JSON.stringify(reportData, null, 2)}</pre>`;
      reportElement.style.display = 'none';
      document.body.appendChild(reportElement);
    }, report);
    
    // Test should pass if more than 70% of features are functioning
    expect(report.overallHealth, 'Overall system health should be above 70%').toBeGreaterThan(0.7);
    expect(criticalIssues.length, 'Should have fewer than 5 critical issues').toBeLessThan(5);
  });
});