#!/bin/bash
set -euo pipefail
cd /root/forge-memecoin-dashboard
python3 generate_data.py >/dev/null
git add -A
if git diff --cached --quiet; then
  exit 0
fi
git -c user.email=forge@seodesignlab.com -c user.name="Forge VM" commit -m "data $(date -u +%Y-%m-%dT%H:%MZ)" >/dev/null
git push origin main >/dev/null
