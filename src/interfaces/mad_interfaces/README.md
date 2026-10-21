# mad_interfaces

팀 간에 주고받는 **공용 메시지 정의**입니다. 여기 정의된 메시지는 팀 간 계약이므로
변경 시 반드시 `🔌 인터페이스 변경 요청` 이슈로 합의 후 PR 을 올립니다. (docs/TEAM_GUIDE.md)

| 메시지 | 토픽 | 발행 | 구독 |
|---|---|---|---|
| `NodeStatus` | `/system/status` | 모든 노드 | `mad_bringup/system_monitor` |

새 메시지를 추가하면 `CMakeLists.txt` 의 `rosidl_generate_interfaces` 와 위 표를 함께 갱신하세요.
