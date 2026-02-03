#!/bin/bash
# Restore .env file from Vaultwarden Secure Note
# Usage: ./restore-env-from-vault.sh [project-name]

set -e

VAULT_SERVER="https://va.ylongwang.top"

# Get project name
if [[ -n "$1" ]]; then
    PROJECT_NAME="$1"
else
    PROJECT_NAME=$(basename "$(pwd)")
fi

ITEM_NAME="${PROJECT_NAME}/.env"

echo "Restoring .env from Vaultwarden for '$PROJECT_NAME'..."

# Configure server if needed
CURRENT_SERVER=$(bw config server 2>/dev/null || echo "")
if [[ "$CURRENT_SERVER" != *"$VAULT_SERVER"* ]]; then
    bw config server "$VAULT_SERVER"
fi

# Check login status
STATUS=$(bw status 2>/dev/null | jq -r '.status' 2>/dev/null || echo "unauthenticated")

if [[ "$STATUS" == "unauthenticated" ]]; then
    echo "Please login first: bw login"
    exit 1
fi

if [[ "$STATUS" == "locked" ]]; then
    echo "Vault is locked. Please unlock:"
    echo "  export BW_SESSION=\$(bw unlock --raw)"
    exit 1
fi

# Sync vault
bw sync > /dev/null

# Get item
ITEM=$(bw list items --search "$ITEM_NAME" 2>/dev/null | jq -r ".[] | select(.name == \"$ITEM_NAME\")" 2>/dev/null || echo "")

if [[ -z "$ITEM" ]]; then
    echo "Error: '$ITEM_NAME' not found in vault"
    echo ""
    echo "Available .env files:"
    bw list items 2>/dev/null | jq -r '.[] | select(.name | endswith("/.env")) | .name' 2>/dev/null || echo "  (none)"
    exit 1
fi

# Extract notes (the .env content)
echo "$ITEM" | jq -r '.notes' > .env

echo "✅ Restored .env for $PROJECT_NAME"
echo "   $(wc -l < .env | tr -d ' ') lines written"
