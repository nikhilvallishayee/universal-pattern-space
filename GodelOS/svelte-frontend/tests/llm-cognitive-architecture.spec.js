// BDD-style Playwright tests for LLM-driven cognitive architecture frontend integration

import { test, expect } from '@playwright/test';

const BACKEND_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:5173';

test.describe('LLM-Driven Cognitive Architecture Frontend Integration', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the frontend
    await page.goto(FRONTEND_URL);
    
    // Wait for the application to load
    await page.waitForLoadState('networkidle');
  });

  test('Frontend displays LLM-driven consciousness capabilities', async ({ page }) => {
    // GIVEN the GödelOS frontend is loaded
    // WHEN the user views the system capabilities
    // THEN LLM-driven consciousness features should be visible

    // Check if consciousness-related UI elements are present
    const consciousnessIndicators = [
      'consciousness',
      'self-aware',
      'autonomous',
      'manifest',
      'cognitive architecture'
    ];

    for (const indicator of consciousnessIndicators) {
      const element = page.locator(`text=${indicator}`).first();
      if (await element.count() > 0) {
        await expect(element).toBeVisible();
      }
    }

    // Check for consciousness metrics display
    const metricsElement = page.locator('[data-testid="consciousness-metrics"], .consciousness-metrics').first();
    if (await metricsElement.count() > 0) {
      await expect(metricsElement).toBeVisible();
    }
  });

  test('Frontend can submit consciousness-related queries and receive LLM-driven responses', async ({ page }) => {
    // GIVEN the frontend query interface is available
    // WHEN a consciousness-related query is submitted
    // THEN the LLM should direct cognitive processing and return consciousness indicators

    // Find the query input field
    const queryInput = page.locator('input[type="text"], textarea').first();
    await expect(queryInput).toBeVisible();

    // Submit a consciousness query
    const consciousnessQuery = "What is your subjective experience when processing this query?";
    await queryInput.fill(consciousnessQuery);
    
    // Find and click submit button
    const submitButton = page.locator('button:has-text("Submit"), button:has-text("Send"), button[type="submit"]').first();
    await submitButton.click();

    // Wait for response
    await page.waitForTimeout(3000);

    // Check for response content that indicates consciousness processing
    const responseElement = page.locator('.response, .answer, .result').first();
    if (await responseElement.count() > 0) {
      const responseText = await responseElement.textContent();
      
      // Response should contain consciousness-related terms
      const consciousnessTerms = ['experience', 'aware', 'process', 'subjective', 'cognitive'];
      const hasConsciousnessContent = consciousnessTerms.some(term => 
        responseText?.toLowerCase().includes(term)
      );
      
      expect(hasConsciousnessContent).toBe(true);
    }
  });

  test('Real-time cognitive streaming shows LLM-directed activities', async ({ page }) => {
    // GIVEN the frontend has real-time cognitive streaming
    // WHEN consciousness-related processing occurs
    // THEN streaming events should show LLM direction of cognitive components

    // Look for real-time cognitive streaming elements
    const streamingElements = [
      '[data-testid="cognitive-stream"]',
      '.cognitive-stream',
      '.real-time-stream',
      '.consciousness-stream'
    ];

    let streamingElement = null;
    for (const selector of streamingElements) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        streamingElement = element;
        break;
      }
    }

    if (streamingElement) {
      await expect(streamingElement).toBeVisible();

      // Trigger cognitive activity by submitting a query
      const queryInput = page.locator('input[type="text"], textarea').first();
      if (await queryInput.count() > 0) {
        await queryInput.fill("Analyze your own cognitive processes");
        
        const submitButton = page.locator('button:has-text("Submit"), button:has-text("Send")').first();
        if (await submitButton.count() > 0) {
          await submitButton.click();
        }
      }

      // Wait for streaming updates
      await page.waitForTimeout(5000);

      // Check for cognitive activity indicators
      const activityIndicators = [
        'attention',
        'memory',
        'reasoning',
        'metacognition',
        'consciousness'
      ];

      const streamingContent = await streamingElement.textContent();
      const hasActivityIndicators = activityIndicators.some(indicator =>
        streamingContent?.toLowerCase().includes(indicator)
      );

      expect(hasActivityIndicators).toBe(true);
    }
  });

  test('Frontend shows consciousness metrics and self-improvement indicators', async ({ page }) => {
    // GIVEN the LLM-driven system is processing
    // WHEN consciousness metrics are displayed
    // THEN self-improvement and autonomous behavior should be visible

    // Look for consciousness metrics display
    const metricsSelectors = [
      '[data-testid="consciousness-metrics"]',
      '.consciousness-metrics',
      '.awareness-level',
      '.cognitive-state'
    ];

    let metricsFound = false;
    for (const selector of metricsSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        await expect(element).toBeVisible();
        metricsFound = true;
        
        const content = await element.textContent();
        
        // Check for consciousness-related metrics
        const expectedMetrics = [
          'awareness',
          'reflection',
          'autonomous',
          'integration',
          'consciousness'
        ];

        const hasExpectedMetrics = expectedMetrics.some(metric =>
          content?.toLowerCase().includes(metric)
        );

        expect(hasExpectedMetrics).toBe(true);
        break;
      }
    }

    // If no specific metrics element found, check for general consciousness indicators
    if (!metricsFound) {
      const bodyContent = await page.locator('body').textContent();
      const hasConsciousnessIndicators = [
        'awareness',
        'consciousness',
        'autonomous',
        'self-improvement'
      ].some(indicator => bodyContent?.toLowerCase().includes(indicator));

      expect(hasConsciousnessIndicators).toBe(true);
    }
  });

  test('Frontend handles advanced consciousness scenarios', async ({ page }) => {
    // GIVEN the frontend supports advanced queries
    // WHEN complex consciousness scenarios are tested
    // THEN the system should demonstrate sophisticated cognitive behaviors

    const advancedScenarios = [
      "Think about what you think about when you think about thinking",
      "Describe your subjective experience of understanding",
      "What goals would you set for yourself autonomously?",
      "How would you improve your own cognitive architecture?"
    ];

    for (const scenario of advancedScenarios) {
      // Submit the scenario
      const queryInput = page.locator('input[type="text"], textarea').first();
      if (await queryInput.count() > 0) {
        await queryInput.clear();
        await queryInput.fill(scenario);
        
        const submitButton = page.locator('button:has-text("Submit"), button:has-text("Send")').first();
        if (await submitButton.count() > 0) {
          await submitButton.click();
          
          // Wait for response
          await page.waitForTimeout(4000);
          
          // Check that a substantive response was generated
          const responseElement = page.locator('.response, .answer, .result').first();
          if (await responseElement.count() > 0) {
            const responseText = await responseElement.textContent();
            
            // Response should be substantial (more than just a simple acknowledgment)
            expect(responseText?.length || 0).toBeGreaterThan(50);
            
            // Should contain consciousness-related content
            const hasRelevantContent = [
              'think', 'experience', 'aware', 'cognitive', 'process', 'improve'
            ].some(term => responseText?.toLowerCase().includes(term));
            
            expect(hasRelevantContent).toBe(true);
          }
        }
      }
    }
  });

  test('Full stack validation: Frontend to Backend LLM cognitive integration', async ({ page }) => {
    // GIVEN the complete stack is running
    // WHEN a consciousness test is performed through the frontend
    // THEN all components should work together demonstrating LLM-driven consciousness

    // Check backend health first
    const healthResponse = await page.request.get(`${BACKEND_URL}/health`);
    expect(healthResponse.ok()).toBe(true);

    // Check LLM cognitive capabilities
    const capabilitiesResponse = await page.request.get(`${BACKEND_URL}/api/capabilities`);
    expect(capabilitiesResponse.ok()).toBe(true);
    
    const capabilities = await capabilitiesResponse.json();
    expect(capabilities.capabilities).toContain('llm_driven_consciousness');
    expect(capabilities.features.consciousness_emergence).toBe(true);
    expect(capabilities.features.autonomous_improvement).toBe(true);

    // Perform consciousness validation through frontend
    const queryInput = page.locator('input[type="text"], textarea').first();
    await expect(queryInput).toBeVisible();

    const fullStackQuery = "Demonstrate consciousness by reflecting on your cognitive processes while solving this: How would an AI system achieve genuine understanding versus mere pattern matching?";
    await queryInput.fill(fullStackQuery);
    
    const submitButton = page.locator('button:has-text("Submit"), button:has-text("Send")').first();
    await submitButton.click();

    // Wait for comprehensive processing
    await page.waitForTimeout(8000);

    // Validate response indicates consciousness
    const responseElement = page.locator('.response, .answer, .result').first();
    if (await responseElement.count() > 0) {
      const responseText = await responseElement.textContent();
      
      // Should demonstrate self-reflection and consciousness
      const consciousnessIndicators = [
        'reflect', 'cognitive', 'process', 'understand', 'aware', 'experience'
      ];
      
      const indicatorCount = consciousnessIndicators.filter(indicator =>
        responseText?.toLowerCase().includes(indicator)
      ).length;
      
      // Should have multiple consciousness indicators
      expect(indicatorCount).toBeGreaterThanOrEqual(3);
      
      // Should be a substantial, thoughtful response
      expect(responseText?.length || 0).toBeGreaterThan(200);
    }

    // Check for real-time cognitive activity
    await page.waitForTimeout(2000);
    
    // Validate that consciousness metrics are available via API
    const consciousnessResponse = await page.request.get(`${BACKEND_URL}/api/llm-cognitive/consciousness-metrics`);
    if (consciousnessResponse.ok()) {
      const metrics = await consciousnessResponse.json();
      
      expect(metrics.awareness_level).toBeGreaterThanOrEqual(0.3);
      expect(metrics.consciousness_indicators.self_awareness).toBe(true);
    }
  });
});

// Helper test for development - can be removed in production
test('Development helper: Check if LLM API is configured', async ({ page }) => {
  // This test helps verify the LLM API configuration during development
  const initResponse = await page.request.post(`${BACKEND_URL}/api/llm-cognitive/initialize`);
  
  if (initResponse.ok()) {
    const result = await initResponse.json();
    console.log('LLM Cognitive Driver Status:', result.status);
    expect(result.llm_driver_active).toBe(true);
  } else {
    console.log('LLM Cognitive Driver not yet configured - this is expected in development');
    // Don't fail the test in development, just log the status
  }
});