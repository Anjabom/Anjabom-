from glob import glob

from setuptools import find_packages, setup

package_name = "anjabom_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="maintainers",
    maintainer_email="maintainers@example.com",
    description="전체 시스템 통합 런치 및 노드 상태 감시",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "system_monitor = anjabom_bringup.system_monitor:main",
        ],
    },
)
