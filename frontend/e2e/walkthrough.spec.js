// The PRODUCT.md walkthrough, driven through the GUI against the real Lean/Z3 backend.
import { test, expect } from "@playwright/test";

async function open(page) {
  await page.goto("/?bridge=http://127.0.0.1:8765");
  await expect(page.getByTestId("lean-status")).toContainText("Lean checker ready");
}

async function pickExperiment(page, industry, experimentId) {
  await page.getByTestId(`tab-${industry}`).click();
  await page.getByTestId(`exp-${experimentId}`).click();
  await expect(page.getByTestId("profile")).toBeVisible();
  await expect(page.getByTestId("confirm-requirements")).toBeEnabled();
}

async function chooseCryostat(page, search, configId) {
  await page.getByTestId("change-cryostat").click();
  await page.getByTestId("catalog-search").fill(search);
  await page.getByTestId(`config-${configId}`).click();
  await expect(page.getByTestId("catalog")).toHaveCount(0);
}

test("boot: Lean ready, every industry with experiments has a tab", async ({ page }) => {
  await open(page);
  await expect(page.locator(".tab")).toHaveCount(20);
  await expect(page.getByText("What would you like to do?")).toBeVisible();
  await expect(page.getByTestId("check-setup")).toBeDisabled();
});

test("Requirements met: frozen tissue on the Leica CM1950, verified badge, checks, report", async ({ page }) => {
  await open(page);
  await pickExperiment(page, "biology_and_biotechnology", "bio_cryosection_frozen_tissue");
  await page.getByTestId("confirm-requirements").click();
  await expect(page.getByTestId("confirm-state")).toContainText("Requirements confirmed");
  await chooseCryostat(page, "CM1950", "leica_cm1950_dualecotec_standard");
  // confirmed + new machine => checked automatically
  await expect(page.getByTestId("result")).toHaveAttribute("data-verdict", "REQUIREMENTS_MET");
  await expect(page.getByTestId("result-headline")).toHaveText("Requirements met");
  await expect(page.getByTestId("verified-badge")).toBeVisible();
  await expect(page.getByTestId("machine-name")).toContainText("Leica");

  await page.getByTestId("see-checks").click();
  await expect(page.getByTestId("checks-drawer")).toBeVisible();
  expect(await page.getByTestId("check-row").count()).toBeGreaterThan(0);
  await expect(page.getByTestId("verification-card")).toBeVisible();
  await page.getByTestId("close-checks").click();

  const [json] = await Promise.all([page.waitForEvent("download"), page.getByTestId("save-json").click()]);
  expect(json.suggestedFilename()).toMatch(/\.json$/);
  const [pdf] = await Promise.all([page.waitForEvent("download"), page.getByTestId("save-pdf").click()]);
  expect(pdf.suggestedFilename()).toMatch(/\.pdf$/);
});

test("Switching cryostats keeps the experiment and never keeps the old result", async ({ page }) => {
  await open(page);
  await pickExperiment(page, "materials_and_nanotechnology", "mat_magnetoresistance_10T");
  await page.getByTestId("confirm-requirements").click();
  await chooseCryostat(page, "DynaCool 9 T", "qd_dynacool_9T_eto_res");
  await expect(page.getByTestId("result")).toHaveAttribute("data-verdict", "DOES_NOT_MEET_REQUIREMENTS");
  await expect(page.getByTestId("result-headline")).toHaveText("Doesn't meet requirements");
  await expect(page.getByTestId("result-message")).toContainText("magnetic field");
  await expect(page.getByTestId("verified-badge")).toHaveCount(0);

  await page.getByTestId("change-cryostat").click();
  await page.getByTestId("catalog-search").fill("DynaCool 14 T");
  await page.getByTestId("config-qd_dynacool_14T_eto_vsm_hc").click();
  // the old (failing) result disappears immediately, then the new machine is checked
  await expect(page.getByTestId("result")).toHaveAttribute("data-verdict", "NEED_MORE_INFORMATION");
  await expect(page.getByTestId("profile")).toContainText("Measure"); // experiment still selected
  await expect(page.getByTestId("machine-gaps")).toBeVisible();
  await expect(page.getByTestId("verified-badge")).toHaveCount(0);
});

test("Unconfirmed requirements give Need more information, then confirm and check", async ({ page }) => {
  await open(page);
  await pickExperiment(page, "biology_and_biotechnology", "bio_cryosection_frozen_tissue");
  await chooseCryostat(page, "CM1950", "leica_cm1950_dualecotec_standard");
  await expect(page.getByTestId("result")).toHaveCount(0); // not confirmed: no automatic check
  await page.getByTestId("check-setup").click();
  await expect(page.getByTestId("result")).toHaveAttribute("data-verdict", "NEED_MORE_INFORMATION");
  await page.getByTestId("confirm-and-check").click();
  await expect(page.getByTestId("result")).toHaveAttribute("data-verdict", "REQUIREMENTS_MET");
});

test("A suggested change is reviewed, accepted and re-checked by Lean", async ({ page }) => {
  await open(page);
  await pickExperiment(page, "quantum_computing_and_sensing", "quantum_mxc_wiring_heat_budget");
  await page.getByTestId("confirm-requirements").click();
  await chooseCryostat(page, "LD400", "bluefors_ld400_hdw");
  await expect(page.getByTestId("result")).toHaveAttribute("data-verdict", "DOES_NOT_MEET_REQUIREMENTS");
  await expect(page.getByTestId("other-options")).toContainText("39");
  await page.locator('[data-testid^="review-fix_"]').first().click();
  await expect(page.getByTestId("fix-review")).toContainText("50");
  await page.getByTestId("accept-fix").click();
  await expect(page.getByTestId("result")).toHaveAttribute("data-verdict", "REQUIREMENTS_MET");
  await expect(page.getByTestId("verified-badge")).toBeVisible();
  await expect(page.getByTestId("fix-note")).toContainText("exactly the setup");
});

test("Editing a requirement resets confirmation and clears the result", async ({ page }) => {
  await open(page);
  await pickExperiment(page, "materials_and_nanotechnology", "mat_magnetoresistance_10T");
  await page.getByTestId("confirm-requirements").click();
  await chooseCryostat(page, "DynaCool 9 T", "qd_dynacool_9T_eto_res");
  await expect(page.getByTestId("result")).toBeVisible();
  await page.getByTestId("profile").getByRole("button", { name: "Review" }).click();
  await page.getByTestId("edit-magnetic_field.max").click();
  const form = page.getByTestId("edit-form-magnetic_field.max");
  await form.getByTestId("edit-form-magnetic_field.max-q").fill("1e4");
  await expect(form.getByTestId("edit-form-magnetic_field.max-save")).toBeDisabled(); // exponent notation refused in the UI
  await form.getByTestId("edit-form-magnetic_field.max-q").fill("8000");
  await form.getByTestId("edit-form-magnetic_field.max-save").click();
  await expect(page.getByTestId("confirm-state")).toContainText("confirm them");
  await expect(page.getByTestId("result")).toHaveCount(0);
  await expect(page.getByTestId("req-magnetic_field.max")).toContainText("Entered by you");
});
