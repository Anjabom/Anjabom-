#!/usr/bin/env bash
# 이슈 작업 시작: 최신 main 에서 규칙에 맞는 브랜치를 만든다.
#   ./scripts/start_task.sh <팀id> <이슈번호> <짧은-설명>
#   예) ./scripts/start_task.sh camera 12 lane-offset
set -euo pipefail
cd "$(dirname "$0")/.."

team=${1:?"팀 id"}; issue=${2:?"이슈 번호"}; desc=${3:?"짧은 설명(영문, 하이픈)"}
if ! python3 scripts/teams.py list | grep -qx "$team"; then
  echo "알 수 없는 팀: $team"; python3 scripts/teams.py list; exit 1
fi
branch="$team/$issue-$desc"

if [ -n "$(git status --porcelain)" ]; then
  echo "커밋하지 않은 변경이 있습니다. 먼저 커밋하거나 git stash 하세요."; exit 1
fi
git fetch origin main
git switch -c "$branch" origin/main
echo "✅ $branch 브랜치에서 작업을 시작하세요. 첫 push 후 Draft PR 을 열면 진행 상황이 보드에 보입니다."
