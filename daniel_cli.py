"""Offline Termux narration CLI. No model imports until preflight succeeds."""
import argparse
import contextlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import wave

VERSION = '0.1.0'
ROOT = Path(os.environ.get('DANIEL_ROOT', Path.home() / 'daniel_voice')).expanduser().resolve()


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('text', nargs='?')
    p.add_argument('destination', nargs='?')
    p.add_argument('--text', dest='explicit_text')
    p.add_argument('--text-file', type=Path)
    p.add_argument('--batch', type=Path, help='UTF-8 file: one utterance per nonempty line, joined into one WAV')
    p.add_argument('--input-wav', type=Path, help='convert an existing WAV, bypassing Piper')
    p.add_argument('--output', type=Path)
    p.add_argument('--voice', default='en_GB-alan-medium')
    p.add_argument('--checkpoint', type=Path, default=ROOT/'DanielUK_200e.pth')
    p.add_argument('--hubert-dir', type=Path, default=ROOT/'rvc-source/assets/hubert_base')
    p.add_argument('--rmvpe-dir', type=Path, default=ROOT/'rvc-source/assets/rmvpe')
    p.add_argument('--voice-dir', type=Path, default=Path.home()/'tts/models')
    p.add_argument('--threads', type=int, choices=range(1, 5), default=2)
    p.add_argument('--timeout', type=int, default=0, help='whole invocation deadline in seconds; 0 disables')
    p.add_argument('--overwrite', action='store_true')
    v = p.add_mutually_exclusive_group()
    v.add_argument('--quiet', action='store_true')
    v.add_argument('--verbose', action='store_true')
    p.add_argument('--json', action='store_true')
    p.add_argument('--version', action='version', version=VERSION)
    return p


def require_file(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f'Missing or empty file: {path}')


def validate_wav(path, output=False):
    with wave.open(str(path), 'rb') as w:
        if w.getnframes() == 0:
            raise ValueError(f'Empty WAV: {path}')
        if output and (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, 40000):
            raise ValueError(f'Expected mono PCM16 40000 Hz WAV: {path}')
        frames = w.getnframes()
        remaining = frames
        while remaining:
            count = min(65536, remaining)
            if len(w.readframes(count)) != count*w.getnchannels()*w.getsampwidth():
                raise ValueError(f'Truncated WAV: {path}')
            remaining -= count
        return frames/w.getframerate()


def preflight(a, needs_piper=True):
    for f in [a.checkpoint, a.hubert_dir/'config.json', a.hubert_dir/'preprocessor_config.json', a.hubert_dir/'pytorch_model.bin', a.rmvpe_dir/'rmvpe.pt']:
        require_file(f)
    if not needs_piper:
        return 22050
    for cmd in ['piper', 'ffmpeg']:
        if not shutil.which(cmd):
            raise ValueError(f'{cmd} is missing from PATH; restore the existing Termux installation')
    if Path(a.voice).name != a.voice or a.voice in ('.', '..'):
        raise ValueError('--voice must be a model name, without directories')
    for suffix in ['.onnx', '.onnx.json']:
        require_file(a.voice_dir/(a.voice+suffix))
    rate = json.loads((a.voice_dir/(a.voice+'.onnx.json')).read_text())['audio']['sample_rate']
    if rate != 22050:
        raise ValueError('This Termux Piper build is verified only for 22050 Hz voices')
    espeak = Path(os.environ.get('ESPEAK_DATA_PATH', str(Path(os.environ.get('PREFIX', sys.prefix))/'share/espeak-ng-data')))
    if not espeak.is_dir():
        raise ValueError(f'Missing eSpeak data: {espeak}')
    os.environ['ESPEAK_DATA_PATH'] = str(espeak)
    os.environ['PIPER_VOICE_PATH'] = str(a.voice_dir.resolve())
    return rate


def chunks(text, limit=350):
    # shortcut: split at whitespace, add sentence-aware pauses after listening tests.
    words = text.split()
    result, part = [], ''
    for word in words:
        if len(word) > limit:
            raise ValueError(f'A word exceeds the {limit}-character chunk limit')
        if part and len(part)+1+len(word) > limit:
            result.append(part)
            part = ''
        part = (part+' '+word).strip()
    if part:
        result.append(part)
    if not result:
        raise ValueError('Text must contain non-whitespace characters')
    return result


def run_command(command, verbose=False):
    with tempfile.TemporaryFile(mode='w+b') as log:
        with subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True) as proc:
            try:
                code = proc.wait()
            except BaseException:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                raise
        log.seek(0, 2)
        size = log.tell()
        log.seek(max(0, size-8192))
        detail = log.read().decode('utf-8', errors='replace')
        if verbose:
            print(detail, file=sys.stderr)
        if code:
            raise RuntimeError(f'{Path(command[0]).name} failed ({code}): {detail.strip()}')


@contextlib.contextmanager
def atomic_output(path, overwrite):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name('.'+path.name+'.lock')
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError(f'Output busy (or stale lock after forced termination): {lock}')
    try:
        if path.exists() and not overwrite:
            raise ValueError(f'Output exists: {path}; use --overwrite')
        with tempfile.TemporaryDirectory(prefix='.daniel-', dir=path.parent) as tmp:
            staging = Path(tmp)/'output.wav'
            yield staging
            validate_wav(staging, output=True)
            if path.exists() and not overwrite:
                raise ValueError(f'Output appeared during conversion: {path}')
            os.replace(staging, path)
    finally:
        lock.rmdir()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    command = argv.pop(0) if argv and argv[0] in ('doctor', 'benchmark') else 'speak'
    a = parser().parse_args(argv)
    started = time.perf_counter()
    def interrupted(signum, frame):
        raise KeyboardInterrupt('deadline exceeded' if signum == signal.SIGALRM else 'interrupted')
    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGALRM)}
    try:
        if a.timeout < 0:
            raise ValueError('--timeout cannot be negative')
        if a.timeout:
            signal.alarm(a.timeout)
        os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
        os.environ.setdefault('OMP_NUM_THREADS', '1')
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        sys.path.insert(0, str(ROOT/'rvc-source'))
        if command == 'doctor':
            preflight(a)
            with contextlib.redirect_stdout(sys.stderr):
                import convert_daniel
                import infer.rmvpe
            result = {'success': True, 'python': sys.version.split()[0], 'packages': {n: importlib.metadata.version(n) for n in ('torch', 'numpy', 'scipy', 'soundfile', 'transformers')}, 'offline': True, 'models_loaded': False}
        else:
            if a.output and a.destination:
                raise ValueError('Choose positional output or --output')
            sources = [a.text, a.explicit_text, a.text_file, a.batch, a.input_wav]
            if command == 'benchmark' and not any(x is not None for x in sources):
                a.input_wav = ROOT/'base.wav'
            elif sum(x is not None for x in sources) != 1:
                raise ValueError('Provide exactly one text, --text, --text-file, --batch or --input-wav')
            if a.input_wav:
                validate_wav(a.input_wav)
                import numpy as np
                import soundfile as sf
                with sf.SoundFile(a.input_wav) as audio:
                    if len(audio)/audio.samplerate < .1:
                        raise ValueError('Input WAV must be at least 0.1 seconds')
                    for block in audio.blocks(blocksize=65536, dtype='float32'):
                        if not np.isfinite(block).all():
                            raise ValueError('Input WAV contains NaN/Inf')
                jobs = [None] * (2 if command == 'benchmark' else 1)
            else:
                source = a.text_file or a.batch
                text = source.read_text(encoding='utf-8-sig') if source else (a.explicit_text if a.explicit_text is not None else a.text)
                jobs = [c for line in text.splitlines() if line.strip() for c in chunks(line)] if a.batch else chunks(text)
                if not jobs:
                    raise ValueError('Empty batch')
            preflight(a, not a.input_wav)
            output = (a.output or Path(a.destination or ('benchmark.wav' if command == 'benchmark' else 'daniel_output.wav'))).expanduser().absolute()
            if output.suffix.lower() != ".wav":
                raise ValueError("Output must have a .wav extension")
            for source in (a.input_wav, a.text_file, a.batch):
                if source and output.resolve() == source.resolve():
                    raise ValueError('Input and output paths must differ')
            records = []
            with atomic_output(output, a.overwrite) as staging:
                with contextlib.ExitStack() as stack:
                    log = stack.enter_context(open(os.devnull, "w")) if a.quiet else sys.stderr
                    stack.enter_context(contextlib.redirect_stdout(log))
                    if a.quiet:
                        stack.enter_context(contextlib.redirect_stderr(log))
                    from convert_daniel import DanielEngine
                    load_start = time.perf_counter()
                    engine = DanielEngine(a.checkpoint, a.hubert_dir, a.rmvpe_dir, a.threads)
                    load_seconds = time.perf_counter()-load_start
                    with wave.open(str(staging), 'wb') as combined:
                        combined.setparams((1, 2, 40000, 0, 'NONE', 'not compressed'))
                        for i, text in enumerate(jobs):
                            job_start = time.perf_counter()
                            base = a.input_wav
                            if text is not None:
                                raw = staging.parent/'base.raw'
                                base = staging.parent/'base.wav'
                                run_command(['piper', '-m', a.voice, '-f', str(raw), '--', text], a.verbose)
                                require_file(raw)
                                if raw.stat().st_size % 4 or raw.read_bytes()[:4] == b'RIFF':
                                    raise ValueError('Piper did not produce expected raw float32 audio')
                                run_command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'f32le', '-ar', '22050', '-ac', '1', '-i', str(raw), '-af', 'volume=0.15,alimiter=limit=0.5', '-c:a', 'pcm_s16le', str(base)], a.verbose)
                            piece = staging.parent/'piece.wav'
                            record = engine.convert(base, piece)
                            validate_wav(piece, output=True)
                            with wave.open(str(piece), 'rb') as w:
                                combined.writeframes(w.readframes(w.getnframes()))
                            record.update(job=i+1, warm=i>0, job_seconds=time.perf_counter()-job_start)
                            record['real_time_factor'] = record['job_seconds']/record['input_seconds']
                            records.append(record)
            result = {'success': True, 'output': str(output), 'jobs': records, 'load_seconds': load_seconds, 'total_seconds': time.perf_counter()-started, 'threads': a.threads, 'device': 'cpu', 'peak_rss_mb': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
            if command == 'benchmark':
                result['historical_baseline_seconds'] = 32.93
                result['cold_seconds'] = load_seconds+records[0]['job_seconds']
        if a.json or command in ('doctor', 'benchmark'):
            print(json.dumps(result))
        elif not a.quiet:
            print(f"Saved: {result['output']}")
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        if a.verbose:
            import traceback
            traceback.print_exc()
        if a.json:
            print(json.dumps({'success': False, 'error': str(exc) or 'interrupted'}))
        else:
            print(f'Error: {exc or "interrupted"}', file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 1
    finally:
        signal.alarm(0)
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == '__main__':
    raise SystemExit(main())
