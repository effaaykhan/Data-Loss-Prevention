# CyberSentinel DLP Agent

A lightweight Data Loss Prevention (DLP) agent for Windows that monitors and protects sensitive data on endpoints. Built with C++ for high performance and minimal resource usage.

## 🚀 Features

- **Real-time Monitoring**: Continuous monitoring of system activities and data access
- **Policy-based Protection**: Configurable policies for data classification and protection
- **Windows Service**: Runs as a background Windows service for persistent protection
- **Heartbeat & Sync**: Regular communication with central server for policy updates
- **Lightweight**: Minimal CPU and memory footprint
- **Easy Management**: Simple PowerShell scripts for installation, updates, and removal

## 📋 Prerequisites

### For Running the Agent
- Windows 10/11 or Windows Server 2016+
- Administrator privileges
- Network connectivity to DLP server

### For Building from Source
- MSYS2 with MinGW-w64 (64-bit)
- G++ compiler with C++23 support
- Required libraries (included in MSYS2):
  - winhttp
  - wbemuuid
  - ole32
  - oleaut32
  - user32
  - ws2_32
  - setupapi
  - advapi32

## 🔧 Installation

### Method 1: Using PowerShell Script (Recommended)

1. **Download the installation script**:
   ```powershell
   # Or clone this repository
   git clone https://github.com/ansh-gadhia/DLP_Agent_VGIPL_CPP.git
   cd DLP_Agent_VGIPL_CPP
   ```

2. **Run the installation script as Administrator**:
   ```powershell
   # Right-click PowerShell and select "Run as Administrator"
   .\agent_install.ps1
   ```

3. **Follow the prompts** to configure:
   - Server URL (e.g., `http://192.168.1.100:55000/api/v1`)
   - Agent Name (defaults to computer name)
   - Agent ID (auto-generated UUID)
   - Heartbeat Interval (default: 30 seconds)
   - Policy Sync Interval (default: 60 seconds)

The script will:
- Download NSSM (Non-Sucking Service Manager)
- Download the latest agent executable from releases
- Create configuration file (`agent_config.json`)
- Install and start the Windows service

### Method 2: Manual Installation

1. **Download the executable** from [Releases](https://github.com/ansh-gadhia/DLP_Agent_VGIPL_CPP/releases)

2. **Create `agent_config.json`** in the same directory:
   ```json
   {
     "server_url": "http://your-server:55000/api/v1",
     "agent_id": "unique-agent-id",
     "agent_name": "HOSTNAME",
     "heartbeat_interval": 30,
     "policy_sync_interval": 60
   }
   ```

3. **Run the agent**:
   ```powershell
   .\cybersentinel_agent.exe
   ```

## 🏗️ Building from Source

### 1. Install MSYS2

Download and install MSYS2 from [msys2.org](https://www.msys2.org/)

### 2. Install Required Packages

```bash
# Open MSYS2 MinGW 64-bit terminal
pacman -S mingw-w64-x86_64-gcc
```

### 3. Compile the Agent

```bash
g++ -std=c++23 -O2 agent.cpp -o cybersentinel_agent.exe \
    -lwinhttp -lwbemuuid -lole32 -loleaut32 -luser32 \
    -lws2_32 -lsetupapi -ladvapi32 -static
```

### Compiler Flags Explained:
- `-std=c++23`: Use C++23 standard
- `-O2`: Optimization level 2
- `-static`: Static linking for standalone executable
- `-l*`: Link required Windows libraries

## 🔄 Updating the Agent

Use the update script to update the agent executable or configuration:

```powershell
# Run as Administrator
.\Upgrade-CyberSentinelAgent.ps1
```

**Update Options:**
1. Update Agent Executable (downloads from releases)
2. Update Configuration (modify agent_config.json)
3. Update Both
4. View Current Configuration
5. Exit

## 🗑️ Uninstallation

Run the uninstall script as Administrator:

```powershell
.\Uninstall-CyberSentinelAgent.ps1
```

**Uninstall Options:**
1. Delete all files and directory (recommended)
2. Keep configuration file and logs
3. Keep everything (only remove service)

## 📁 File Structure

```
C:\Program Files\CyberSentinel\
├── cybersentinel_agent.exe    # Main agent executable
├── agent_config.json          # Configuration file
├── nssm.exe                   # Service manager
├── service.log                # Agent logs
└── service_error.log          # Error logs
```

## ⚙️ Configuration

Edit `agent_config.json` to configure the agent:

```json
{
  "server_url": "http://server:55000/api/v1",
  "agent_id": "unique-identifier",
  "agent_name": "AGENT-NAME",
  "heartbeat_interval": 30,
  "policy_sync_interval": 60
}
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `server_url` | DLP server API endpoint | Required |
| `agent_id` | Unique agent identifier (UUID) | Auto-generated |
| `agent_name` | Display name for the agent | Computer name |
| `heartbeat_interval` | Seconds between heartbeat signals | 30 |
| `policy_sync_interval` | Seconds between policy synchronization | 60 |


## 🔒 Security Considerations

- The agent requires **Administrator privileges** to monitor system activities
- All communication with the server should use **HTTPS** in production
- Protect the `agent_config.json` file (contains agent credentials)
- Review logs regularly for suspicious activity
- Keep the agent updated to the latest version

## 🐛 Troubleshooting

### Service Won't Start

1. Check if the executable exists:
   ```powershell
   Test-Path "C:\Program Files\CyberSentinel\cybersentinel_agent.exe"
   ```

2. Verify configuration file:
   ```powershell
   Get-Content "C:\Program Files\CyberSentinel\agent_config.json"
   ```


### Cannot Connect to Server

- Verify server URL in `agent_config.json`
- Check network connectivity: `Test-NetConnection server-address -Port 55000`
- Ensure firewall allows outbound connections
- Verify server is running and accessible

### High CPU/Memory Usage

- Check `heartbeat_interval` and `policy_sync_interval` (increase if too frequent)
- Review logs for excessive errors or retries
- Ensure server is responding properly


## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
