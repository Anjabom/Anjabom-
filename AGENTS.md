# AGENTS.md - AI 코딩 도구 공용 지침

이 파일은 이 저장소에서 일하는 **모든 AI 코딩 도구**(Claude Code, OpenAI Codex, Grok Build 등)가 읽는 규칙의 원본이다.
`CLAUDE.md` 는 이 파일을 가져오기만 한다. 도구별 설정 파일에 규칙을 따로 쓰지 말고 여기에만 쓴다.
(사람용 상세 문서: `docs/GUIDE.md`, `docs/CONTRIBUTING.md`, `docs/AI_TOOLS.md`)

## 프로젝트
- 자율주행 차량: **ROS2 Humble + Ubuntu 22.04 + Python 3.10**(일부 C/C++) + Arduino
- 4개 팀이 한 저장소를 쓴다. 팀과 담당 폴더는 아래 표와 `config/teams.yml` 이 기준이다.
- **작업할 팀 폴더의 `AGENTS.md` 를 반드시 먼저 읽는다.** (예: `src/camera/AGENTS.md`) 팀별 규칙이 이 파일보다 우선한다.

<!-- BEGIN TEAMS (scripts/teams.py sync 가 생성) -->
| 팀 id | 이름 | 담당 폴더 | 설명 |
|---|---|---|---|
| `camera` | 카메라 | `src/camera/` | 카메라 기반 인지 (차선/객체/신호 인식) |
| `gps` | GPS | `src/gps/` | GPS/IMU 기반 측위 및 경로 |
| `lidar` | 라이다 | `src/lidar/` | 라이다 기반 인지 (장애물/거리) |
| `control` | 제어 | `src/control/`, `firmware/` | 판단/제어 및 아두이노 펌웨어 |
<!-- END TEAMS -->

공용 영역: `src/interfaces/`(팀 간 메시지 계약), `src/bringup/`(통합 런치), `config/`, `.github/`, `.devcontainer/`

## 반드시 지킬 것
1. **ROS2 Humble API 만 사용한다.** ROS1(`rospy`, `roscpp`, `catkin`) 금지. Jazzy 이후 전용 기능 금지. 노드는 `rclpy`/`rclcpp`, 빌드는 `colcon`, Python 패키지는 `ament_python`, C++ 은 `ament_cmake`.
2. **명령은 공용 개발 컨테이너 안에서 실행한다** (`/ws` 가 저장소 루트). 윈도우 PowerShell 등 호스트에서 빌드/테스트를 돌리지 않는다. 컨테이너 밖이라면 사용자에게 알린다.
3. **요청받은 팀 폴더 안에서만 수정한다.** 다른 팀 폴더, `src/interfaces/`, `src/bringup/`, `.github/`, `.devcontainer/`, `requirements*.txt` 는 사용자가 명시적으로 요청한 경우에만 바꾼다.
4. **자동 생성 파일은 직접 고치지 않는다**: `.github/CODEOWNERS`, `.github/labeler.yml`, `.github/labels.json`, `.github/teams.json`, `.github/release.yml`, 각 폴더의 `CLAUDE.md`, 이 파일의 팀 표. → `config/teams.yml` 수정 후 `python3 scripts/teams.py sync`.
5. **팀 간 메시지는 `src/interfaces/anjabom_interfaces/msg/` 에만 정의**하고, 기존 필드는 삭제/이름변경/타입변경하지 않는다(추가만). 바꿔야 하면 코드를 고치기 전에 사용자에게 "인터페이스 변경 요청 이슈" 가 필요하다고 알린다.
6. **비밀값 금지**: API 키, 토큰, 비밀번호를 코드·설정·로그·커밋 메시지에 쓰지 않는다. 환경 변수로 받는다.
7. **의존성 추가**: apt/ROS 패키지는 해당 패키지의 `package.xml`, pip 는 `requirements.txt` 에 `이름==버전` 으로. `apt install`/`pip install` 을 직접 실행해 해결하고 끝내지 않는다.
8. 하드코딩 대신 ROS 파라미터(`declare_parameter`)와 `config/*.yaml` 을 쓴다. 각 노드는 `/system/status` 에 `anjabom_interfaces/NodeStatus` 하트비트를 1Hz 이상 발행한다.
9. 테스트를 지우거나 건너뛰게 만들어서 통과시키지 않는다.

## 빌드 / 테스트 (컨테이너 안)
```bash
./scripts/check.sh <팀id>            # 스타일 + 해당 팀 패키지 빌드/테스트 (PR 전 필수)
colcon build --symlink-install --packages-select <패키지>
colcon test --packages-select <패키지> && colcon test-result --verbose
pre-commit run --all-files           # 스타일만
./scripts/new_package.sh <팀id> <패키지> python|cpp   # 새 패키지
```
- 빌드/테스트를 실행할 수 없는 환경(클라우드 에이전트 등)이면 PR 본문의 "테스트 방법"에 **실행하지 못했다고 명시**한다.

## Git / PR 규칙
- `main` 에 직접 커밋/푸시하지 않는다. 브랜치: `<팀id>/<이슈번호>-<짧은-설명>` (예: `camera/12-lane-offset`). 시작은 `./scripts/start_task.sh <팀id> <이슈> <설명>`.
- 커밋 메시지: `<팀id>: <무엇을 했는지> (#이슈번호)` - 한국어 가능.
- `git commit --no-verify`, `git push --force` 를 쓰지 않는다. pre-commit 이 파일을 고치면 `git add` 후 다시 커밋.
- PR 은 `.github/pull_request_template.md` 를 채운다: `Closes #이슈`, 테스트 방법, 다른 팀 영향, **사용한 AI 도구 체크**.
- PR 하나는 이슈 하나, 변경 400줄 이하를 목표로 한다. 크면 나눈다.
- 최종 책임과 리뷰는 사람이 한다. AI 는 PR 을 승인하거나 병합하지 않는다.

## 코드 스타일
- Python: ruff (`pyproject.toml`, 줄 길이 120), 타입 힌트 권장. C/C++/Arduino: clang-format (Google, 120).
- 로그는 `self.get_logger()` 사용, `print` 금지(스크립트 제외).
- 주석/문서는 한국어 가능. 식별자는 영어.
