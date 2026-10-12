#!/usr/bin/env bash
# antar — secure env loader. Reads secrets from the TERMINAL (never chat, never argv,
# never committed). Run:  source scripts/load-env.sh   (or)  ./scripts/load-env.sh --write
set -euo pipefail

ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"
umask 077   # any file we write is 0600

_read_secret() {  # $1=var  $2=current  $3=prompt
  local var="$1" cur="$2" prompt="$3" val
  if [ -n "${!var:-}" ]; then return 0; fi            # already in environment
  if [ -n "$cur" ]; then echo "$var=<set in .env>" >>/dev/null; fi
  read -r -s -p "  $prompt [$var]: " val; echo
  if [ -n "$val" ]; then printf '%s=%s\n' "$var" "$val" >>"$ENV_FILE.tmp"; fi
}

echo "antar env setup — secrets stay in this terminal, written to .env (chmod 600, gitignored)."
: >"$ENV_FILE.tmp"
_read_secret NEATLOGS_API_KEY "" "neatlogs project key (fnq_…)"
_read_secret LITELLM_API_KEY "" "hackathon LiteLLM key (or a BYOK key below)"
read -r -p "  Optional BYOK (press Enter to skip each):" >/dev/null || true
_read_secret OPENAI_API_KEY "" "OpenAI key (sk-…)"
_read_secret GROQ_API_KEY "" "Groq key (gsk_…)"
_read_secret ANTHROPIC_API_KEY "" "Anthropic key (sk-ant-…)"

# GitHub token: reuse the gh keyring session — no paste needed.
if ! grep -q '^GITHUB_TOKEN=' "$ENV_FILE.tmp"; then
  if command -v gh >/dev/null 2>&1 && gh auth token >/dev/null 2>&1; then
    printf 'GITHUB_TOKEN=%s\n' "$(gh auth token)" >>"$ENV_FILE.tmp"
    echo "  GITHUB_TOKEN ← reused from gh keyring session"
  fi
fi

cat "$ENV_FILE.tmp" >>"$ENV_FILE"
rm -f "$ENV_FILE.tmp"
chmod 600 "$ENV_FILE"
echo "✓ wrote $ENV_FILE (600). To load into your shell:  set -a; . ./.env; set +a"
