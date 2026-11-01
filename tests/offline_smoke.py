"""Real-model test: deny Python network connections and synthesize two jobs."""
from pathlib import Path
import socket
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daniel_cli

def blocked(*args, **kwargs):
    raise AssertionError('Network access attempted during offline inference')
socket.socket.connect = blocked
socket.socket.connect_ex = blocked
socket.create_connection = blocked
raise SystemExit(daniel_cli.main(sys.argv[1:]))
