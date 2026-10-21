#!/usr/bin/env bash
# 개발 환경 초기 설정. devcontainer 생성 시 자동 실행되며, 직접 실행해도 된다.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "▶ pre-commit 훅 설치"
pre-commit install --install-hooks

echo "▶ ROS 의존성 설치 (rosdep)"
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  sudo rosdep init
fi
rosdep update --rosdistro "${ROS_DISTRO}"
rosdep install --from-paths src --ignore-src -y --rosdistro "${ROS_DISTRO}"

echo "▶ 아두이노 보드 코어 설치"
for sketch in firmware/arduino/*/sketch.yaml; do
  [ -f "$sketch" ] || continue
  fqbn=$(sed -n 's/^default_fqbn:[[:space:]]*//p' "$sketch")
  arduino-cli core install "${fqbn%:*}"
done

if [ -z "$(git config user.name || true)" ]; then
  echo "⚠️  git config --global user.name / user.email 을 설정하세요."
fi
echo "✅ 설정 완료. ./scripts/check.sh 로 빌드/테스트를 확인하세요."
