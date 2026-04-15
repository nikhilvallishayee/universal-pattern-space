const { test, expect } = require('@playwright/test');

test.describe('Pre-flight validation', () => {
  test('environment is ready', () => {
    const passed = process.env.PREFLIGHT_OK === 'true';
    console.log(passed ? '✅ pre-flight script passed' : '❌ pre-flight script failed');
    expect(passed).toBe(true);
  });
});
