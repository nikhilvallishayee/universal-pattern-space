import { test, expect } from '@playwright/test';


// Tests for transparency stream functionality

// Scenario: Starting a new session via the form and seeing live steps
// Scenario: Automatic reconnection after simulated server interruption

test.describe('Transparency Streams', () => {
  test('🟢 should start a session and stream steps live', async ({ page }) => {
    // --- Network mocks for backend APIs ---
    let sessionStarted = false;

    // Mock active sessions endpoint
    await page.route('http://localhost:8000/api/transparency/sessions/active', route => {
      if (sessionStarted) {
        route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify({
            active_sessions: [
              {
                session_id: 'session123',
                status: 'in_progress',
                query: 'test query'
              }
            ]
          })
        });
      } else {
        route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify({ active_sessions: [] })
        });
      }
    });

    // Mock session start endpoint
    await page.route('http://localhost:8000/api/transparency/session/start', route => {
      sessionStarted = true;
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ session_id: 'session123' })
      });
    });

    // Mock session trace endpoint
    await page.route(
      'http://localhost:8000/api/transparency/session/session123/trace',
      route => {
        route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify({
            session_id: 'session123',
            steps: [
              { step_type: 'think', content: 'First step' },
              { step_type: 'act', content: 'Second step' }
            ],
            decision_points: []
          })
        });
      }
    );

    // --- Test flow ---
    // Given the Reasoning Session Viewer is open
    await page.goto('http://localhost:3001/');
    await page.waitForSelector('[data-testid="app-container"]');
    await page.click('[data-testid="nav-item-reasoning"]');

    // When the user starts a new session via the form
    page.once('dialog', dialog => dialog.accept('test query'));
    await page.click('button.start-session-btn');

    // Then live steps should appear
    await page.waitForSelector('.step-item');
    const steps = page.locator('.step-item');
    await expect(steps).toHaveCount(2); // ✅ Two steps visible
  });

  test('🔄 should reconnect after server interruption', async ({ page }) => {
    // --- Mock WebSocket to observe reconnection attempts ---
    await page.evaluateOnNewDocument(() => {
      const instances = [];
      class MockWebSocket {
        constructor(url) {
          this.url = url;
          instances.push(this);
          setTimeout(() => this.onopen && this.onopen({}), 0);
        }
        send() {}
        close() {
          setTimeout(() => this.onclose && this.onclose({ code: 1006 }), 0);
        }
        addEventListener(type, handler) {
          this['on' + type] = handler;
        }
        removeEventListener() {}
      }
      window.WebSocket = MockWebSocket;
      window.__wsInstances = instances;
    });

    // Given an active connection
    await page.goto('http://localhost:3001/');
    await page.waitForSelector('[data-testid="app-container"]');

    // Record initial connection count
    const initial = await page.evaluate(() => window.__wsInstances.length);

    // Force disconnection by closing the first WebSocket instance
    await page.evaluate(() => {
      if (window.__wsInstances.length > 0 && window.__wsInstances[0]) {
        window.__wsInstances[0].close();
      }
    });

    // Wait for reconnection attempt
    await page.waitForTimeout(2500);

    // Then the client reconnects automatically
    const after = await page.evaluate(() => window.__wsInstances.length);
    expect(after).toBeGreaterThan(initial); // 🔁 Reconnection attempted
  });
});

// Mock data for API responses
const MOCK_STATS = {
  status: 'Active',
  transparency_level: 'Detailed',
  total_sessions: 1,
  active_sessions: 1,
};

const MOCK_SESSIONS = {
  active_sessions: [
    {
      session_id: 'session-1',
      query: 'Test session',
      transparency_level: 'detailed',
      start_time: Date.now(),
    },
  ],
};

const MOCK_TRACE = {
  session_id: 'session-1',
  steps: [
    { id: 1, message: 'Initial reasoning step' },
  ],
};

// BDD style tests for transparency streams with emoji output

test.describe('Transparency Streams', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept API calls and return mock data
    await page.route('**/api/transparency/**', (route) => {
      const url = route.request().url();
      if (url.endsWith('/statistics')) {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_STATS) });
      } else if (url.endsWith('/sessions/active')) {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SESSIONS) });
      } else if (/\/session\/[^/]+\/trace$/.test(url)) {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TRACE) });
      } else {
        route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
      }
    });
  });

  test('Dashboard connects to streams', async ({ page }) => {
    await test.step('Given the app is loaded 🏁', async () => {
      await page.goto('/');
    });

    await test.step('When the user opens the transparency dashboard 🔍', async () => {
      await page.click('[data-testid="nav-item-transparency"]');
      await page.waitForSelector('.activity-feed');
    });

    await test.step('Then real-time activity is visible 🛰️', async () => {
      await expect(page.locator('.activity-feed')).toBeVisible();
    });

    console.log('🎉 Transparency dashboard stream test completed');
  });

  test('Reasoning session viewer connects to stream', async ({ page }) => {
    await test.step('Given the app is loaded 🏁', async () => {
      await page.goto('/');
    });

    await test.step('When the user opens the reasoning session viewer 📡', async () => {
      await page.click('[data-testid="nav-item-reasoning"]');
      await page.waitForSelector('.reasoning-session-viewer');
    });

    await test.step('Then the viewer displays session list 📋', async () => {
      await expect(page.locator('.reasoning-session-viewer')).toBeVisible();
    });

    console.log('✅ Reasoning session viewer stream test completed');
  });
});

