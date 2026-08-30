#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "SSID";
const char* password = "PASSWORD";

const char* wsHost = "192.168.1.1";
const uint16_t wsPort = 8080;
const char* wsPath = "/ws";

WebSocketsClient webSocket;

unsigned long lastSend = 0;
const unsigned long sendInterval = 3000;
void sendHello() {
  StaticJsonDocument<128> doc;
  doc["type"] = "hello";
  doc["role"] = "device";
  String out;
  serializeJson(doc, out);
  webSocket.sendTXT(out);
}

void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.println("[WS] Terputus dari server");
      break;

    case WStype_CONNECTED:
      Serial.println("[WS] Terhubung ke server!");
      sendHello();
      break;

    case WStype_TEXT:
      Serial.printf("[WS] Pesan dari server: %s\n", payload);
      break;

    case WStype_ERROR:
      Serial.println("[WS] Terjadi error");
      break;

    default:
      break;
  }
}

void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Menghubungkan ke WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Terhubung! IP ESP32: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  dht.begin();

  connectWiFi();

  webSocket.begin(wsHost, wsPort, wsPath);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(3000);
}

void loop() {
  webSocket.loop();

  unsigned long now = millis();
  if (now - lastSend < sendInterval) {
    return;
  }
  lastSend = now;

  float suhu = dht.readTemperature();
  float kelembapan = dht.readHumidity();

  if (isnan(suhu) || isnan(kelembapan)) {
    Serial.println("Gagal membaca data dari sensor DHT11!");
    return;
  }

  StaticJsonDocument<128> doc;
  doc["type"] = "data";
  doc["suhu"] = suhu;
  doc["kelembapan"] = kelembapan;

  String out;
  serializeJson(doc, out);
  webSocket.sendTXT(out);

  Serial.printf("Terkirim -> suhu: %.1f C, kelembapan: %.1f %%\n", suhu, kelembapan);
}
