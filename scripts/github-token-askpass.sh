#!/usr/bin/env bash
set -euo pipefail

TOKEN_FILE="${GITHUB_TOKEN_FILE:-/root/.github-mintwiki-token}"
PROMPT="${1:-}"

case "$PROMPT" in
  *Username*)
    printf '%s\n' "x-access-token"
    ;;
  *Password*)
    if [ ! -r "$TOKEN_FILE" ]; then
      echo "GitHub token file is not readable: $TOKEN_FILE" >&2
      exit 1
    fi
    tr -d '\r\n' < "$TOKEN_FILE"
    printf '\n'
    ;;
  *)
    printf '\n'
    ;;
esac

