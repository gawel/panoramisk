import subprocess

import pytest

from panoramisk import utils


class Asterisk:
    def __init__(self):
        self.cwd = 'tests/docker'
        self.proc = None

    def start(self):
        self.stop()
        self.proc = subprocess.Popen(
            ['docker-compose', 'up'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.cwd
        )
        for line in iter(self.proc.stdout.readline, b''):
            if b'Asterisk Ready.' in line:
                break

    def logs(self, tail=20):
        proc = subprocess.Popen(
            ['docker-compose', 'logs', '--tail=%s' % tail],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.cwd,
            encoding='utf8',
        )
        stdout, _ = proc.communicate()
        print(stdout)
        return stdout

    def stop(self):
        if self.proc is not None:
            self.proc.kill()
            subprocess.check_call(
                ['docker-compose', 'down', '-v'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.cwd,
            )


@pytest.fixture
def asterisk(request):
    utils.EOL = '\r\n'
    server = Asterisk()
    yield server
    server.stop()
