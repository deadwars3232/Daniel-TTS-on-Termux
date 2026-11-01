import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
import daniel_cli as cli


def wav(path, n=400):
    with wave.open(str(path), 'wb') as w:
        w.setparams((1, 2, 40000, 0, 'NONE', 'not compressed'))
        w.writeframes(b'\x01\x00'*n)


class CLI(unittest.TestCase):
    def test_arguments(self):
        a = cli.parser().parse_args(['Hello', 'some path.wav'])
        self.assertEqual((a.text, a.destination), ('Hello', 'some path.wav'))

    def test_chunks(self):
        text = 'Hello, “Daniel”!\n' * 200
        parts = cli.chunks(text)
        self.assertEqual(' '.join(parts).split(), text.split())
        self.assertTrue(all(len(p) <= 350 for p in parts))
        for text in ('  ', 'x'*351):
            with self.assertRaises(ValueError): cli.chunks(text)

    def test_atomic_failure_and_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'out.wav'
            p.write_bytes(b'original')
            with self.assertRaises(ValueError):
                with cli.atomic_output(p, False): pass
            with self.assertRaises(RuntimeError):
                with cli.atomic_output(p, True) as temp:
                    wav(temp)
                    raise RuntimeError('failed conversion')
            self.assertEqual(p.read_bytes(), b'original')
            with self.assertRaises((wave.Error, EOFError)):
                with cli.atomic_output(p, True) as temp: temp.write_bytes(b'bad')
            with cli.atomic_output(p, True) as temp: wav(temp)
            self.assertEqual(cli.validate_wav(p, True), .01)
            self.assertEqual(list(Path(d).iterdir()), [p])

    def test_cancel_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(KeyboardInterrupt):
                with cli.atomic_output(Path(d)/'out.wav', False) as temp:
                    wav(temp)
                    raise KeyboardInterrupt()
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_failed_subprocess(self):
        with self.assertRaisesRegex(RuntimeError, 'failed'):
            cli.run_command([sys.executable, '-c', 'raise SystemExit(7)'])

    def test_empty_text_without_model_import(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            status = cli.main(['--text', ' ', '--json'])
        self.assertEqual(status, 1)
        self.assertFalse(json.loads(out.getvalue())['success'])

    def test_missing_model(self):
        a = cli.parser().parse_args(['--checkpoint', '/missing/daniel.pth'])
        with self.assertRaisesRegex(ValueError, 'Missing or empty'):
            cli.preflight(a)

    def test_invalid_output_parent(self):
        with tempfile.TemporaryDirectory() as d:
            parent = Path(d)/'file'
            parent.write_text('keep')
            with self.assertRaises(FileExistsError):
                with cli.atomic_output(parent/'out.wav', False): pass
            self.assertEqual(parent.read_text(), 'keep')

    def test_truncated_wav(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'bad.wav'
            wav(p)
            p.write_bytes(p.read_bytes()[:-2])
            with self.assertRaisesRegex(ValueError, 'Truncated'):
                cli.validate_wav(p)

    def test_batch_reuses_engine(self):
        instances = []
        class Engine:
            def __init__(self, *args): instances.append(self)
            def convert(self, source, target):
                wav(target)
                return {'input_seconds': .01}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/'text.txt').write_text('One.\n\nTwo.', encoding='utf-8')
            def command(args, verbose):
                if args[0] == 'piper': Path(args[args.index('-f')+1]).write_bytes(b'\0'*16)
            with patch.object(cli, 'preflight'), patch.object(cli, 'run_command', command), patch.dict(sys.modules, {'convert_daniel': type('Module', (), {'DanielEngine': Engine})}):
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    status = cli.main(['--batch', str(p/'text.txt'), '--output', str(p/'out.wav'), '--json'])
            self.assertEqual(status, 0)
            self.assertEqual(len(instances), 1)
            self.assertEqual(len(json.loads(out.getvalue())['jobs']), 2)
            self.assertEqual(cli.validate_wav(p/'out.wav', True), .02)

if __name__ == '__main__': unittest.main()
