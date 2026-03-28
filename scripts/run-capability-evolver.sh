#!/bin/zsh
set -euo pipefail
cd /Users/ai/.openclaw/workspace/skills/capability-evolver
export EVOLVE_STRATEGY="${EVOLVE_STRATEGY:-auto}"
export EVOLVE_ALLOW_SELF_MODIFY="${EVOLVE_ALLOW_SELF_MODIFY:-false}"
export EVOLVE_LOAD_MAX="${EVOLVE_LOAD_MAX:-100}"
exec /Users/ai/.nvm/versions/node/v22.22.0/bin/node index.js --loop
