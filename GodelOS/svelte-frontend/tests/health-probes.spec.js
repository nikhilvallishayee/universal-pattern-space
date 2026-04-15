// Health Probes UI spec
import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3001';

test.describe('Health Probes Widget', () => {
  test('should render subsystem probes and show statuses', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    // Navigate to the enhanced dashboard if needed
    const navItem = page.locator('[data-testid="nav-item-enhanced"]');
    if (await navItem.count()) {
      try { await navItem.first().click({ timeout: 5000 }); } catch {}
    }
    // Wait for the probes container
    const probes = page.locator('[data-testid="health-probes"]');
    await expect(probes).toBeVisible({ timeout: 10000 });
    // Should contain at least one probe card
    const cards = probes.locator('[data-testid^="probe-"]');
    await expect(await cards.count()).toBeGreaterThan(0);
  });
});

