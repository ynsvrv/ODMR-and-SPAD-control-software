#include <SPI.h>

volatile boolean received;
volatile byte SlaveReceived;

int data_counter = 0; //test for serial
int second_byte = false;

unsigned short numbers[512];

void setup() {
    Serial.begin(115200);

    pinMode(MISO, OUTPUT); // Sets MISO as OUTPUT

    SPCR |= _BV(SPE); // Turn on SPI in Slave Mode

    received = false;

    SPI.attachInterrupt(); // Interrupt ON is set for SPI communication

    int max_number_excl = pow(2, 10) - 1;

    //Fill numbers randomly
    for(int i = 0; i < 512; i++){
      numbers[i] = random(max_number_excl)*i;
    }

    //Serial.println("Setup complete");
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

    //Simulate a received byte
    if(data_counter == 0) {
      //send start bytes
      SlaveReceived = 0xFF;
    } else {
      if(second_byte == false){
        SlaveReceived = lowByte(numbers[data_counter - 1]);
      }else{
        SlaveReceived = highByte(numbers[data_counter - 1]);
      }
    }

    if(second_byte == false){
      second_byte = true;
    }else{
      second_byte = false;
      data_counter++;
    }

    received = true;

    if(data_counter == 513) {
      data_counter = 0;
    }
}
