# 통합 개발 시스템 사용 설명서

이 문서 하나로 전체 흐름을 이해할 수 있게 정리했습니다. 세부 내용은 각 링크 문서를 참고하세요.

## 0. 전체 그림

```
 ┌──────────── 개발 (어느 PC 든 같은 환경) ────────────┐        ┌──────── GitHub (Organization) ────────┐
 │ 윈도우(WSL2) / 우분투 / 본체 노트북                 │  push  │ PR ─▶ CI(변경 팀만 빌드·테스트)        │
 │   └─ 공용 개발 컨테이너 (Ubuntu22.04+Humble, 고정)  │ ─────▶ │    ─▶ 코드 오너(해당 팀) 리뷰          │
 │       colcon build / test / ros2 launch            │        │    ─▶ main 병합 (Squash)               │
 └────────────────────────────────────────────────────┘        │ 이슈 + Projects 보드 = 누가 무엇을    │
                                                                │ 야간 전체 빌드 / 오래된 PR 경보        │
 ┌──────── 본체 노트북 (차량) ────────┐   실기 테스트 버튼     │ 공용 이미지(GHCR) 자동 빌드            │
 │ self-hosted runner + 센서/아두이노  │ ◀──────────────────── │ 릴리스 태그(v0.x.y) = 기준 버전        │
 └────────────────────────────────────┘                        └──────────────┬─────────────────────────┘
                                                                              │ 매주 월 / 매월 1일
                                                                              ▼
                                                                  노션 "작업 기록" 데이터베이스
```

| 원래 문제 | 이 시스템의 해결 |
|---|---|
| 같은 저장소를 받아도 버전이 다름 | 모든 PC 가 **같은 공용 이미지**에서 개발 + 릴리스 태그로 기준 버전 고정 |
| 윈도우/저사양 PC 때문에 OS·환경이 다름 | WSL2 안에서 같은 컨테이너, 본체 사양 기록·비교·제한, 본체 실기 테스트 |
| 합칠 때 병목 | 작은 PR 을 자주 병합, 인터페이스 계약, 변경 범위 CI, 야간 통합 빌드, 뒤처진 PR 경보 |
| 누가 무엇을 하는지 모름 | 이슈 → 브랜치 → PR 자동 연결, 보드, 주간·월간 리포트 (GitHub + 노션) |

---

## 1. 관리자: 처음 한 번 (약 1~2시간)

| 순서 | 할 일 | 문서 |
|---|---|---|
| 1 | Organization 생성, 저장소 이전, 팀원 초대, 팀 6개 생성 | [ORG_SETUP.md 1~3](ORG_SETUP.md) |
| 2 | `config/teams.yml` 에 org 이름 → `teams.py sync` → PR 병합 → 라벨 동기화 실행 | [ORG_SETUP.md 4](ORG_SETUP.md) |
| 3 | main 보호 규칙(Ruleset), Squash 병합 설정 | [ORG_SETUP.md 5](ORG_SETUP.md) |
| 4 | Projects 보드 생성과 자동화 | [ORG_SETUP.md 6](ORG_SETUP.md) |
| 5 | 공용 개발 이미지 빌드 → Public 으로 공개 | [ORG_SETUP.md 7](ORG_SETUP.md) |
| 6 | 본체 노트북: Docker 설치, `--capture` 로 기준 환경 기록, 러너 등록 | [TARGET_ENV.md](TARGET_ENV.md) |
| 7 | 노션 통합 토큰과 데이터베이스 ID 등록 | [NOTION.md](NOTION.md) |
| 8 | 팀원별 `ROS_DOMAIN_ID` 배정표 공유 | [TEAM_GUIDE.md](TEAM_GUIDE.md#ros_domain_id-배정) |

## 2. 새 팀원 / 새 노트북에 적용하기 (약 30~60분)

1. GitHub 계정을 만들고, Organization 초대 메일을 수락합니다.
2. 자기 OS 에 맞게 설치합니다: [윈도우](DEV_ENV.md#윈도우-노트북) / [우분투](DEV_ENV.md#우분투-노트북)
   - 핵심: Docker 와 VS Code 를 설치하고, 저장소를 clone 한 뒤 **Reopen in Container** 를 누릅니다.
3. 컨테이너 터미널에서 확인합니다.
   ```bash
   python3 scripts/env_check.py          # "✅ 소프트웨어 환경이 본체와 일치" 가 나오면 성공
   ./scripts/check.sh                    # 스타일·빌드·테스트 통과 확인
   ```
4. [CONTRIBUTING.md](CONTRIBUTING.md) 를 읽습니다 (10분).

> 노트북을 바꾸거나 포맷해도 2~3단계만 다시 하면 됩니다. 개발 환경은 전부 이미지와 저장소 안에 있으므로, 따로 설치하거나 기억해야 할 것이 없습니다.

## 3. 하루 작업 예시: 카메라 팀 A 가 "차선 중심 오프셋" 기능 개발

```bash
# (GitHub) Issues → New issue → ✨ 기능 개발 → 담당 팀: camera → #12 생성, Assignee = 나
#          → 보드에 자동 등록, team:camera 라벨 자동 부여

./scripts/start_task.sh camera 12 lane-offset        # 최신 main 에서 camera/12-lane-offset 브랜치
./scripts/new_package.sh camera camera_lane python   # (처음이면) 패키지 생성

# ... 코드 작성 ...  센서가 없으면: ros2 bag play <공유 드라이브의 bag> --loop
colcon build --symlink-install --packages-select camera_lane
source install/setup.bash && ros2 run camera_lane lane_node

git add -p && git commit -m "camera: 차선 중심 오프셋 계산 (#12)"
git push -u origin HEAD          # → 출력된 링크로 Draft PR 생성, 본문에 "Closes #12"
```

다음 날:
```bash
./scripts/sync_main.sh           # 다른 팀이 병합한 것을 받아와 충돌을 작게 유지
# ... 마무리 ...
./scripts/check.sh camera        # CI 와 같은 검사
git push                         # PR → Ready for review
```
- 카메라 팀원이 리뷰·승인하고 `CI 통과` 가 뜨면 **Squash and merge** 합니다. 이슈 #12 가 자동으로 닫히고 보드에서 Done 으로 이동합니다.
- 성능이 중요한 변경이면 병합 전에 **Actions → 본체 노트북 실기 테스트** 를 내 브랜치로 실행해 봅니다.

## 4. 팀 간 협업 예시: 카메라 → 제어로 새 메시지 전달

1. 카메라 팀이 `🔌 인터페이스 변경 요청` 이슈를 만듭니다: `LaneInfo.msg` 추가 (offset, curvature).
2. 제어 팀이 이슈에서 필드를 확인하고 👍 를 남깁니다.
3. `shared/15-lane-info-msg` 브랜치에서 `src/interfaces/anjabom_interfaces/msg/LaneInfo.msg` 와 `CMakeLists.txt`, README 표만 바꾼 PR 을 올립니다. 모든 팀이 자동으로 멘션되고, `leads` 가 승인하면 병합합니다.
4. 이후 카메라 팀(발행)과 제어 팀(구독)이 각자 자기 폴더에서 독립적으로 PR 을 올립니다. 메시지가 먼저 main 에 들어가 있으므로 서로 기다릴 필요가 없습니다.

## 5. 통합과 차량 실행

| 언제 | 무엇을 | 어떻게 |
|---|---|---|
| 매일 새벽 | main 전체 빌드·테스트 | 자동 (Nightly). 실패하면 `🚨` 이슈가 생성됨 |
| 팀 기능 준비되면 | 통합 런치에 추가 | `system.launch.py` 의 `TEAM_LAUNCHES` 에 한 줄 추가하는 PR |
| 수시로 | 본체 하드웨어에서 검증 | Actions → 본체 노트북 실기 테스트 → 브랜치 선택 |
| 주 1회 (예: 금요일) | 기준 버전 만들기 | Actions → 버전 릴리스 → minor. 코드와 개발 이미지에 같은 태그가 붙음 |
| 차량 테스트·시연·대회 | 태그 버전으로 실행 | 본체: `git switch --detach v0.3.0` → `./scripts/dev.sh --hw ...` ([DEV_ENV.md](DEV_ENV.md#본체-노트북)) |

## 6. 진행 상황 보기 / 기록

| 무엇 | 어디서 |
|---|---|
| 지금 누가 무엇을 하는지 | GitHub Projects 보드 → `담당자별` 뷰 |
| 팀별 상황 | 보드 → `팀별` 뷰, 또는 Issues 에서 `label:team:camera` |
| 지난주 결과 (월요일 회의) | `📊 주간 리포트` 이슈 / 노션 `작업 기록` |
| 지난달 결과 (월간 회고) | `📅 월간 리포트` 이슈 / 노션 `작업 기록` (유형: 월간) |
| 막힌 작업 | `status:blocked` 라벨, 리포트의 ⛔ 항목. 회의에서 가장 먼저 다룹니다 |
| 파일을 누가 언제 바꿨나 | GitHub 파일 화면 → History / Blame |

**회의 추천 순서 (주 1회, 20분)**: 주간 리포트 화면 공유 → ⛔ 막힌 작업 해결 → 오래된 PR(`status:stale`) 정리 → 다음 주 이슈 배정 → (필요하면) 릴리스 실행

## 7. 바뀔 때

| 상황 | 할 일 |
|---|---|
| 팀 이름/역할/인원 변경 | GitHub 팀 수정 → `config/teams.yml` 수정 → `python3 scripts/teams.py sync` → PR ([TEAM_GUIDE.md](TEAM_GUIDE.md#팀-구성-변경하기)) |
| 새 pip/apt 의존성 | `requirements.txt` 또는 `package.xml` 에 추가 → PR 병합 → 이미지 자동 재빌드 → 모두 Rebuild Container |
| 본체 노트북 교체·업그레이드 | 새 본체에서 `--capture` → PR, 러너 재등록 |
| ROS 배포판 변경 | [DEV_ENV.md - ROS 배포판을 바꿀 때](DEV_ENV.md#ros-배포판을-바꿀-때-관리자) |

## 8. 자동화 한눈에 보기

| 워크플로 | 언제 | 하는 일 |
|---|---|---|
| CI | PR, main push | 스타일 검사, 변경된 팀 패키지만 빌드·테스트, 아두이노 컴파일 → `CI 통과` |
| PR 자동화 | PR 열림/수정 | 팀 라벨, 규칙 안내 댓글, 공용 영역 변경 시 전 팀 멘션, 보드 등록 |
| 이슈 자동화 | 이슈 생성 | 양식의 팀 선택으로 라벨, 보드 등록 |
| PR 상태 점검 | 평일 08:43 | 3일 넘은 PR, main 보다 20커밋 뒤처진 PR 경보 |
| Nightly 통합 빌드 | 매일 03:17 | main 전체 빌드, 실패 시 이슈 생성/복구 시 닫기 |
| 공용 개발 이미지 | 의존성 변경 병합 시 | 이미지 빌드 → GHCR |
| 본체 노트북 실기 테스트 | 수동 | 본체에서 빌드·테스트·통합 실행 |
| 진행 리포트 | 월 09:07, 매월 1일 09:13 | 주간/월간 리포트 → GitHub 이슈 + 노션 |
| 버전 릴리스 | 수동 | CI 확인 → 태그·릴리스 노트, 이미지 태그 |
| 라벨 동기화 | teams.yml 변경 병합 시 | 라벨 생성/갱신 |
