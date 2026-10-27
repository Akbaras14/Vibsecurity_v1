import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
try {
  await page.goto('http://127.0.0.1:3001');
  const input = page.getByLabel('Tugas baru');
  await input.fill('Periksa proyek di VibeSec');
  await page.getByRole('button', { name: 'Tambah', exact: true }).click();
  await page.getByRole('checkbox').check();
  await page.getByLabel('Tampilkan').selectOption('active');
  await page.getByText('Tidak ada tugas pada filter ini.').waitFor();
  await page.reload();
  await page.getByRole('checkbox').waitFor();
  assert(await page.getByRole('checkbox').isChecked());
  await page.getByRole('button', { name: 'Hapus tugas: Periksa proyek di VibeSec' }).click();
  await page.getByText('Belum ada tugas. Tambahkan tugas pertama di atas.').waitFor();
  await input.fill('<script>alert(1)</script>');
  await page.getByRole('button', { name: 'Tambah', exact: true }).click();
  await page.getByText('<script>alert(1)</script>', { exact: true }).waitFor();
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.evaluate(() => localStorage.setItem('vibesec-todo-demo-v1', '{invalid'));
  await page.reload();
  await page.getByRole('status').filter({ hasText: 'tidak dapat dibaca' }).waitFor();
  assert.deepEqual(errors, []);
  console.log('Todo demo passed: add, complete, filter, reload, delete, escaped text, invalid storage, mobile layout.');
} finally { await browser.close(); }
