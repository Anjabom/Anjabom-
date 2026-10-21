"""전체 시스템 통합 런치.

각 팀은 자기 패키지에 `<패키지>/launch/<이름>.launch.py` 를 만들고,
통합할 준비가 되면 아래 TEAM_LAUNCHES 에 한 줄 추가하는 PR 을 올린다.
설치되지 않은 패키지는 건너뛰므로 일부 팀만 있어도 실행된다.
"""

import os

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

# (패키지 이름, launch 파일 이름)
TEAM_LAUNCHES = [
    # ("camera_lane", "camera.launch.py"),
    # ("gps_localization", "gps.launch.py"),
    # ("lidar_obstacle", "lidar.launch.py"),
    # ("control_driver", "control.launch.py"),
]


def generate_launch_description() -> LaunchDescription:
    config = os.path.join(get_package_share_directory("anjabom_bringup"), "config", "system.yaml")
    actions = [Node(package="anjabom_bringup", executable="system_monitor", parameters=[config], output="screen")]
    for package, launch_file in TEAM_LAUNCHES:
        try:
            share = get_package_share_directory(package)
        except PackageNotFoundError:
            actions.append(LogInfo(msg=f"[bringup] {package} 미설치 - 건너뜀"))
            continue
        path = os.path.join(share, "launch", launch_file)
        actions.append(IncludeLaunchDescription(PythonLaunchDescriptionSource(path)))
    return LaunchDescription(actions)
