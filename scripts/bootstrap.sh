#!/usr/bin/env bash
set -euo pipefail
make up
(make app &) 
sleep 2
make load || true
make gate || true
