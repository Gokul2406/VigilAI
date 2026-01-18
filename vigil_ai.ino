/*
 * Arduino UNO - NRF24L01 Receiver
 * CE Pin: 9
 * CSN Pin: 10
 * 
 * Wiring:
 * NRF24L01 -> Arduino UNO
 * VCC -> 3.3V (IMPORTANT: NOT 5V!)
 * GND -> GND
 * CE -> Pin 9
 * CSN -> Pin 10
 * SCK -> Pin 13
 * MOSI -> Pin 11
 * MISO -> Pin 12
 */

#include <SPI.h>
#include <RF24.h>

RF24 radio(9, 10);

const byte address[5] = {0x30, 0x30, 0x30, 0x30, 0x31}; // "00001" in ASCII

void setup() {
  Serial.begin(9600);
  
  delay(100);
  
  Serial.println("Initializing NRF24L01...");
  
  if (!radio.begin()) {
    Serial.println("Radio hardware not responding!");
    while (1); 
  }
  
  Serial.println("Radio initialized!");
  
  radio.setPALevel(RF24_PA_LOW);
  
  radio.setDataRate(RF24_250KBPS);
  
  // Set channel (MUST match Raspberry Pi)
  radio.setChannel(76);
  
  // Disable auto-acknowledgment (MUST match Raspberry Pi)
  radio.setAutoAck(false);
  
  radio.setPayloadSize(1);
  
  radio.openReadingPipe(1, address);
  
  radio.startListening();
  
  Serial.println("Configuration:");
  Serial.println("- Power: LOW");
  Serial.println("- Data Rate: 250KBPS");
  Serial.println("- Channel: 76");
  Serial.println("- Auto-ACK: Disabled");
  Serial.println("- Payload: 1 byte");
  Serial.print("- Address: ");
  for(int i = 0; i < 5; i++) {
    Serial.print("0x");
    Serial.print(address[i], HEX);
    Serial.print(" ");
  }
  Serial.println();
  
  Serial.println("\n=== NRF24L01 Receiver Ready ===");
  Serial.println("Waiting for data...\n");
}

void loop() {
  if (radio.available()) {
    uint8_t receivedData;
    
    radio.read(&receivedData, sizeof(receivedData));
    
    Serial.print(">>> RECEIVED: ");
    Serial.print(receivedData);
    Serial.print(" (0x");
    Serial.print(receivedData, HEX);
    Serial.println(")");
    
    if (receivedData >= 0 && receivedData <= 2) {
      Serial.print("✓ Valid data: ");
      Serial.println(receivedData);
      
      switch(receivedData) {
        case 0:
          Serial.println("Normal Interaction");
          break;
        case 1:
          Serial.println("Pre-Stampede, Situation getting tense");
          break;
        case 2:
          Serial.println("STAMPEDE !!!");
          break;
      }
    } else {
      Serial.print("✗ Invalid data: ");
      Serial.println(receivedData);
    }
    Serial.println();
  }
  
  delay(10);
}
