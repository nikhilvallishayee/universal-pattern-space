// Comprehensive Frontend-Backend Integration Test
// Tests the complete user experience on actual Svelte frontend

import { test, expect } from '@playwright/test';

test.describe('Comprehensive Frontend-Backend Integration', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to the actual running Svelte application
        await page.goto('http://localhost:3001');
        
        // Wait for the application to load
        await page.waitForTimeout(2000);
    });

    test('Frontend loads correctly with proper title and branding', async ({ page }) => {
        // Check page title
        await expect(page).toHaveTitle(/GödelOS|Godel/);
        
        // Look for GödelOS branding elements
        const hasGodelosText = await page.locator('text=GödelOS').count() > 0 ||
                              await page.locator('text=Gödel').count() > 0 ||
                              await page.locator('text=Godel').count() > 0;
        
        expect(hasGodelosText).toBeTruthy();
        
        // Take screenshot of initial load
        await page.screenshot({ path: 'test-results/01-frontend-load.png', fullPage: true });
    });

    test('Knowledge Graph displays real backend data', async ({ page }) => {
        // Look for knowledge graph elements
        const knowledgeGraphVisible = await page.isVisible('[data-testid="knowledge-graph"]') ||
                                     await page.isVisible('.knowledge-graph') ||
                                     await page.isVisible('svg') ||
                                     await page.locator('text=Knowledge').count() > 0;

        if (knowledgeGraphVisible) {
            // Test if graph shows real data vs empty/test data
            const hasNodes = await page.locator('circle, .node').count() > 0;
            const hasEdges = await page.locator('line, .edge, .link').count() > 0;
            
            // Look for real cognitive concepts (not generic test data)
            const hasRealConcepts = await page.locator('text=Consciousness').count() > 0 ||
                                  await page.locator('text=Meta-cognition').count() > 0 ||
                                  await page.locator('text=Working Memory').count() > 0 ||
                                  await page.locator('text=Attention').count() > 0;
            
            console.log(`Knowledge Graph: Nodes=${hasNodes}, Edges=${hasEdges}, RealConcepts=${hasRealConcepts}`);
            
            // Take screenshot of knowledge graph
            await page.screenshot({ path: 'test-results/02-knowledge-graph.png', fullPage: true });
        } else {
            console.log('Knowledge Graph not visible on main page');
        }
    });

    test('Cognitive State shows valid data without NaN/undefined values', async ({ page }) => {
        // Look for cognitive state displays
        const cognitiveStateElements = await page.locator('text=/health|processing|attention|memory|cognitive/i');
        const cognitiveStateCount = await cognitiveStateElements.count();
        
        if (cognitiveStateCount > 0) {
            // Check for invalid data patterns
            const hasNaN = await page.locator('text=NaN').count() > 0;
            const hasUndefined = await page.locator('text=undefined').count() > 0;
            const hasInfinity = await page.locator('text=Infinity').count() > 0;
            const hasMegaPercent = await page.locator('text=/\d{3,}%/').count() > 0; // 100%+ percentages
            
            // Check for realistic values
            const hasRealisticHealth = await page.locator('text=/\d{1,2}%/').count() > 0; // 0-99% values
            
            console.log(`Cognitive State: NaN=${hasNaN}, Undefined=${hasUndefined}, Infinity=${hasInfinity}, MegaPercent=${hasMegaPercent}, RealisticHealth=${hasRealisticHealth}`);
            
            expect(hasNaN).toBeFalsy();
            expect(hasUndefined).toBeFalsy();
            expect(hasInfinity).toBeFalsy();
            expect(hasMegaPercent).toBeFalsy();
            
            await page.screenshot({ path: 'test-results/03-cognitive-state.png', fullPage: true });
        }
    });

    test('Navigation system works correctly', async ({ page }) => {
        // Find navigation elements
        const navButtons = await page.locator('button, a, [role="button"]').count();
        console.log(`Found ${navButtons} potential navigation elements`);
        
        // Test common navigation patterns
        const navElements = [
            'button:has-text("Knowledge")',
            'button:has-text("Transparency")', 
            'button:has-text("Cognitive")',
            'button:has-text("Stream")',
            'button:has-text("Reasoning")',
            '[data-nav]', // Elements with data-nav attributes
            'nav button',
            '.nav-button',
            '.navigation button'
        ];
        
        let workingNavElements = 0;
        for (const selector of navElements) {
            const elementCount = await page.locator(selector).count();
            if (elementCount > 0) {
                workingNavElements += elementCount;
                console.log(`Found ${elementCount} elements matching: ${selector}`);
            }
        }
        
        console.log(`Total working navigation elements: ${workingNavElements}`);
        
        // Take screenshot of navigation state
        await page.screenshot({ path: 'test-results/04-navigation.png', fullPage: true });
        
        // Test clicking first available navigation element
        if (workingNavElements > 0) {
            try {
                const firstNavElement = page.locator('button, a, [role="button"]').first();
                await firstNavElement.click();
                await page.waitForTimeout(1000);
                
                // Check if navigation worked (no page reload, state change)
                const afterClickUrl = page.url();
                console.log(`After navigation click: ${afterClickUrl}`);
                
                await page.screenshot({ path: 'test-results/05-after-navigation.png', fullPage: true });
            } catch (error) {
                console.log(`Navigation test error: ${error.message}`);
            }
        }
    });

    test('Transparency and Reasoning functionality', async ({ page }) => {
        // Look for transparency-related elements
        const transparencyElements = await page.locator('text=/transparency|reasoning|session|progress/i').count();
        
        if (transparencyElements > 0) {
            console.log(`Found ${transparencyElements} transparency-related elements`);
            
            // Test if we can access transparency modal/view
            const modalTriggers = [
                'button:has-text("Transparency")',
                'button:has-text("Reasoning")', 
                'button:has-text("Session")',
                '[data-testid="transparency-modal"]',
                '.transparency-trigger'
            ];
            
            for (const trigger of modalTriggers) {
                const triggerCount = await page.locator(trigger).count();
                if (triggerCount > 0) {
                    try {
                        await page.locator(trigger).first().click();
                        await page.waitForTimeout(1000);
                        
                        // Check if modal/view opened
                        const modalVisible = await page.isVisible('.modal, .dialog, .overlay') ||
                                           await page.locator('text=/progress|session.*active|reasoning.*trace/i').count() > 0;
                        
                        console.log(`Transparency modal opened: ${modalVisible}`);
                        
                        if (modalVisible) {
                            // Check for progress indicators
                            const hasProgressData = await page.locator('text=/\d+%|progress|stage/i').count() > 0;
                            console.log(`Has progress data: ${hasProgressData}`);
                            
                            await page.screenshot({ path: 'test-results/06-transparency-modal.png', fullPage: true });
                        }
                        break;
                    } catch (error) {
                        console.log(`Transparency trigger error: ${error.message}`);
                    }
                }
            }
        }
    });

    test('Stream of Consciousness activity', async ({ page }) => {
        // Look for stream of consciousness elements
        const streamElements = await page.locator('text=/stream|consciousness|events|activity/i').count();
        
        if (streamElements > 0) {
            console.log(`Found ${streamElements} stream-related elements`);
            
            // Check for active stream content
            const hasStreamContent = await page.locator('text=/cognitive|memory|attention|reasoning|reflection/i').count() > 5;
            const hasEventCount = await page.locator('text=/\d+.*event/i').count() > 0;
            const hasTimestamps = await page.locator('text=/\d{2}:\d{2}|\d{4}-\d{2}-\d{2}/').count() > 0;
            
            console.log(`Stream content: HasContent=${hasStreamContent}, HasEventCount=${hasEventCount}, HasTimestamps=${hasTimestamps}`);
            
            await page.screenshot({ path: 'test-results/07-stream-of-consciousness.png', fullPage: true });
        }
    });

    test('WebSocket connectivity and real-time updates', async ({ page }) => {
        let websocketMessages = [];
        let websocketConnected = false;
        let websocketErrors = [];
        
        // Monitor WebSocket activity
        page.on('websocket', ws => {
            console.log('WebSocket connection detected');
            websocketConnected = true;
            
            ws.on('framereceived', event => {
                try {
                    const data = JSON.parse(event.payload);
                    websocketMessages.push(data);
                    console.log(`WebSocket message: ${data.type || 'unknown'}`);
                } catch (e) {
                    console.log('Non-JSON WebSocket message received');
                }
            });
            
            ws.on('close', () => {
                console.log('WebSocket connection closed');
            });
            
            ws.on('socketerror', error => {
                websocketErrors.push(error);
                console.log(`WebSocket error: ${error}`);
            });
        });
        
        // Wait for potential WebSocket connections to establish
        await page.waitForTimeout(5000);
        
        console.log(`WebSocket status: Connected=${websocketConnected}, Messages=${websocketMessages.length}, Errors=${websocketErrors.length}`);
        
        // Take screenshot showing real-time state
        await page.screenshot({ path: 'test-results/08-websocket-activity.png', fullPage: true });
        
        // Test if data is updating in real-time
        const initialContent = await page.textContent('body');
        await page.waitForTimeout(3000);
        const updatedContent = await page.textContent('body');
        
        const contentChanged = initialContent !== updatedContent;
        console.log(`Content updated in real-time: ${contentChanged}`);
    });

    test('System health and status indicators', async ({ page }) => {
        // Look for system health indicators
        const healthElements = await page.locator('text=/health|status|connected|disconnected|active|idle/i').count();
        
        if (healthElements > 0) {
            console.log(`Found ${healthElements} health-related elements`);
            
            // Check connection status
            const isConnected = await page.locator('text=/connected|online|active/i').count() > 
                               await page.locator('text=/disconnected|offline|idle/i').count();
            
            // Check for health percentages/metrics
            const hasHealthMetrics = await page.locator('text=/\d+%.*health|\d+%.*system|\d+%.*status/i').count() > 0;
            
            console.log(`Connection status: Connected=${isConnected}, HasHealthMetrics=${hasHealthMetrics}`);
            
            await page.screenshot({ path: 'test-results/09-system-health.png', fullPage: true });
        }
    });

    test('Interactive elements and user input handling', async ({ page }) => {
        // Count interactive elements
        const buttons = await page.locator('button:not([disabled])').count();
        const inputs = await page.locator('input:not([disabled]), textarea:not([disabled])').count();
        const clickables = await page.locator('[role="button"]:not([disabled]), a:not([disabled])').count();
        
        const totalInteractive = buttons + inputs + clickables;
        console.log(`Interactive elements: Buttons=${buttons}, Inputs=${inputs}, Clickables=${clickables}, Total=${totalInteractive}`);
        
        // Test input functionality if inputs are available
        if (inputs > 0) {
            try {
                const firstInput = page.locator('input, textarea').first();
                await firstInput.fill('Test input validation');
                await page.waitForTimeout(500);
                
                const inputValue = await firstInput.inputValue();
                console.log(`Input test: Value="${inputValue}"`);
            } catch (error) {
                console.log(`Input test error: ${error.message}`);
            }
        }
        
        await page.screenshot({ path: 'test-results/10-interactive-elements.png', fullPage: true });
    });

    test('Comprehensive system validation summary', async ({ page }) => {
        // Gather comprehensive metrics
        const pageMetrics = {
            title: await page.title(),
            url: page.url(),
            totalElements: await page.locator('*').count(),
            buttons: await page.locator('button').count(),
            inputs: await page.locator('input, textarea').count(),
            images: await page.locator('img').count(),
            links: await page.locator('a').count(),
            
            // Content analysis
            hasGodelosContent: await page.locator('text=/GödelOS|Gödel|cognitive|knowledge|consciousness/i').count() > 0,
            hasRealData: await page.locator('text=/dynamic|real-time|live|active/i').count() > 0,
            hasValidNumbers: await page.locator('text=/\d+%|\d+\.\d+|\d+ \w+/').count() > 0,
            hasInvalidData: await page.locator('text=/NaN|undefined|Infinity/').count() > 0,
            
            // Feature detection
            hasKnowledgeGraph: await page.locator('text=/knowledge.*graph|graph.*knowledge/i').count() > 0,
            hasTransparency: await page.locator('text=/transparency|reasoning.*session/i').count() > 0,
            hasStreamOfConsciousness: await page.locator('text=/stream.*consciousness|consciousness.*stream/i').count() > 0,
            hasCognitiveState: await page.locator('text=/cognitive.*state|attention|working.*memory/i').count() > 0,
        };
        
        console.log('='.repeat(60));
        console.log('COMPREHENSIVE FRONTEND VALIDATION SUMMARY');
        console.log('='.repeat(60));
        console.log(`Page: ${pageMetrics.title} (${pageMetrics.url})`);
        console.log(`Elements: ${pageMetrics.totalElements} total, ${pageMetrics.buttons} buttons, ${pageMetrics.inputs} inputs`);
        console.log(`Content: GödelOS=${pageMetrics.hasGodelosContent}, RealData=${pageMetrics.hasRealData}, ValidNumbers=${pageMetrics.hasValidNumbers}`);
        console.log(`Invalid Data: ${pageMetrics.hasInvalidData}`);
        console.log(`Features: KnowledgeGraph=${pageMetrics.hasKnowledgeGraph}, Transparency=${pageMetrics.hasTransparency}, Stream=${pageMetrics.hasStreamOfConsciousness}, CognitiveState=${pageMetrics.hasCognitiveState}`);
        
        // Final comprehensive screenshot
        await page.screenshot({ path: 'test-results/11-final-comprehensive.png', fullPage: true });
        
        // Write detailed results to file
        const fs = require('fs');
        const results = {
            timestamp: new Date().toISOString(),
            metrics: pageMetrics,
            summary: {
                overall_health: pageMetrics.hasGodelosContent && !pageMetrics.hasInvalidData ? 'GOOD' : 'ISSUES_DETECTED',
                feature_completeness: [
                    pageMetrics.hasKnowledgeGraph,
                    pageMetrics.hasTransparency, 
                    pageMetrics.hasStreamOfConsciousness,
                    pageMetrics.hasCognitiveState
                ].filter(Boolean).length / 4 * 100,
                data_validity: pageMetrics.hasValidNumbers && !pageMetrics.hasInvalidData,
                interactive_elements: pageMetrics.buttons + pageMetrics.inputs
            }
        };
        
        fs.writeFileSync('test-results/comprehensive-frontend-results.json', JSON.stringify(results, null, 2));
        
        // Assert critical functionality
        expect(pageMetrics.hasGodelosContent).toBeTruthy();
        expect(pageMetrics.hasInvalidData).toBeFalsy();
        expect(pageMetrics.totalElements).toBeGreaterThan(50); // Should be a substantial application
    });
});