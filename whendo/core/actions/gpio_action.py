"""
These classes perform simple operations on pins.
"""
try:
    import RPi.GPIO as GPIO
except:
    import Mock.GPIO as GPIO

import logging
from whendo.core.action import Action

logger = logging.getLogger(__name__)


class SetPin(Action):
    """
    For the specified pin, sets to HIGH if on=True, to LOW if on=False.
    """

    pin: int
    on: bool

    def description(self):
        return f"This action sets pin ({self.pin}) output to ({'GPIO.HIGH' if self.on else 'GPIO.LOW'})."

    def execute(self, tag: str = None, scheduler_info: dict = None):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.HIGH if self.on else GPIO.LOW)
        return self.on


class TogglePin(Action):
    """
    For the specified pin, sets to HIGH if LOW, to LOW if HIGH.
    """

    pin: int

    def description(self):
        return f"This action sets pin ({self.pin}) output to GPIO.HIGH if GPIO.input is GPIO.LOW else GPIO.LOW."

    def execute(self, tag: str = None, scheduler_info: dict = None):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)
        result = not GPIO.input(self.pin)
        GPIO.output(self.pin, result)
        return result


class CleanupPins(Action):
    """
    Clean up the pins. See the docs for GPIO.cleanup().
    """

    cleanup_pins: str = "cleanup_pins"

    def description(self):
        return f"This action executes GPIO.cleanup."

    def execute(self, tag: str = None, scheduler_info: dict = None):
        GPIO.cleanup()
        return False
