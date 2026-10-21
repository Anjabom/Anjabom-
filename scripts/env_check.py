#!/usr/bin/env python3
"""본체 노트북(기준 환경)과 현재 PC 의 개발 환경을 비교한다.

  python3 scripts/env_check.py --capture   # 본체 노트북에서 1회: config/target_env.yml 기록 → PR
  python3 scripts/env_check.py             # 아무 PC(우분투/WSL/컨테이너)에서: 기준과 비교

소프트웨어(OS/ROS/Python/패키지 버전)가 다르면 종료 코드 1.
하드웨어(CPU/RAM/GPU)는 경고만 하고, 본체 성능에 맞추는 docker 옵션을 알려 준다.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "config" / "target_env.yml"


def run(cmd: list[str]) -> str:
    if not shutil.which(cmd[0]):
        return ""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def collect() -> dict:
    cpuinfo = read("/proc/cpuinfo")
    model = re.search(r"^model name\s*:\s*(.+)$", cpuinfo, re.M)
    mem = re.search(r"^MemTotal:\s*(\d+)", read("/proc/meminfo"), re.M)
    gpu = run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"])
    if not gpu:
        gpu = "; ".join(
            line.split(": ", 1)[-1] for line in run(["lspci"]).splitlines() if "VGA" in line or "3D" in line
        )
    os_release = dict(
        line.split("=", 1) for line in read("/etc/os-release").splitlines() if "=" in line and not line.startswith("#")
    )
    kernel = platform.release()

    ros_pkgs = {}
    for line in run(["dpkg-query", "-W", "-f=${Package} ${Version}\\n", "ros-*"]).splitlines():
        name, _, ver = line.partition(" ")
        if ver:
            ros_pkgs[name] = ver
    pip_raw = run([sys.executable, "-m", "pip", "list", "--format=json", "--disable-pip-version-check"])
    pip_pkgs = {p["name"].lower(): p["version"] for p in json.loads(pip_raw)} if pip_raw.startswith("[") else {}

    return {
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "hostname": platform.node(),
        "hardware": {
            "arch": platform.machine(),
            "cpu_model": model.group(1).strip() if model else "",
            "cpu_cores": os.cpu_count(),
            "ram_gb": round(int(mem.group(1)) / 1024 / 1024, 1) if mem else None,
            "gpu": gpu or "없음",
        },
        "os": {
            "name": os_release.get("PRETTY_NAME", "").strip('"'),
            "kernel": kernel,
            "in_container": Path("/.dockerenv").exists(),
            "wsl": "microsoft" in kernel.lower(),
        },
        "software": {
            "ros_distro": os.environ.get("ROS_DISTRO", ""),
            "python": platform.python_version(),
            "gcc": (run(["gcc", "--version"]).splitlines() or [""])[0],
            "cmake": (run(["cmake", "--version"]).splitlines() or [""])[0],
            "arduino_cli": run(["arduino-cli", "version"]),
        },
        "ros_packages": ros_pkgs,
        "pip_packages": pip_pkgs,
    }


def diff_versions(target: dict, current: dict) -> list[str]:
    out = []
    for name in sorted(set(target) | set(current)):
        t, c = target.get(name), current.get(name)
        if t != c:
            out.append(f"{name}: 기준 {t or '없음'} / 현재 {c or '없음'}")
    return out


def check(target: dict, cur: dict) -> int:
    errors, warnings = 0, 0
    print(f"== 본체 노트북 기준 환경과 비교 (기준: {target.get('hostname')}, {target.get('captured_at')}) ==")
    where = "컨테이너" if cur["os"]["in_container"] else ("WSL" if cur["os"]["wsl"] else "호스트")
    print(f"현재: {cur['hostname']} ({where})\n")

    print("[소프트웨어] - 달라지면 '내 PC 에선 되는데' 문제가 생깁니다")
    checks = [
        ("OS", target["os"]["name"], cur["os"]["name"]),
        ("ROS", target["software"]["ros_distro"], cur["software"]["ros_distro"]),
        ("Python", target["software"]["python"], cur["software"]["python"]),
        ("GCC", target["software"]["gcc"], cur["software"]["gcc"]),
        ("CMake", target["software"]["cmake"], cur["software"]["cmake"]),
        ("CPU 아키텍처", target["hardware"]["arch"], cur["hardware"]["arch"]),
    ]
    for name, t, c in checks:
        ok = t == c
        errors += not ok
        print(f"  {'✅' if ok else '❌'} {name:<10} 기준 {t or '-'} / 현재 {c or '-'}")
    for title, key in (("ROS(apt) 패키지", "ros_packages"), ("pip 패키지", "pip_packages")):
        diffs = diff_versions(target.get(key, {}), cur.get(key, {}))
        errors += bool(diffs)
        print(f"  {'✅' if not diffs else '❌'} {title}: {'일치' if not diffs else f'{len(diffs)}개 다름'}")
        for d in diffs[:15]:
            print(f"       - {d}")
        if len(diffs) > 15:
            print(f"       ... 외 {len(diffs) - 15}개")

    print("\n[하드웨어] - 성능(처리 속도, FPS, 지연) 에 영향")
    th, ch = target["hardware"], cur["hardware"]
    print(f"  CPU  기준 {th['cpu_model']} ({th['cpu_cores']}코어) / 현재 {ch['cpu_model']} ({ch['cpu_cores']}코어)")
    print(f"  RAM  기준 {th['ram_gb']}GB / 현재 {ch['ram_gb']}GB")
    print(f"  GPU  기준 {th['gpu']} / 현재 {ch['gpu']}")
    limit = []
    if ch["cpu_cores"] and th["cpu_cores"] and ch["cpu_cores"] > th["cpu_cores"]:
        limit.append(f'"--cpus={th["cpu_cores"]}"')
    if ch["ram_gb"] and th["ram_gb"] and ch["ram_gb"] > th["ram_gb"]:
        limit.append(f'"--memory={int(th["ram_gb"])}g"')
    if limit:
        warnings += 1
        print("  ⚠️  이 PC 가 본체보다 사양이 높습니다. 성능을 본체에 맞춰 보려면 devcontainer.json runArgs 에 추가:")
        print(f"       {', '.join(limit)}")
    if ch["cpu_cores"] and th["cpu_cores"] and ch["cpu_cores"] < th["cpu_cores"]:
        warnings += 1
        print(
            "  ⚠️  이 PC 가 본체보다 느립니다. 여기서 느린 것은 본체에서 괜찮을 수 있으니"
            " 성능 판단은 본체 실기 테스트로."
        )
    if ("없음" in th["gpu"]) != ("없음" in ch["gpu"]):
        warnings += 1
        print("  ⚠️  GPU 유무가 다릅니다. GPU 를 쓰는 코드는 본체 실기 테스트(vehicle-test)로 확인하세요.")

    print()
    if errors:
        print(f"❌ 소프트웨어 차이 {errors}건. 공용 개발 컨테이너(docs/DEV_ENV.md)에서 개발하면 해결됩니다.")
        print("   본체 노트북 쪽이 바뀐 것이라면: 본체에서 --capture 후 PR (관리자)")
        return 1
    print(f"✅ 소프트웨어 환경이 본체와 일치합니다.{f' (하드웨어 참고 사항 {warnings}건)' if warnings else ''}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--capture", action="store_true", help="현재 PC 를 기준 환경으로 기록 (본체 노트북에서만)")
    args = parser.parse_args()

    current = collect()
    if args.capture:
        header = (
            "# 본체 노트북(기준 환경) 정보 - python3 scripts/env_check.py --capture 로 생성\n"
            "# 본체의 ROS/패키지를 바꿨다면 다시 캡처해서 PR 로 올린다.\n"
        )
        TARGET.write_text(header + yaml.safe_dump(current, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"기록 완료: {TARGET.relative_to(ROOT)} → 커밋 후 PR 을 올리세요.")
        return 0

    target = yaml.safe_load(TARGET.read_text(encoding="utf-8")) if TARGET.exists() else None
    if not target or not target.get("hardware"):
        print(
            "기준 환경이 아직 기록되지 않았습니다."
            " 본체 노트북에서 `python3 scripts/env_check.py --capture` 를 실행하세요."
        )
        return 0
    return check(target, current)


if __name__ == "__main__":
    sys.exit(main())
