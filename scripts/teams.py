#!/usr/bin/env python3
"""config/teams.yml 을 기준으로 팀 관련 파일을 생성/검사한다.

사용법:
  python3 scripts/teams.py sync            # 생성 파일 갱신
  python3 scripts/teams.py check           # 생성 파일이 최신인지 검사 (CI용)
  git diff --name-only origin/main | python3 scripts/teams.py changed
                                           # 변경 파일 → 영향 받는 팀/빌드 범위 (CI용)
  python3 scripts/teams.py list            # 팀 ID 목록
  python3 scripts/teams.py image           # 공용 개발 이미지 이름
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "teams.yml"
GENERATED_HEADER = "자동 생성 파일 - 직접 수정하지 말고 config/teams.yml 수정 후 `python3 scripts/teams.py sync` 실행"

ISSUE_FORMS = [
    ROOT / ".github" / "ISSUE_TEMPLATE" / "1-feature.yml",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "2-bug.yml",
    ROOT / ".github" / "ISSUE_TEMPLATE" / "3-interface-change.yml",
]
BEGIN_MARK = "# BEGIN TEAM OPTIONS"
END_MARK = "# END TEAM OPTIONS"

# 팀과 무관하게 항상 존재하는 라벨
STATIC_LABELS = [
    ("type:feature", "a2eeef", "새 기능"),
    ("type:bug", "d73a4a", "버그"),
    ("type:interface", "fbca04", "팀 간 인터페이스(메시지) 변경"),
    ("type:chore", "c5def5", "빌드/CI/환경/리팩터링"),
    ("type:docs", "0075ca", "문서"),
    ("status:in-progress", "fef2c0", "작업 중"),
    ("status:blocked", "b60205", "다른 작업/팀을 기다리는 중"),
    ("status:review-needed", "0052cc", "리뷰 필요"),
    ("status:stale", "cccccc", "오래 열려 있는 PR - 병합 또는 분할 필요"),
    ("status:behind-main", "e99695", "main 보다 많이 뒤처짐 - main 병합 필요"),
    ("priority:high", "b60205", "우선순위 높음"),
    ("priority:medium", "fbca04", "우선순위 보통"),
    ("priority:low", "0e8a16", "우선순위 낮음"),
    ("area:shared", "fbca04", "공용 영역(인터페이스/통합 런치) 변경"),
    ("ci:nightly-failure", "b60205", "야간 통합 빌드 실패"),
    ("report:weekly", "bfdadc", "주간 진행 리포트"),
    ("report:monthly", "bfdadc", "월간 진행 리포트"),
    ("ai:claude", "d4c5f9", "Claude Code 로 작성/수정"),
    ("ai:codex", "d4c5f9", "OpenAI Codex 로 작성/수정"),
    ("ai:grok", "d4c5f9", "Grok 으로 작성/수정"),
    ("ai:other", "d4c5f9", "기타 AI 도구로 작성/수정"),
]

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_config() -> dict:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    ids = set()
    for team in cfg.get("teams", []):
        tid = team["id"]
        if not ID_RE.match(tid):
            sys.exit(f"잘못된 팀 id '{tid}': 영문 소문자/숫자/하이픈만 사용")
        if tid in ids:
            sys.exit(f"팀 id 중복: {tid}")
        ids.add(tid)
        team.setdefault("color", "ededed")
        team.setdefault("description", team["name"])
        team["paths"] = [p.rstrip("/") + "/" for p in team.get("paths", [])]
    for area in cfg.get("shared", []):
        area["path"] = area["path"].rstrip("/") + "/"
    return cfg


def handle(org: str, team_slug: str) -> str:
    return f"@{org}/{team_slug}"


# ── 생성기 ────────────────────────────────────────────────────


def gen_codeowners(cfg: dict) -> str:
    org = cfg["org"]
    lines = [f"# {GENERATED_HEADER}", "#", "# 마지막에 매칭되는 규칙이 우선한다.", ""]
    lines.append(f"* {handle(org, cfg['maintainers_team'])}")
    lines.append("")
    lines.append("# 팀별 담당 영역")
    for team in cfg["teams"]:
        for path in team["paths"]:
            lines.append(f"/{path} {handle(org, team['github_team'])}")
    lines.append("")
    lines.append("# 공용 영역")
    for area in cfg.get("shared", []):
        owners = " ".join(handle(org, cfg[f"{o}_team"]) for o in area["owners"])
        lines.append(f"/{area['path']} {owners}")
    return "\n".join(lines) + "\n"


def gen_labeler(cfg: dict) -> str:
    """actions/labeler@v5 설정: 변경 경로 / 브랜치 이름으로 팀 라벨 부여."""
    lines = [f"# {GENERATED_HEADER}", ""]
    for team in cfg["teams"]:
        lines.append(f'"team:{team["id"]}":')
        lines.append("  - any:")
        lines.append("      - changed-files:")
        lines.append("          - any-glob-to-any-file:")
        for path in team["paths"]:
            lines.append(f'              - "{path}**"')
        lines.append(f'      - head-branch: ["^{team["id"]}/"]')
    shared_notify = [a["path"] for a in cfg.get("shared", []) if a.get("notify_all_teams")]
    if shared_notify:
        lines.append('"area:shared":')
        lines.append("  - changed-files:")
        lines.append("      - any-glob-to-any-file:")
        for path in shared_notify:
            lines.append(f'          - "{path}**"')
        lines.append('"type:interface":')
        lines.append("  - changed-files:")
        lines.append("      - any-glob-to-any-file:")
        lines.append('          - "src/interfaces/**"')
    return "\n".join(lines) + "\n"


def gen_labels(cfg: dict) -> str:
    labels = [
        {"name": f"team:{t['id']}", "color": t["color"], "description": f"{t['name']} 팀 - {t['description']}"[:100]}
        for t in cfg["teams"]
    ]
    labels += [{"name": n, "color": c, "description": d} for n, c, d in STATIC_LABELS]
    return json.dumps(labels, ensure_ascii=False, indent=2) + "\n"


def gen_teams_json(cfg: dict) -> str:
    """워크플로(JavaScript)에서 읽는 팀 정보."""
    org = cfg["org"]
    data = {
        "_generated": GENERATED_HEADER,
        "org": org,
        "teams": [
            {
                "id": t["id"],
                "name": t["name"],
                "label": f"team:{t['id']}",
                "handle": handle(org, t["github_team"]),
                "paths": t["paths"],
            }
            for t in cfg["teams"]
        ],
        "shared": [
            {
                "path": a["path"],
                "owners": [handle(org, cfg[f"{o}_team"]) for o in a["owners"]],
                "notify_all_teams": bool(a.get("notify_all_teams")),
            }
            for a in cfg.get("shared", [])
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def gen_release(cfg: dict) -> str:
    """GitHub 자동 릴리스 노트 분류 (.github/release.yml)."""
    lines = [f"# {GENERATED_HEADER}", "changelog:", "  categories:"]
    lines += ["    - title: 🔌 인터페이스 변경", "      labels: [type:interface]"]
    for team in cfg["teams"]:
        lines += [f"    - title: {team['name']} 팀", f"      labels: [team:{team['id']}]"]
    lines += ["    - title: 기타", "      labels: ['*']"]
    return "\n".join(lines) + "\n"


def team_options_block(cfg: dict, indent: str) -> str:
    opts = [f"{indent}- {t['id']} ({t['name']})" for t in cfg["teams"]]
    opts.append(f"{indent}- shared (공용/여러 팀)")
    return "\n".join(opts)


def update_issue_form(text: str, cfg: dict) -> str:
    pattern = re.compile(rf"^(?P<indent>[ \t]*){re.escape(BEGIN_MARK)}\n.*?^[ \t]*{re.escape(END_MARK)}", re.S | re.M)

    def repl(m: re.Match) -> str:
        indent = m.group("indent")
        return f"{indent}{BEGIN_MARK}\n{team_options_block(cfg, indent)}\n{indent}{END_MARK}"

    new, n = pattern.subn(repl, text)
    if n == 0:
        raise SystemExit("이슈 템플릿에서 팀 옵션 마커를 찾지 못했습니다")
    return new


DEVCONTAINER = ROOT / ".devcontainer" / "devcontainer.json"
DEV_IMAGE_RE = re.compile(r'"image": "ghcr\.io/[^"]*"')


def dev_image(cfg: dict) -> str:
    """GHCR 이미지 이름 (.github/workflows/dev-image.yml 이 올리는 이름과 같아야 함)."""
    return f"ghcr.io/{cfg['org'].lower()}/anjabom-dev:humble"


# ── AI 코딩 도구 지침 (AGENTS.md / CLAUDE.md) ─────────────────
# 규칙 원본은 AGENTS.md (Codex, Grok 등이 읽음). CLAUDE.md 는 그것을 가져오기만 한다.

AGENTS_ROOT = ROOT / "AGENTS.md"
AGENTS_TEAMS_RE = re.compile(r"(<!-- BEGIN TEAMS[^\n]*-->\n).*?(<!-- END TEAMS -->)", re.S)
CLAUDE_STUB = (
    "<!-- 자동 생성 (scripts/teams.py sync). 규칙은 같은 폴더의 AGENTS.md 에 쓴다 - 모든 AI 도구 공용 -->\n"
    "@AGENTS.md\n"
)


def update_agents_root(text: str, cfg: dict) -> str:
    rows = ["| 팀 id | 이름 | 담당 폴더 | 설명 |", "|---|---|---|---|"]
    for t in cfg["teams"]:
        paths = ", ".join(f"`{p}`" for p in t["paths"])
        rows.append(f"| `{t['id']}` | {t['name']} | {paths} | {t['description']} |")
    new, n = AGENTS_TEAMS_RE.subn(lambda m: m.group(1) + "\n".join(rows) + "\n" + m.group(2), text)
    if n == 0:
        raise SystemExit("AGENTS.md 에서 팀 표 마커를 찾지 못했습니다")
    return new


def team_agents_stub(cfg: dict, team: dict, path: str) -> str:
    """팀 폴더 AGENTS.md 초안. 없을 때만 만들고, 이후에는 팀이 직접 관리한다."""
    return (
        f"# {team['name']} 팀 AI 지침 (`{path}`)\n\n"
        "<!-- 이 파일은 팀이 직접 관리한다. 루트 AGENTS.md 의 규칙 위에 팀 규칙만 추가한다. -->\n\n"
        f"- 팀: {team['name']} (`{team['id']}`) - {team['description']}\n"
        f"- 담당 폴더: {', '.join(f'`{p}`' for p in team['paths'])}\n"
        f"- 빌드/테스트: `./scripts/check.sh {team['id']}`\n"
        f"- 브랜치: `{team['id']}/<이슈번호>-<설명>`\n\n"
        "## 팀 규칙\n\n"
        "- (예: 발행/구독 토픽과 메시지 타입, 좌표계와 단위, 주기(Hz), 센서 드라이버, 금지 사항)\n"
    )


def render_all(cfg: dict) -> dict[Path, str]:
    gh = ROOT / ".github"
    out = {
        gh / "CODEOWNERS": gen_codeowners(cfg),
        gh / "labeler.yml": gen_labeler(cfg),
        gh / "labels.json": gen_labels(cfg),
        gh / "teams.json": gen_teams_json(cfg),
        gh / "release.yml": gen_release(cfg),
    }
    for form in ISSUE_FORMS:
        out[form] = update_issue_form(form.read_text(encoding="utf-8"), cfg)
    out[DEVCONTAINER] = DEV_IMAGE_RE.sub(f'"image": "{dev_image(cfg)}"', DEVCONTAINER.read_text(encoding="utf-8"))
    out[AGENTS_ROOT] = update_agents_root(AGENTS_ROOT.read_text(encoding="utf-8"), cfg)
    out[ROOT / "CLAUDE.md"] = CLAUDE_STUB
    for team in cfg["teams"]:
        for p in team["paths"]:
            agents = ROOT / p / "AGENTS.md"
            out[agents] = agents.read_text(encoding="utf-8") if agents.exists() else team_agents_stub(cfg, team, p)
            out[ROOT / p / "CLAUDE.md"] = CLAUDE_STUB
    return out


# ── 명령 ──────────────────────────────────────────────────────


def cmd_sync(cfg: dict) -> int:
    for path, content in render_all(cfg).items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"갱신: {path.relative_to(ROOT)}")
    if cfg["org"] == "CHANGE_ME":
        print("⚠️  config/teams.yml 의 org 를 실제 Organization 이름으로 바꾸세요.")
    return 0


def cmd_check(cfg: dict) -> int:
    stale = [
        str(p.relative_to(ROOT))
        for p, c in render_all(cfg).items()
        if not p.exists() or p.read_text(encoding="utf-8") != c
    ]
    if stale:
        print("다음 파일이 config/teams.yml 과 동기화되지 않았습니다:")
        for s in stale:
            print(f"  - {s}")
        print("→ python3 scripts/teams.py sync 실행 후 커밋하세요.")
        return 1
    print("팀 설정 동기화 OK")
    return 0


# 이 경로가 바뀌면 전체 빌드/테스트
FULL_BUILD_PREFIXES = (
    ".devcontainer/",
    ".dockerignore",
    "scripts/",
    ".github/workflows/ci.yml",
    "requirements.txt",
    "requirements-dev.txt",
)


def cmd_changed(cfg: dict) -> int:
    """stdin 의 변경 파일 목록 → GITHUB_OUTPUT 형식(key=value)."""
    files = [line.strip() for line in sys.stdin if line.strip()]
    teams: list[str] = []
    team_paths: list[str] = []
    full = False
    for f in files:
        owner = next((t for t in cfg["teams"] for p in t["paths"] if f.startswith(p)), None)
        if owner:
            if owner["id"] not in teams:
                teams.append(owner["id"])
            team_paths += [p.rstrip("/") for p in owner["paths"] if f.startswith(p) and p.startswith("src/")]
        elif f.startswith("src/") or f.startswith(FULL_BUILD_PREFIXES):
            full = True
    print(f"teams={' '.join(teams)}")
    print(f"full={'true' if full else 'false'}")
    print(f"ros_paths={' '.join(sorted(set(team_paths)))}")
    print(f"ros={'true' if (full or team_paths) else 'false'}")
    print(f"firmware={'true' if full or any(f.startswith('firmware/') for f in files) else 'false'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["sync", "check", "changed", "list", "image"])
    args = parser.parse_args()
    cfg = load_config()
    if args.command == "image":
        print(dev_image(cfg))
        return 0
    if args.command == "list":
        print("\n".join(t["id"] for t in cfg["teams"]))
        return 0
    return {"sync": cmd_sync, "check": cmd_check, "changed": cmd_changed}[args.command](cfg)


if __name__ == "__main__":
    sys.exit(main())
