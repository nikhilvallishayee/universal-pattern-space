const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  testMatch: /.*\.spec\.js/,
  fullyParallel: false, // Run tests sequentially for better stability
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : 1,
  outputDir: './test-results',
  reporter: [
    ['html', { outputFolder: './playwright-report-output' }],
    ['json', { outputFile: './test-results/test-results.json' }],
    ['list']
  ],
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:3001',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: process.env.PLAYWRIGHT_HEADLESS !== 'false',
    timeout: parseInt(process.env.PLAYWRIGHT_TEST_TIMEOUT) || 60000
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    }
  ],
  globalSetup: require.resolve('./scripts/preflight.js'),
  webServer: {
    command: 'echo "Using existing servers"',
    port: 3001,
    reuseExistingServer: true,
  }
});
