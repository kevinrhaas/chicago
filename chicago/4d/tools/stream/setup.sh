#!/bin/bash
# T-3794 / T-3795: set up cloud play in the chicago-stream project. Safe to run again: each step
# checks what is already there. Run where gcloud is signed in as the project's owner (Cloud
# Shell is simplest), from the repository:
#
#   bash chicago/4d/tools/stream/setup.sh [project]
#
# It makes
#   stream-starter@   the starter's account: may start and delete machines, write the ledger
#   stream-machine@   each machine's account: may only delete (its own) machines
#   <project>-ledger  the bucket holding each month's machine-hours (hours/YYYY-MM.json)
#   a firewall rule   HTTPS (and HTTP for the certificate) to machines tagged chicago-stream
#   chicago-stream-starter  the Cloud Run service (tools/stream/starter), open to the browser;
#                     who may start a machine is checked inside it, against the Firestore rules
#   budget-alerts     the Pub/Sub topic the $100 budget reports to, pushed to the starter's
#                     /budget, which stops every machine at 100 % (T-3795)
# and prints the starter's address for js/sign-in-config.js (streamStarter).
set -euo pipefail
PROJECT=${1:-chicago-stream}
REGION=us-central1
HERE=$(cd "$(dirname "$0")" && pwd)
gc() { gcloud --project "$PROJECT" "$@"; }

echo "== APIs"
gc services enable compute.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  pubsub.googleapis.com storage.googleapis.com billingbudgets.googleapis.com iam.googleapis.com

echo "== accounts"
for sa in stream-starter stream-machine; do
  gc iam service-accounts describe "$sa@$PROJECT.iam.gserviceaccount.com" >/dev/null 2>&1 \
    || gc iam service-accounts create "$sa" --display-name "Chicago 4D $sa"
done
STARTER="stream-starter@$PROJECT.iam.gserviceaccount.com"
MACHINE="stream-machine@$PROJECT.iam.gserviceaccount.com"
# A machine may delete machines and nothing else.
gc iam roles describe streamSelfDelete >/dev/null 2>&1 || gc iam roles create streamSelfDelete \
  --title "Chicago stream machine: delete itself" --permissions compute.instances.delete,compute.instances.get --stage GA
gcloud projects add-iam-policy-binding "$PROJECT" --member "serviceAccount:$MACHINE" --role "projects/$PROJECT/roles/streamSelfDelete" --condition None >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT" --member "serviceAccount:$STARTER" --role roles/compute.instanceAdmin.v1 --condition None >/dev/null
gcloud iam service-accounts add-iam-policy-binding "$MACHINE" --project "$PROJECT" --member "serviceAccount:$STARTER" --role roles/iam.serviceAccountUser >/dev/null

echo "== ledger bucket"
BUCKET="$PROJECT-ledger"
gcloud storage buckets describe "gs://$BUCKET" >/dev/null 2>&1 \
  || gcloud storage buckets create "gs://$BUCKET" --project "$PROJECT" --location "$REGION" --uniform-bucket-level-access
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --member "serviceAccount:$STARTER" --role roles/storage.objectAdmin >/dev/null

echo "== firewall"
gc compute firewall-rules describe allow-chicago-stream >/dev/null 2>&1 || gc compute firewall-rules create allow-chicago-stream \
  --network default --direction INGRESS --allow tcp:80,tcp:443 --target-tags chicago-stream --source-ranges 0.0.0.0/0 \
  --description "Chicago 4D cloud play: the stream (443) and its certificate (80)"

echo "== starter"
# Cloud Run builds the starter from source with the project's default compute account, which
# new projects no longer give the Cloud Build role by themselves.
NUM=$(gcloud projects describe "$PROJECT" --format "value(projectNumber)")
gcloud projects add-iam-policy-binding "$PROJECT" --member "serviceAccount:$NUM-compute@developer.gserviceaccount.com" \
  --role roles/cloudbuild.builds.builder --condition None >/dev/null
SERVICE=chicago-stream-starter
SECRET=$(gc run services describe "$SERVICE" --region "$REGION" --format=json 2>/dev/null \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((e.get("value","") for e in d["spec"]["template"]["spec"]["containers"][0].get("env",[]) if e["name"]=="BUDGET_SECRET"),""))' 2>/dev/null || true)
[ -n "$SECRET" ] || SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
gc run deploy "$SERVICE" --source "$HERE/starter" --region "$REGION" --service-account "$STARTER" \
  --allow-unauthenticated --max-instances 2 --memory 256Mi --cpu 1 --timeout 600 --quiet \
  --set-env-vars "LEDGER_BUCKET=$BUCKET,MACHINE_SA=$MACHINE,MAX_MACHINES=1,BUDGET_SECRET=$SECRET"
URL=$(gc run services describe "$SERVICE" --region "$REGION" --format "value(status.url)")

echo "== budget stop"
gc pubsub topics describe budget-alerts >/dev/null 2>&1 || gc pubsub topics create budget-alerts
if gc pubsub subscriptions describe budget-alerts-to-starter >/dev/null 2>&1; then
  gc pubsub subscriptions modify-push-config budget-alerts-to-starter --push-endpoint "$URL/budget?secret=$SECRET"
else
  gc pubsub subscriptions create budget-alerts-to-starter --topic budget-alerts --push-endpoint "$URL/budget?secret=$SECRET" --ack-deadline 60
fi
ACCOUNT=$(gcloud billing projects describe "$PROJECT" --format "value(billingAccountName)" | sed 's#billingAccounts/##')
BUDGET=$(gcloud billing budgets list --billing-account "$ACCOUNT" --format "value(name)" --filter "displayName:chicago-stream" | head -1)
if [ -n "$BUDGET" ]; then
  gcloud billing budgets update "$BUDGET" --billing-account "$ACCOUNT" --notifications-rule-pubsub-topic "projects/$PROJECT/topics/budget-alerts"
  echo "budget $BUDGET reports to budget-alerts"
else
  echo "!! no budget named chicago-stream found on billing account $ACCOUNT: link its alerts to projects/$PROJECT/topics/budget-alerts by hand"
fi

echo
echo "starter: $URL"
echo "put it in chicago/4d/renderers/web/js/sign-in-config.js as streamStarter"
