#!/usr/bin/env bash
set -euo pipefail

echo '--- Neurocore lint ---'
cd '/c/Users/jonny/OneDrive/Documents/AEGIS/neurocore'
npx tsc --noEmit

echo '--- Neurocore tests ---'
npm test

echo '--- OMNIBUS tests ---'
cd '/c/Users/jonny/OneDrive/Desktop/AQB/OMNIBUS'
npm test

echo '--- Start OMNIBUS ---'
node server.cjs &
SERVER_PID=$!
sleep 2

echo '--- Neurocore health ---'
curl -s http://localhost:3000/api/neurocore/health

echo '--- Neurocore intent probe ---'
curl -s -X POST http://localhost:3000/api/neurocore/intent \
  -H 'content-type: application/json' \
  -d '{"intent":"probe","source":"mock","confidence":0.9,"features":{},"requiresConfirmation":false}'

echo '--- Cleanup ---'
kill "$SERVER_PID" || true
