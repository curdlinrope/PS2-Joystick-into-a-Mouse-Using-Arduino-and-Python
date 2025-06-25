const int xPin = A0;
const int yPin = A1;
const int buttonPin = 7;

void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  Serial.begin(9600);
}

void loop() {
  int xVal = analogRead(xPin) - 512;
  int yVal = analogRead(yPin) - 512;
  bool isPressed = digitalRead(buttonPin) == LOW;

  if (isPressed) {
    Serial.println("PRESS");
  } else {
    Serial.print(xVal);
    Serial.print(",");
    Serial.println(yVal);
  }

  delay(10);
}
