import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config = os.path.join(get_package_share_directory("anjabom_fusion"), "config", "fusion.yaml")
    return LaunchDescription(
        [Node(package="anjabom_fusion", executable="fusion_node", parameters=[config], output="screen")]
    )
