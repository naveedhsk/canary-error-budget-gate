#!/usr/bin/env bash
set -euo pipefail
curl -sSf http://localhost:8080 >/dev/null && echo OK || exit 1
