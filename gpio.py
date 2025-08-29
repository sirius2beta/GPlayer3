import Jetson.GPIO as GPIO
import time

PIN = 29  # BOARD pin 31

GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN, GPIO.OUT)

GPIO.output(PIN, GPIO.HIGH)  # LED ON
time.sleep(10)
GPIO.output(PIN, GPIO.LOW)   # LED OFF

GPIO.cleanup()
