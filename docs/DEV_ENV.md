# 개발 환경 설정

모든 팀원이 **같은 OS, 같은 ROS2(Humble), 같은 도구 버전**으로 개발하도록 Docker 기반 devcontainer 를 제공합니다.
CI 도 같은 베이스 이미지(`ros:humble-ros-base-jammy`)를 씁니다.

## 방법 A. devcontainer (권장)

### 1회 준비 (Ubuntu 22.04 호스트)
```bash
# Docker 설치
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER     # 로그아웃 후 다시 로그인

# VS Code 설치 후 확장 "Dev Containers" (ms-vscode-remote.remote-containers) 설치
```

### 저장소 받기 / 열기
```bash
git clone https://github.com/<org>/<repo>.git
cd <repo>
export ROS_DOMAIN_ID=12            # 본인 번호 (TEAM_GUIDE.md 참고)
code .
```
VS Code 에서 `Reopen in Container` 를 누릅니다(처음 한 번은 이미지 빌드로 5~10분 소요). 컨테이너가 만들어지면 `scripts/setup.sh` 가 자동으로 실행되어 다음을 설정합니다.
- pre-commit 훅 설치
- `rosdep install` 로 모든 패키지 의존성 설치
- 아두이노 보드 코어 설치

### 빌드 / 실행
```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch anjabom_bringup system.launch.py
```

### 실제 센서 / 아두이노 연결
`.devcontainer/devcontainer.json` 의 `runArgs` 에서 `--privileged`, `--volume=/dev:/dev` 주석을 해제한 뒤 **Rebuild Container** 를 실행합니다.
GUI(rviz2) 를 쓰려면 호스트에서 `xhost +local:` 을 실행하고, `containerEnv` 에 `"DISPLAY": "${localEnv:DISPLAY}"`, `runArgs` 에 `--volume=/tmp/.X11-unix:/tmp/.X11-unix` 를 추가합니다.

## 방법 B. 호스트에 직접 설치 (차량 PC / Jetson 등)

이미 Ubuntu 22.04 + ROS2 Humble 이 설치된 PC 라면:
```bash
sudo apt install python3-colcon-common-extensions python3-rosdep python3-pip
pip3 install -r requirements-dev.txt
# arduino-cli (Dockerfile 과 같은 버전)
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/v1.1.1/install.sh | BINDIR=$HOME/.local/bin sh -s 1.1.1
./scripts/setup.sh
```
> 버전이 달라지지 않도록, 의존성은 `apt install` 로 직접 설치하지 말고 `package.xml` 에 적은 뒤 `rosdep install` 로 설치합니다.

## 새 패키지 만들기
```bash
./scripts/new_package.sh camera camera_lane python    # 또는 cpp
```
`src/camera/camera_lane` 이 생성되고 `rclpy`(또는 `rclcpp`) 와 `anjabom_interfaces` 의존성이 들어갑니다.

## 자주 쓰는 스크립트

| 명령 | 설명 |
|---|---|
| `./scripts/start_task.sh <팀> <이슈> <설명>` | 최신 main 에서 작업 브랜치 생성 |
| `./scripts/sync_main.sh` | 작업 브랜치에 최신 main 병합 |
| `./scripts/check.sh [팀]` | 스타일 + 빌드 + 테스트 + 아두이노 컴파일 (CI 와 동일) |
| `./scripts/new_package.sh <팀> <이름> [python\|cpp]` | ROS2 패키지 생성 |
| `python3 scripts/teams.py sync` | 팀 설정 변경 후 생성 파일 갱신 |

## ROS 배포판을 바꿀 때
다음 세 곳의 값을 함께 바꾸고 PR 을 올립니다. 모든 팀이 영향을 받으니 리더 회의에서 먼저 합의합니다.
- `.devcontainer/Dockerfile` 의 `ARG ROS_DISTRO`
- `.devcontainer/devcontainer.json` 의 `ROS_DISTRO`
- `.github/workflows/ci.yml` 의 `ROS_DISTRO`, `container:` 이미지 태그

## 문제 해결
| 증상 | 해결 |
|---|---|
| 다른 사람 토픽이 보임 | `echo $ROS_DOMAIN_ID` 확인 → 본인 번호로 설정 |
| `Package 'xxx' not found` | `source install/setup.bash`, 또는 `rosdep install --from-paths src --ignore-src -y` |
| 커밋이 pre-commit 에 막힘 | 자동 수정된 파일을 `git add` 후 다시 커밋. 메시지를 읽고 직접 수정 |
| main 에 커밋했다며 막힘 | `git switch -c <팀>/<이슈>-<설명>` 으로 브랜치를 만들고 거기서 커밋 |
| `/dev/ttyACM0` 권한 오류 | 호스트: `sudo usermod -aG dialout $USER` 후 재로그인. 컨테이너는 privileged 설정 |
