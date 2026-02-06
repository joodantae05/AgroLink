#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecureBearSSL.h>
#include <time.h>

const char* WIFI_SSID = "CHANGE_ME";
const char* WIFI_PASS = "CHANGE_ME";

const char* API_HOST = "example.local";
const char* API_PATH = "/api/v1/devices/00000000-0000-0000-0000-000000000000/telemetry";
const char* DEVICE_ID = "agrolink-esp-001";
const char* API_KEY = "CHANGE_ME";

const unsigned long MEASURE_INTERVAL_MS = 5UL * 60UL * 1000UL;

unsigned long lastMeasure = 0;

float readHumidity() { return 62.0f; }
float readTemperature() { return 23.6f; }
float readPressure() { return 1008.0f; }
float readSoilPH() { return 6.40f; }

String isoTimeUtc() {
  time_t now = time(nullptr);
  struct tm* t = gmtime(&now);
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", t);
  return String(buf);
}

String buildPayload() {
  String ts = isoTimeUtc();
  String payload = "{";
  payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"ts\":\"" + ts + "\",";
  payload += "\"readings\":[";

  payload += "{\"type\":\"humidity\",\"value\":" + String(readHumidity(), 1) + ",\"unit\":\"%\"},";
  payload += "{\"type\":\"temperature\",\"value\":" + String(readTemperature(), 1) + ",\"unit\":\"c\"},";
  payload += "{\"type\":\"pressure\",\"value\":" + String(readPressure(), 1) + ",\"unit\":\"hpa\"},";
  payload += "{\"type\":\"soil_ph\",\"value\":" + String(readSoilPH(), 2) + ",\"unit\":\"ph\"}";

  payload += "]}";

  return payload;
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(500);
  }
}

void sendTelemetry() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWifi();
  }

  std::unique_ptr<BearSSL::WiFiClientSecure> client(new BearSSL::WiFiClientSecure);
  client->setInsecure();

  HTTPClient https;
  String url = String("https://") + API_HOST + API_PATH;

  if (!https.begin(*client, url)) {
    return;
  }

  https.addHeader("Content-Type", "application/json");
  https.addHeader("X-API-Key", API_KEY);

  String payload = buildPayload();
  int code = https.POST(payload);
  https.end();

  (void)code;
}

void setup() {
  Serial.begin(115200);
  connectWifi();
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
}

void loop() {
  unsigned long now = millis();
  if (now - lastMeasure >= MEASURE_INTERVAL_MS) {
    lastMeasure = now;
    sendTelemetry();
  }
}
