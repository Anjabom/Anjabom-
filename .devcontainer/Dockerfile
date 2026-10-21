# 팀 공용 개발 환경 = "본체 노트북 기준 환경".
# CI(.github/workflows/dev-image.yml)가 이 파일로 이미지를 만들어 GHCR 에 올리고,
# 모든 팀원(우분투/윈도우)과 본체 노트북, CI 가 그 **같은 이미지**를 받아 쓴다.
# → 각자 빌드하면 시점마다 apt 패키지 버전이 달라질 수 있으므로, 직접 빌드는 이미지 수정 테스트용으로만 쓴다.
ARG ROS_DISTRO=humble
FROM ros:${ROS_DISTRO}-ros-base-jammy
ARG ROS_DISTRO
ARG ARDUINO_CLI_VERSION=1.1.1

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=${ROS_DISTRO}

# 본체 노트북과 같은 ROS 구성(desktop: rviz2, rqt 포함) + 개발 도구
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-${ROS_DISTRO}-desktop \
        sudo git curl ca-certificates bash-completion usbutils \
        python3-pip python3-pytest python3-yaml \
        python3-colcon-common-extensions python3-rosdep \
        clang-format gdb \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/v${ARDUINO_CLI_VERSION}/install.sh \
        | BINDIR=/usr/local/bin sh -s ${ARDUINO_CLI_VERSION}

# Python 패키지 (버전 고정): requirements.txt = 실행용, requirements-dev.txt = 개발 도구
COPY requirements.txt requirements-dev.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt -r /tmp/requirements-dev.txt

# 모든 ROS 패키지의 의존성(package.xml)을 이미지에 미리 설치 → 누구나 같은 버전
# (.dockerignore 가 src/ 에서 package.xml 만 넘겨 주므로 코드가 바뀌어도 이 단계는 캐시됨)
COPY src/ /tmp/deps/src/
RUN apt-get update \
    && (rosdep init 2>/dev/null || true) \
    && rosdep update --rosdistro ${ROS_DISTRO} \
    && rosdep install --from-paths /tmp/deps/src --ignore-src -y --rosdistro ${ROS_DISTRO} \
    && rm -rf /var/lib/apt/lists/* /tmp/deps

# 일반 사용자(uid 1000)로 작업 → 호스트(우분투/WSL)와 파일 권한이 일치
ARG USERNAME=ubuntu
ARG USER_UID=1000
RUN (id -u ${USER_UID} >/dev/null 2>&1 || useradd -m -s /bin/bash -u ${USER_UID} ${USERNAME}) \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
    && usermod -aG dialout,video,plugdev ${USERNAME} \
    && printf '%s\n' \
        "source /opt/ros/${ROS_DISTRO}/setup.bash" \
        '[ -f /ws/install/setup.bash ] && source /ws/install/setup.bash' \
        >> /etc/bash.bashrc
USER ${USERNAME}
RUN rosdep update --rosdistro ${ROS_DISTRO}

# AI 코딩 도구(scripts/ai_tools.sh)용 경로. 실행 파일은 ~/.local, 로그인 정보는 ~/.ai-config 에 두고
# devcontainer/dev.sh 가 두 경로를 Docker 볼륨으로 연결한다 (→ 이미지에서 ~/.local 에 다른 것을 설치하지 말 것)
ENV PATH=/home/${USERNAME}/.local/bin:${PATH} \
    CLAUDE_CONFIG_DIR=/home/${USERNAME}/.ai-config/claude \
    CODEX_HOME=/home/${USERNAME}/.ai-config/codex
RUN mkdir -p ~/.local/bin ~/.ai-config/claude ~/.ai-config/codex ~/.ai-config/grok \
    && ln -s ~/.ai-config/grok ~/.grok

# 아두이노 보드 코어 (버전 고정)
ARG ARDUINO_AVR_CORE=arduino:avr@1.8.6
RUN arduino-cli core update-index && arduino-cli core install ${ARDUINO_AVR_CORE}
WORKDIR /ws
