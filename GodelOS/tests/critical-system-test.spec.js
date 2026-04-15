// Quick Critical System Test
// Tests the most important functionality issues identified by user

import { test, expect } from '@playwright/test';

test.describe('Critical System Issues Validation', () => {
    test('Backend API connectivity and data validation', async ({ page }) => {
        console.log('🔗 Testing Backend API connectivity...');
        
        // Test knowledge graph API
        const response = await page.request.get('http://localhost:8000/api/knowledge/graph');
        const graphData = await response.json();
        
        console.log(`Knowledge Graph: ${graphData.statistics?.node_count || 0} nodes, ${graphData.statistics?.edge_count || 0} edges`);
        console.log(`Data Source: ${graphData.statistics?.data_source || 'unknown'}`);
        
        expect(response.ok()).toBeTruthy();
        expect(graphData.statistics?.node_count).toBeGreaterThan(0);
        expect(graphData.statistics?.data_source).toBe('dynamic_processing');
    });

    test('Reasoning sessions progress beyond 0%', async ({ page }) => {
        console.log('🧠 Testing reasoning session progress...');
        
        // Create reasoning session
        const createResponse = await page.request.post('http://localhost:8000/api/transparency/reasoning-session', {
            data: { query: 'Test reasoning progress' }
        });
        
        const sessionData = await createResponse.json();
        console.log(`Created session: ${sessionData.session_id}`);
        
        // Wait and check progress
        await page.waitForTimeout(3000);
        
        const progressResponse = await page.request.get(`http://localhost:8000/api/transparency/session/${sessionData.session_id}/progress`);
        const progressData = await progressResponse.json();
        
        console.log(`Progress: ${progressData.progress}% - Status: ${progressData.status}`);
        
        expect(progressResponse.ok()).toBeTruthy();
        expect(progressData.progress).toBeGreaterThan(0);
    });

    test('Stream of consciousness has actual events', async ({ page }) => {
        console.log('🌊 Testing stream of consciousness...');
        
        const streamResponse = await page.request.get('http://localhost:8000/api/enhanced-cognitive/stream/events');
        const streamData = await streamResponse.json();
        
        console.log(`Events: ${streamData.total_events}, Content length: ${streamData.content_length}`);
        
        expect(streamResponse.ok()).toBeTruthy();
        expect(streamData.total_events).toBeGreaterThan(0);
        expect(streamData.content_length).toBeGreaterThan(0);
    });

    test('Frontend loads and displays valid data', async ({ page }) => {
        console.log('🖥️  Testing frontend functionality...');
        
        await page.goto('http://localhost:3001');
        await page.waitForTimeout(3000);
        
        // Check for GödelOS content
        const hasGodelosContent = await page.locator('text=/GödelOS|Gödel|cognitive|knowledge/i').count() > 0;
        console.log(`Has GödelOS content: ${hasGodelosContent}`);
        
        // Check for invalid data
        const hasNaN = await page.locator('text=NaN').count() > 0;
        const hasUndefined = await page.locator('text=undefined').count() > 0;
        const hasMegaPercent = await page.locator('text=/\d{3,}%/').count() > 0;
        
        console.log(`Invalid data: NaN=${hasNaN}, undefined=${hasUndefined}, MegaPercent=${hasMegaPercent}`);
        
        // Count interactive elements  
        const buttons = await page.locator('button').count();
        const inputs = await page.locator('input, textarea').count();
        
        console.log(`Interactive elements: ${buttons} buttons, ${inputs} inputs`);
        
        await page.screenshot({ path: 'test-results/frontend-validation.png', fullPage: true });
        
        expect(hasGodelosContent).toBeTruthy();
        expect(hasNaN).toBeFalsy();
        expect(hasUndefined).toBeFalsy();
        expect(hasMegaPercent).toBeFalsy();
        expect(buttons + inputs).toBeGreaterThan(5);
    });

    test('WebSocket connectivity', async ({ page }) => {
        console.log('🔌 Testing WebSocket connectivity...');
        
        let websocketConnected = false;
        let messageCount = 0;
        
        page.on('websocket', ws => {
            websocketConnected = true;
            ws.on('framereceived', () => messageCount++);
        });
        
        await page.goto('http://localhost:3001');
        await page.waitForTimeout(5000);
        
        console.log(`WebSocket: Connected=${websocketConnected}, Messages=${messageCount}`);
        
        // WebSocket might not be immediately testable, so just check if frontend tries to connect
        expect(websocketConnected || messageCount > 0).toBeTruthy();
    });

    test('Comprehensive system summary', async ({ page }) => {
        console.log('📋 Generating comprehensive system summary...');
        
        // Backend tests
        const healthResponse = await page.request.get('http://localhost:8000/health');
        const healthData = await healthResponse.json();
        
        const cognitiveResponse = await page.request.get('http://localhost:8000/api/cognitive/state');
        const cognitiveData = await cognitiveResponse.json();
        
        const transparencyResponse = await page.request.get('http://localhost:8000/api/transparency/statistics');
        const transparencyData = await transparencyResponse.json();
        
        // Frontend test
        await page.goto('http://localhost:3001');
        await page.waitForTimeout(2000);
        
        const pageMetrics = {
            title: await page.title(),
            elements: await page.locator('*').count(),
            buttons: await page.locator('button').count(),
            inputs: await page.locator('input, textarea').count()
        };
        
        const summary = {
            timestamp: new Date().toISOString(),
            backend: {
                health: healthData.status,
                cognitive_health: cognitiveData?.cognitive_state?.system_health?.overall || 0,
                sessions: transparencyData?.sessions?.total || 0,
                active_connections: healthData.active_connections || 0
            },
            frontend: {
                title: pageMetrics.title,
                total_elements: pageMetrics.elements,
                interactive_elements: pageMetrics.buttons + pageMetrics.inputs,
                fully_loaded: pageMetrics.elements > 50
            }
        };
        
        console.log('='.repeat(60));
        console.log('COMPREHENSIVE SYSTEM SUMMARY');
        console.log('='.repeat(60));
        console.log(`Backend Health: ${summary.backend.health}`);
        console.log(`Cognitive Health: ${(summary.backend.cognitive_health * 100).toFixed(0)}%`);
        console.log(`Total Sessions: ${summary.backend.sessions}`);
        console.log(`Frontend: ${summary.frontend.title} (${summary.frontend.total_elements} elements)`);
        console.log(`Interactive Elements: ${summary.frontend.interactive_elements}`);
        console.log(`System Status: ${summary.backend.health === 'healthy' && summary.frontend.fully_loaded ? '✅ FUNCTIONAL' : '⚠️  ISSUES DETECTED'}`);
        
        // Write results
        require('fs').writeFileSync('test-results/system-summary.json', JSON.stringify(summary, null, 2));
        
        await page.screenshot({ path: 'test-results/final-system-state.png', fullPage: true });
        
        expect(summary.backend.health).toBe('healthy');
        expect(summary.frontend.fully_loaded).toBeTruthy();
    });
});