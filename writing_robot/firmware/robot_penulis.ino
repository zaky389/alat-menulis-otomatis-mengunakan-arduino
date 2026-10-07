/*
 * ================================================================
 * ROBOT PENULIS AI - Firmware Arduino
 * ================================================================
 * 
 * Firmware untuk mengontrol stepper motor XY dan servo pen up/down.
 * Menerima G-code sederhana melalui Serial dari Python.
 * 
 * PERINTAH YANG DIDUKUNG:
 *   G0  X__ Y__ F__  -> Rapid move (pen up, gerak cepat)
 *   G1  X__ Y__ F__  -> Linear move (pen down, menulis)
 *   G28              -> Home semua axis
 *   M3  S__          -> Set sudut servo (pen up/down)
 *   M5               -> Servo off
 *   M17              -> Enable motors
 *   M18              -> Disable motors
 *   M114             -> Report posisi
 *   M999             -> Reset
 * 
 * KONEKSI PIN:
 *   Stepper X: STEP=2, DIR=5, EN=8
 *   Stepper Y: STEP=3, DIR=6, EN=8
 *   Servo:     Pin 11
 *   Endstop X: Pin 9
 *   Endstop Y: Pin 10
 * 
 * ================================================================
 */

#include <Arduino.h>

#if __has_include(<Servo.h>)
#include <Servo.h>
#else
// Fallback for environments without the Arduino Servo library installed.
class Servo {
public:
    void attach(int) {}
    void write(int) {}
};
#endif

// ================================================================
// PIN DEFINITIONS (CNC Shield V3 compatible)
// ================================================================
#define STEP_X_PIN    2
#define DIR_X_PIN     5
#define STEP_Y_PIN    3
#define DIR_Y_PIN     6
#define ENABLE_PIN    8     // Shared enable untuk semua stepper

#define SERVO_PIN     11    // Pin servo (pen up/down)

#define ENDSTOP_X_PIN 9     // Limit switch X (opsional)
#define ENDSTOP_Y_PIN 10    // Limit switch Y (opsional)

// ================================================================
// KONFIGURASI MOTOR
// ================================================================
#define STEPS_PER_MM  80.0  // Steps per milimeter
                            // GT2 belt + 20T pulley + 1/16 microstepping
                            // = 200 * 16 / (20 * 2) = 80

#define MAX_FEEDRATE  3600  // Maximum feedrate (mm/min)
#define DEFAULT_FEEDRATE 1200  // Default feedrate (mm/min)

#define HOMING_SPEED  500   // Homing speed (mm/min)

// ================================================================
// KONFIGURASI SERVO
// ================================================================
#define PEN_UP_ANGLE   70   // Sudut servo pen naik
#define PEN_DOWN_ANGLE 40   // Sudut servo pen turun
#define PEN_DELAY      150  // Delay setelah gerakan servo (ms)

// ================================================================
// VARIABEL GLOBAL
// ================================================================
Servo penServo;

float currentX = 0.0;  // Posisi X saat ini (mm)
float currentY = 0.0;  // Posisi Y saat ini (mm)
float feedrate = DEFAULT_FEEDRATE;  // Kecepatan saat ini (mm/min)

bool motorsEnabled = true;
bool penDown = false;

// Buffer untuk parsing G-code
char cmdBuffer[128];
int cmdIndex = 0;

// ================================================================
// SETUP
// ================================================================
void setup() {
    Serial.begin(115200);
    
    // Setup pin motor
    pinMode(STEP_X_PIN, OUTPUT);
    pinMode(DIR_X_PIN, OUTPUT);
    pinMode(STEP_Y_PIN, OUTPUT);
    pinMode(DIR_Y_PIN, OUTPUT);
    pinMode(ENABLE_PIN, OUTPUT);
    
    // Enable motors
    digitalWrite(ENABLE_PIN, LOW);  // LOW = enabled untuk CNC Shield
    
    // Setup endstops
    pinMode(ENDSTOP_X_PIN, INPUT_PULLUP);
    pinMode(ENDSTOP_Y_PIN, INPUT_PULLUP);
    
    // Setup servo
    penServo.attach(SERVO_PIN);
    penServo.write(PEN_UP_ANGLE);
    delay(500);
    
    Serial.println("ROBOT_PENULIS_READY");
}

// ================================================================
// MAIN LOOP
// ================================================================
void loop() {
    // Baca perintah serial
    while (Serial.available() > 0) {
        char c = Serial.read();
        
        if (c == '\n' || c == '\r') {
            if (cmdIndex > 0) {
                cmdBuffer[cmdIndex] = '\0';
                processCommand(cmdBuffer);
                cmdIndex = 0;
            }
        } else {
            if (cmdIndex < sizeof(cmdBuffer) - 1) {
                cmdBuffer[cmdIndex++] = c;
            }
        }
    }
}

// ================================================================
// COMMAND PARSER
// ================================================================
void processCommand(char* cmd) {
    // Skip whitespace
    while (*cmd == ' ') cmd++;
    
    if (cmd[0] == 'G') {
        int gcode = atoi(cmd + 1);
        
        switch (gcode) {
            case 0:   // G0 - Rapid move
            case 1: { // G1 - Linear move
                float targetX = currentX;
                float targetY = currentY;
                float f = feedrate;
                
                // Parse parameters
                char* ptr = cmd;
                while (*ptr) {
                    if (*ptr == 'X' || *ptr == 'x') {
                        targetX = atof(ptr + 1);
                    } else if (*ptr == 'Y' || *ptr == 'y') {
                        targetY = atof(ptr + 1);
                    } else if (*ptr == 'F' || *ptr == 'f') {
                        f = atof(ptr + 1);
                    }
                    ptr++;
                }
                
                feedrate = constrain(f, 1, MAX_FEEDRATE);
                linearMove(targetX, targetY, feedrate);
                break;
            }
            
            case 28: // G28 - Home
                homeAxes();
                break;
                
            default:
                Serial.print("error:unknown G");
                Serial.println(gcode);
                return;
        }
    }
    else if (cmd[0] == 'M') {
        int mcode = atoi(cmd + 1);
        
        switch (mcode) {
            case 3: { // M3 S__ - Set servo angle
                char* sPtr = strchr(cmd, 'S');
                if (!sPtr) sPtr = strchr(cmd, 's');
                if (sPtr) {
                    int angle = atoi(sPtr + 1);
                    angle = constrain(angle, 0, 180);
                    penServo.write(angle);
                    penDown = (angle <= PEN_DOWN_ANGLE + 10);
                    delay(PEN_DELAY);
                }
                break;
            }
            
            case 5: // M5 - Servo off
                penServo.write(PEN_UP_ANGLE);
                penDown = false;
                delay(PEN_DELAY);
                break;
                
            case 17: // M17 - Enable motors
                digitalWrite(ENABLE_PIN, LOW);
                motorsEnabled = true;
                break;
                
            case 18: // M18 - Disable motors
                digitalWrite(ENABLE_PIN, HIGH);
                motorsEnabled = false;
                break;
                
            case 114: // M114 - Report position
                Serial.print("X:");
                Serial.print(currentX, 3);
                Serial.print(" Y:");
                Serial.print(currentY, 3);
                Serial.print(" Pen:");
                Serial.println(penDown ? "DOWN" : "UP");
                return;
                
            case 999: // M999 - Reset
                currentX = 0;
                currentY = 0;
                penServo.write(PEN_UP_ANGLE);
                penDown = false;
                Serial.println("reset");
                break;
                
            default:
                Serial.print("error:unknown M");
                Serial.println(mcode);
                return;
        }
    }
    else {
        Serial.println("error:unknown command");
        return;
    }
    
    Serial.println("ok");
}

// ================================================================
// GERAKAN LINEAR (Bresenham-like algorithm)
// ================================================================
void linearMove(float targetX, float targetY, float feed) {
    // Hitung delta dalam steps
    long deltaStepsX = (long)((targetX - currentX) * STEPS_PER_MM);
    long deltaStepsY = (long)((targetY - currentY) * STEPS_PER_MM);
    
    // Set direction
    digitalWrite(DIR_X_PIN, deltaStepsX >= 0 ? HIGH : LOW);
    digitalWrite(DIR_Y_PIN, deltaStepsY >= 0 ? HIGH : LOW);
    
    long absX = abs(deltaStepsX);
    long absY = abs(deltaStepsY);
    long maxSteps = max(absX, absY);
    
    if (maxSteps == 0) return;
    
    // Hitung delay per step berdasarkan feedrate
    // feed dalam mm/min -> mm/s = feed/60
    // step_delay = 1/speed_in_steps_per_sec
    float distanceMM = sqrt(sq(targetX - currentX) + sq(targetY - currentY));
    float timeSeconds = distanceMM / (feed / 60.0);
    float stepDelayUs = (timeSeconds / maxSteps) * 1000000.0;
    
    // Clamp minimum delay
    stepDelayUs = max(stepDelayUs, 25.0);
    
    // Bresenham line algorithm
    long errorX = 0;
    long errorY = 0;
    
    for (long i = 0; i < maxSteps; i++) {
        errorX += absX;
        errorY += absY;
        
        if (errorX >= maxSteps) {
            errorX -= maxSteps;
            digitalWrite(STEP_X_PIN, HIGH);
        }
        if (errorY >= maxSteps) {
            errorY -= maxSteps;
            digitalWrite(STEP_Y_PIN, HIGH);
        }
        
        delayMicroseconds((unsigned int)min(stepDelayUs, 16000.0));
        
        digitalWrite(STEP_X_PIN, LOW);
        digitalWrite(STEP_Y_PIN, LOW);
        
        if (stepDelayUs > 16000) {
            // Untuk delay sangat panjang, gunakan delay bertahap
            delay((unsigned long)(stepDelayUs / 1000.0) - 16);
        }
    }
    
    currentX = targetX;
    currentY = targetY;
}

// ================================================================
// HOMING
// ================================================================
void homeAxes() {
    // Angkat pena dulu
    penServo.write(PEN_UP_ANGLE);
    penDown = false;
    delay(PEN_DELAY);
    
    // Home X (gerak ke kiri sampai endstop)
    digitalWrite(DIR_X_PIN, LOW);  // Arah negatif
    while (digitalRead(ENDSTOP_X_PIN) == HIGH) {
        digitalWrite(STEP_X_PIN, HIGH);
        delayMicroseconds(400);
        digitalWrite(STEP_X_PIN, LOW);
        delayMicroseconds(400);
    }
    
    // Home Y (gerak ke atas sampai endstop)
    digitalWrite(DIR_Y_PIN, LOW);  // Arah negatif
    while (digitalRead(ENDSTOP_Y_PIN) == HIGH) {
        digitalWrite(STEP_Y_PIN, HIGH);
        delayMicroseconds(400);
        digitalWrite(STEP_Y_PIN, LOW);
        delayMicroseconds(400);
    }
    
    // Mundur sedikit dari endstop
    digitalWrite(DIR_X_PIN, HIGH);
    digitalWrite(DIR_Y_PIN, HIGH);
    for (int i = 0; i < 160; i++) {  // ~2mm
        digitalWrite(STEP_X_PIN, HIGH);
        digitalWrite(STEP_Y_PIN, HIGH);
        delayMicroseconds(400);
        digitalWrite(STEP_X_PIN, LOW);
        digitalWrite(STEP_Y_PIN, LOW);
        delayMicroseconds(400);
    }
    
    currentX = 0.0;
    currentY = 0.0;
}
