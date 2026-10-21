# 팀 공용 개발 환경. 모든 팀원/CI 가 같은 이미지로 빌드한다.
# ROS 배포판을 바꾸려면 devcontainer.json 과 .github/workflows/ci.yml 의 ROS_DISTRO 를 함께 바꾼다.
ARG ROS_DISTRO=humble
FROM ros:${ROS_DISTRO}-ros-base
ARG ROS_DISTRO
ARG ARDUINO_CLI_VERSION=1.1.1

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=${ROS_DISTRO}

RUN apt-get update && apt-get install -y --no-install-recommends \
        sudo git curl ca-certificates bash-completion \
        python3-pip python3-pytest python3-yaml \
        python3-colcon-common-extensions python3-rosdep \
        clang-format gdb \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/v${ARDUINO_CLI_VERSION}/install.sh \
        | BINDIR=/usr/local/bin sh -s ${ARDUINO_CLI_VERSION}

COPY requirements-dev.txt /tmp/requirements-dev.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements-dev.txt

# 일반 사용자(uid 1000)로 작업 → 호스트(우분투)와 파일 권한이 일치
ARG USERNAME=ubuntu
ARG USER_UID=1000
RUN (id -u ${USER_UID} >/dev/null 2>&1 || useradd -m -s /bin/bash -u ${USER_UID} ${USERNAME}) \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
    && usermod -aG dialout,video ${USERNAME} \
    && printf '%s\n' \
        "source /opt/ros/${ROS_DISTRO}/setup.bash" \
        '[ -f /ws/install/setup.bash ] && source /ws/install/setup.bash' \
        >> /etc/bash.bashrc
USER ${USERNAME}
