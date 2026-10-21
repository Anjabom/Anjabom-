#!/usr/bin/env bash
# VS Code 없이 공용 개발 컨테이너(본체 노트북과 동일한 환경)에 들어간다.
# 본체 노트북에서 차량을 실행할 때도 이 스크립트를 쓰면 모든 PC 와 같은 환경이 된다.
#
#   ./scripts/dev.sh                 컨테이너 셸 (이미 떠 있으면 그 안으로 들어감)
#   ./scripts/dev.sh --hw            + 센서/아두이노(USB) 접근
#   ./scripts/dev.sh --match-target  + CPU/RAM 을 본체 노트북 사양으로 제한
#   ./scripts/dev.sh --pull          최신 공용 이미지 받기
#   ./scripts/dev.sh -- <명령>       명령만 실행 (예: -- ros2 launch mad_bringup system.launch.py)
#   ./scripts/dev.sh -- claude       AI 도구를 컨테이너 안에서 실행 (처음 한 번: -- ./scripts/ai_tools.sh install)
set -euo pipefail
cd "$(dirname "$0")/.."

image=$(sed -n 's/^[[:space:]]*"image": "\(.*\)",*$/\1/p' .devcontainer/devcontainer.json)
name="${DEV_NAME:-mad-dev-${USER:-dev}}"
tty=(-i); [ -t 0 ] && tty=(-it)   # CI 처럼 터미널이 없으면 -t 제외
args=(--rm "${tty[@]}" --name "$name" --network host --ipc host
      -v "$PWD:/ws" -w /ws
      -e "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}" -e "DISPLAY=${DISPLAY:-}"
      -v /tmp/.X11-unix:/tmp/.X11-unix
      # AI 코딩 도구 (devcontainer 와 같은 볼륨 → 한 번 로그인하면 공유)
      -v mad-ai-bin:/home/ubuntu/.local -v mad-ai-config:/home/ubuntu/.ai-config
      -e ANTHROPIC_API_KEY -e OPENAI_API_KEY -e XAI_API_KEY)
cmd=(bash)

while [ $# -gt 0 ]; do
  case "$1" in
    --hw) args+=(--privileged -v /dev:/dev) ;;
    --match-target)
      cores=$(sed -n 's/^  cpu_cores: \([0-9]*\)$/\1/p' config/target_env.yml)
      ram=$(sed -n 's/^  ram_gb: \([0-9]*\).*$/\1/p' config/target_env.yml)
      if [ -z "$cores" ]; then echo "config/target_env.yml 이 아직 기록되지 않았습니다."; exit 1; fi
      args+=(--cpus "$cores" --memory "${ram}g")
      echo "본체 사양으로 제한: CPU ${cores}코어, RAM ${ram}GB" ;;
    --pull) docker pull "$image"; exit 0 ;;
    --) shift; cmd=("$@"); break ;;
    *) sed -n '2,10p' "$0"; exit 1 ;;
  esac
  shift
done

if docker ps --format '{{.Names}}' | grep -qx "$name"; then
  exec docker exec "${tty[@]}" "$name" "${cmd[@]}"
fi
if command -v xhost >/dev/null && [ -n "${DISPLAY:-}" ]; then
  xhost +local: >/dev/null 2>&1 || true   # 컨테이너의 GUI(rviz2) 허용
fi
exec docker run "${args[@]}" "$image" "${cmd[@]}"
