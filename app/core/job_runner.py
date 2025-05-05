import asyncio
import os
import signal
from typing import List, Optional


class JobRunner:
    def __init__(self, command: List[str], job=None, cwd=None, env=None):
        self.command = command
        self.process: Optional[asyncio.subprocess.Process] = None
        self.job = job
        self.cwd = cwd
        self.env = env or os.environ.copy()
        self.cancelled = False

    async def start(self):
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            cwd=self.cwd,
            env=self.env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        if self.job:
            self.job.status = f"Running: {' '.join(self.command)}"
            self.job.runner = self

        await self._stream_output()

        if self.job and not self.cancelled:
            self.job.status = f"Finished: {' '.join(self.command)}"

    async def _stream_output(self):
        assert self.process and self.process.stdout
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace").strip()
            if self.job:
                self.job.stdout_log.append(decoded)
            print(decoded)  # Optional: system log

        await self.process.wait()

    def cancel(self):
        if self.process and self.process.returncode is None:
            try:
                self.process.send_signal(signal.SIGTERM)
                self.cancelled = True
                if self.job:
                    self.job.status = "Cancelled by user"
            except Exception as e:
                if self.job:
                    self.job.stdout_log.append(f"Cancel error: {e}")

    def is_running(self) -> bool:
        return self.process is not None and self.process.returncode is None