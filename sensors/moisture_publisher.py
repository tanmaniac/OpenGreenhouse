# Publishes moisture readings from a YL-69 moisture sensor connected to an ADS1115 ADC

import argparse
import json
import time

import redis
import glog
import busio
import board
import digitalio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

SLEEP_TIME_SEC = 10


def parse_args():
    parser = argparse.ArgumentParser(prog="moisture_publisher",
                                     description="YL-69 moisture sensor data publisher. Reads ADC input from the first I2C bank \
                                         (pins 3 and 5 on Raspberry Pi header), and expects the analog input to be on pin A0.")
    parser.add_argument("sensor_enable", type=int,
                        help="GPIO pin which is connected to the base of the transistor which enables the moisture sensor")
    parser.add_argument(
        "topic", type=str, help="Name of the topic under which messages will be published (will be prefixed by \"sensor_msgs/\"")
    parser.add_argument("--redis_host", type=str, default="localhost",
                        help="Hostname or IP of redis server")
    parser.add_argument("--redis_port", type=int, default=6379,
                        help="Port of redis server")

    args = parser.parse_args()
    return args


def get_board_pin(gpio_pin: int):
    """
    Given a GPIO pin, this function returns a pin mapping, provided the
    requested pin is one of the pins listed below. We disallow certain pins to
    prevent conflicts with SPI and I2C interfaces.
    """
    board_pins = {
        4: board.D4,
        17: board.D17,
        27: board.D27,
        22: board.D22,
        5: board.D5,
        6: board.D6,
        7: board.D7,
        13: board.D13,
        19: board.D19,
        26: board.D26,
        23: board.D23,
        24: board.D24,
        25: board.D25,
        12: board.D12,
        16: board.D16,
        20: board.D20,
        21: board.D21
    }

    if gpio_pin in board_pins.keys():
        return board_pins[gpio_pin]
    else:
        raise RuntimeError(
            f"Failed to create pin mapping - GPIO pin {gpio_pin} is invalid")


def get_adc_interface():
    """
    Create and return an ADS1115 object set up for reading analog inputs
    """
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    return ads


def setup_moisture_sensor(gpio_pin: int):
    """
    Sets up the GPIO pin that enables/disables the moisture sensor
    """
    pin = get_board_pin(gpio_pin)
    sensor_enable = digitalio.DigitalInOut(pin)
    sensor_enable.direction = digitalio.Direction.OUTPUT
    return sensor_enable


def main(args):
    # Connect to redis
    redis_client = redis.Redis(
        host=args.redis_host, port=args.redis_port, db=0)
    glog.info(
        f"Connected to redis instance at {args.redis_host}:{args.redis_port}")
    topic = f"sensor_msgs/{args.topic}"

    # Set up analog-to-digital converter
    sensor_enable = setup_moisture_sensor(args.sensor_enable)
    adc = get_adc_interface()
    glog.info("Set up I2C interface and connected to ADS1115")
    input_channel = AnalogIn(adc, ADS.P0)
    glog.info("Ready to read input on channel P0")

    glog.info(f"Starting to publish messages as JSONs on topic {topic}")
    # Start polling sensor and publishing to redis
    while True:
        # Enable sensor and wait a second
        sensor_enable.value = True
        time.sleep(0.5)
        # Take a reading
        value, voltage = input_channel.value, input_channel.voltage
        time.sleep(0.5)
        # Disable the sensor again
        sensor_enable.value = False

        glog.info(f"value: {value}, raw voltage: {voltage}")

        message = {"value": value, "voltage": voltage}
        redis_client.publish(topic, json.dumps(message))

        # Sleep for a second
        time.sleep(SLEEP_TIME_SEC)


if __name__ == "__main__":
    args = parse_args()
    main(args)
