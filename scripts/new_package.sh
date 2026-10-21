#!/usr/bin/env bash
# 팀 폴더에 ROS2 패키지 생성
#   ./scripts/new_package.sh <팀id> <패키지이름> [python|cpp]
set -euo pipefail
cd "$(dirname "$0")/.."

team=${1:?"팀 id 필요 (python3 scripts/teams.py list)"}
name=${2:?"패키지 이름 필요 (예: ${1}_lane_detector)"}
lang=${3:-python}

if ! python3 scripts/teams.py list | grep -qx "$team"; then
  echo "알 수 없는 팀: $team"; python3 scripts/teams.py list; exit 1
fi

case "$lang" in
  python) build_type=ament_python; deps=(rclpy anjabom_interfaces) ;;
  cpp)    build_type=ament_cmake;  deps=(rclcpp anjabom_interfaces) ;;
  *) echo "언어는 python 또는 cpp"; exit 1 ;;
esac

# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"
mkdir -p "src/$team"
cd "src/$team"
ros2 pkg create "$name" --build-type "$build_type" --license Apache-2.0 \
  --dependencies "${deps[@]}"
echo "✅ src/$team/$name 생성 완료"
