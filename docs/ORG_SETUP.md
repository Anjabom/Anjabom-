# GitHub Organization 설정 가이드 (관리자용)

> 이 문서는 **처음 한 번** 관리자가 GitHub 웹에서 해야 하는 설정입니다. 전체 흐름은 [GUIDE.md](GUIDE.md) 를 먼저 보세요.
> 코드(워크플로, 템플릿, CODEOWNERS 등)는 저장소에 이미 들어 있고, 여기서는 GitHub 설정 화면에서만 할 수 있는 일을 다룹니다.

## 0. 현재 상태 (2026-10-21 기준)

| 항목 | 상태 | 해야 할 일 |
|---|---|---|
| Organization | ✅ `MAD2027` 생성됨 | - |
| 저장소 | ✅ `MAD2027/MAD2027` (public) 로 이전됨 | 옛 주소로 받은 팀원은 `git remote set-url origin https://github.com/MAD2027/MAD2027.git` |
| `config/teams.yml` 의 `org` | ✅ `MAD2027` 로 설정 (PR #1 에 포함) | - |
| 팀 (`maintainers`, `leads`, `team-*`) | 없음 | 팀원 초대와 팀 생성 (3단계) |
| 브랜치 보호 | 없음 | 규칙 설정 (5단계) |

## 1. Organization 만들기 (무료)

1. GitHub 우측 상단 프로필 → **Your organizations** → **New organization**
2. **Free** 플랜 선택
3. 이름 입력 (예: `anjabom-auto`). 이 이름이 `config/teams.yml` 의 `org` 값이 됩니다.
4. "My personal account" 선택 → 생성

> **public / private 선택 기준**
> GitHub Free 플랜의 Organization 은 **public 저장소에서만** 브랜치 보호 규칙과 "코드 오너 리뷰 필수"가 동작합니다.
> 코드를 비공개로 해야 한다면, 학생이면 [GitHub Education](https://education.github.com/) 혜택으로 Team 플랜을 무료로 신청하거나 Team 플랜을 결제해야 합니다.
> public 저장소는 Actions 실행 시간도 무제한 무료입니다.

## 2. 저장소를 Organization 으로 이전

1. `Anjabom/Anjabom-` → **Settings** → 맨 아래 **Danger Zone** → **Transfer ownership**
2. 새 소유자에 1단계에서 만든 Organization 이름 입력 → 이전
3. (권장) **Settings → General → Repository name** 에서 이름을 알아보기 쉽게 변경 (예: `autonomous-car`)
   - 이전/이름 변경 후 옛 주소는 자동으로 새 주소로 연결되지만, 팀원은 아래 명령으로 주소를 갱신하세요.
   ```bash
   git remote set-url origin https://github.com/<org>/<repo>.git
   ```

## 3. 팀원 초대와 팀 만들기

**People → Invite member** 로 모든 팀원을 초대합니다 (역할: Member).

**Teams → New team** 으로 아래 팀을 만듭니다. 팀 slug 는 `config/teams.yml` 의 `github_team` 과 같아야 합니다.

| 팀 slug | 구성원 | 역할 |
|---|---|---|
| `maintainers` | 프로젝트 관리자 + 각 팀 리더 | 공용 영역(통합 런치, CI, 설정) 승인 |
| `leads` | 각 팀 리더 4명 | 인터페이스(메시지) 변경 승인 |
| `team-camera` | 카메라 팀원 | `src/camera/` 승인 |
| `team-gps` | GPS 팀원 | `src/gps/` 승인 |
| `team-lidar` | 라이다 팀원 | `src/lidar/` 승인 |
| `team-control` | 제어 팀원 | `src/control/`, `firmware/` 승인 |

각 팀 페이지 → **Repositories → Add repository** → 저장소 선택 → 권한 **Write**
(`maintainers` 팀은 **Maintain**)

> 팀 이름/구성이 바뀌면: GitHub 팀을 바꾸고 → `config/teams.yml` 수정 → `python3 scripts/teams.py sync` → PR.
> 자세한 내용은 [TEAM_GUIDE.md](TEAM_GUIDE.md#팀-구성-변경하기) 를 참고하세요.

## 4. 저장소에 Organization 이름 반영

> ✅ `MAD2027` 로 이미 반영했습니다 (PR #1). Organization 이름을 바꾸게 되면 아래 절차를 따릅니다.

```bash
# config/teams.yml 의 org: CHANGE_ME → 실제 이름 (예: anjabom-auto)
python3 scripts/teams.py sync      # CODEOWNERS 등 재생성
git switch -c chore/0-set-org origin/main
git commit -am "chore: Organization 이름 설정"
git push -u origin HEAD            # → PR 생성 → 병합
```

병합 후 **Actions → 라벨 동기화 → Run workflow** 를 한 번 실행하면 `team:camera`, `status:blocked` 등의 라벨이 생성됩니다.

## 5. main 브랜치 보호 (Rulesets)

**Settings → Rules → Rulesets → New ruleset → New branch ruleset**

- Ruleset name: `main 보호`, Enforcement: **Active**
- Bypass list: (비워 두기. 긴급할 때만 관리자 추가)
- Target branches: **Include default branch**
- 체크할 항목:
  - ✅ **Restrict deletions**
  - ✅ **Block force pushes**
  - ✅ **Require a pull request before merging**
    - Required approvals: **1**
    - ✅ Dismiss stale pull request approvals when new commits are pushed
    - ✅ **Require review from Code Owners** ← 팀 폴더는 그 팀이, 인터페이스는 리더가 승인
    - ✅ Require conversation resolution before merging
    - Allowed merge methods: **Squash** (PR 하나 = main 커밋 하나 → 기록이 깔끔)
  - ✅ **Require status checks to pass**
    - **Add checks** → `CI 통과` 추가 (CI 를 한 번 이상 실행한 뒤에 목록에 나타납니다)
    - "Require branches to be up to date" 는 **끄기** 권장 (16명이 쓰면 매번 재실행 대기 → 병목). 대신 야간 통합 빌드가 main 을 검증합니다.

**Settings → General → Pull Requests**
- ✅ Allow squash merging (나머지 merge/rebase 는 해제)
- ✅ Always suggest updating pull request branches
- ✅ Automatically delete head branches

## 6. 진행 상황 보드 (GitHub Projects)

1. Organization → **Projects → New project → Board** 템플릿, 이름: `개발 현황`
2. 필드 추가 (우측 상단 `...` → Settings → Custom fields):
   - `Status` (기본): `Todo`, `In Progress`, `In Review`, `Blocked`, `Done`
   - `Team` (Single select): `카메라`, `GPS`, `라이다`, `제어`, `공용`
   - `Iteration` (반복 주기 1주): 주간 계획용
3. **Workflows** (프로젝트 `...` → Workflows) 에서 켜기:
   - **Auto-add to project**: 필터 `is:issue,pr` + 이 저장소 → 새 이슈/PR 자동 등록
   - **Item closed** → Status `Done`
   - **Pull request merged** → Status `Done`
   - **Pull request linked to issue** → Status `In Review`
4. 뷰 만들기:
   - `팀별`: Board, **Group by: Labels** (또는 Team 필드)
   - `담당자별`: Table, **Group by: Assignees** → "누가 무엇을 하는지" 한눈에
   - `로드맵`: Roadmap, Iteration 기준

> 무료 플랜에서 Auto-add 워크플로가 부족하면 Actions 로 등록할 수 있습니다:
> - **Settings → Secrets and variables → Actions → Variables**: `PROJECT_URL` = 프로젝트 URL
> - **Secrets**: `PROJECT_TOKEN` = `project` 권한이 있는 Personal Access Token (classic)
> 설정하면 `pr-automation.yml`, `issue-automation.yml` 이 이슈/PR 을 자동 등록합니다. 설정하지 않으면 이 단계는 건너뜁니다.

## 7. Actions 설정과 공용 개발 이미지

**Settings → Actions → General**
- Actions permissions: **Allow all actions and reusable workflows**
- Fork pull request workflows: **Require approval for all external contributors** (외부인이 본체 노트북 러너에서 코드를 실행하지 못하게)
- Workflow permissions: **Read repository contents** (각 워크플로가 필요한 권한만 따로 요청합니다)

**Settings → Advanced Security** (public 저장소는 무료)
- ✅ **Secret Protection** (Secret scanning) 과 ✅ **Push protection**: AI 도구나 사람이 API 키·토큰을 커밋하면 push 단계에서 차단합니다. 저장소의 pre-commit `API 키/토큰 커밋 차단` 훅과 이중 방어입니다.

**공용 개발 이미지 만들기** (모든 PC 가 본체와 같은 환경을 쓰기 위한 핵심)
1. 이 PR 이 병합되면 `공용 개발 이미지` 워크플로가 자동으로 실행됩니다. 실행되지 않았다면 **Actions → 공용 개발 이미지 → Run workflow** 로 직접 실행합니다 (약 15~20분).
2. 끝나면 Organization → **Packages → anjabom-dev → Package settings** 에서:
   - **Change visibility → Public**: 팀원이 로그인 없이 받을 수 있습니다. 저장소가 private 이면 Private 로 두고, 팀원은 `docker login ghcr.io` 를 해야 합니다.
   - **Manage Actions access** 에 이 저장소가 Write 로 있는지 확인합니다.
3. 이후 CI 도 자동으로 이 이미지를 사용합니다.

## 8. 본체 노트북, 노션 연동

- 본체 노트북 기준 환경 기록과 실기 테스트 러너 등록: [TARGET_ENV.md](TARGET_ENV.md)
- 주간·월간 작업 기록을 노션에 연동 (`NOTION_TOKEN`, `NOTION_DATABASE_ID`): [NOTION.md](NOTION.md)

## 9. 확인 체크리스트

- [ ] 모든 팀원이 Organization 에 가입하고 각 팀에 속해 있다
- [ ] `config/teams.yml` 의 `org` 가 실제 이름이고, CODEOWNERS 에 오류 표시가 없다 (GitHub 에서 CODEOWNERS 파일을 열었을 때 빨간 경고가 없어야 함)
- [ ] 라벨 동기화 워크플로를 실행했다
- [ ] main 에 직접 push 하면 거부된다
- [ ] 테스트 PR 을 올렸을 때 팀 라벨이 붙고, 코드 오너 리뷰가 요청되고, `CI 통과` 체크가 돈다
- [ ] 새 이슈가 프로젝트 보드에 자동으로 나타난다
- [ ] `ghcr.io/<org>/anjabom-dev:humble` 이미지가 있고 Public 이다
- [ ] 본체 노트북에서 `--capture` 한 `config/target_env.yml` 이 main 에 있다
- [ ] 본체 노트북 러너가 Settings → Actions → Runners 에 `Idle` 로 보인다
- [ ] 진행 리포트를 수동 실행했을 때 노션 데이터베이스에 행이 생긴다
