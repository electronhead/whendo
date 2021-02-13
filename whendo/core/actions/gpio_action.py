"""
These classes perform simple operations on pins.
"""
try:
    import RPi.GPIO as GPIO
except:
    import Mock.GPIO as GPIO

from whendo.core.action import Action

class SetPin(Action):
    """
    For the specified pin, sets to HIGH if on=True, to LOW if on=False.
    """
    pin:int
    on:bool

    def execute(self, tag:str=None, scheduler_info:dict=None):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.HIGH if self.on else GPIO.LOW)

class TogglePin(Action):
    """
    For the specified pin, sets to HIGH if LOW, to LOW if HIGH.
    """
    pin:int

    def execute(self, tag:str=None, scheduler_info:dict=None):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, not GPIO.input(self.pin))

class Cleanup(Action):
    """
    Clean up the pins. See the docs for GPIO.cleanup().
    """
    cleanup:str='cleanup'

    def execute(self, tag:str=None, scheduler_info:dict=None):
        GPIO.cleanup()