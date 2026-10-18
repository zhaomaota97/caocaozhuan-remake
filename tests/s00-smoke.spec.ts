import { test, expect } from '@playwright/test';

async function advanceOpening(page: any) {
  for (let i = 0; i < 4; i++) {
    await page.waitForTimeout(2500);
    await page.evaluate(() => {
      const scene = (window as any).battleGame.scene.getScene('default');
      const hit = scene.modal?.getData('nativeHitRegions')?.[0];
      if (hit) hit.command();
    });
  }
  await page.waitForTimeout(3000);
}

test('S_00 battle shell loads and supports native viewport interactions', async ({ page }) => {
  await page.setViewportSize({width: 1120, height: 640});
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5174/');
  await advanceOpening(page);

  await expect.poll(() => page.evaluate(() => {
    const scene = (window as any).battleGame.scene.getScene('default');
    return scene.units.length;
  })).toBe(26);

  await page.mouse.click(360, 80);
  await page.mouse.click(360, 80, {button: 'right'});
  await expect.poll(() => page.evaluate(() => Boolean((window as any).battleGame.scene.getScene('default').contextMenu))).toBe(true);

  const before = await page.evaluate(() => (window as any).battleGame.scene.getScene('default').cameras.main.scrollY);
  await page.mouse.wheel(0, 500);
  const after = await page.evaluate(() => (window as any).battleGame.scene.getScene('default').cameras.main.scrollY);
  expect(after).toBeGreaterThanOrEqual(before);
  expect(errors).toEqual([]);
});

test('S_00 enemy turn completes and advances the round', async ({ page }) => {
  await page.setViewportSize({width: 1120, height: 640});
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5174/');
  await advanceOpening(page);
  const beforeTurn = await page.evaluate(() => (window as any).battleGame.scene.getScene('default').currentTurn);
  await page.evaluate(() => (window as any).battleGame.scene.getScene('default').finishTurn());
  await expect.poll(() => page.evaluate(() => (window as any).battleGame.scene.getScene('default').turnTransitioning), {timeout: 30000}).toBe(false);
  await expect.poll(() => page.evaluate(() => (window as any).battleGame.scene.getScene('default').currentTurn), {timeout: 30000}).toBe(beforeTurn + 1);
  expect(errors).toEqual([]);
});

test('S_00 victory state locks battlefield input', async ({ page }) => {
  await page.setViewportSize({width: 1120, height: 640});
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5174/');
  await advanceOpening(page);
  const result = await page.evaluate(() => {
    const scene = (window as any).battleGame.scene.getScene('default');
    scene.openS00Victory();
    const before = scene.selected;
    scene.select(scene.units[0]);
    return {ended: scene.battleEnded, modal: Boolean(scene.modal), unchanged: before === scene.selected};
  });
  expect(result).toEqual({ended: true, modal: true, unchanged: true});
  expect(errors).toEqual([]);
});

test('S_00 defeat state opens failure modal', async ({ page }) => {
  await page.setViewportSize({width: 1120, height: 640});
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5174/');
  await advanceOpening(page);
  const result = await page.evaluate(() => {
    const scene = (window as any).battleGame.scene.getScene('default');
    scene.openS00Defeat();
    return {ended: scene.battleEnded, modal: Boolean(scene.modal)};
  });
  expect(result).toEqual({ended: true, modal: true});
  expect(errors).toEqual([]);
});

test('S_00 information panels use current level data', async ({ page }) => {
  await page.setViewportSize({width: 1120, height: 640});
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5174/');
  await advanceOpening(page);
  const result = await page.evaluate(() => {
    const scene = (window as any).battleGame.scene.getScene('default');
    const panels = ['showConditions', 'showInventory', 'showRoster', 'showItemEncyclopedia'];
    for (const name of panels) { scene.modal?.destroy(); scene.modal = undefined; scene[name](); }
    return {map: scene.mapId, units: scene.units.length};
  });
  expect(result).toEqual({map: 0, units: 26});
  expect(errors).toEqual([]);
});

test('S_00 context menu remains hittable after scrolling', async ({ page }) => {
  await page.setViewportSize({width: 1120, height: 640});
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5174/');
  await advanceOpening(page);
  await page.mouse.wheel(0, 500);
  await page.evaluate(() => {
    const scene = (window as any).battleGame.scene.getScene('default');
    const scroll = scene.cameras.main.scrollY;
    const unit = scene.units.find((u: any) => u.side === 'player' && !u.nativeHidden && u.hp > 0 && 56 + u.y * 48 + 24 - scroll > 60 && 56 + u.y * 48 + 24 - scroll < 620);
    scene.select(unit);
  });
  const position = await page.evaluate(() => {
    const scene = (window as any).battleGame.scene.getScene('default');
    const unit = scene.selected;
    return {x: unit.x * 48 + 24, y: 56 + unit.y * 48 + 24 - scene.cameras.main.scrollY};
  });
  await page.mouse.click(position.x, position.y, {button: 'right'});
  await expect.poll(() => page.evaluate(() => Boolean((window as any).battleGame.scene.getScene('default').contextMenu))).toBe(true);
  expect(errors).toEqual([]);
});
