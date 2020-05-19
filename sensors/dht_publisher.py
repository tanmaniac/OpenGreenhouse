# Publishes the current temperature and humidity on redis

import argparse
import json
import time

import redis
import glog
import adafruit_dht
import board


def parse_args():
    parser = argparse.ArgumentParser(prog="DHT11 sensor data publisher")
    parser.add_argument("gpio_pin", type=int,
                        help="Board GPIO pin number to read")
    parser.add_argument(
        "topic", type=str, help="Name of the topic under which messages will be published (will be prefixed by \"sensor_msgs/\"")
    parser.add_argument("--redis_host", type=str, default="localhost",
                        help="Hostname or IP of redis server")
    parser.add_argument("--redis_port", type=int, default=6379,
                        help="Port of redis server")

    args = parser.parse_args()
    return args


def dht_factory(gpio_pin: int):
    """
    Given a GPIO pin, this function returns a DHT device instance, provided the
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
        return adafruit_dht.DHT11(board_pins[gpio_pin])
    else:
        raise RuntimeError(
            f"Failed to create DHT11 device - GPIO pin {gpio_pin} is invalid")


def main(args):
    # Connect to redis
    redis_client = redis.Redis(
        host=args.redis_host, port=args.redis_port, db=0)
    glog.info(
        f"Connected to redis instance at {args.redis_host}:{args.redis_port}")
    topic = f"sensor_msgs/{args.topic}"

    # Set up DHT device
    dht_device = dht_factory(args.gpio_pin)
    glog.info(f"Set up DHT11 sensor on GPIO pin {args.gpio_pin}")

    glog.info(f"Publishing messages as JSONs on topic {topic}")

    # Start polling sensor and publishing to redis
    temperature_c = 0
    humidity = 0
    should_publish = False
    while True:
        try:
            # Get values from sensor
            temperature_c = dht_device.temperature
            humidity = dht_device.humidity
            # If we got this far, we should publish
            should_publish = True
        except RuntimeError as error:
            # Errors with DHT sensor are frequent, so just log the error and keep going - but don't publish!
            glog.error(f"Ignoring sensor error: {error.args[0]}")
            should_publish = False

        if should_publish:
            message = {"temperature_c": temperature_c, "humidity": humidity}
            redis_client.publish(topic, json.dumps(message))

        # Sleep for a second
        time.sleep(1)


if __name__ == "__main__":
    args = parse_args()
    main(args)
