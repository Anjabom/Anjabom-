# 각 노드가 주기적으로 /system/status 에 발행하는 상태(하트비트).
# mad_bringup/system_monitor 가 이를 모아 끊긴 노드를 경고한다.

uint8 OK=0
uint8 WARN=1
uint8 ERROR=2

std_msgs/Header header
string team          # config/teams.yml 의 팀 id (camera, gps, lidar, control ...)
string node_name
uint8 level
string message
