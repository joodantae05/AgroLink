#include <Arduino.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecureBearSSL.h>
#include <time.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// -------------------- CONFIG --------------------
#define DHTPIN D5
#define DHTTYPE DHT11

#define SOIL_PIN A0

const char* WIFI_SSID = "CHANGE_ME";
const char* WIFI_PASS = "CHANGE_ME";
const char* API_HOST = "example.local";
const char* API_PATH = "/api/v1/devices/00000000-0000-0000-0000-000000000000/telemetry";
const char* API_KEY = "CHANGE_ME";

const unsigned long LOOP_DELAY_MS = 3000UL;
const unsigned long TELEMETRY_INTERVAL_MS = 15000UL;

// Adresse LCD : souvent 0x27, parfois 0x3F
LiquidCrystal_I2C lcd(0x27, 20, 4);
DHT dht(DHTPIN, DHTTYPE);

// Calibration capteur de sol
// A ajuster apres test
const int SOIL_DRY = 850;   // valeur quand le capteur est sec / a l'air
const int SOIL_WET = 350;   // valeur quand le capteur est tres humide

unsigned long lastTelemetryMs = 0;

struct Measurement {
  float temperature;
  float humidityAir;
  int soilRaw;
  int soilPercent;
  bool dhtOk;
};

// -------------------- FONCTIONS --------------------
int readSoilRaw() {
  return analogRead(SOIL_PIN);
}

int soilPercentFromRaw(int raw) {
  int pct = map(raw, SOIL_DRY, SOIL_WET, 0, 100);

  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;

  return pct;
}

void displayError(const String& msg) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Erreur");
  lcd.setCursor(0, 1);
  lcd.print(msg);
}

bool connectWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    return true;
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  Serial.print("Connexion WiFi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi OK, IP: ");
    Serial.println(WiFi.localIP());
    return true;
  }

  Serial.println("WiFi KO");
  return false;
}

String isoTimeUtc() {
  time_t now = time(nullptr);
  if (now < 1700000000) {
    return "";
  }

  struct tm* t = gmtime(&now);
  if (!t) {
    return "";
  }

  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", t);
  return String(buf);
}

void appendReading(String& payload, bool& first, const char* type, float value, const char* unit, int decimals) {
  if (!first) {
    payload += ",";
  }
  first = false;

  payload += "{\"type\":\"";
  payload += type;
  payload += "\",\"value\":";
  payload += String(value, decimals);
  payload += ",\"unit\":\"";
  payload += unit;
  payload += "\"}";
}

String buildPayload(const Measurement& m) {
  String payload = "{";
  String ts = isoTimeUtc();
  if (ts.length() > 0) {
    payload += "\"ts\":\"";
    payload += ts;
    payload += "\",";
  }
  payload += "\"readings\":[";

  bool first = true;
  if (m.dhtOk) {
    appendReading(payload, first, "temperature", m.temperature, "c", 1);
    appendReading(payload, first, "humidity_air", m.humidityAir, "%", 1);
  }
  appendReading(payload, first, "humidity_soil", static_cast<float>(m.soilPercent), "%", 0);

  payload += "]}";
  return payload;
}

bool sendTelemetry(const Measurement& m) {
  if (!connectWifi()) {
    return false;
  }

  BearSSL::WiFiClientSecure client;
  client.setInsecure();

  HTTPClient https;
  String url = String("https://") + API_HOST + API_PATH;

  if (!https.begin(client, url)) {
    Serial.println("Erreur init HTTPS");
    return false;
  }

  https.addHeader("Content-Type", "application/json");
  https.addHeader("X-API-Key", API_KEY);

  String payload = buildPayload(m);
  int code = https.POST(payload);
  https.end();

  Serial.print("Telemetry code: ");
  Serial.println(code);

  return code >= 200 && code < 300;
}

Measurement readMeasurement() {
  Measurement m;
  m.temperature = dht.readTemperature();
  m.humidityAir = dht.readHumidity();
  m.soilRaw = readSoilRaw();
  m.soilPercent = soilPercentFromRaw(m.soilRaw);
  m.dhtOk = !isnan(m.temperature) && !isnan(m.humidityAir);
  return m;
}

void printSerial(const Measurement& m) {
  Serial.println("------ MESURE ------");

  if (!m.dhtOk) {
    Serial.println("Erreur lecture DHT11");
  } else {
    Serial.print("Temperature air: ");
    Serial.print(m.temperature);
    Serial.println(" C");

    Serial.print("Humidite air: ");
    Serial.print(m.humidityAir);
    Serial.println(" %");
  }

  Serial.print("Humidite sol brute: ");
  Serial.println(m.soilRaw);

  Serial.print("Humidite sol %: ");
  Serial.print(m.soilPercent);
  Serial.println(" %");
}

void renderLcd(const Measurement& m) {
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Serre connectee");

  lcd.setCursor(0, 1);
  if (!m.dhtOk) {
    lcd.print("Temp: ERR");
  } else {
    lcd.print("Temp: ");
    lcd.print(m.temperature, 1);
    lcd.print((char)223); // symbole degre
    lcd.print("C");
  }

  lcd.setCursor(0, 2);
  if (!m.dhtOk) {
    lcd.print("Hum Air: ERR");
  } else {
    lcd.print("Hum Air: ");
    lcd.print(m.humidityAir, 1);
    lcd.print("%");
  }

  lcd.setCursor(0, 3);
  lcd.print("Hum Sol: ");
  lcd.print(m.soilPercent);
  lcd.print("%");
}

// -------------------- SETUP --------------------
void setup() {
  Serial.begin(115200);
  delay(300);

  Wire.begin(D2, D1);  // SDA, SCL pour ESP8266

  lcd.init();
  lcd.backlight();
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Demarrage...");

  dht.begin();
  connectWifi();
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");

  Serial.println("Systeme demarre");
}

// -------------------- LOOP --------------------
void loop() {
  Measurement m = readMeasurement();

  printSerial(m);
  renderLcd(m);

  unsigned long now = millis();
  if (now - lastTelemetryMs >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryMs = now;
    sendTelemetry(m);
  }

  delay(LOOP_DELAY_MS);
}
