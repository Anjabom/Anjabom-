#!/usr/bin/env bash
# 본체 노트북 실기 테스트 (공용 컨테이너 안에서 실행). .github/workflows/vehicle-test.yml 이 호출한다.
# 직접 실행: ./scripts/dev.sh --hw -- ./scripts/vehicle_test.sh 20
set -eo pipefail
duration=${1:-20}

# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"
echo "▶ 환경 비교"
python3 scripts/env_check.py || true

echo "▶ 빌드 / 테스트"
colcon build --event-handlers console_cohesion+
colcon test --event-handlers console_cohesion+
colcon test-result --verbose

echo "▶ 통합 실행 ${duration}초 (system.launch.py)"
# shellcheck disable=SC1091
source install/setup.bash
set +e
timeout --signal=INT "${duration}" ros2 launch anjabom_bringup system.launch.py
rc=$?
set -e
# timeout 으로 끝난 것(124)이 정상: 그 전에 죽었다면 실패
if [ "$rc" -ne 124 ]; then
  echo "❌ 통합 실행이 ${duration}초 전에 종료됨 (exit $rc)"; exit 1
fi
echo "✅ 본체 실기 테스트 통과"
