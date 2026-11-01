"""Exercise real process signals with a lightweight fake inference backend."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


class Cancellation(unittest.TestCase):
    def test_subprocess_cancel(self):
        import daniel_cli as cli
        def cancel(signum, frame):
            raise KeyboardInterrupt()
        old = signal.signal(signal.SIGALRM, cancel)
        try:
            signal.setitimer(signal.ITIMER_REAL, .2)
            started = time.monotonic()
            with self.assertRaises(KeyboardInterrupt):
                cli.run_command([sys.executable, '-c', 'import time; time.sleep(30)'])
            self.assertLess(time.monotonic()-started, 5)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)

    def test_sigterm_cleans_atomic_output(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            output = p/'out.wav'
            output.write_bytes(b'original')
            script = '''
import sys, time
from pathlib import Path
import daniel_cli as cli
class Engine:
    def __init__(self, *args):
        Path(sys.argv[2]).write_text('ready')
        time.sleep(30)
cli.preflight = lambda *args: None
sys.modules['convert_daniel'] = type('Module', (), {'DanielEngine': Engine})
raise SystemExit(cli.main(['hello', sys.argv[1], '--overwrite', '--json']))
'''
            proc = subprocess.Popen([sys.executable, '-c', script, str(output), str(p/'ready')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic()+10
                while not (p/'ready').exists() and proc.poll() is None and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue((p/'ready').exists())
                proc.send_signal(signal.SIGTERM)
                stdout, stderr = proc.communicate(timeout=10)
                self.assertEqual(proc.returncode, 130, (stdout, stderr))
                self.assertEqual(output.read_bytes(), b'original')
                self.assertEqual(sorted(x.name for x in p.iterdir()), ['out.wav', 'ready'])
            finally:
                if proc.poll() is None: proc.kill()
                proc.communicate()

if __name__ == '__main__': unittest.main()
