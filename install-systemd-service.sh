#! /bin/bash

mkdir -p /usr/local/bin
cp $(dirname $0)/amdgpu_fan_ctrl.py /usr/local/bin/amdgpu-fan-ctrl
cp $(dirname $0)/amdgpu-fan-ctrl.service /etc/systemd/system/amdgpu-fan-ctrl.service

systemctl daemon-reload
systemctl start amdgpu-fan-ctrl.service
systemctl enable amdgpu-fan-ctrl.service
