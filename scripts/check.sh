#!/usr/bin/env bash
# PR 올리기 전 로컬 검사 (CI 와 동일한 순서)
#   ./scripts/check.sh            전체
#   ./scripts/check.sh camera     특정 팀 폴더의 패키지 + 그에 의존하는 패키지만
set -euo pipefail
cd "$(dirname "$0")/.."

echo "▶ 1/4 코드 스타일 (pre-commit)"
pre-commit run --all-files

# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"

select_args=()
if [ $# -gt 0 ]; then
  mapfile -t pkgs < <(colcon list --names-only --base-paths "src/$1")
  if [ ${#pkgs[@]} -eq 0 ]; then
    echo "src/$1 에 ROS 패키지가 없습니다."; exit 0
  fi
  select_args=(--packages-above-and-dependencies "${pkgs[@]}")
fi

echo "▶ 2/4 빌드 (colcon build)"
colcon build --symlink-install "${select_args[@]}"

echo "▶ 3/4 테스트 (colcon test)"
test_args=()
[ $# -gt 0 ] && test_args=(--packages-above "${pkgs[@]}")
colcon test "${test_args[@]}" --event-handlers console_direct+
colcon test-result --verbose

echo "▶ 4/4 아두이노 컴파일"
for dir in firmware/arduino/*/; do
  [ -f "${dir}sketch.yaml" ] && arduino-cli compile "$dir"
done

echo "✅ 모든 검사 통과 - PR 을 올려도 됩니다."
