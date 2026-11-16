import { expect, test } from "@playwright/test";

test.describe("landing page", () => {
  test("says it is a scam text checker and shows example output before any check", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Sentinel/);
    await expect(page.getByRole("heading", { level: 1, name: "Scam text checker." })).toBeVisible();
    await expect(page.getByLabel("Paste the text you received")).toBeVisible();
    await expect(page.locator(".out-sample .ln-verdict")).toContainText("This looks like a scam");
    await expect(page.getByRole("heading", { name: "Four tricks scam texts use" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "How Sentinel decides" })).toBeVisible();
    await expect(page.locator(".flow .flow-node h3")).toHaveText(["Spam pattern check", "Pressure tactic check", "Risk decision"]);
  });

  test("an empty press on the homepage explains what to do", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Check this message" }).click();
    await expect(page.locator(".term-out p.error[role=alert]")).toHaveText("Paste the text you received first, then press Check.");
    await expect(page.getByLabel("Paste the text you received")).toBeFocused();
  });

  test("checks a message right on the homepage: transcript, verdict, then the full breakdown", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    const out = page.locator(".term-out");
    await expect(out.locator(".ln-flag")).toHaveCount(3);
    await expect(out.locator(".ln-verdict")).toContainText("This looks like a scam");
    await expect(out.locator(".ln-verdict")).toContainText("High risk");
    // the transcript carries the verdict; the breakdown below doesn't repeat it as a second headline
    await expect(page.getByTestId("results").getByRole("heading", { name: "Full breakdown" })).toBeVisible();
  });

  test("has no horizontal scroll", async ({ page }) => {
    await page.goto("/");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  });
});

test.describe("check a message", () => {
  test("pressing Check with nothing pasted explains what to do and focuses the field", async ({ page }) => {
    await page.goto("/check");
    const submit = page.getByRole("button", { name: "Check this message" });
    await expect(submit).toBeEnabled();
    await page.getByLabel("Message to check").fill("   ");
    await submit.click();
    await expect(page.locator("p.error[role=alert]")).toHaveText("Paste the text you received first, then press Check.");
    await expect(page.getByLabel("Message to check")).toBeFocused();
    await expect(page.getByTestId("results")).toHaveCount(0);
  });

  test("scam message: verdict, risk scale, highlights and explanation cards", async ({ page }) => {
    await page.goto("/check");
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();

    const results = page.getByTestId("results");
    await expect(results.getByRole("heading", { name: "This looks like a scam" })).toBeVisible();
    await expect(results.getByRole("img", { name: "Overall risk: High" })).toBeVisible();
    await expect(results.getByRole("heading", { name: "Spam pattern match" })).toBeVisible();

    // highlighted evidence in the user's own message
    const marks = results.locator(".bubble mark.hl");
    expect(await marks.count()).toBeGreaterThanOrEqual(4);
    await expect(results.locator(".bubble mark.hl-fear").first()).toBeVisible();

    // one explanation card per detected tactic, each with what-to-do advice
    for (const name of ["Urgency", "Fear", "Pretending to be official"]) {
      const card = results.locator("article.xcard", { has: page.getByRole("heading", { name }) });
      await expect(card).toBeVisible();
      await expect(card.getByText("What to do")).toBeVisible();
    }
    await expect(results.getByRole("heading", { name: "What to do now" })).toBeVisible();
    // the limitation note is always visible, not hidden in a disclosure
    await expect(results.getByText("Sentinel analyzes message content, not the identity of its sender.", { exact: false })).toBeVisible();
  });

  test("highlight colours are the tactic colours, not the browser's default <mark> yellow", async ({ page }) => {
    await page.goto("/check");
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    const bg = await page.locator(".bubble mark.hl").first().evaluate((el) => getComputedStyle(el).backgroundColor);
    expect(bg).toBe("rgba(0, 0, 0, 0)");
  });

  test("normal message: low risk, calm guidance, no explanation cards", async ({ page }) => {
    await page.goto("/check");
    await page.getByRole("button", { name: "Friend’s message" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    const results = page.getByTestId("results");
    await expect(results.getByRole("heading", { name: "This looks like a normal message" })).toBeVisible();
    await expect(results.getByText("Low risk isn’t a guarantee")).toBeVisible();
    await expect(results.locator("article.xcard")).toHaveCount(0);
  });

  test("check another message resets the form and focuses the input", async ({ page }) => {
    await page.goto("/check");
    await page.getByRole("button", { name: "Prize win" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    await page.getByRole("button", { name: "Check another message" }).click();
    await expect(page.getByTestId("results")).toHaveCount(0);
    await expect(page.getByLabel("Message to check")).toHaveValue("");
    await expect(page.getByLabel("Message to check")).toBeFocused();
  });

  test("too-long messages are blocked with a clear counter", async ({ page }) => {
    await page.goto("/check");
    await page.getByLabel("Message to check").fill("a".repeat(2001));
    await expect(page.getByText("2001 / 2000 — too long")).toBeVisible();
    await expect(page.getByRole("button", { name: "Check this message" })).toBeDisabled();
  });

  test("API failure shows a helpful error, not a crash", async ({ page }) => {
    await page.route("**/api/analyze", (r) => r.fulfill({ status: 500, body: "boom" }));
    await page.goto("/check");
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    // (Next.js also renders an empty role="alert" route announcer, so scope to our error box)
    await expect(page.locator("p.error[role=alert]")).toHaveText("Sentinel couldn't check this message right now. Try again in a moment.");
  });

  test("user text is rendered as text, never as HTML", async ({ page }) => {
    let dialog = false;
    page.on("dialog", (d) => { dialog = true; void d.dismiss(); });
    await page.goto("/check");
    const payload = '<img src=x onerror="alert(1)"> URGENT verify now <script>alert(2)</script>';
    await page.getByLabel("Message to check").fill(payload);
    await page.getByRole("button", { name: "Check this message" }).click();
    await expect(page.getByTestId("results")).toBeVisible();
    await expect(page.locator(".bubble img")).toHaveCount(0);
    await expect(page.locator(".bubble")).toContainText("<img src=x");
    expect(dialog).toBe(false);
  });
});

test("highlights stay on the right words when the message contains emoji", async ({ page }) => {
  await page.goto("/check");
  await page.getByLabel("Message to check").fill("🚨🚨 URGENT: your account will be suspended 💳 verify immediately");
  await page.getByRole("button", { name: "Check this message" }).click();
  const marks = page.locator(".bubble mark.hl");
  await expect(marks.first()).toBeVisible();
  const texts = (await marks.allTextContents()).map((t) => t.replace(/\[[^:]+: |\]/g, ""));
  expect(texts).toContain("URGENT");
  expect(texts.some((t) => t.includes("will be suspended"))).toBe(true);
  // no broken surrogate halves anywhere in the bubble
  expect(await page.locator(".bubble").textContent()).not.toMatch(/[\uD800-\uDFFF](?![\uDC00-\uDFFF])/u);
});

test("a slow check can't overwrite the screen after 'Check another message'", async ({ page }) => {
  await page.goto("/check");
  await page.getByRole("button", { name: "Bank alert" }).click();
  await page.getByRole("button", { name: "Check this message" }).click();
  await expect(page.getByTestId("results")).toBeVisible();
  // second check is slow…
  await page.route("**/api/analyze", async (r) => { await new Promise((res) => setTimeout(res, 1500)); await r.continue().catch(() => {}); });
  await page.getByRole("button", { name: "Prize win" }).click();
  await page.getByRole("button", { name: "Check this message" }).click();
  // …and the user resets before it returns
  await page.getByRole("button", { name: "Friend’s message" }).click();
  await page.waitForTimeout(2000);
  await expect(page.getByTestId("results")).toHaveCount(0);
  await expect(page.getByLabel("Message to check")).toHaveValue(/Running 10 mins late/);
});

test("risk chart: status icon+label, figure per tactic row, keyboard tooltip, table view", async ({ page }) => {
  await page.goto("/check");
  await page.getByRole("button", { name: "Bank alert" }).click();
  await page.getByRole("button", { name: "Check this message" }).click();
  const results = page.getByTestId("results");
  await expect(results.locator(".status")).toHaveText("High risk");
  await expect(results.locator(".status svg")).toHaveCount(1);

  const rows = results.locator(".tactic-row");
  await expect(rows).toHaveCount(4);
  for (let i = 0; i < 4; i++) await expect(rows.nth(i).locator(".fig")).toHaveText(/Strong|Present|Faint hint|Not found/);

  await rows.first().focus();
  await expect(page.getByRole("tooltip")).toContainText("Urgency");
  await rows.first().blur();
  await expect(page.getByRole("tooltip")).toHaveCount(0);

  await results.getByText("Show these numbers as a table").click();
  const table = results.locator(".numbers table");
  await expect(table.getByRole("row")).toHaveCount(7); // header + overall + spam + 4 tactics
  await expect(table).toContainText("Overall risk");
});

test("API contract: rejects blank input with 422", async ({ request }) => {
  const r = await request.post("/api/analyze", { data: { text: "   " } });
  expect(r.status()).toBe(422);
});

// ---------------- opt-in AI explanation (/api/contextual is mocked: no paid calls in tests) ----------------
const AI_OK = {
  status: "ok", model: "claude-haiku-5-5", redacted: true,
  analysis: {
    intent_summary: "Pretends to be your bank and pushes you to a fake verification link.",
    implicit_tactics: [{ type: "lookalike_link", quote: "hsbc-secure-check.com", why: "Not HSBC's real website." }],
    sensitive_requests: [{ kind: "bank_login", quote: "verify immediately" }],
    explanation: "Banks don't ask you to verify your account through a link in a text.",
    safe_next_steps: ["Don't tap the link.", "Call HSBC on the number on your card."],
  },
};

test.describe("AI explanation (opt-in)", () => {
  test("is off by default, discloses Anthropic, and sends nothing unless ticked", async ({ page }) => {
    let calls = 0;
    await page.route("**/api/contextual", (r) => { calls++; return r.fulfill({ json: AI_OK }); });
    await page.goto("/check");
    const box = page.getByLabel("Also get an AI explanation (optional)");
    await expect(box).not.toBeChecked();
    await expect(page.locator("#ai-optin-desc")).toContainText("Anthropic");
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    await expect(page.getByTestId("results")).toBeVisible();
    await expect(page.getByTestId("ai-card")).toHaveCount(0);
    expect(calls).toBe(0);
  });

  test("when ticked: sends consent, shows the card, and the risk rating is unchanged", async ({ page }) => {
    let body: unknown = null;
    await page.route("**/api/contextual", (r) => { body = r.request().postDataJSON(); return r.fulfill({ json: AI_OK }); });
    await page.goto("/check");
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    const ratingWithout = await page.getByTestId("results").locator(".status").textContent();

    await page.getByRole("button", { name: "Check another message" }).click();
    await page.getByLabel("Also get an AI explanation (optional)").check();
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    const card = page.getByTestId("ai-card");
    await expect(card).toContainText("Pretends to be your bank");
    await expect(card).toContainText("It asks for bank login details");
    await expect(card).toContainText("doesn’t change the risk rating");
    expect(body).toMatchObject({ consent: true });
    await expect(page.getByTestId("results").locator(".status")).toHaveText(ratingWithout ?? "");
  });

  test("shows a prominent separate AI warning when Low conflicts with AI findings", async ({ page }) => {
    const lowResult = {
      text: "Hi Mum, this is my new number. Can you send me £200?",
      verdict: "This looks like a normal message",
      risk_level: "low",
      risk_score: 0.1,
      scam_probability: 0.1,
      classifier_label: "legitimate",
      marketing_message: false,
      tactics: [],
      tactics_detected: [],
      advice: "Check with the person another way.",
    };
    await page.route("**/api/analyze", (r) => r.fulfill({ json: lowResult }));
    await page.route("**/api/contextual", (r) => r.fulfill({
      json: {
        ...AI_OK,
        analysis: {
          ...AI_OK.analysis,
          implicit_tactics: [{ type: "trust_building", quote: "this is my new number", why: "It builds trust through a new contact." }],
          sensitive_requests: [{ kind: "payment", quote: "send me £200", }],
        },
      },
    }));
    await page.goto("/check");
    await page.getByLabel("Message to check").fill(lowResult.text);
    await page.getByLabel("Also get an AI explanation (optional)").check();
    await page.getByRole("button", { name: "Check this message" }).click();
    const results = page.getByTestId("results");
    await expect(results.getByRole("heading", { name: "This looks like a normal message" })).toBeVisible();
    const warning = page.getByTestId("ai-additional-warning");
    await expect(warning).toBeVisible();
    await expect(warning).toContainText("Additional warning detected by AI");
    await expect(warning).toContainText("original classifier result remains Low risk");
    await expect(results.locator(".status")).toHaveText("Low risk");
  });

  test("unavailable and network failures degrade to a note; the main result stays", async ({ page }) => {
    await page.route("**/api/contextual", (r) => r.fulfill({ json: { status: "unavailable", reason: "daily_limit" } }));
    await page.goto("/check");
    await page.getByLabel("Also get an AI explanation (optional)").check();
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    await expect(page.getByTestId("ai-card")).toContainText("reached today's limit");
    await expect(page.getByRole("heading", { name: "This looks like a scam" })).toBeVisible();

    await page.unroute("**/api/contextual");
    await page.route("**/api/contextual", (r) => r.abort("failed"));
    await page.getByRole("button", { name: "Check another message" }).click();
    await page.getByRole("button", { name: "Prize win" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    await expect(page.getByTestId("ai-card")).toContainText("isn't available right now");
    await expect(page.getByTestId("results").locator(".status")).toBeVisible();
  });

  test("a contextual 429 is shown as a temporary AI-service problem", async ({ page }) => {
    await page.route("**/api/contextual", (r) => r.fulfill({ status: 429, body: "rate limited" }));
    await page.goto("/check");
    await page.getByLabel("Also get an AI explanation (optional)").check();
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    await expect(page.getByTestId("ai-card")).toContainText("AI service is busy right now");
    await expect(page.getByTestId("results").locator(".status")).toHaveText("High risk");
  });

  test("AI text is rendered as text, never as HTML", async ({ page }) => {
    let dialog = false;
    page.on("dialog", (d) => { dialog = true; void d.dismiss(); });
    const evil = { ...AI_OK, analysis: { ...AI_OK.analysis, intent_summary: '<img src=x onerror="alert(1)">', explanation: "<script>alert(2)</script>" } };
    await page.route("**/api/contextual", (r) => r.fulfill({ json: evil }));
    await page.goto("/check");
    await page.getByLabel("Also get an AI explanation (optional)").check();
    await page.getByRole("button", { name: "Bank alert" }).click();
    await page.getByRole("button", { name: "Check this message" }).click();
    await expect(page.getByTestId("ai-card")).toContainText("<img src=x");
    await expect(page.getByTestId("ai-card").locator("img")).toHaveCount(0);
    expect(dialog).toBe(false);
  });
});
