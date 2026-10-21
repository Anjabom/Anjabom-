# 개발 흐름 (모든 팀원 필독)

> 핵심 규칙 3가지
> 1. **모든 작업은 이슈에서 시작한다.** 이슈가 없으면 아무도 내가 뭘 하는지 모른다.
> 2. **main 에 직접 push 하지 않는다.** 브랜치 → PR → 리뷰 → 병합.
> 3. **작게, 자주 병합한다.** 브랜치는 2~3일 안에 병합. 오래 들고 있을수록 합칠 때 아프다.

```
 이슈 생성 ──▶ 브랜치 생성 ──▶ 개발/커밋 ──▶ Draft PR ──▶ 리뷰 요청 ──▶ CI 통과 + 승인 ──▶ Squash 병합
 (보드: Todo)  (In Progress)                (보드에 보임)  (In Review)                      (Done, 이슈 자동 닫힘)
```

## 1. 이슈 만들기

GitHub → **Issues → New issue** → 양식 선택

| 양식 | 언제 |
|---|---|
| ✨ 기능 개발 | 새 기능, 개선, 일반 작업 |
| 🐞 버그 | 오동작 |
| 🔌 인터페이스 변경 요청 | 팀 간 메시지(`src/interfaces/`) 추가/변경 |

- **담당 팀**을 고르면 `team:xxx` 라벨이 자동으로 붙고 보드에 등록됩니다.
- 작업을 시작할 때 오른쪽 **Assignees** 에 자기 자신을 지정하세요. 이렇게 해야 "누가 하는지"가 보입니다.
- 3일 넘게 걸릴 작업은 여러 이슈로 나눕니다.
- 다른 팀 작업을 기다리고 있으면 `status:blocked` 라벨을 붙이고, 무엇을 기다리는지 댓글로 남깁니다.

## 2. 브랜치 만들기

이름 규칙: `<팀>/<이슈번호>-<짧은-설명>` (영문 소문자, 하이픈)

```bash
./scripts/start_task.sh camera 12 lane-offset
# = git fetch origin main && git switch -c camera/12-lane-offset origin/main
```

| 접두사 | 용도 |
|---|---|
| `camera/`, `gps/`, `lidar/`, `control/` | 각 팀 작업 (`config/teams.yml` 의 팀 id) |
| `shared/` | 인터페이스, 통합 런치 등 공용 작업 |
| `hotfix/`, `docs/`, `chore/` | 긴급 수정, 문서, 빌드/환경 |

## 3. 개발하고 커밋하기

```bash
git add -p                      # 바꾼 부분을 확인하며 담기
git commit -m "camera: 차선 중심 오프셋 계산 추가 (#12)"
```

- 커밋 메시지는 `<팀>: <무엇을 했는지> (#이슈번호)` 형식으로 씁니다.
- 커밋할 때 pre-commit 이 코드 스타일을 자동으로 검사하고 고칩니다. 고쳐진 파일이 있으면 `git add` 후 다시 커밋하세요.
- **하루에 한 번 이상** main 의 최신 변경을 받아옵니다. 충돌을 작을 때 해결하기 위해서입니다.
  ```bash
  ./scripts/sync_main.sh
  ```

## 4. PR 올리기

```bash
./scripts/check.sh camera        # 로컬 검사 (스타일 + 빌드 + 테스트). 전체는 인자 없이
git push -u origin HEAD
```

push 하면 터미널에 PR 생성 링크가 나옵니다.

- **작업 초반에 Draft PR 을 열어 두세요.** 다른 사람이 진행 상황을 볼 수 있습니다.
- 제목은 `[camera] 차선 중심 오프셋 발행` 형식으로 쓰고, 본문에는 `Closes #12` 를 넣습니다. 그래야 병합할 때 이슈가 자동으로 닫힙니다.
- 완성되면 **Ready for review** 를 누릅니다. 코드 오너(해당 팀)에게 리뷰가 자동으로 요청됩니다.

PR 을 올리면 자동으로 일어나는 일:

| 자동화 | 내용 |
|---|---|
| 팀 라벨 | 브랜치 이름과 변경 경로로 `team:xxx` 라벨 부여 |
| 규칙 안내 | 브랜치 이름, 이슈 연결, PR 크기(400줄)를 확인해 댓글로 안내 |
| CI | 바뀐 팀의 패키지와 그 패키지에 의존하는 패키지만 빌드·테스트. 아두이노가 바뀌면 컴파일 검사 |
| 공용 영역 알림 | `src/interfaces/`, `src/bringup/` 이 바뀌면 모든 팀을 멘션 |
| 상태 점검 (매일) | 3일 넘게 열린 PR → `status:stale`, main 보다 20커밋 이상 뒤처짐 → `status:behind-main` |

## 5. 리뷰하기

- 리뷰 요청을 받으면 **하루 안에** 응답합니다. 리뷰 대기가 가장 큰 병목입니다.
- 볼 것: 동작하는가 / 테스트가 있는가 / 토픽 이름·메시지 타입이 인터페이스 문서와 맞는가 / 타임아웃·예외 처리
- 승인(Approve) 1개와 `CI 통과` 가 모두 있어야 병합할 수 있습니다.

## 6. 병합

- **Squash and merge** 버튼으로 병합합니다. 병합 후 브랜치는 자동으로 삭제됩니다.
- 로컬 정리:
  ```bash
  git switch main && git pull --ff-only
  git branch -d camera/12-lane-offset
  ```

## 진행 상황 확인하는 곳

| 알고 싶은 것 | 볼 곳 |
|---|---|
| 지금 누가 무엇을 하나 | Projects 보드 → `담당자별` 뷰 |
| 팀별 진행 상황 | Projects 보드 → `팀별` 뷰, 또는 Issues 에서 `label:team:camera` |
| 이번 주 / 이번 달 무엇이 끝났나 | 매주 월요일, 매월 1일 자동 생성되는 `📊 주간 리포트`, `📅 월간 리포트` 이슈와 노션 `작업 기록` 데이터베이스 |
| 내 코드가 본체에서도 도나 | Actions → `본체 노트북 실기 테스트` 실행 ([TARGET_ENV.md](TARGET_ENV.md)) |
| 특정 파일을 누가 언제 바꿨나 | GitHub 파일 화면 → **History** / **Blame**, 또는 `git log -p <파일>` |
| 어느 버전이 안정 버전인가 | **Releases** (태그) |
| main 이 깨졌나 | README 의 CI 배지, `ci:nightly-failure` 이슈 |

## 막혔을 때

- 충돌 해결: [TEAM_GUIDE.md - 충돌 해결](TEAM_GUIDE.md#충돌-해결)
- 개발 환경 문제: [DEV_ENV.md](DEV_ENV.md)
