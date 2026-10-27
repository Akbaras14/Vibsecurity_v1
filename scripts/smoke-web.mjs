// Run against a local API and worker. Uses a temporary project, deleted in finally.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';

const web = process.env.TEST_WEB_URL || 'http://127.0.0.1:3000';
const api = process.env.TEST_API_URL || 'http://127.0.0.1:8000/api';
assert(['localhost', '127.0.0.1'].includes(new URL(web).hostname), 'Only test a local frontend.');
assert(['localhost', '127.0.0.1'].includes(new URL(api).hostname), 'Only test a local backend.');
const zip = execFileSync(process.env.VIBESEC_PYTHON || 'python', ['-c',
  "import io,sys,zipfile; b=io.BytesIO(); z=zipfile.ZipFile(b,'w'); z.writestr('app.js','eval(location.search);'); z.writestr('package-lock.json',sys.argv[1]); z.close(); sys.stdout.buffer.write(b.getvalue())",
  JSON.stringify({ name: 'vibesec-smoke', version: '1.0.0', lockfileVersion: 3, packages: {
    '': { name: 'vibesec-smoke', version: '1.0.0', dependencies: { lodash: '4.17.20' } },
    'node_modules/lodash': { version: '4.17.20', resolved: 'https://registry.npmjs.org/lodash/-/lodash-4.17.20.tgz' }
  } })]);
const browser = await chromium.launch({ headless: true,
  ...(process.env.TEST_CHROMIUM ? { executablePath: process.env.TEST_CHROMIUM } : {}) });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
let projectId;
let scanId;
try {
  await page.goto(`${web}/dashboard`);
  await page.getByRole('heading', { name: 'Ringkasan keamanan' }).waitFor();
  await page.getByRole('link', { name: '＋ Tambah proyek', exact: true }).click();
  await page.getByLabel('Nama proyek').fill(`[SMOKE] VibeSec ${Date.now()}`);
  await page.getByLabel('Teknologi', { exact: true }).fill('JavaScript');
  await page.getByText('Data penelitian dan asal proyek (opsional)', { exact: true }).click();
  await page.getByLabel('Kode sampel').fill('SMOKE-LOCAL');
  await page.getByRole('button', { name: 'Buat proyek', exact: true }).click();
  await page.waitForURL(/\/projects\/[a-f0-9]{32}$/);
  projectId = new URL(page.url()).pathname.split('/').at(-1);
  await page.getByText('Risiko tertinggi', { exact: true }).waitFor();
  await page.locator('input[type="file"]').setInputFiles({ name: 'smoke.zip', mimeType: 'application/zip', buffer: zip });
  await page.getByRole('button', { name: 'Mulai pemindaian →', exact: true }).click();
  await page.waitForURL(/\/scans\/[a-f0-9]{32}$/);
  scanId = new URL(page.url()).pathname.split('/').at(-1);
  let result;
  for (let attempt = 0; attempt < 660; attempt++) {
    const response = await fetch(`${api}/scans/${scanId}`);
    assert(response.ok, 'Scan API must respond.');
    result = (await response.json()).data;
    if (!['queued', 'running'].includes(result.status)) break;
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  assert(!['queued', 'running'].includes(result.status), 'Worker must finish the test scan.');
  if (process.env.TEST_REQUIRE_SCANNERS === '1') {
    assert.equal(result.status, 'completed', 'Both real scanners must finish successfully.');
    assert(result.summary.methods.sast > 0 && result.summary.methods.sca > 0,
      'Controlled sample must produce SAST and SCA findings.');
  }
  await page.reload();
  await page.getByRole('heading', { name: 'Daftar temuan', exact: true }).waitFor();
  await page.locator('summary').filter({ hasText: /^Distribusi hasil$/ }).click();
  await page.getByRole('heading', { name: 'Distribusi hasil', exact: true }).waitFor();
  const exported = await fetch(`${api}/scans/${scanId}/export?format=json`).then(response => response.json());
  assert.equal(exported.scan.id, scanId);
  assert.equal(exported.scan.sha256.length, 64);
  await page.getByRole('link', { name: 'Laporan ↗', exact: true }).click();
  await page.getByRole('heading', { name: 'Identitas analisis', exact: true }).waitFor();
  await page.getByRole('heading', { name: 'Batas analisis', exact: true }).waitFor();
  await page.emulateMedia({ media: 'print' });
  assert.equal(await page.locator('.sidebar').isVisible(), false);
  await page.emulateMedia({ media: 'screen' });
  await mkdir('.cache/screenshots', { recursive: true });
  await page.screenshot({ path: '.cache/screenshots/report.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${web}/projects`);
  await page.getByRole('heading', { name: 'Daftar proyek', exact: true }).waitFor();
  await page.getByRole('button', { name: 'Buka atau tutup navigasi' }).click();
  assert.equal(await page.locator('.sidebar').isVisible(), true);
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await page.getByRole('heading', { name: 'Ringkasan keamanan' }).waitFor();
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.screenshot({ path: '.cache/screenshots/mobile.png', fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${web}/dashboard`);
  await page.getByRole('heading', { name: 'Aktivitas terbaru', exact: true }).waitFor();
  await page.getByText('Rekap penelitian', { exact: true }).click();
  await page.getByRole('heading', { name: 'Status scan terbaru per proyek', exact: true }).waitFor();
  await page.getByRole('heading', { name: 'Distribusi hasil', exact: true }).waitFor();
  await page.screenshot({ path: '.cache/screenshots/dashboard.png', fullPage: true });
  await page.goto(`${web}/projects/${projectId}`);
  await page.getByRole('button', { name: 'Hapus proyek', exact: true }).click();
  await page.getByRole('button', { name: 'Ya, hapus proyek', exact: true }).click();
  await page.waitForURL(`${web}/projects`);
  projectId = null;
  assert.deepEqual(errors, [], 'No browser runtime errors.');
  console.log(`Web smoke passed: create → upload → scan (${result.status}) → export → print → mobile → delete.`);
} finally {
  if (projectId) {
    const response = await fetch(`${api}/projects/${projectId}`, { method: 'DELETE' });
    if (!response.ok) console.error('Test project cleanup pending:', projectId, '— let worker finish, then delete it.');
  }
  await browser.close();
}
