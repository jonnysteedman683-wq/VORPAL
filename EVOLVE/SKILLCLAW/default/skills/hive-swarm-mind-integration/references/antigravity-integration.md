# Antigravity integration (full detail)

Load this file when invoking Antigravity tasks through OMNIBUS, or
when `agy` is not found on PATH on this Windows host.

## Backend route

OMNIBUS can invoke Antigravity tasks through a backend route, which is useful for the daily 5AM upgrade and hourly optimization jobs already scheduled in this setup.

Add in `server.cjs`:

```js
app.post('/api/antigravity/run', async (req, res) => {
  const { prompt, model, timeoutMs, workdir } = req.body || {};
  const task = typeof prompt === 'string' && prompt.trim() ? prompt.trim() : 'Run OMNIBUS maintenance and suggest improvements.';
  const targetDir = workdir || __dirname;
  const printTimeout = Math.min(Math.max(timeoutMs || 5 * 60 * 1000, 1000), 20 * 60 * 1000);
  const command = `"${process.env.AG_BIN || 'agy'}" -p ${JSON.stringify(task)} ${model ? `--model ${JSON.stringify(model)}` : ''} --print-timeout ${printTimeout}`;

  try {
    const result = await new Promise((resolve, reject) => {
      const proc = require('child_process').exec(command, { cwd: targetDir, maxBuffer: 1024 * 1024 * 5 }, (error, stdout, stderr) => {
        resolve({ ok: !error, stdout: stdout || '', stderr: stderr || '', code: error ? (error.code || 1) : 0 });
      });
      if (proc.pid && typeof proc.kill === 'function') {
        setTimeout(() => proc.kill('SIGTERM'), printTimeout + 1000).unref?.();
      }
    });

    telemetry.intents.push({ id: `ag-${Date.now()}`, intent: 'antigravity-run', provider: 'system', confidence: 1, latencyMs: 0, status: result.ok ? 'completed' : 'failed', timestamp: Date.now(), raw: { prompt: task, model, workdir: targetDir, timeoutMs: printTimeout } });

    res.json({ success: result.ok, command, workdir: targetDir, timeoutMs: printTimeout, stdout: result.stdout, stderr: result.stderr, code: result.code });
  } catch (err) {
    res.status(500).json({ success: false, command, workdir: targetDir, timeoutMs: printTimeout, error: err.message });
  }
});
```

Pitfall: this route shells out to `agy`. If Antigravity is installed only as the Electron app on Windows, there may be no `agy` on PATH. In that case either:
- add `AG_BIN` env var pointing to a real CLI wrapper, or
- create a wrapper script at a known path and point `AG_BIN` to it.

## Windows Antigravity paths

On this Windows host, Antigravity installs as:
- Electron app: `C:\Users\jonny\AppData\Local\Programs\antigravity\Antigravity.exe`
- Agent API wrapper: `C:\Users\jonny\.gemini\antigravity\bin\agentapi.bat`
- Language server: `C:\Users\jonny\AppData\Local\Programs\antigravity\resources\bin\language_server.exe`

There is no standalone `agy.exe` on PATH by default. If `command -v agy` fails, do not assume Antigravity is absent; check the installed app paths above and decide whether to create a wrapper or use the agent API path.
