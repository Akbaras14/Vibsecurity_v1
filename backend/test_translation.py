import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from . import translation


class TranslationCheck(unittest.TestCase):
    def test_preserves_code_urls_original_and_uses_cache(self):
        class Tokenizer:
            def tokenize(self, text):
                return text.split()
            def detokenize(self, tokens):
                return 'Indonesia ' + ' '.join(tokens)
            def normalize(self, text):
                return text
            def process_line(self, text):
                return text
        class Translator:
            def translate_batch(self, tokens, **kwargs):
                return [SimpleNamespace(hypotheses=tokens)]
        source = 'Unsafe `eval(input)` see https://example.com\n```js\neval(input)\n```'
        finding = {'title': 'Unsafe code', 'detail': {'description': source, 'snippet': 'eval(input)'}}
        with tempfile.TemporaryDirectory() as directory, patch.object(translation, 'DIRECTORY', Path(directory)), \
                patch.object(translation, 'engine', return_value=(Translator(), (Tokenizer(),) * 4)) as engine:
            translation.translate_finding(finding)
            result = finding['detail']['translation']
            self.assertEqual(result['status'], 'completed')
            for protected in ('`eval(input)`', 'https://example.com', '```js\neval(input)\n```'):
                self.assertIn(protected, result['description'])
            self.assertEqual(finding['detail']['description'], source)
            self.assertEqual(finding['detail']['snippet'], 'eval(input)')
            engine.reset_mock()
            translation.translate_finding(finding)
            engine.assert_not_called()

    def test_missing_model_does_not_break_scan(self):
        finding = {'title': 'Unsafe code', 'detail': {}}
        with tempfile.TemporaryDirectory() as directory, patch.object(translation, 'DIRECTORY', Path(directory)), \
                patch.object(translation, 'engine', side_effect=RuntimeError('missing model')), \
                self.assertLogs('vibesec.worker'):
            translation.translate_finding(finding)
        self.assertEqual(finding['detail']['translation']['status'], 'failed')
