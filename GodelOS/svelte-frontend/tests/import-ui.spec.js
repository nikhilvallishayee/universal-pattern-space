import { test, expect } from '@playwright/test';

test.describe('Smart Import modal UX', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="sidebar-nav"]', { timeout: 15000 });
  });

  test('opens Knowledge Import modal and shows tabs', async ({ page }) => {
    await page.getByTestId('nav-item-import').click();
    await page.getByRole('button', { name: /Open Knowledge Import/i }).click();

    // Modal title visible
    await expect(page.getByRole('heading', { name: /Smart Knowledge Import/i })).toBeVisible();

    // Tabs present
    await expect(page.getByText('File')).toBeVisible();
    await expect(page.getByText('URL')).toBeVisible();
    await expect(page.getByText('Text')).toBeVisible();
    await expect(page.getByText('API')).toBeVisible();
  });
});

