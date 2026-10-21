# 센서 융합과 최종 통합 절차

> 카메라·GPS·라이다 팀이 각자 개발한 코드를 **최종적으로 하나로 융합해 자율주행**하기까지의 과정입니다.
> 융합은 **각 팀 리더가 함께**(`@MAD2027/leads`) 맡습니다.

## 핵심: "새 워크스페이스" 를 만들지 않는다

예전 방식은 팀마다 워크스페이스를 따로 두고, 마지막에 새 워크스페이스로 모아 합쳤습니다. 이 방식은 모으는 순간 버전, 토픽 이름, 좌표계, 시간 기준이 한꺼번에 어긋나는 병목이 생깁니다.

이 저장소는 **처음부터 하나의 colcon 워크스페이스**이고, 팀별 폴더가 각자의 작업 공간 역할을 합니다. 융합은 같은 워크스페이스 안의 **한 계층(`src/fusion`)** 으로 둡니다.

```
src/camera  ─▶ 카메라 출력 ─┐
src/gps     ─▶ GPS 출력 ────┼─▶ src/fusion (융합·판단, 리더 공동) ─▶ 융합 결과 ─▶ src/control ─▶ 아두이노
src/lidar   ─▶ 라이다 출력 ─┘
     ▲ 출력 메시지 형식 = src/interfaces (약속)    ▲ 무엇을 받을지 = fusion_inputs.yaml
```

- 각 팀은 끝까지 **자기 폴더에서 독립적으로** 개발·테스트합니다.
- `colcon build` 한 번이 곧 "융합 워크스페이스" 빌드입니다. 최종 통합 때 파일을 옮기거나 합치는 작업이 없습니다.
- 팀 코드가 main 에 병합될 때마다 CI 가 **그 코드에 의존하는 융합 패키지까지** 함께 빌드·테스트하므로, 문제는 마지막이 아니라 그때그때 드러납니다.

## 단계별 진행

### 0단계. 기존 팀 워크스페이스 옮기기 (처음 한 번)
이미 따로 개발 중인 워크스페이스나 저장소가 있다면, 그 안의 ROS 패키지를 해당 팀 폴더로 옮깁니다.
```bash
./scripts/start_task.sh camera <이슈번호> import-legacy
# 다른 저장소의 패키지를 이력과 함께 가져오기 (예: 카메라 팀 기존 저장소)
git subtree add --prefix=src/camera/<패키지폴더> https://github.com/<소유자>/<저장소> <브랜치>
./scripts/check.sh camera          # 공용 컨테이너에서 빌드 확인
git push -u origin HEAD            # → PR → 카메라 팀 리뷰 → 병합
```
- 저장소 안에 패키지가 여러 개면 저장소 통째로 `src/camera/<이름>/` 아래에 두어도 됩니다 (colcon 이 하위 패키지를 모두 찾음).
- 옮긴 뒤 옛 저장소는 보관만 하고 수정하지 않습니다.

### 1단계. 센서 팀 개발 + 출력 약속을 그때그때 정하기
센서 팀 출력은 개발하면서 정해집니다. **정해지는 순간** 아래를 합니다. (마지막에 몰아서 하지 않는 것이 핵심)

| 무엇이 정해지면 | 누가 | 할 일 |
|---|---|---|
| 표준 메시지로 충분한 출력 (예: `/gps/fix` `sensor_msgs/NavSatFix`) | 센서 팀 | PR 에 "융합 입력 추가 필요" 라고 적기 → 리더가 `fusion_inputs.yaml` 에 추가 |
| 새 메시지가 필요한 출력 (예: 차선 정보, 장애물 목록) | 센서 팀 → 리더 | `🔌 인터페이스 변경 요청` 이슈 → `src/interfaces` 에 메시지 정의 → `fusion_inputs.yaml` 에 추가 |
| 센서 장착 위치 | 리더 | 통합 런치에 static TF 로 정의 (`base_link` → `camera_link` 등) |

`src/fusion/mad_fusion/config/fusion_inputs.yaml` 예:
```yaml
inputs:
  - name: lane
    team: camera
    topic: /camera/lane_info
    type: mad_interfaces/msg/LaneInfo
    timeout_sec: 0.2     # 이보다 오래되면 "끊김"
    required: true       # 이 입력 없이는 융합하지 않음
```
- 입력을 추가하면 `fusion_node` 가 자동으로 구독하고, 끊긴 입력을 `/system/status` 로 경고합니다.

### 2단계. 데이터 녹화 (본체 노트북)
센서를 단 본체에서 모든 팀 출력을 **동시에** 녹화합니다. 융합 개발과 테스트의 기준 데이터가 됩니다.
```bash
./scripts/dev.sh --hw
ros2 launch mad_bringup system.launch.py        # (다른 터미널) 각 팀 노드 실행
./scripts/record_all.sh school_loop                 # fusion_inputs.yaml 의 토픽 + /tf 녹화
```
녹화 파일(`bags/`)은 git 에 올리지 않고 팀 공유 드라이브에 올립니다.

### 3단계. 융합 개발 (리더 공동, 어느 PC 에서나)
```bash
./scripts/start_task.sh fusion <이슈번호> lane-obstacle-merge
ros2 bag play bags/school_loop_... --clock --loop     # 녹화 데이터 재생
ros2 launch mad_fusion fusion.launch.py use_sim_time:=true
```
- 융합 로직은 `fusion_node.py` 의 `fuse()` 에서 시작해 별도 모듈로 키웁니다. 순수 계산은 ROS 없이 단위 테스트합니다.
- 융합 결과 메시지를 `src/interfaces` 에 정의하면 제어 팀이 그 토픽을 받아 개발합니다.

### 4단계. 최종 통합 (마일스톤)
각 팀 기능이 준비되면 통합 런치에 넣고, 본체에서 확인한 뒤 버전을 고정합니다.

1. 각 팀이 자기 패키지에 `launch/<팀>.launch.py` 를 두고, `src/bringup/mad_bringup/launch/system.launch.py` 의 `TEAM_LAUNCHES` 에 한 줄 추가하는 PR 을 올립니다. (`mad_fusion` 은 이미 들어 있음)
2. 리더가 센서 위치 static TF 를 통합 런치에 넣습니다.
3. **Actions → 본체 노트북 실기 테스트** 를 main 으로 실행합니다 (전체 빌드 → 테스트 → 통합 실행).
4. 아래 체크리스트를 확인합니다.
5. **Actions → 버전 릴리스** 로 `v0.x.0` 을 만듭니다. 이 태그가 "이 날짜에 융합까지 확인된 버전" 입니다. 시연·대회에는 태그 버전을 씁니다.

#### 통합 체크리스트
- [ ] `ros2 launch mad_bringup system.launch.py` 로 모든 팀 노드가 한 번에 뜬다
- [ ] `system_monitor` 에 하트비트 끊김/ERROR 가 없다
- [ ] `fusion_node` 상태가 "모든 입력 수신 중" 이다 (`ros2 topic echo /system/status`)
- [ ] `ros2 run tf2_tools view_frames` 의 TF 트리가 `map → odom → base_link → 센서` 로 이어진다
- [ ] 각 입력 토픽의 주기가 기대값과 맞다 (`ros2 topic hz <토픽>`)
- [ ] 녹화 bag 재생으로 융합 결과가 나온다 (센서 없는 PC 에서도)
- [ ] 본체 노트북 실기 테스트 통과
- [ ] 릴리스 태그 생성

## 역할 정리

| 역할 | 하는 일 |
|---|---|
| 센서 팀 (카메라·GPS·라이다) | 자기 폴더 개발, 출력 토픽/메시지 결정, `header.stamp`/`frame_id` 규칙 준수, 통합 런치 등록 |
| 제어 팀 | 융합 결과를 받아 경로 추종·제어, 아두이노 펌웨어 |
| 팀 리더 공동 (`leads`) | `src/interfaces` 약속 승인, `fusion_inputs.yaml` 관리, 융합 로직, static TF, 최종 통합·릴리스 |
| 본체 노트북 담당 | 데이터 녹화, 실기 테스트 러너 유지 |
