# Anjabom 자율주행

ROS2 Humble (Ubuntu 22.04) + Python/C++ + Arduino 기반 자율주행 프로젝트입니다.
카메라 · GPS · 라이다 · 제어 4개 팀(팀당 약 4명)이 **하나의 저장소**에서 함께 개발합니다.

## 이 저장소의 팀 개발 시스템

| 문제 | 해결 장치 |
|---|---|
| 같은 저장소를 받아도 사람마다 버전/환경이 다름 | 모든 PC 가 GHCR 의 **같은 공용 개발 이미지**(Ubuntu 22.04 + Humble, 의존성 고정)를 사용, 릴리스 태그로 기준 버전 표시 |
| 윈도우·사양이 다른 노트북 | WSL2 안에서 같은 컨테이너, 본체 노트북 사양 기록·비교(`env_check.py`)·자원 제한, rosbag 재생, 본체 실기 테스트 러너 |
| 팀/팀원 결과물을 합칠 때 병목 | 작은 PR 을 자주 병합 (main 보호), 팀 간 메시지를 `src/interfaces` 에 계약으로 관리, PR 마다 변경 범위만 빠르게 검사하는 CI, 야간 전체 통합 빌드, 뒤처진 PR 조기 경보 |
| 여러 AI 도구(Claude Code, Codex, Grok) 혼용 | 공용 지침 `AGENTS.md`(+팀별), AI 도구를 컨테이너 안에서 실행, `ai:*` 라벨과 리포트 집계, 비밀값 커밋 차단 |
| 누가 언제 무엇을 하는지 모름 | 이슈 → 브랜치 → PR 연결 규칙, 팀 라벨 자동 부여, Projects 보드, 주간·월간 리포트 자동 생성 (GitHub 이슈 + 노션) |

## 시작하기

**처음이라면 [docs/GUIDE.md](docs/GUIDE.md) (사용 설명서) 부터 읽으세요.**

| 누구 | 읽을 문서 |
|---|---|
| **새 노트북 / 새 팀원** | [docs/DEV_ENV.md](docs/DEV_ENV.md) - 윈도우·우분투·본체 노트북별 설치 |
| **관리자** (처음 한 번) | [docs/ORG_SETUP.md](docs/ORG_SETUP.md) - Organization, 팀, 브랜치 보호, 프로젝트 보드 설정 |
| **모든 팀원** | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) - 이슈 → 브랜치 → PR 흐름 |
| **본체 노트북 담당** | [docs/TARGET_ENV.md](docs/TARGET_ENV.md) - 기준 환경, 실기 테스트 |
| **노션 기록** | [docs/NOTION.md](docs/NOTION.md) |
| **AI 도구 사용자** | [docs/AI_TOOLS.md](docs/AI_TOOLS.md) - Claude Code · Codex · Grok 공용 규칙(`AGENTS.md`), 컨테이너 안 실행 |
| **팀 리더** | [docs/TEAM_GUIDE.md](docs/TEAM_GUIDE.md) - 인터페이스 변경, 팀 구성 변경, 릴리스 |
| **팀 리더 (융합 공동 담당)** | [docs/INTEGRATION.md](docs/INTEGRATION.md) - 센서 팀 출력 융합과 최종 통합 절차 |

### 하루 작업 흐름 요약

```bash
# 1. GitHub 에서 이슈 만들기 (예: #12), Assignee 에 본인 지정
./scripts/start_task.sh camera 12 lane-offset   # 2. 브랜치 생성
# 3. 개발 & 커밋:  git commit -m "camera: 차선 오프셋 계산 (#12)"
./scripts/sync_main.sh                          # 4. 매일 main 받아오기
./scripts/check.sh camera                       # 5. 로컬 검사
git push -u origin HEAD                         # 6. PR 생성 (본문에 Closes #12)
```

## 구조

```
src/camera|gps|lidar|control/   팀별 ROS2 패키지
src/fusion/                     센서 융합·판단 (anjabom_fusion, 팀 리더 공동)
src/interfaces/                 팀 간 공용 메시지 (anjabom_interfaces)
src/bringup/                    통합 런치 + 노드 상태 감시 (anjabom_bringup)
firmware/arduino/               아두이노 스케치
config/teams.yml                팀 구성 (여기만 고치면 CODEOWNERS/라벨/템플릿 자동 갱신)
config/target_env.yml           본체 노트북 기준 환경 (env_check.py --capture)
AGENTS.md, CLAUDE.md            AI 코딩 도구 공용 지침 (팀 폴더마다 하나씩)
scripts/                        개발 도우미
.github/                        CI, 자동화, 이슈/PR 템플릿
.devcontainer/                  공용 개발 환경
```

## 실행

```bash
# 공용 컨테이너 안에서
colcon build --symlink-install && source install/setup.bash
ros2 launch anjabom_bringup system.launch.py
```
