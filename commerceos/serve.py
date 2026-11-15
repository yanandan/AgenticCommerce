"""Run the API and Streamlit together on a single-container web host."""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def main() -> int:
    port = int(os.environ.get('PORT', '10000'))
    api_port = int(os.environ.get('COMMERCEOS_API_PORT', '8765'))
    if not 1 <= port <= 65535 or not 1 <= api_port <= 65535 or port == api_port:
        raise ValueError('Public and internal API ports must be distinct and between 1 and 65535')
    api_url = f'http://127.0.0.1:{api_port}'
    processes = []
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        api = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'commerceos.api.main:app',
                                '--host', '127.0.0.1', '--port', str(api_port)])
        processes.append(api)
        deadline = time.monotonic() + 30
        while not stopping:
            if api.poll() is not None:
                return api.returncode or 1
            try:
                with urlopen(f'{api_url}/products/search?q=running', timeout=1) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError):
                pass
            if time.monotonic() > deadline:
                raise RuntimeError('API startup exceeded 30 seconds')
            time.sleep(0.2)
        if stopping:
            return 0
        env = dict(os.environ, COMMERCEOS_API_URL=api_url)
        ui = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run',
            str(Path(__file__).parent / 'ui' / 'app.py'),
            '--server.address', '0.0.0.0', '--server.port', str(port),
            '--server.headless', 'true', '--browser.gatherUsageStats', 'false',
        ], env=env)
        processes.append(ui)
        while not stopping:
            for process in processes:
                if process.poll() is not None:
                    return process.returncode or 1
            time.sleep(0.2)
        return 0
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    sys.exit(main())
