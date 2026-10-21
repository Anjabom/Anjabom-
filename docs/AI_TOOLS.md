# AI 코딩 도구 사용 규칙 (Claude Code · Codex · Grok)

팀원마다 다른 AI 도구를 써도 **결과물은 같은 규칙과 같은 환경**을 거치도록 만든 구조입니다.

## 한눈에 보기

| 원칙 | 어떻게 보장하나 |
|---|---|
| 모든 AI 가 같은 규칙을 안다 | 규칙 원본은 루트 `AGENTS.md` 하나. 팀별 규칙은 `src/<팀>/AGENTS.md`. `CLAUDE.md` 는 `@AGENTS.md` 만 가져온다 (자동 생성) |
| AI 가 돌리는 빌드/테스트도 본체와 같은 환경 | AI 도구를 **공용 개발 컨테이너 안에** 설치해서 실행 (`scripts/ai_tools.sh`) |
| AI 가 규칙을 어겨도 main 은 안전 | 강제 장치는 도구와 무관한 곳에: pre-commit 훅, CI, 코드 오너 리뷰, main 보호 |
| 누가 어떤 AI 로 무엇을 했는지 보인다 | PR 템플릿 체크 + 커밋 트레일러 → `ai:claude`/`ai:codex`/`ai:grok` 라벨 → 주간·월간 리포트(GitHub, 노션)에 집계 |
| 책임은 사람에게 | PR 을 올린 사람이 AI 코드를 읽고 이해할 책임. 리뷰·승인·병합은 사람만 |
| 비밀값 유출 방지 | pre-commit `API 키/토큰 커밋 차단` 훅 + GitHub Push protection |

## 도구별로 읽는 지침 파일

| 도구 | 읽는 파일 | 비고 |
|---|---|---|
| **OpenAI Codex** | `AGENTS.md` (루트 → 현재 폴더까지) | 기본 크기 한도 32KiB. 루트 파일은 짧게 유지 |
| **Grok Build** | `AGENTS.md`, `CLAUDE.md` (루트 → 현재 폴더까지) | 둘 다 읽는다. `CLAUDE.md` 는 한 줄뿐이라 중복 없음 |
| **Claude Code** | `CLAUDE.md` → `@AGENTS.md` 가져옴. 팀 폴더 파일을 열면 그 폴더의 `CLAUDE.md` 도 로드 | `CLAUDE.md` 가 있으면 기본 설정에서 `AGENTS.md` 를 직접 읽지 않으므로 import 방식을 쓴다 |

- 루트 `AGENTS.md` 에는 "작업할 팀 폴더의 `AGENTS.md` 를 먼저 읽어라" 는 지시가 있어, 저장소 루트에서 실행해도 팀 규칙을 찾아 읽습니다.
- **규칙을 바꿀 때는 `AGENTS.md` 만 고칩니다.** `CLAUDE.md` 와 팀 표는 `python3 scripts/teams.py sync` 가 관리합니다 (CI 가 동기화 검사).
- 도구 전용 설정(`.claude/`, `~/.codex/config.toml`, `.grok/rules/`)에 팀 규칙을 넣지 않습니다. 그 도구를 안 쓰는 사람에게는 적용되지 않기 때문입니다. 개인 취향 설정은 괜찮습니다 (`CLAUDE.local.md`, `AGENTS.override.md` 등은 `.gitignore` 처리됨).

### 팀 규칙 채우기 (팀 리더)
`src/<팀>/AGENTS.md` 의 "팀 규칙" 에 AI 가 자주 틀리는 것을 적습니다. 예:
```markdown
## 팀 규칙
- 입력: /camera/image_raw (sensor_msgs/Image, 640x480, 30Hz). 출력: /lane_info (anjabom_interfaces/LaneInfo)
- 좌표계: 차량 기준 x 전방, y 좌측, 단위 m / rad
- OpenCV 는 cv_bridge 로 변환. 이미지 처리 루프에서 동적 메모리 할당 금지
- 파라미터는 config/camera.yaml 에서만 조정
```

## 설치와 로그인 (공용 컨테이너 안)

컨테이너를 처음 만들 때 `scripts/setup.sh` 가 세 도구를 자동으로 설치합니다.
```bash
./scripts/ai_tools.sh status            # 설치 상태
./scripts/ai_tools.sh install codex     # 특정 도구만 설치/재설치
```
- 일부만 쓰려면 호스트에서 `export ANJABOM_AI_TOOLS="claude"` (없으면 `none`) 후 컨테이너를 다시 만듭니다.
- **로그인은 컨테이너 터미널에서 한 번만** 합니다. 실행 파일과 로그인 정보는 Docker 볼륨(`anjabom-ai-bin`, `anjabom-ai-config`)에 저장돼서 Rebuild Container 후에도 유지되고, `./scripts/dev.sh` 와도 공유됩니다.

| 도구 | 실행 / 로그인 | API 키로 쓰려면 (호스트에서 export 후 컨테이너 재생성) |
|---|---|---|
| Claude Code | `claude` → 브라우저 로그인 안내를 따름 | `ANTHROPIC_API_KEY` |
| Codex | `codex` → "Sign in with ChatGPT" | `OPENAI_API_KEY` |
| Grok Build | `grok` → 브라우저에서 grok.com 로그인 | `XAI_API_KEY` |

### VS Code 확장(Claude Code, Codex 등)을 쓸 때
**Reopen in Container 상태에서 확장을 설치**하면 확장이 컨테이너 안에서 동작합니다 (VS Code 가 "컨테이너에 설치" 버튼을 보여 줍니다). 윈도우 VS Code 에 로컬로 설치된 확장은 윈도우에서 명령을 실행하므로 쓰지 않습니다.

### 윈도우 사용자 주의
PowerShell 이나 CMD 에서 `claude`/`codex`/`grok` 을 실행하면 AI 가 **윈도우에서** 빌드와 테스트를 돌립니다. 본체와 환경이 달라지므로 반드시 컨테이너 터미널(VS Code 터미널, 또는 WSL 에서 `./scripts/dev.sh -- claude`)에서 실행합니다.

## 클라우드 에이전트 (Codex 클라우드, Claude Code 웹 등)

브라우저에서 저장소를 맡겨 PR 을 받는 방식도 쓸 수 있지만 한계가 있습니다.
- 각 서비스의 자체 컨테이너에서 실행되므로 **ROS2 Humble 빌드를 못 해 봤을 수 있습니다.** → 그런 PR 은 반드시 CI(`CI 통과`)와 코드 오너 리뷰를 거치고, 하드웨어 관련이면 본체 실기 테스트를 돌립니다.
- 브랜치 이름이 `codex/...`, `claude/...` 처럼 정해지는 경우 그대로 허용하고 `ai:*` 라벨이 붙습니다. 팀 라벨은 변경 경로로 붙습니다.
- PR 본문의 "AI 도구 사용" 과 "테스트 방법" 은 PR 을 연 사람이 직접 채웁니다.

## 함께 쓸 때 피해야 할 것
- **한 이슈 = 한 브랜치 = 한 담당자.** 같은 파일을 여러 AI 로 동시에 고치지 않습니다.
- AI 에게 "전체 리팩터링", "모든 파일 정리" 같은 넓은 작업을 시키지 않습니다. 다른 팀 폴더까지 바뀌어 리뷰와 병합이 막힙니다 (코드 오너 승인 필요).
- AI 가 `--no-verify`, `--force`, 테스트 삭제로 문제를 "해결" 하지 않게 합니다 (`AGENTS.md` 에 금지 명시, CI 가 다시 검사).
- AI 출력에 키·토큰을 붙여 넣지 않습니다. 붙여 넣었다면 즉시 키를 폐기(재발급)합니다.

## AI 사용 기록
- PR 템플릿의 **AI 도구 사용** 에 체크합니다. 커밋에 `Co-Authored-By: Claude ...` 같은 트레일러가 있으면 자동으로도 감지합니다.
- AI 를 사용했는데 "직접 읽고 이해했다" 항목이 비어 있으면 PR 안내 댓글이 알려 줍니다.
- 주간·월간 리포트와 노션 `작업 기록` 의 **AI 활용 PR** 에 도구별 병합 PR 수가 집계됩니다.
