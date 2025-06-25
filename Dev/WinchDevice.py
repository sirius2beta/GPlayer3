/*
  Examples:
    stepper settings:          s,2000 1000 [operaton, maxSpeed acceleration]
    stepper control:           c,10000 [operaton, steps]
    stepper stop:              z,2
    set tension limit          st,-1000
    reset position             re
    return tension             t
*/
#include <AccelStepper.h>
#include <Arduino.h>
#include <U8g2lib.h>
#include "HX711.h"
#ifdef U8X8_HAVE_HW_SPI
#include <SPI.h>
#endif
#ifdef U8X8_HAVE_HW_I2C
#include <Wire.h>
#endif
U8G2_SSD1306_128X64_NONAME_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ 5, /* data=*/ 4, /* reset=*/ U8X8_PIN_NONE);  //ESP8266板子搭配SSD1306用這行
//U8G2_SSD1306_128X32_UNIVISION_1_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);
#define STEP_PIN 14
#define DIR_PIN 12

#define UPBTN 18
#define DOWNBTN 21
#define STOPBTN 19
#define SETBTN 13

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = 26;
const int LOADCELL_SCK_PIN = 33;

int WL = 0;

int BTN_STATE = 0; // 0:stop 1:up 2:down 3:reset
bool remote_controlling = false;
bool remote_rundown = false;
int PRE_BTN_STATE = -1;

int SCREEN_RATE = 1000;
int SCREEN_T = 0;

int STEPPER_CURRENT_P = 0;
int OFFSET_P = 0;

String isRunning = "S";


HX711 scale;



int split(String& lstr, String& str, char sign){
  int index = str.indexOf(sign);
      
  if(index != -1){
    lstr = str.substring(0, index);
    str = str.substring(index+1, str.length());
  }else{
    lstr = str.substring(index+1, str.length());   
  }
  return index;
}

AccelStepper stepper = AccelStepper(1, STEP_PIN, DIR_PIN, 4, 5);
long reading = -60000;
TaskHandle_t Task1;

void Task1code( void * parameter) {
    while(true) {
      reading = scale.read();
      delay(100);
  
    }
}

void setup() {
  Serial.begin(9600);
  
  pinMode(UPBTN, INPUT_PULLUP);
  pinMode(DOWNBTN, INPUT_PULLUP);
  pinMode(STOPBTN, INPUT_PULLUP);
  pinMode(SETBTN, INPUT_PULLUP);
  stepper.setMaxSpeed(1000);
  stepper.setAcceleration(500);
  u8g2.begin();
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_logisoso16_tf); //設定字型
  u8g2.drawStr(0,16,String("Pos:"+String(0)).c_str());  //輸出文字
  u8g2.sendBuffer();
  
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  Serial.println(xPortGetCoreID());
  
  xTaskCreatePinnedToCore(
      Task1code, /* Function to implement the task */
      "Task1", /* Name of the task */
      10000,  /* Stack size in words */
      NULL,  /* Task input parameter */
      0,  /* Priority of the task */
      &Task1,  /* Task handle. */
      0); /* Core where the task should run */

  delay(1000);

  
}

unsigned long initialT = millis();
int interval = 0;
int preinterval = 0;

void loop() {
  if(digitalRead(STOPBTN) == LOW){
    BTN_STATE = 0;
  }else if(digitalRead(UPBTN) == LOW){
    BTN_STATE = 1;
  }else if(digitalRead(DOWNBTN) == LOW){
    BTN_STATE = 2;
  }else if(digitalRead(SETBTN) == LOW){
    BTN_STATE = 3;
  }

  //long reading = scale.read();
  
  if(reading> WL){
    
    if(PRE_BTN_STATE == 2 || remote_rundown == true){
      BTN_STATE = 0;
      remote_rundown = false;
      Serial.println("STOP !");
      OFFSET_P = stepper.currentPosition()+OFFSET_P;
      stepper.setCurrentPosition(0);
      u8g2.clearBuffer();
      u8g2.setFont(u8g2_font_logisoso16_tf); //設定字型
      u8g2.drawStr(0,16,String("Pos:"+String(STEPPER_CURRENT_P)).c_str());  //輸出文字
      //u8g2.updateDisplayArea(0, 0,16, 8);
      u8g2.sendBuffer();
    }
  }

  if(BTN_STATE == 0){ //run up 
    if(PRE_BTN_STATE == 0){
      stepper.run();
      
    }else{
      Serial.println("STOP !");
      OFFSET_P = stepper.currentPosition()+OFFSET_P;
      stepper.setCurrentPosition(0);
      u8g2.clearBuffer();
      u8g2.setFont(u8g2_font_logisoso16_tf); //設定字型
      u8g2.drawStr(0,16,String("Pos:"+String(STEPPER_CURRENT_P)).c_str());  //輸出文字
      //u8g2.updateDisplayArea(0, 0,16, 8);
      u8g2.sendBuffer();
    }
    
  }else if(BTN_STATE == 1){ //run up 
    if(PRE_BTN_STATE == 1){
      stepper.run();
    }else if(PRE_BTN_STATE == 2){
      Serial.println("STOP !");
      OFFSET_P = stepper.currentPosition()+OFFSET_P;
      stepper.setCurrentPosition(0);
      delay(500);
      Serial.println("RUN UP !");
      u8g2.clearBuffer();
      u8g2.setFont(u8g2_font_logisoso16_tf); //設定字型
      u8g2.drawStr(0,16,String("Pos: running").c_str());  //輸出文字
      u8g2.drawStr(0,40, "  RUN UP!!");
      u8g2.setFont(u8g2_font_open_iconic_arrow_2x_t);
      u8g2.setCursor(0,40);
      u8g2.drawGlyph(0, 40, 0x47);
      //u8g2.updateDisplayArea(0, 0,16, 8);
      u8g2.sendBuffer();
      stepper.move(-1000000);
    }else{
      Serial.println("RUN UP !");
      u8g2.clearBuffer();
      u8g2.setFont(u8g2_font_logisoso16_tf); //設定字型
      u8g2.drawStr(0,16,String("Pos: running").c_str());  //輸出文字
      u8g2.drawStr(0,40, "  RUN UP!!");
      u8g2.setFont(u8g2_font_open_iconic_arrow_2x_t);
      u8g2.setCursor(0,40);
      u8g2.drawGlyph(0, 40, 0x47);
      //u8g2.updateDisplayArea(0, 0,16, 8);
      u8g2.sendBuffer();
      stepper.move(-1000000);
    }
    
  }else if(BTN_STATE == 2){ //run down
    if(PRE_BTN_STATE == 2){
      stepper.run();
    }else if(PRE_BTN_STATE == 1){
      Serial.println("STOP !");
      OFFSET_P = stepper.currentPosition()+OFFSET_P;
      stepper.setCurrentPosition(0);
      delay(500);
      u8g2.clearBuffer();
      u8g2.setFont(u8g2_font_logisoso16_tf); //設定字型
      u8g2.drawStr(0,16,String("Pos: running").c_str());  //輸出文字
      u8g2.drawStr(0,40, "  RUN DOWN!!");
      u8g2.setFont(u8g2_font_open_iconic_arrow_2x_t);
      u8g2.setCursor(0,40);
      u8g2.drawGlyph(0, 40, 0x44);
      Serial.println("RUN DOWN !");
      u8g2.sendBuffer();
      stepper.move(1000000);
    }else{
      u8g2.clearBuffer();
      u8g2.setFont(u8g2_font_logisoso16_tf); //設定字型
      u8g2.drawStr(0,16,String("Pos: running").c_str());  //輸出文字
      u8g2.drawStr(0,40, "  RUN DOWN!!");
      u8g2.setFont(u8g2_font_open_iconic_arrow_2x_t);
      u8g2.setCursor(0,40);
      u8g2.drawGlyph(0, 40, 0x44);
      Serial.println("RUN DOWN !");
      u8g2.sendBuffer();
      //steppers.setSpeed(3000);
      stepper.move(1000000);
    }
    
  }else if(BTN_STATE == 3){
      stepper.setCurrentPosition(0);
      OFFSET_P = 0;
      WL = reading + 10000;
    
  }else{

    stepper.run();
    
  }

  PRE_BTN_STATE = BTN_STATE;

  STEPPER_CURRENT_P = OFFSET_P + stepper.currentPosition();
  
  
  unsigned long currentT = millis();
  

  
  if(currentT-initialT >= 250){
    initialT = currentT;
    interval++;
  }

  long int t1 = millis();
  if(stepper.currentPosition() == stepper.targetPosition()){
    remote_controlling = false;
    isRunning = "S"; //R = running
  }else{
    isRunning = "R";  // S = stopped
  }
  if(currentT-SCREEN_T > SCREEN_RATE){
    SCREEN_T = currentT;
    Serial.println("cs,"+String(STEPPER_CURRENT_P)+","+String(reading)+","+isRunning);
    
  }

  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    Serial.flush();
    Serial.print("Receive data: ");
    Serial.println(data);
    int field = 0;
    String operation = "0";
    int index = 0;
    while(index != -1){
      index = data.indexOf(',');
      String ldata = "";
      
      if(index != -1){
        ldata = data.substring(0, index);
        data = data.substring(index+1, data.length());
      }else{
        ldata = data.substring(index+1, data.length());
      }

      
      if(field == 0){  
        //operation field
        // s : set data
        // c : control 
        // r : reset
        // z : stop, just for stepper motors
        operation = ldata;
        Serial.print("Operation:");
        Serial.println(ldata);
        if(operation == "re"){
          // reset tension and current position
          Serial.println("ack,re,0");
          stepper.setCurrentPosition(0);
          OFFSET_P = 0;
          WL = reading + 10000;
        }else if(ldata == "rq"){
          Serial.println("rs,0");
        }else if(ldata == "z"){
          //stop
          Serial.println("ack,z,0");
          OFFSET_P = stepper.currentPosition()+OFFSET_P;
          stepper.setCurrentPosition(0);
          //BTN_STATE = 0;
          
        }else if(ldata == "rp"){
          // reset current position
          stepper.setCurrentPosition(0);
          OFFSET_P = 0;
        }
      }else if(field == 1){
        if(operation == "s"){ //set
          int field2 = 0;
          String tmpdata = ldata;
          String ldata2;
          int index2 = 0;
          int pin1 = 0;  //dirPin or
          int pin2 = 0;  //setPin
          int maxSpeed = 0;
          int acc = 0;
          while(index2 != -1){
            index2 = split(ldata2, tmpdata, ' ');
            if(field2 == 0){
              Serial.print("Speed:");
              Serial.println(ldata2);//setMaxSpeed
              maxSpeed = ldata2.toInt();
            }else{
              Serial.print("Acc:");
              Serial.println(ldata2);//setMaxSpeed
              acc = ldata2.toInt();
              stepper.setAcceleration(acc);
              stepper.setMaxSpeed(maxSpeed);
            }
            field2++;
          }
        }else if(operation == "c"){
          //set move() position
          long steps = ldata.toInt()-STEPPER_CURRENT_P;
          if(steps>0){
            remote_rundown = true;
          }
          remote_controlling = true;
          stepper.move(steps);
          Serial.print("set move to:");
          Serial.println(steps);
        }else if(operation == "st"){
          //set tension
          long tension = ldata.toInt();
          WL = tension;
          Serial.print("set tension:");
          Serial.println(WL);
        }else if(operation == "t"){
          WL = ldata.toInt();
          Serial.print("WL:");
          Serial.println(WL);
        }
      }
      field ++;
    } 
  }
    long int t2 = millis();
}
