#!/bin/bash
# T-3793: turns a fresh Ubuntu accelerator machine (NVIDIA driver already in the image) into the
# streaming machine, then powers it off so build-image.sh can make the image from its disk.
# Runs once, as the build machine's startup-script; session.sh comes in as metadata too.
#
#   Docker + the NVIDIA container toolkit   the town's browser runs in a container with the GPU
#   lscr.io/linuxserver/chromium            Chromium inside the Selkies web streamer (WebSockets)
#   Caddy                                   HTTPS (a certificate for <ip>.sslip.io) and the
#                                           per-session gate in front of the streamer
#   chicago-stream.service                  runs session.sh at every boot of a session machine
set -euxo pipefail
exec > >(tee -a /var/log/chicago-provision.log) 2>&1
[ -f /var/lib/chicago-provisioned ] && exit 0
export DEBIAN_FRONTEND=noninteractive
MD=http://metadata.google.internal/computeMetadata/v1

# The image needs no GPU to be built (the driver comes with the base image): when Google has none
# free, build-image.sh builds on a plain machine and the GPU checks wait for the first session.
GPU=0; grep -qi 0x10de /sys/bus/pci/devices/*/vendor && GPU=1
if [ "$GPU" = 1 ]; then
  for i in $(seq 1 30); do nvidia-smi && break; sleep 10; done
  nvidia-smi --query-gpu=name,driver_version --format=csv
fi

apt-get update
apt-get install -y ca-certificates curl gnupg jq
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release; echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --batch --yes --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' > /etc/apt/sources.list.d/nvidia-container-toolkit.list
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --batch --yes --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt > /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io nvidia-container-toolkit caddy
# Google's driver is the compute-only "server" set: no OpenGL/EGL and no video encoder, so the
# town drew in software and the stream was encoded by the CPU (found 2026-11-27). Add those parts
# of the same driver, at the installed version.
DRV=$(dpkg-query -W -f '${Package}\n' 'libnvidia-compute-*-server' | sed -n 's/^libnvidia-compute-\([0-9]*\)-server$/\1/p' | head -1)
if [ -n "$DRV" ]; then
  VER=$(dpkg-query -W -f '${Version}' "libnvidia-compute-$DRV-server")
  apt-get install -y "libnvidia-gl-$DRV-server=$VER" "libnvidia-encode-$DRV-server=$VER" \
    "libnvidia-decode-$DRV-server=$VER" "libnvidia-extra-$DRV-server=$VER"
fi
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
# Caddy starts only with a session's own Caddyfile (session.sh).
systemctl disable --now caddy

# The registry drops connections now and then (seen 2026-11-27): retry the pull.
for _ in 1 2 3 4 5 6; do docker pull lscr.io/linuxserver/chromium:latest && break; sleep 20; done
docker image inspect lscr.io/linuxserver/chromium:latest >/dev/null
# The GPU reaches a container.
[ "$GPU" = 0 ] || docker run --rm --gpus all --runtime nvidia --entrypoint nvidia-smi lscr.io/linuxserver/chromium:latest -L
# The image cannot start without them (above): fail the build rather than ship a CPU-drawn town.
[ -z "${DRV:-}" ] || ls /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 /usr/lib/x86_64-linux-gnu/libEGL_nvidia.so.0

install -d /opt/chicago-stream
curl -sf -H 'Metadata-Flavor: Google' "$MD/instance/attributes/session-script" > /opt/chicago-stream/session.sh
chmod 755 /opt/chicago-stream/session.sh
cat > /etc/systemd/system/chicago-stream.service <<'EOF'
[Unit]
Description=Chicago 4D cloud play session
After=docker.service network-online.target google-guest-agent.service
Wants=network-online.target
Requires=docker.service

[Service]
Type=simple
ExecStart=/opt/chicago-stream/session.sh
Restart=no

[Install]
WantedBy=multi-user.target
EOF
systemctl enable chicago-stream.service

# Lighter boots: nothing else on the machine needs to start.
systemctl disable --now unattended-upgrades.service apt-daily.timer apt-daily-upgrade.timer || true
apt-get clean
touch /var/lib/chicago-provisioned
echo "CHICAGO PROVISIONED" > /dev/ttyS0 || true
echo "CHICAGO PROVISIONED"
sync
# build-image.sh reads the line above from the console while the machine still runs.
sleep 45
poweroff
