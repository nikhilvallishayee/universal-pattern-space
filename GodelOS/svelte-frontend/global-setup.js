// Global setup to ensure backend is up before tests
export default async () => {
  const url = process.env.BACKEND_URL || 'http://localhost:8000/api/health';
  const timeoutMs = parseInt(process.env.BACKEND_WAIT_TIMEOUT || '120000', 10);
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url, { method: 'GET' });
      if (res.ok) {
        // Backend healthy
        return;
      }
    } catch (e) {
      // ignore until timeout
    }
    await new Promise(r => setTimeout(r, 1500));
  }
  console.warn(`[global-setup] Backend did not become healthy at ${url} within ${timeoutMs}ms. Tests may fail.`);
};

