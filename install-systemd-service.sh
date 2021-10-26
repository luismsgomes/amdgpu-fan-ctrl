#! /bin/bash

# stop service if running
systemctl stop amdgpu-fan-ctrl.service > /dev/null 2>&1 || true

mkdir -p /usr/local/bin
cp $(dirname $0)/amdgpu_fan_ctrl.py /usr/local/bin/amdgpu-fan-ctrl
chmod +x /usr/local/bin/amdgpu-fan-ctrl
cp $(dirname $0)/amdgpu-fan-ctrl.service /etc/systemd/system/amdgpu-fan-ctrl.service

systemctl daemon-reload
systemctl start amdgpu-fan-ctrl.service
systemctl enable amdgpu-fan-ctrl.service
