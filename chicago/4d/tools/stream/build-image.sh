#!/bin/bash
# T-3793: build the streaming machine image into chicago-stream (image family `chicago-stream`).
#
#   bash tools/stream/build-image.sh [project]
#
# Run where gcloud is signed in as the project's owner (Cloud Shell is simplest). It starts one
# Spot g2-standard-4 (one L4) from Google's newest Ubuntu 22.04 accelerator image (the NVIDIA
# driver comes with it), lets machine/provision.sh install the rest and power off, makes the
# image from its disk, and deletes the build machine. About 15 minutes, well under $1.
set -euo pipefail
PROJECT=${1:-chicago-stream}
HERE=$(cd "$(dirname "$0")" && pwd)
STAMP=$(date -u +%Y%m%d-%H%M)
NAME="stream-build-$STAMP"
FAMILY=$(gcloud compute images list --project ubuntu-os-accelerator-images \
  --filter="family~^ubuntu-accelerator-2204-amd64-with-nvidia" --format="value(family)" | sort -uV | tail -1)
[ -n "$FAMILY" ] || { echo "no Ubuntu accelerator image family found"; exit 1; }
echo "base image family: $FAMILY"

ZONE=""
for z in us-central1-a us-central1-b us-central1-c; do
  if gcloud compute instances create "$NAME" --project "$PROJECT" --zone "$z" \
      --machine-type g2-standard-4 --provisioning-model SPOT --instance-termination-action STOP \
      --maintenance-policy TERMINATE --image-project ubuntu-os-accelerator-images --image-family "$FAMILY" \
      --boot-disk-size 50GB --boot-disk-type pd-balanced --network-tier STANDARD \
      --labels app=chicago-stream-build \
      --metadata-from-file "startup-script=$HERE/machine/provision.sh,session-script=$HERE/machine/session.sh"; then
    ZONE=$z; break
  fi
  echo "no Spot L4 in $z; trying the next zone"
done
[ -n "$ZONE" ] || { echo "no zone had a Spot L4 free; try again later"; exit 1; }
cleanup() { gcloud compute instances delete "$NAME" --project "$PROJECT" --zone "$ZONE" --quiet || true; }
trap cleanup EXIT

echo "provisioning (the machine powers itself off when done)…"
for _ in $(seq 1 90); do
  status=$(gcloud compute instances describe "$NAME" --project "$PROJECT" --zone "$ZONE" --format="value(status)")
  [ "$status" = "TERMINATED" ] && break
  sleep 20
done
[ "$status" = "TERMINATED" ] || { echo "the build machine did not finish in 30 minutes"; exit 1; }
if ! gcloud compute instances get-serial-port-output "$NAME" --project "$PROJECT" --zone "$ZONE" 2>/dev/null | grep -q "CHICAGO PROVISIONED"; then
  echo "the build machine stopped without finishing (Spot reclaimed, or provision.sh failed); serial tail:"
  gcloud compute instances get-serial-port-output "$NAME" --project "$PROJECT" --zone "$ZONE" 2>/dev/null | tail -40
  exit 1
fi
gcloud compute images create "chicago-stream-$STAMP" --project "$PROJECT" \
  --source-disk "$NAME" --source-disk-zone "$ZONE" --family chicago-stream \
  --labels app=chicago-stream --description "Chicago 4D cloud play: Ubuntu + NVIDIA L4 driver, Docker, Selkies Chromium, Caddy (tools/stream/machine)"
echo "image chicago-stream-$STAMP is the newest in family chicago-stream"
