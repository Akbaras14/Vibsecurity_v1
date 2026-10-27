import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const web = 'http://127.0.0.1:3000';
const api = 'http://127.0.0.1:8000/api';
const scan = 'b4b01f8620714f968bd70f6ed7f7f610';
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on('pageerror', e => errors.push(e.message));
let project;
try {
  await page.goto(`${web}/dashboard`);
  await page.getByRole('heading', { name: 'Ringkasan keamanan', exact: true }).waitFor();
  await page.getByRole('heading', { name: 'Aktivitas terbaru', exact: true }).waitFor();
  assert.equal(await page.getByRole('heading', { name: 'Rancangan 12 sampel penelitian', exact: true }).isVisible(), false);
  await page.screenshot({ path: '.cache/screenshots/dashboard-compact.png', fullPage: true });
  await page.getByText('Rekap penelitian', { exact: true }).click();
  await page.getByRole('heading', { name: 'Rancangan 12 sampel penelitian', exact: true }).waitFor();
  await page.goto(`${web}/projects/new`);
  assert.equal(await page.getByLabel('Kode sampel').isVisible(), false);
  await page.getByLabel('Nama proyek').fill('[UJI UI RINGKAS] Metadata');
  await page.getByText('Data penelitian dan asal proyek (opsional)', { exact: true }).click();
  await page.getByLabel('Kode sampel').fill('UI-COMPACT');
  await page.getByLabel('Kelompok sampel').selectOption('chatbot');
  await page.getByLabel('Alat AI').fill('Uji antarmuka');
  await page.getByText('Data penelitian dan asal proyek (opsional)', { exact: true }).click();
  await page.getByRole('button', { name: 'Buat proyek', exact: true }).click();
  await page.waitForURL(/\/projects\/[a-f0-9]{32}$/);
  project = new URL(page.url()).pathname.split('/').at(-1);
  let saved = (await fetch(`${api}/projects/${project}`).then(r => r.json())).data;
  assert.equal(saved.sample_code, 'UI-COMPACT');
  assert.equal(saved.sample_group, 'chatbot');
  await page.getByText('Ubah informasi proyek', { exact: true }).click();
  await page.getByRole('button', { name: 'Simpan perubahan', exact: true }).click();
  await page.getByRole('status').filter({ hasText: 'tersimpan' }).waitFor();
  saved = (await fetch(`${api}/projects/${project}`).then(r => r.json())).data;
  assert.equal(saved.ai_tool, 'Uji antarmuka');
  assert.equal(saved.sample_code, 'UI-COMPACT');
  await page.goto(`${web}/scans/${scan}`);
  await page.getByRole('heading', { name: 'Daftar temuan', exact: true }).waitFor();
  assert.equal(await page.getByLabel('Catatan pemeriksaan cakupan dan konfigurasi').isVisible(), false);
  assert.equal(await page.getByLabel('Semua metode').isVisible(), false);
  await page.getByLabel('Cari kerentanan').fill('GHSA-23c5-xmqv-rm74');
  await page.getByText('1 hasil', { exact: true }).waitFor();
  await page.locator('summary').filter({ hasText: /^Filter lainnya/ }).click();
  await page.getByLabel('Semua metode').selectOption('sca');
  await page.getByRole('button', { name: 'Hapus semua filter', exact: true }).click();
  await page.locator('summary').filter({ hasText: /^Distribusi hasil$/ }).click();
  await page.getByRole('heading', { name: 'Distribusi hasil', exact: true }).waitFor();
  await page.locator('summary').filter({ hasText: /^Distribusi hasil$/ }).click();
  for (const route of ['/dashboard', `/scans/${scan}`, '/projects/new']) {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(web + route);
    await page.locator('h1').waitFor();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, route);
  }
  await page.screenshot({ path: '.cache/screenshots/form-compact-mobile.png', fullPage: true });
  assert.deepEqual(errors, []);
  console.log('Compact UI passed: disclosures, search/filter, hidden metadata saved and preserved, mobile layout.');
} finally {
  if (project) {
    const response = await fetch(`${api}/projects/${project}`, { method: 'DELETE' });
    assert(response.ok, 'Temporary project cleanup must succeed.');
  }
  await browser.close();
}
