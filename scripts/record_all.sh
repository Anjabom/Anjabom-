#!/usr/bin/env bash
# 본체 노트북에서 모든 센서 팀 출력을 한 번에 rosbag 으로 녹화한다 (공용 컨테이너 안에서 실행).
# 녹화한 bag 은 센서가 없는 PC 에서 융합/제어 개발과 통합 테스트에 쓴다.
#
#   ./scripts/record_all.sh [이름]        예) ./scripts/record_all.sh drive_school_loop
#
# 녹화 토픽: src/fusion/mad_fusion/config/fusion_inputs.yaml 의 입력 + /tf /tf_static /system/status
#           + 환경 변수 EXTRA_TOPICS (공백 구분, 예: "/camera/image_raw /scan")
set -euo pipefail
cd "$(dirname "$0")/.."

name=${1:-drive}_$(date +%Y%m%d_%H%M%S)
mapfile -t topics < <(python3 - <<'PY'
import yaml
data = yaml.safe_load(open("src/fusion/mad_fusion/config/fusion_inputs.yaml", encoding="utf-8")) or {}
for item in data.get("inputs") or []:
    print(item["topic"])
PY
)
read -ra extra <<< "${EXTRA_TOPICS:-}"
topics+=(/tf /tf_static /system/status "${extra[@]}")

echo "녹화: bags/$name"
printf '  %s\n' "${topics[@]}"
mkdir -p bags
# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"
exec ros2 bag record -o "bags/$name" "${topics[@]}"
