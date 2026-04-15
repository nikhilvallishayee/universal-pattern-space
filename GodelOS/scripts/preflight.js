const fs = require('fs');
const path = require('path');

module.exports = async () => {
  const requiredModules = [
    'aria-query',
  ];
  const missing = [];

  for (const mod of requiredModules) {
    try {
      require.resolve(mod);
    } catch (err) {
      missing.push(mod);
    }
  }

  try {
    const vitePkg = require.resolve('vite/package.json');
    const viteCli = path.join(path.dirname(vitePkg), 'dist', 'node', 'cli.js');
    if (!fs.existsSync(viteCli)) {
      missing.push('vite/dist/node/cli.js');
    }
  } catch (err) {
    missing.push('vite/dist/node/cli.js');
  }

  try {
    const { chromium } = require('playwright');
    const execPath = chromium.executablePath();
    if (!fs.existsSync(execPath)) {
      missing.push('Chromium binary');
    }
  } catch (err) {
    missing.push('playwright/chromium');
  }

  if (missing.length) {
    const message = `Missing dependencies:\n - ${missing.join('\n - ')}`;
    console.error(`\u274c ${message}`);
    throw new Error(message);
  }

  console.log('\u2705 Pre-flight checks passed');
  process.env.PREFLIGHT_OK = 'true';
};
