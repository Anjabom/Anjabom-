// 예시 스케치: 시리얼로 "S<조향>,T<속도>\n" 명령을 받아 출력.
// 일정 시간 명령이 없으면 정지(워치독) - 실제 구동 코드로 교체해서 사용.

const unsigned long COMMAND_TIMEOUT_MS = 500;
unsigned long lastCommandMs = 0;
int steering = 0;
int throttle = 0;

void applyOutputs() {
  // TODO(control): 실제 모터/서보 출력으로 교체
}

void parseCommand(const String &line) {
  int comma = line.indexOf(',');
  if (line.length() < 4 || line[0] != 'S' || comma < 0 || line[comma + 1] != 'T') {
    return;
  }
  steering = line.substring(1, comma).toInt();
  throttle = line.substring(comma + 2).toInt();
  lastCommandMs = millis();
}

void setup() { Serial.begin(115200); }

void loop() {
  if (Serial.available()) {
    parseCommand(Serial.readStringUntil('\n'));
  }
  if (millis() - lastCommandMs > COMMAND_TIMEOUT_MS) {
    throttle = 0;  // 통신 끊김 → 정지
  }
  applyOutputs();
}
