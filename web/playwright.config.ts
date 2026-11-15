import { defineConfig, devices } from "@playwright/test";

const PY = process.env.VERITAS_PYTHON ?? "../.venv/bin/python";
const BASE = process.env.E2E_BASE_URL;

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: true,
  reporter: [["list"]],
  use: {
    baseURL: BASE ?? "http://localhost:3000",
    trace: "retain-on-failure",
    // Protected Vercel previews: run via `vc env run -- …` so VERCEL_OIDC_TOKEN is injected (never printed).
    extraHTTPHeaders: BASE && process.env.VERCEL_OIDC_TOKEN
      ? { "x-vercel-trusted-oidc-idp-token": process.env.VERCEL_OIDC_TOKEN }
      : undefined,
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
    // iPhone viewport + touch, rendered by Chromium (WebKit can't be installed in this environment)
    { name: "iphone-size", use: { ...devices["iPhone 13"], browserName: "chromium" } },
  ],
  // Against a deployed URL (E2E_BASE_URL) we start nothing; locally we run the real API + Next.
  webServer: BASE
    ? undefined
    : [
        {
          command: `${PY} -m uvicorn veritas.api:app --port 8000 --app-dir ../src`,
          url: "http://127.0.0.1:8000/api/health",
          reuseExistingServer: true,
        },
        { command: "npx next dev -p 3000", url: "http://localhost:3000", reuseExistingServer: true },
      ],
});
