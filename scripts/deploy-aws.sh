#!/usr/bin/env bash
# antar — AWS deploy (App Runner, the simplest container service).
# Secrets come from Secrets Manager / env — NEVER baked into the image or args.
# Prereq: an authenticated AWS CLI (`aws login` / `aws sts get-caller-identity`).
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
APP="${ANTAR_APP_NAME:-antar}"
ECR_REPO="$APP"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "== sanity: AWS identity =="
aws sts get-caller-identity >/dev/null   # fails loudly if session expired

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

echo "== create ECR repo (idempotent) =="
aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$ECR_REPO" --region "$REGION" \
       --image-scanning-configuration scanOnPush=true >/dev/null

echo "== build + push =="
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ECR_URI"
docker build -t "$ECR_REPO:$IMAGE_TAG" .
docker tag "$ECR_REPO:$IMAGE_TAG" "$ECR_URI/$ECR_REPO:$IMAGE_TAG"
docker push "$ECR_URI/$ECR_REPO:$IMAGE_TAG"

echo "== secrets (create if missing; values read from your env) =="
# Store NEATLOGS_API_KEY / LITELLM_API_KEY in Secrets Manager, referenced by App Runner.
# aws secretsmanager create-secret --name antar/neatlogs --secret-string "$NEATLOGS_API_KEY"

echo "== App Runner service =="
echo "Create/Update App Runner pointing at $ECR_URI/$ECR_REPO:$IMAGE_TAG on port 8000."
echo "Wire secrets from Secrets Manager as environment variables. (Console or"
echo "aws apprunner create-service --service-name $APP --source-configuration ...) "
echo "Done. Image: $ECR_URI/$ECR_REPO:$IMAGE_TAG"
