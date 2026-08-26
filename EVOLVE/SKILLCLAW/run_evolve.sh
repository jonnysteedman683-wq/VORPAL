#!/usr/bin/env bash
# =============================================================================
# VORPAL · SkillClaw Evolve — one-shot evolution pass
# Wired 2026-08-26 by Hermes. Pipeline verified green against Nous inference.
#
# What it does: drains session JSONs from EVOLVE/SKILLCLAW/default/sessions/,
# has the LLM (stealth/ox-alpha via Nous) analyze them against the staged skill
# library in EVOLVE/SKILLCLAW/default/skills/, and evolves skill bundles with
# versioned history (skills/<name>/history/vN.md + vN_evidence.md).
#
# Auth: reads the Nous access_token from Hermes auth.json (never prints it).
# Usage:   bash run_evolve.sh [--publish-mode direct|validated] [--interval N]
#   --once (default): one cycle, then exit.   --interval N: daemon loop, N sec.
# Exit codes: 0 = clean cycle (even if LLM chose skip), 1 = pipeline error.
# =============================================================================
set -euo pipefail

HERMES_AUTH="C:/Users/jonny/AppData/Local/hermes/auth.json"
WS="C:/Users/jonny/OneDrive/Desktop/VORPAL/EVOLVE/SKILLCLAW"
SC_DIR="C:/Users/jonny/skillclaw"
GROUP_ID="default"
PUBLISH_MODE="${1:-direct}"  # 'direct' = write evolved skills to workspace (then sync to live); 'validated' = stage for review
INTERVAL="${2:-}"

TOKEN="$(python -c "import json;print(json.load(open('$HERMES_AUTH'))['providers']['nous']['access_token'])")"

export OPENAI_API_KEY="$TOKEN"
export OPENAI_BASE_URL="https://inference-api.nousresearch.com/v1"
export EVOLVE_MODEL="stealth/ox-alpha"

cd "$SC_DIR"
# NOTE: do NOT pass --use-skillclaw-config here — it re-imports the dead
# DeepSeek key from ~/.skillclaw/config.yaml and overrides the env auth below.
ARGS=(--engine workflow --storage-backend local \
      --local-root "$WS" --group-id "$GROUP_ID" --publish-mode "$PUBLISH_MODE")

if [ -n "$INTERVAL" ]; then
  exec .venv/Scripts/python.exe -m evolve_server "${ARGS[@]}" --interval "$INTERVAL"
else
  exec .venv/Scripts/python.exe -m evolve_server "${ARGS[@]}" --once
fi
