#!/bin/bash
# EC2 Setup Script for Rate Limiter API
# Tested on Amazon Linux 2023

set -e

echo "=== Installing Python 3.11 ==="
sudo dnf install -y python3.11 python3.11-pip

echo "=== Installing and Starting Redis ==="
sudo dnf install -y redis6
sudo systemctl enable redis6
sudo systemctl start redis6

echo "=== Cloning Repository ==="
cd /home/ec2-user
git clone https://github.com/RajLaskar10/rate-limiter.git
cd rate-limiter

echo "=== Installing Python Dependencies ==="
pip3.11 install -r requirements.txt

echo "=== Creating systemd Service ==="
sudo tee /etc/systemd/system/rate-limiter.service > /dev/null <<EOF
[Unit]
Description=Rate Limiter API
After=network.target redis6.service

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/rate-limiter
ExecStart=/usr/bin/python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable rate-limiter
sudo systemctl start rate-limiter

echo ""
echo "=== Setup Complete ==="
echo "API is running on port 8000"
echo "Check status: sudo systemctl status rate-limiter"
echo "View logs:    sudo journalctl -u rate-limiter -f"
