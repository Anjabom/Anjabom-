# 융합 팀 AI 지침 (`src/fusion/`)

<!-- 이 파일은 팀 리더(leads)가 함께 관리한다. 루트 AGENTS.md 의 규칙 위에 융합 규칙만 추가한다. -->

- 담당: 각 팀 리더 공동 (`@MAD2027/leads`) - 센서 융합과 판단
- 담당 폴더: `src/fusion/`
- 빌드/테스트: `./scripts/check.sh fusion`
- 브랜치: `fusion/<이슈번호>-<설명>`

## 구조
- 입력 목록: `mad_fusion/config/fusion_inputs.yaml` - 센서 팀 출력(토픽/타입/허용 지연/필수 여부). 센서 팀 출력이 정해질 때마다 여기에 추가한다.
- 노드: `mad_fusion/fusion_node.py` - 입력을 모두 구독하고, 필수 입력이 신선할 때 `fuse()` 를 `rate_hz` 주기로 호출. 융합 로직은 `fuse()` 와 별도 모듈에 작성한다.
- 순수 로직(시간 동기화, 좌표 변환 계산, 판단)은 ROS 의존 없는 모듈로 분리해 단위 테스트한다 (`mad_fusion/inputs.py` 참고).

## 융합 규칙
- 센서 팀 코드를 융합 폴더에 복사하지 않는다. **토픽으로만** 받는다. 필요한 출력이 없으면 해당 팀에 이슈를 연다.
- 서로 다른 센서는 `header.stamp` 기준으로 맞춘다 (가까운 시각끼리 매칭, 필요하면 `message_filters.ApproximateTimeSynchronizer`). 수신 시각으로 맞추지 않는다.
- 좌표 변환은 `tf2_ros` 로 한다. 센서 위치(외부 파라미터)를 코드에 하드코딩하지 않고 static TF(통합 런치)로 정의한다.
- 융합 결과 메시지는 `src/interfaces` 에 정의하고, 제어 팀이 구독한다.
- 개발/테스트는 본체에서 녹화한 bag(`./scripts/record_all.sh`)을 `use_sim_time:=true` 로 재생해서 한다.
