"""Local English–Indonesian translation; original scanner evidence stays intact."""
import hashlib
import json
import logging
import re
from functools import lru_cache
from .config import ROOT
from .store import connect, query

DIRECTORY = ROOT / 'storage' / 'translation'
PROTECTED = re.compile(r'(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]+`|https?://[^\s<>]+)', re.MULTILINE)


@lru_cache(maxsize=1)
def engine():
    import ctranslate2
    from sacremoses import MosesTokenizer, MosesDetokenizer, MosesPunctNormalizer
    from subword_nmt.apply_bpe import BPE
    model = DIRECTORY / 'translate-en_id-1_9'
    with (model / 'bpe.model').open(encoding='utf-8') as stream:
        bpe = BPE(stream)
    return (ctranslate2.Translator(str(model / 'model'), device='cpu', compute_type='int8', intra_threads=2),
            (MosesTokenizer('en'), MosesDetokenizer('id'), MosesPunctNormalizer('en'), bpe))


def translate(text, heartbeat=lambda: None):
    translator, (tokenizer, detokenizer, normalizer, bpe) = engine()
    output = []
    for index, part in enumerate(PROTECTED.split(text)):
        if index % 2 or not part.strip():
            output.append(part)
            continue
        # Keep paragraphs and whitespace while bounding each inference to 180 tokens.
        for line in part.splitlines(keepends=True):
            if not line.strip():
                output.append(line)
                continue
            tokens = bpe.process_line(' '.join(tokenizer.tokenize(normalizer.normalize(line.strip())))).split()
            translated = []
            for start in range(0, len(tokens), 180):
                heartbeat()
                result = translator.translate_batch([tokens[start:start + 180]], beam_size=4, max_decoding_length=512)[0]
                translated.append(detokenizer.detokenize(' '.join(result.hypotheses[0]).replace('@@ ', '').split()))
            output.append(line[:len(line) - len(line.lstrip())] + ' '.join(translated) + line[len(line.rstrip()):])
    return ''.join(output)


def translate_finding(finding, heartbeat=lambda: None):
    detail = finding['detail']
    source = [finding['title'], detail.get('description') or finding['title']]
    key = hashlib.sha256(json.dumps(source, ensure_ascii=False).encode()).hexdigest()
    cache = DIRECTORY / 'cache' / (key + '.json')
    try:
        if cache.exists():
            result = json.loads(cache.read_text(encoding='utf-8'))
        else:
            result = {'status': 'completed', 'language': 'id', 'engine': 'Argos en-id 1.9 / CTranslate2',
                      'title': translate(source[0], heartbeat), 'description': translate(source[1], heartbeat)}
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
        detail['translation'] = result
    except (ImportError, OSError, RuntimeError, ValueError):
        logging.getLogger('vibesec.worker').exception('Terjemahan lokal gagal')
        detail['translation'] = {'status': 'failed', 'language': 'id'}


def backfill():
    with connect() as db:
        rows = query(db, 'SELECT id,title,detail FROM findings').fetchall()
    for row in rows:
        row['detail'] = json.loads(row['detail'])
        if row['detail'].get('translation', {}).get('status') == 'completed':
            continue
        translate_finding(row)
        with connect() as db:
            query(db, 'UPDATE findings SET detail=%s WHERE id=%s', (json.dumps(row['detail']), row['id']))
    print('Terjemahan temuan tersimpan.', flush=True)


if __name__ == '__main__':
    backfill()
