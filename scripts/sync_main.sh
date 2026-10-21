#!/usr/bin/env bash
# 작업 브랜치에 최신 main 을 반영한다. (하루 한 번 이상 권장 → 충돌을 작게 유지)
set -euo pipefail
cd "$(dirname "$0")/.."

branch=$(git branch --show-current)
if [ "$branch" = main ]; then
  git pull --ff-only origin main; exit 0
fi
git fetch origin main
behind=$(git rev-list --count HEAD..origin/main)
echo "main 보다 ${behind}개 커밋 뒤처져 있습니다. 병합합니다."
git merge --no-edit origin/main
echo "✅ 완료. 충돌이 났다면 해결 후 git commit, 그리고 ./scripts/check.sh"
