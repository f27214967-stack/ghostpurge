# GhostPurge 👻

Advanced multi-format post-uninstall cleanup service for Debian 13.
Supports Apt, Dpkg, Flatpak, Snap, AppImage, Steam, Pip and Npm.

## Features

- Aggressive, conservative, and hyper-aggressive cleanup modes
- Full support for all modern package managers

## Local Installation (Development)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

## Service Deployment (Production)

GhostPurge is designed to run in the background via `systemd`. Follow these steps to install it on your system (Debian/Ubuntu):

1. **Copy the project to /opt**
```bash
sudo cp -r . /opt/ghostpurge
cd /opt/ghostpurge
sudo rm -rf venv
sudo python3 -m venv venv
sudo /opt/ghostpurge/venv/bin/pip install -e .
```

2. **Install and adapt configuration**
It is crucial to adapt the configuration file to your system username so that the paths to Pip, Npm, and Steam are correct.

```bash
sudo mkdir -p /etc/ghostpurge
sudo cp conf/config.yaml.template /etc/ghostpurge/config.yaml

# Edit the file to replace "/home/user" with your actual user directory
sudo nano /etc/ghostpurge/config.yaml
```

3. **Enable Systemd service**
```bash
sudo cp systemd/ghostpurge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ghostpurge
```

4. **Check status**
```bash
systemctl status ghostpurge
tail -f /var/log/ghostpurge.log
```
