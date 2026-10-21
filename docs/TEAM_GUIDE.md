# 팀 간 협업 규칙

## 저장소 구조와 담당

```
src/
├── camera/        카메라 팀 ROS2 패키지
├── gps/           GPS 팀
├── lidar/         라이다 팀
├── control/       제어 팀
├── interfaces/    🔌 팀 간 공용 메시지 (anjabom_interfaces) - 리더 승인 필요
└── bringup/       🚗 전체 통합 런치 + 노드 상태 감시 (anjabom_bringup)
firmware/arduino/  아두이노 스케치 (제어 팀)
config/teams.yml   팀 구성 (단일 진실 공급원)
scripts/           개발 도우미 스크립트
docs/              문서
```

- 담당자는 `.github/CODEOWNERS` 로 정해집니다. 이 파일은 `config/teams.yml` 에서 자동 생성됩니다.
- **다른 팀 폴더를 고쳐야 하면** 그 팀에 이슈를 남기거나, 직접 PR 을 올리고 그 팀의 리뷰를 받습니다. 코드 오너 승인이 필수라서, 그 팀이 모르게 바뀌는 일은 없습니다.

## 팀 간 인터페이스 (가장 중요)

팀끼리는 **토픽 이름과 메시지 타입**으로만 연결됩니다. 이 약속이 지켜지면 각 팀은 따로 개발해도 마지막에 문제없이 붙습니다.

### 규칙
1. 팀 간에 주고받는 커스텀 메시지는 **반드시** `src/interfaces/anjabom_interfaces/msg/` 에 정의합니다. 팀 패키지 안에 따로 만들지 않습니다.
2. 표준 메시지(`sensor_msgs`, `geometry_msgs`, `nav_msgs`)로 충분하면 표준 메시지를 씁니다.
3. 토픽 이름, 타입, 발행/구독 팀을 `src/interfaces/anjabom_interfaces/README.md` 의 표에 기록합니다.
4. **하위 호환을 유지합니다.** 필드는 추가만 하고, 삭제·이름 변경·타입 변경은 하지 않습니다. 꼭 필요하면 새 메시지를 만들고 옛 메시지는 나중에 지웁니다.

### 변경 절차
1. `🔌 인터페이스 변경 요청` 이슈를 생성합니다. 자동으로 `area:shared` 라벨이 붙습니다.
2. 영향 받는 팀이 이슈에 👍 또는 의견을 남깁니다. 리더 회의에서 정해도 됩니다.
3. `shared/<이슈번호>-<설명>` 브랜치에서 메시지만 바꾸는 **작은 PR** 을 올립니다. 모든 팀이 자동으로 멘션됩니다.
4. `leads` 팀이 승인하면 병합합니다. 그다음 각 팀이 자기 코드를 맞추는 PR 을 따로 올립니다.

### 각 노드가 지켜야 할 공통 규칙
- 1초에 한 번 이상 `/system/status` (`anjabom_interfaces/NodeStatus`) 를 발행합니다. `team` 에는 팀 id 를 넣습니다. `system_monitor` 가 노드가 끊기면 경고합니다.
- 파라미터는 코드에 하드코딩하지 말고 `config/*.yaml` 과 `declare_parameter` 로 받습니다.
- 각 팀 패키지에는 `launch/<팀>.launch.py` 를 둡니다. 통합할 준비가 되면 `src/bringup/anjabom_bringup/launch/system.launch.py` 의 `TEAM_LAUNCHES` 에 한 줄을 추가하는 PR 을 올립니다.

## 버전 관리 (모두가 같은 버전을 쓰는 법)

| 무엇 | 어떻게 고정하나 |
|---|---|
| OS / ROS2 | Ubuntu 22.04 + ROS2 Humble. devcontainer(Docker) 이미지가 동일 ([DEV_ENV.md](DEV_ENV.md)) |
| ROS 패키지 의존성 | 각 패키지 `package.xml` 에 적고 `rosdep install` 로 설치. 수동 `apt install` 금지 |
| 개발 도구 | `requirements-dev.txt`, `.pre-commit-config.yaml` 에 버전 고정 |
| 아두이노 | `arduino-cli` 버전은 Dockerfile 과 CI 에, 보드는 `sketch.yaml` 에 고정. 라이브러리는 `sketch.yaml` 의 profiles 사용 |
| 코드 기준점 | 통합 테스트를 통과한 시점에 **Release 태그**(`v0.3.0`)를 만듭니다. 차량 테스트, 시연, 대회 때는 태그 버전을 사용 |

### 릴리스 만들기 (주 1회 권장, 관리자)
**Actions → 버전 릴리스 → Run workflow** 를 실행합니다. main 의 CI 가 통과 상태일 때만 태그가 만들어지고, 팀별로 분류된 릴리스 노트가 자동으로 작성됩니다.

```bash
# 특정 버전으로 차량 실행
git fetch --tags && git switch --detach v0.3.0
colcon build && ros2 launch anjabom_bringup system.launch.py
```

## ROS_DOMAIN_ID 배정

같은 와이파이에 있으면 다른 사람의 토픽이 섞입니다. 사람마다 다른 번호를 씁니다.

| 범위 | 사용 |
|---|---|
| `0` | 실제 차량 (통합 테스트) |
| `10~19` | 카메라 팀 개인 |
| `20~29` | GPS 팀 개인 |
| `30~39` | 라이다 팀 개인 |
| `40~49` | 제어 팀 개인 |

```bash
echo 'export ROS_DOMAIN_ID=12' >> ~/.bashrc   # 본인 번호
```

## 충돌 해결

충돌은 **자주 main 을 받아오면 작게** 끝납니다. (`./scripts/sync_main.sh`)

```bash
./scripts/sync_main.sh
# CONFLICT (content): Merge conflict in src/camera/.../node.py
# 1) 파일을 열어 <<<<<<< ======= >>>>>>> 부분을 정리 (VS Code: "Accept Both/Current/Incoming")
# 2) 정리 후
git add <파일>
git commit                 # 병합 커밋 완료
./scripts/check.sh         # 빌드/테스트 확인
git push
```

- 남의 팀 코드와 충돌했으면 **혼자 결정하지 말고** 그 코드 작성자에게 물어봅니다. `git log -p <파일>` 로 작성자를 찾을 수 있습니다.
- 꼬였으면 병합을 취소합니다: `git merge --abort`
- 공용 브랜치(main 등)에서 `git push --force` 는 금지입니다. 자기 작업 브랜치에서만, 그것도 꼭 필요할 때만 `--force-with-lease` 를 씁니다.

## 팀 구성 변경하기

팀 이름이나 역할은 언제든 바뀔 수 있습니다. **`config/teams.yml` 한 곳만** 고치면 됩니다.

### 예: "라이다" 팀을 "인지(perception)" 팀으로 바꾸기
1. GitHub Organization → Teams 에서 `team-perception` 을 만들거나 기존 팀 이름을 변경하고, 팀원과 저장소 권한을 확인합니다.
2. `config/teams.yml` 을 수정합니다.
   ```yaml
   - id: perception
     name: 인지
     description: 라이다/카메라 융합 인지
     github_team: team-perception
     color: "5319e7"
     paths:
       - src/perception/
   ```
3. 폴더를 옮기고 생성 파일을 갱신합니다.
   ```bash
   git mv src/lidar src/perception
   python3 scripts/teams.py sync
   ./scripts/check.sh
   ```
4. **PR 을 병합하기 전에** GitHub **Issues → Labels** 에서 예전 라벨 `team:lidar` 의 이름을 `team:perception` 으로 바꿉니다. 이렇게 하면 기존 이슈와 PR 에도 새 이름이 그대로 반영됩니다.
5. `chore/<이슈>-rename-team` 브랜치로 PR 을 올리고 병합합니다. 병합하면 라벨 색상과 설명이 자동으로 갱신됩니다.

`scripts/teams.py sync` 가 다시 만드는 파일:
`.github/CODEOWNERS`, `.github/labeler.yml`, `.github/labels.json`, `.github/teams.json`, `.github/release.yml`, 이슈 양식의 팀 선택지

동기화를 잊으면 CI(`팀 설정 동기화 검사`)가 실패하므로 놓칠 일은 없습니다.

## 데이터 (rosbag 등)

- rosbag, 대용량 모델, 데이터셋은 **저장소에 올리지 않습니다** (`.gitignore` 처리됨). 공유 드라이브에 두고 이슈나 PR 에 링크를 남깁니다.
- 1MB 를 넘는 파일은 pre-commit 이 커밋을 막습니다.
