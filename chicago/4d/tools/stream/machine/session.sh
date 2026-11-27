#!/bin/bash
# T-3793 / T-3794: one cloud play session, run at boot by chicago-stream.service.
#
# The starter put the session on the machine's metadata: chicago-url (the year to open) and
# session-token (the secret in the player's link). This script
#   1. writes a Caddyfile for https://<external ip with dashes>.sslip.io: the link
#      ?k=<token> sets a cookie and every later request must carry it, so the stream answers
#      only the player who was handed the link;
#   2. starts Chromium in the Selkies streamer with the GPU, opening the town at that year
#      (the player signs in inside the stream, as on any device: the machine holds no sign-in);
#   3. sets the guest attribute chicago/ready=1 once the stream answers through HTTPS, which the
#      starter reads to hand back the link;
#   4. deletes its own machine after ten minutes with nobody connected. Google deletes it after
#      two hours in any case (maxRunDuration, set by the starter).
set -uo pipefail
MD=http://metadata.google.internal/computeMetadata/v1
md() { curl -sf -H 'Metadata-Flavor: Google' "$MD/$1"; }
guest() { curl -sf -X PUT --data "$2" -H 'Metadata-Flavor: Google' "$MD/instance/guest-attributes/chicago/$1" || true; }

URL=$(md instance/attributes/chicago-url) || { echo "no session on this machine"; exit 0; }
TOKEN=$(md instance/attributes/session-token)
[[ "$TOKEN" =~ ^[0-9a-f]{32,}$ ]] || { echo "bad session token"; exit 1; }
[[ "$URL" =~ ^https://[a-z0-9./-]+/$ ]] || { echo "bad town address"; exit 1; }
IP=$(md instance/network-interfaces/0/access-configs/0/external-ip)
HOST="${IP//./-}.sslip.io"
NAME=$(md instance/name)
ZONE=$(md instance/zone | awk -F/ '{print $NF}')
PROJECT=$(md project/project-id)
guest ready 0

cat > /etc/caddy/Caddyfile <<EOF
{
	admin off
}
$HOST {
	@enter query k=$TOKEN
	handle @enter {
		header Set-Cookie "chicago_stream=$TOKEN; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=7200"
		redir * / 302
	}
	@ok header_regexp session Cookie chicago_stream=$TOKEN
	handle @ok {
		reverse_proxy 127.0.0.1:3000
	}
	handle {
		respond "This cloud machine belongs to another session." 403
	}
}
EOF
systemctl start caddy

docker rm -f town >/dev/null 2>&1 || true
# The starter only asks for GPU machines; without one (an admin's plumbing test on a plain
# machine) the town still opens, drawn by the CPU.
# With the GPU the town draws on it and the stream is encoded on it (NVENC): the container gets
# the render node and the modeset device, and the CDI list of driver files is made afresh so it
# names the graphics and encoder libraries (a list made before they were installed left them out,
# and Chromium fell back to drawing in software; 2026-11-27).
GPU=()
if grep -qi 0x10de /sys/bus/pci/devices/*/vendor; then
  nvidia-ctk cdi generate --output=/var/run/cdi/nvidia.yaml >/dev/null 2>&1 || true
  GPU=(--gpus all --runtime nvidia --device /dev/nvidia-modeset --device /dev/dri:/dev/dri
       -e NVIDIA_DRIVER_CAPABILITIES=all -e DRINODE=/dev/dri/renderD128 -e DRI_NODE=/dev/dri/renderD128)
fi
# The player gets the town and nothing else: no desktop menus or window frames, no file
# transfer, no shared viewers, no clipboard and no Selkies side panel.
LOCK=(-e HARDEN_DESKTOP=true -e HARDEN_OPENBOX=true -e NO_DECOR=true
      -e SELKIES_FILE_TRANSFERS=none -e SELKIES_ENABLE_SHARING=false
      -e "SELKIES_ENABLE_CLIPBOARD=false|locked" -e "SELKIES_UI_SHOW_SIDEBAR=false|locked")
docker run -d --name town "${GPU[@]}" "${LOCK[@]}" \
  -e PUID=1000 -e PGID=1000 -e TZ=America/Chicago -e TITLE="Chicago 4D" \
  -e CHROME_CLI="--kiosk --start-fullscreen --ignore-gpu-blocklist --enable-gpu-rasterization --autoplay-policy=no-user-gesture-required $URL" \
  -p 127.0.0.1:3000:3000 --shm-size=2g \
  lscr.io/linuxserver/chromium:latest

# Ready once the certificate is issued and the streamer answers through the gate.
for _ in $(seq 1 120); do
  if curl -sf -o /dev/null --resolve "$HOST:443:127.0.0.1" -H "Cookie: chicago_stream=$TOKEN" "https://$HOST/"; then
    guest ready 1; echo "session ready on $HOST"; break
  fi
  sleep 3
done

# Idle watch: nobody connected for ten minutes ends the session.
idle=0
while sleep 30; do
  if [ "$(ss -Htn state established '( sport = :443 )' | wc -l)" -gt 0 ]; then idle=0; else idle=$((idle + 30)); fi
  if [ "$idle" -ge 600 ]; then
    echo "idle ten minutes: ending the session"
    guest ready 0
    tok=$(md instance/service-accounts/default/token | jq -r .access_token)
    curl -sf -X DELETE -H "Authorization: Bearer $tok" \
      "https://compute.googleapis.com/compute/v1/projects/$PROJECT/zones/$ZONE/instances/$NAME" >/dev/null || poweroff
    sleep 300
    poweroff
  fi
done
