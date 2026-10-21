# 본체 노트북 = 기준 환경

> 목표: **윈도우에서 개발하든, 사양이 다른 우분투 노트북에서 개발하든, 본체 노트북에서 개발하는 것과 같은 조건**을 만든다.

## 왜 OS 나 사양이 다르면 문제가 생기나

| 차이 | 생기는 문제 |
|---|---|
| OS (윈도우 vs 우분투) | ROS2 Humble 은 Ubuntu 22.04 가 공식 환경입니다. 경로 구분자, 줄바꿈(CRLF), 권한, 시리얼 포트 이름(`COM3` vs `/dev/ttyACM0`) 등이 모두 다릅니다. |
| 패키지 버전 | 같은 우분투라도 설치 시점에 따라 OpenCV, numpy, ROS 패키지 버전이 달라 "내 PC 에선 되는데"가 생깁니다. |
| 하드웨어 사양 | 고사양 PC 에서는 30FPS 가 나오던 노드가 본체에서는 10FPS 로 떨어질 수 있습니다. 타이밍이나 타임아웃 버그가 본체에서만 나타납니다. |
| 센서 유무 | 집에는 라이다나 아두이노가 없어 실제 입력으로 테스트할 수 없습니다. |

## 해결 구조: 4단계

```
            ┌─────────────────────── 공용 개발 이미지 (GHCR) ───────────────────────┐
            │ Ubuntu 22.04 + ROS2 Humble desktop + rosdep 의존성 + pip(버전 고정)    │
            │ + arduino-cli/코어(버전 고정)  ← Dockerfile 로 CI 가 빌드, 한 번 만들면 고정 │
            └───────────────────────────────────────────────────────────────────────┘
                 ▲                  ▲                    ▲                  ▲
         윈도우 노트북        우분투 노트북           본체 노트북              CI
        (WSL2 + Docker)       (Docker)          (Docker + 센서 연결)   (GitHub Actions)
        ①소프트웨어 동일     ①소프트웨어 동일       ①기준 그 자체           ①동일
        ②CPU/RAM 제한        ②CPU/RAM 제한         ④실기 테스트 러너
        ③rosbag 으로 센서 재생
```

### ① 소프트웨어를 완전히 같게: 공용 개발 이미지
- `.devcontainer/Dockerfile` 로 만든 이미지를 **CI 가 한 번 빌드해 GHCR 에 올리고**, 모든 PC 는 그 이미지를 **받아서** 씁니다. 각자 빌드하지 않으므로 패키지 버전이 1비트도 다르지 않습니다.
- 본체 노트북도 같은 이미지 안에서 실행합니다 (`./scripts/dev.sh --hw`). 본체에 직접 설치한 패키지가 바뀌어도 영향을 받지 않습니다.
- 의존성은 이렇게 추가합니다:
  - apt/ROS 패키지 → 해당 패키지의 `package.xml` 에 `<depend>` 추가
  - pip 패키지 → `requirements.txt` 에 `이름==버전` 추가
  - 아두이노 코어/라이브러리 → 스케치의 `sketch.yaml` profile 에 버전과 함께 추가
  - PR 이 main 에 병합되면 **이미지가 자동으로 다시 빌드**됩니다. 팀원은 Rebuild Container 를 하면 됩니다.
- 릴리스(`v0.3.0`)를 만들면 이미지에도 `humble-v0.3.0` 태그가 붙습니다. 몇 달 뒤에도 그 버전의 환경을 그대로 재현할 수 있습니다.

### ② 하드웨어 차이를 줄이기: 본체 사양 기록과 제한
1. 본체 노트북에서 한 번 실행합니다 (공용 컨테이너 안에서).
   ```bash
   ./scripts/dev.sh
   python3 scripts/env_check.py --capture     # config/target_env.yml 생성
   ```
   생성된 `config/target_env.yml` 을 PR 로 올립니다. 본체의 CPU, RAM, GPU, OS, 모든 패키지 버전이 기록됩니다.
2. 다른 PC 에서는 비교만 합니다 (devcontainer 를 만들 때 자동으로 실행됨).
   ```bash
   python3 scripts/env_check.py
   ```
   소프트웨어가 다르면 ❌ 로 표시되고, 사양이 더 높으면 본체에 맞추는 옵션을 알려 줍니다.
3. 성능을 본체 수준으로 맞춰 보고 싶을 때:
   - 우분투: `./scripts/dev.sh --match-target`, 또는 devcontainer.json 의 `--cpus`/`--memory` 주석 해제
   - 윈도우: `%UserProfile%\.wslconfig` 의 `processors`, `memory` 를 본체 값으로 설정 ([DEV_ENV.md](DEV_ENV.md#윈도우-노트북))

> CPU 개수와 메모리를 제한해도 CPU 종류나 GPU 차이까지 똑같이 만들 수는 없습니다. **성능에 대한 최종 판단은 ④ 본체 실기 테스트**로 합니다.

### ③ 센서가 없는 PC: rosbag 으로 재생
- 본체에서 실제 주행 데이터를 녹화해 팀 공유 드라이브에 올립니다.
  ```bash
  ros2 bag record -o drive_20261021 /camera/image_raw /scan /gps/fix /imu/data
  ```
- 다른 PC 에서는 받아서 재생합니다. 노드는 실제 센서와 똑같은 토픽을 받습니다.
  ```bash
  ros2 bag play drive_20261021 --loop
  ```
- rosbag 은 용량이 커서 git 에 올리지 않습니다 (`.gitignore` 처리됨).

### ④ 본체 노트북 실기 테스트 (self-hosted runner)
본체 노트북을 GitHub Actions 러너로 등록해 두면, **어느 PC 에서 개발했든 버튼 하나로 본체 하드웨어에서 검증**할 수 있습니다.

- 실행: GitHub → **Actions → 본체 노트북 실기 테스트 → Run workflow → 브랜치 선택**
- 수행 내용 (`scripts/vehicle_test.sh`): 환경 비교 → 빌드 → 테스트 → `system.launch.py` 를 N초 동안 통합 실행 (노드가 죽으면 실패)
- 본체가 꺼져 있으면 켜질 때까지 대기 상태로 남습니다.

#### 본체 노트북을 러너로 등록 (관리자 1회)
1. 본체에 Docker 를 설치합니다: `curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER`
2. GitHub 저장소 → **Settings → Actions → Runners → New self-hosted runner** → Linux / x64 를 선택하고, 화면의 명령을 본체 터미널에서 그대로 실행합니다.
   - `./config.sh` 실행 중 라벨을 물으면 **`vehicle`** 을 입력합니다.
3. 서비스로 등록해 부팅 시 자동으로 실행되게 합니다.
   ```bash
   sudo ./svc.sh install && sudo ./svc.sh start
   ```
4. ⚠️ **보안** (public 저장소이므로 필수): **Settings → Actions → General → Fork pull request workflows** 에서 **Require approval for all external contributors** 를 선택합니다. 외부인의 PR 이 본체에서 코드를 실행하지 못하게 하기 위해서입니다.

## 원격으로 본체에 접속해 개발하기 (선택)

센서 디버깅처럼 꼭 본체에서 해야 하는 작업은, 자기 노트북에서 **본체에 원격 접속**해 진행할 수 있습니다.
1. 본체와 팀원 PC 에 [Tailscale](https://tailscale.com/) 을 설치합니다 (무료, 학교/집 어디서든 접속 가능).
2. 본체에 SSH 서버를 설치합니다: `sudo apt install openssh-server`
3. 팀원은 VS Code 확장 **Remote - SSH** 로 `ssh <계정>@<본체 tailscale 이름>` 에 접속합니다. 본체 위에서 직접 편집, 실행, 디버깅할 수 있습니다.

> 본체를 여러 명이 동시에 쓰면 서로 방해가 됩니다. 원격 접속은 실기 디버깅에만 쓰고, 평소 개발은 각자 PC 의 공용 컨테이너에서 합니다.
