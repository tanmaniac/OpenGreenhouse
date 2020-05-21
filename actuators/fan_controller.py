# Turns on fan if too hot

import argparse
import json
import time

import redis
import glog
import board
import digitalio

def parse_args():
    """ Parse command line args to get temperature and gpio pin """
    parser = argparse.ArgumentParser(prog="Fan controller")
    parser.add_argument("gpio_pin", type=int,
                        help="Board GPIO pin number to read")
    parser.add_argument(
        "threshold", type=int, help="Temperature threshold")
    parser.add_argument("--redis_host", type=str, default="localhost",
                        help="Hostname or IP of redis server")
    parser.add_argument("--redis_port", type=int, default=6379,
                        help="Port of redis server")

    args = parser.parse_args()
    
    return args

def pin_mapping(gpio_pin: int):
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

def subscribe_pubsub(topic, redis_host, redis_port):
    """ Subscribe to topic on redis, get message from topic and return response as string """
    # Connect to redis
    redis_client = redis.Redis(
        host=redis_host, port=redis_port, db=0)
    glog.info(
        f"Connected to redis instance at {args.redis_host}:{args.redis_port}")

    # Subscribe to topic and get message
    pubsub = redis_client.pubsub()
    pubsub.subscribe(topic)
    pubsub.get_message() # ignore initial subscribed message

    return pubsub

def read_message(pubsub):
    """ Call get_message until message is found, then return the message """
    while True:
        message = pubsub.get_message()
        if message:
            return message

def get_current_temp(message):
    """ Decode json message and return the current temperature """
    decoded_json = json.loads(message['data'])
    temp = decoded_json["temperature_c"]

    return temp

def main(args):
    """ It's a main function, what more can I say """
    # Get args
    gpio_pin = args.gpio_pin
    threshold = args.threshold
    redis_host = args.redis_host
    redis_port = args.redis_port

    # Find pin and set up fan
    pin = pin_mapping(args.gpio_pin)
    fan = digitalio.DigitalInOut(pin)
    fan.direction = digitalio.Direction.OUTPUT
    
    # Subscribe to sensor_msgs/humidity1 on redis
    p = subscribe_pubsub("sensor_msgs/humidity1", redis_host, redis_port)

    # Keep checking the temperature and turn the fan on/off based on threshold 
    while True:
        # Read message to get temperature
        message = read_message(p)

        temp = get_current_temp(message)
        glog.info(f"Temperature: {temp}")
    
        if temp == None:
            continue
        
        # Turn fan on/off
        if temp >= threshold:
            fan.value = True
            glog.info("Fan is on")
        else:
            fan.value = False
            glog.info(f"Fan is off")
        
        time.sleep(1)

if __name__ == "__main__":
    args = parse_args()
    main(args)