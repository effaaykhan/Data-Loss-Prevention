# Windows Agent Installer (PowerShell)

`install_windows_agent.ps1` automates fetching the Windows agent from git, creating a venv, installing dependencies, templating `agent_config.json`, and registering a SYSTEM/AtStartup Scheduled Task with restart-on-failure.

## Arguments
- `-ManagerUrl` (string): Manager API base. Default `http://localhost:55000/api/v1`.
- `-InstallDir` (string): Agent install path. Default `%ProgramFiles%\CyberSentinel\agent`.
- `-ConfigDir` (string): Config/log path. Default `%ProgramData%\CyberSentinel`.
- `-VenvDir` (string): Virtualenv path. Default `<InstallDir>\venv`.
- `-RepoUrl` (string): Git repo URL. Default `https://github.com/YOUR_ORG/Data-Loss-Prevention.git`.
- `-Branch` (string): Branch to checkout. Default `main`.
- `-Ref` (string): Optional commit/tag override after branch.
- `-ServiceName` (string): Scheduled Task name. Default `CyberSentinelAgent`.
- `-LogPath` (string): Optional log path override. Default `<ConfigDir>\cybersentinel_agent.log`.
- `-NoStart` (switch): Register task but do not start it.
- `-Force` (switch): Re-clone and overwrite existing config/venv.
- Use parentheses around `-and` expressions if you run into PS parsing quirks on some hosts.
- If `CYBERSENTINEL_SERVER_URL` or `MANAGER_URL` is set in the environment and you omit `-ManagerUrl`, the installer uses that value.

## Usage Examples
- Fresh install (defaults):  
  `powershell -ExecutionPolicy Bypass -File .\install_windows_agent.ps1 -ManagerUrl "http://localhost:55000/api/v1"`

- Install to a custom path and specific branch:  
  `powershell -ExecutionPolicy Bypass -File .\install_windows_agent.ps1 -ManagerUrl "http://mgr:55000/api/v1" -InstallDir "C:\CyberSentinel\agent" -Branch main`

- Pin to a commit and skip immediate start:  
  `powershell -ExecutionPolicy Bypass -File .\install_windows_agent.ps1 -ManagerUrl "http://mgr:55000/api/v1" -Ref abc123 -NoStart`

- Re-provision with overwrite:  
  `powershell -ExecutionPolicy Bypass -File .\install_windows_agent.ps1 -ManagerUrl "http://mgr:55000/api/v1" -Force`

## Notes
- Requires admin, git, and Python 3.10+ on PATH.
- The Scheduled Task runs as SYSTEM at startup with restart-on-failure.
- Config is written to `<ConfigDir>\agent_config.json`; existing config is preserved unless `-Force` is used.
- Logs by default are written next to the agent if not configured: `C:\Program Files\CyberSentinel\agent\cybersentinel_agent.log`. If you set `-LogPath`, they can go under `<ConfigDir>`.
- Remote host example:  
  `powershell -ExecutionPolicy Bypass -File .\install_windows_agent.ps1 -ManagerUrl "http://<HOST>:55000/api/v1"`

## Useful Commands (Windows)
- Check task status: `Get-ScheduledTask -TaskName CyberSentinelAgent`
- Task info: `Get-ScheduledTaskInfo -TaskName CyberSentinelAgent`
- Tail logs (default path): `Get-Content 'C:\Program Files\CyberSentinel\agent\cybersentinel_agent.log' -Tail 50`
- Start/Stop task: `Start-ScheduledTask -TaskName CyberSentinelAgent` / `Stop-ScheduledTask -TaskName CyberSentinelAgent`

# Linux Agent Installer (bash)

`install_linux_agent.sh` automates fetching the Linux agent from git, creating a venv, installing dependencies, templating `agent_config.json`, and registering a systemd service with boot autostart.

## Arguments
- `--manager-url` (default `http://localhost:55000/api/v1`)
- `--install-dir` (default `/opt/cybersentinel/agent`)
- `--config-dir` (default `/etc/cybersentinel`)
- `--venv-dir` (default `<install-dir>/.venv`)
- `--repo-url` (default `https://github.com/YOUR_ORG/Data-Loss-Prevention.git`)
- `--branch` (default `main`)
- `--ref` (optional commit/tag)
- `--service-name` (default `cybersentinel-agent`)
- `--log-path` (default `<install-dir>/cybersentinel_agent.log`)
- `--no-start` (skip starting service)
- `--force` (re-clone and overwrite config/venv)
- If `CYBERSENTINEL_SERVER_URL` is set and you omit `--manager-url`, the installer uses that value.

### Remote host example
`sudo CYBERSENTINEL_SERVER_URL=http://<HOST>:55000/api/v1 bash scripts/install_linux_agent.sh --force`

## Usage Examples
- Fresh install:  
  `sudo bash scripts/install_linux_agent.sh --manager-url http://localhost:55000/api/v1`
- Pin to commit and skip start:  
  `sudo bash scripts/install_linux_agent.sh --manager-url http://localhost:55000/api/v1 --ref abc123 --no-start`
- Re-provision with overwrite:  
  `sudo bash scripts/install_linux_agent.sh --manager-url http://localhost:55000/api/v1 --force`

## Notes
- Requires root/sudo, git, python3.10+, systemd.
- Service autostarts on boot (`WantedBy=multi-user.target`), `Restart=on-failure`, env `CYBERSENTINEL_SERVER_URL` set from `--manager-url`.
- Config is written to `<config-dir>/agent_config.json`; existing config is preserved unless `--force` is used.
- Logs: the agent writes to `~/cybersentinel_agent.log` (for root, `/root/cybersentinel_agent.log`). Check that file or use `journalctl -u <service-name>`.

## Useful Commands (Linux)
- `systemctl status cybersentinel-agent`
- `journalctl -u cybersentinel-agent -n 50`
- `sudo tail -n 50 /root/cybersentinel_agent.log`
- `sudo systemctl start|stop|restart cybersentinel-agent`
