#!/bin/bash
# Sync .env file to Vaultwarden as Secure Note
# Usage: ./sync-env-to-vault.sh [.env file path]

set -e

ENV_FILE="${1:-.env}"
VAULT_SERVER="https://va.ylongwang.top"

# Check if .env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: $ENV_FILE not found"
    exit 1
fi

# Get project name from directory
PROJECT_NAME=$(basename "$(dirname "$(realpath "$ENV_FILE")")")
ITEM_NAME="${PROJECT_NAME}/.env"

echo "Syncing $ENV_FILE to Vaultwarden as '$ITEM_NAME'..."

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

# Check if item already exists
EXISTING_ID=$(bw list items --search "$ITEM_NAME" 2>/dev/null | jq -r ".[] | select(.name == \"$ITEM_NAME\") | .id" 2>/dev/null || echo "")

ENV_CONTENT=$(cat "$ENV_FILE")

if [[ -n "$EXISTING_ID" ]]; then
    # Update existing item
    echo "Updating existing item..."
    bw get item "$EXISTING_ID" | jq --arg notes "$ENV_CONTENT" '.notes = $notes' | bw encode | bw edit item "$EXISTING_ID" > /dev/null
    echo "✅ Updated: $ITEM_NAME"
else
    # Create new item
    echo "Creating new item..."
    jq -n \
        --arg name "$ITEM_NAME" \
        --arg notes "$ENV_CONTENT" \
        '{type: 2, name: $name, notes: $notes, secureNote: {type: 0}}' | bw encode | bw create item > /dev/null
    echo "✅ Created: $ITEM_NAME"
fi

echo "Done! View in Vaultwarden: $VAULT_SERVER"
