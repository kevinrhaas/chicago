#!/bin/bash
# T-3793: build the streaming machine image into chicago-stream (image family `chicago-stream`).
#
#   bash tools/stream/build-image.sh [project]
#
# Run where gcloud is signed in as the project's owner (Cloud Shell is simplest). It starts one
# g2-standard-4 (one L4) from Google's newest Ubuntu 22.04 accelerator image (the NVIDIA
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

# L4s are often all taken (2026-11-27: none free in any US zone, Spot or on demand). The image is
# the same whatever GPU builds it (the driver serves both), so the build tries an L4 in each zone,
# then a T4 (n1-standard-4), then a machine with no GPU at all. It goes on demand: well under $1 a build.
ZONE=""
try() { # zone machine-type [accelerator]
  gcloud compute instances create "$NAME" --project "$PROJECT" --zone "$1" \
    --machine-type "$2" ${3:+--accelerator "$3"} --provisioning-model STANDARD \
    --maintenance-policy TERMINATE --image-project ubuntu-os-accelerator-images --image-family "$FAMILY" \
    --boot-disk-size 50GB --boot-disk-type pd-balanced --network-tier STANDARD \
    --labels app=chicago-stream-build \
    --metadata-from-file "startup-script=$HERE/machine/provision.sh,session-script=$HERE/machine/session.sh"
}
for z in us-central1-a us-central1-b us-central1-c us-east4-a us-east4-c us-east1-b us-east1-c us-east1-d us-west1-a us-west1-b us-west4-a us-west4-c; do
  if try "$z" g2-standard-4; then ZONE=$z; break; fi
  echo "no L4 in $z; trying the next zone"
done
if [ -z "$ZONE" ]; then
  for z in us-central1-a us-central1-b us-central1-c us-central1-f us-east4-a us-east4-b us-east4-c us-east1-c us-east1-d us-west1-a us-west1-b us-west4-a us-west4-b; do
    if try "$z" n1-standard-4 type=nvidia-tesla-t4,count=1; then ZONE=$z; break; fi
    echo "no T4 in $z; trying the next zone"
  done
fi
if [ -z "$ZONE" ]; then
  echo "no L4 or T4 free anywhere; building on a plain machine (the GPU is checked at the first session)"
  for z in us-central1-a us-central1-b us-central1-c; do
    if try "$z" n1-standard-4; then ZONE=$z; break; fi
  done
fi
[ -n "$ZONE" ] || { echo "no zone could start the build machine; try again later"; exit 1; }
cleanup() { gcloud compute instances delete "$NAME" --project "$PROJECT" --zone "$ZONE" --quiet || true; }
trap cleanup EXIT

echo "provisioning (the machine powers itself off when done)…"
# The console is readable only while the machine runs, so the finish line is watched for here.
done=0
for _ in $(seq 1 90); do
  status=$(gcloud compute instances describe "$NAME" --project "$PROJECT" --zone "$ZONE" --format="value(status)")
  [ "$status" = "TERMINATED" ] && break
  if gcloud compute instances get-serial-port-output "$NAME" --project "$PROJECT" --zone "$ZONE" 2>/dev/null > "/tmp/$NAME.console"; then
    grep -q "CHICAGO PROVISIONED" "/tmp/$NAME.console" && done=1
  fi
  sleep 15
done
[ "$status" = "TERMINATED" ] || { echo "the build machine did not finish in 25 minutes"; exit 1; }
if [ "$done" != 1 ]; then
  echo "the build machine stopped without finishing (provision.sh failed); console tail:"
  grep startup-script "/tmp/$NAME.console" | tail -40
  exit 1
fi
gcloud compute images create "chicago-stream-$STAMP" --project "$PROJECT" \
  --source-disk "$NAME" --source-disk-zone "$ZONE" --family chicago-stream \
  --labels app=chicago-stream --description "Chicago 4D cloud play: Ubuntu + NVIDIA driver (L4 or T4), Docker, Selkies Chromium, Caddy (tools/stream/machine)"
echo "image chicago-stream-$STAMP is the newest in family chicago-stream"
