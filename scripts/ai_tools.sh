#!/usr/bin/env bash
# 공용 개발 컨테이너 안에 AI 코딩 도구(Claude Code, Codex, Grok Build)를 설치/확인한다.
# AI 가 실행하는 빌드·테스트도 컨테이너(=본체 기준 환경) 안에서 돌게 하기 위함.
#
#   ./scripts/ai_tools.sh install [도구...]   설치 (이미 있으면 건너뜀). 기본: $ANJABOM_AI_TOOLS 또는 전부
#   ./scripts/ai_tools.sh status              설치/로그인 상태
#
# 실행 파일(~/.local)과 로그인 정보(~/.ai-config)는 Docker 볼륨에 있어 컨테이너를 다시 만들어도 유지된다.
set -uo pipefail

AI_CONFIG="${HOME}/.ai-config"
BIN="${HOME}/.local/bin"
ALL_TOOLS="claude codex grok"

declare -A INSTALL_URL=(
  [claude]="https://claude.ai/install.sh"
  [codex]="https://chatgpt.com/codex/install.sh"
  [grok]="https://x.ai/cli/install.sh"
)
declare -A INSTALL_SHELL=([claude]=bash [codex]=sh [grok]=bash)

prepare_dirs() {
  mkdir -p "$BIN" "$AI_CONFIG/claude" "$AI_CONFIG/codex" "$AI_CONFIG/grok"
  # Grok 은 설정 위치를 바꾸는 환경 변수가 없어 ~/.grok 을 볼륨 안으로 연결한다
  if [ -d "$HOME/.grok" ] && [ ! -L "$HOME/.grok" ]; then
    cp -a "$HOME/.grok/." "$AI_CONFIG/grok/" && rm -rf "$HOME/.grok"
  fi
  [ -L "$HOME/.grok" ] || ln -s "$AI_CONFIG/grok" "$HOME/.grok"
}

# 설치 스크립트가 PATH 밖에 설치했으면 ~/.local/bin 에 연결
link_binary() {
  local name=$1 found
  command -v "$name" >/dev/null && return 0
  found=$(find "$HOME/.local" "$AI_CONFIG" -maxdepth 5 -type f -name "$name" -perm -u+x 2>/dev/null | head -n1)
  [ -n "$found" ] && ln -sf "$found" "$BIN/$name"
  command -v "$name" >/dev/null
}

install_tool() {
  local name=$1
  if command -v "$name" >/dev/null; then
    echo "  ✅ $name 이미 설치됨 ($("$name" --version 2>/dev/null | head -n1))"
    return 0
  fi
  echo "  ▶ $name 설치 중..."
  if curl -fsSL "${INSTALL_URL[$name]}" | "${INSTALL_SHELL[$name]}" >/dev/null 2>&1 && link_binary "$name"; then
    echo "  ✅ $name 설치 완료"
  else
    echo "  ⚠️  $name 설치 실패 (네트워크 확인 후 ./scripts/ai_tools.sh install $name)"
    return 1
  fi
}

status() {
  for name in $ALL_TOOLS; do
    if command -v "$name" >/dev/null; then
      echo "  ✅ $name $("$name" --version 2>/dev/null | head -n1)"
    else
      echo "  ·  $name 미설치"
    fi
  done
  echo "  로그인 정보 위치: $AI_CONFIG (볼륨, 컨테이너 재생성 후에도 유지)"
}

case "${1:-status}" in
  install)
    shift
    prepare_dirs
    tools="${*:-${ANJABOM_AI_TOOLS:-$ALL_TOOLS}}"
    [ "$tools" = none ] && { echo "AI 도구 설치 건너뜀 (ANJABOM_AI_TOOLS=none)"; exit 0; }
    rc=0
    for name in $tools; do
      if [ -z "${INSTALL_URL[$name]:-}" ]; then echo "알 수 없는 도구: $name ($ALL_TOOLS)"; rc=1; continue; fi
      install_tool "$name" || rc=1
    done
    exit $rc ;;
  status) status ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac
