#include <SPI.h>

volatile boolean received;
volatile byte SlaveReceived;

void setup() {
    Serial.begin(115200);

    pinMode(MISO, OUTPUT); // Sets MISO as OUTPUT

    SPCR |= _BV(SPE); // Turn on SPI in Slave Mode

    received = false;

    SPI.attachInterrupt(); // Interrupt ON is set for SPI communication

    Serial.println("Setup complete");
}

ISR(SPI_STC_vect) // Interrupt routine function
{
    SlaveReceived = SPDR; // Value received from master is stored in variable SlaveReceived
    received = true;      // Sets received as True
}

void loop() {

    if (received) {
        Serial.write(SlaveReceived);
        received = false;
    }
}
