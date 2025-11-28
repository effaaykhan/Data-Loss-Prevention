import os
import json
import subprocess
import shutil
import requests
import sys
import time

# ---------------- Utility Functions ---------------- #

def run(cmd, strict=True):
    """Run a command. If strict=False, ignore errors."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if strict and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def download(url, dest):
    """Download a file from GitHub."""
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Failed to download {url} ({r.status_code})")
    with open(dest, "wb") as f:
        f.write(r.content)


def kill_agent_processes():
    """Kill only python processes running agent.py (not the installer)."""
    print("Checking for running agent processes...")

    # Use WMIC to list python.exe processes with their command lines
    plist = subprocess.run(
        'wmic process where "Name=\'python.exe\'" get ProcessId,CommandLine /FORMAT:CSV',
        shell=True, capture_output=True, text=True
    ).stdout

    for line in plist.splitlines():
        if "agent.py" in line.lower():
            try:
                pid = line.strip().split(",")[-1]
                if pid.isdigit():
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                    print(f"Killed agent process PID {pid}")
            except Exception:
                pass


# ---------------- Main Installer ---------------- #

def main():

    print("\n=== CyberSentinel DLP – Windows Agent Installer ===\n")

    # ---------------- User Input ---------------- #
    server_ip = input("Enter Server IP: ").strip()
    agent_name = input("Enter Agent Name: ").strip()
    agent_id = input("Enter Agent ID: ").strip()

    if not (server_ip and agent_name and agent_id):
        raise ValueError("Server IP, Agent Name, and Agent ID are required.")

    # ---------------- Paths ---------------- #
    install_dir = r"C:\CyberSentinel\WindowsAgent"
    nssm = r"C:\Users\Firdo\Downloads\nssm-2.24\nssm-2.24\win64\nssm.exe"
    service_name = "CyberSentinel-DLP Agent"

    # ---------------- Stop old service ---------------- #
    print("\nStopping existing service (if any)...")
    run(f'"{nssm}" stop "{service_name}"', strict=False)
    run(f'"{nssm}" remove "{service_name}" confirm', strict=False)

    # ---------------- Kill old agent processes ---------------- #
    kill_agent_processes()
    time.sleep(1)

    # ---------------- Clean install directory ---------------- #
    print("\nCleaning installation folder...")

    if os.path.exists(install_dir):
        try:
            shutil.rmtree(install_dir)
        except Exception:
            time.sleep(1)
            shutil.rmtree(install_dir)

    os.makedirs(install_dir, exist_ok=True)

    # ---------------- Download agent files from GitHub ---------------- #
    print("\nDownloading agent files from GitHub...\n")

    base = "https://raw.githubusercontent.com/effaaykhan/Data-Loss-Prevention/main/agents/endpoint/windows"

    github_files = {
        "agent.py": f"{base}/agent.py",
        "agent_config.json": f"{base}/agent_config.json",
        "requirements.txt": f"{base}/requirements.txt",
    }

    for filename, url in github_files.items():
        dest = os.path.join(install_dir, filename)
        download(url, dest)
        print(f"Downloaded: {filename}")

    # ---------------- Update configuration ---------------- #
    print("\nUpdating agent_config.json...")

    config_path = os.path.join(install_dir, "agent_config.json")
    with open(config_path, "r") as f:
        cfg = json.load(f)

    cfg["server_url"] = f"http://{server_ip}:55000/api/v1"
    cfg["agent_name"] = agent_name
    cfg["agent_id"] = agent_id

    with open(config_path, "w") as f:
        json.dump(cfg, f, indent=2)

    # ---------------- Install dependencies ---------------- #
    print("\nInstalling dependencies...")

    requirements_path = os.path.join(install_dir, "requirements.txt")
    run(f'pip install -r "{requirements_path}"')

    # ---------------- Install NSSM service ---------------- #
    print("\nInstalling NSSM service...")

    python_path = sys.executable
    script_path = os.path.join(install_dir, "agent.py")

    # Create service
    run(f'"{nssm}" install "{service_name}" "{python_path}" "{script_path}"')

    # Set working directory
    run(f'"{nssm}" set "{service_name}" AppDirectory "{install_dir}"')

    # Auto start
    run(f'"{nssm}" set "{service_name}" Start SERVICE_AUTO_START')

    # ---------------- Start service ---------------- #
    print("\nStarting service...")
    run(f'"{nssm}" start "{service_name}"')

    # ---------------- Finish ---------------- #
    print("\n=== INSTALLATION COMPLETE ===")
    print(f"Service Installed: {service_name}")
    print(f"Installation Directory: {install_dir}")
    print("Agent is now running.\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\nInstaller failed:", e)
        sys.exit(1)
