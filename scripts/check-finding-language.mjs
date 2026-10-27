import assert from 'node:assert/strict';
import { findingText } from '../app/components/finding-language.mjs';

const finding = { source_id: 'GHSA-23c5-xmqv-rm74', title: 'Original title', description: 'Original evidence', path: 'package-lock.json' };
const before = structuredClone(finding);
const text = findingText(finding);
assert.equal(text.translated, true);
assert.match(text.title, /penolakan layanan/);
assert.match(text.description, /pengaturan bawaan/);
assert.deepEqual(finding, before);
assert.equal(findingText({ ...finding, source_id: 'CVE-alias', aliases: [finding.source_id] }).title, text.title);
assert.match(findingText({ source_id: 'GHSA-2g4f-4pwh-qvx6' }).description, /opsi \$data diaktifkan/);
const unknown = findingText({ source_id: '__proto__', title: 'Original', description: 'Untranslated' });
assert.deepEqual(unknown, { title: 'Original', description: 'Untranslated', translated: false });
const automatic = findingText({ ...finding, translation: { status: 'completed', title: 'Judul otomatis', description: 'Bukti otomatis' } });
assert.equal(automatic.description, 'Bukti otomatis');
assert.equal(automatic.automatic, true);
console.log('Indonesian finding explanations: identity, aliases, prerequisites, fallback, and unchanged evidence passed.');
