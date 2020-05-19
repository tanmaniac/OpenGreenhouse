# OpenGreenhouse

This repository contains code for a smart greenhouse controlled by a Raspberry Pi Zero W. It handles sensing the temperature, humidity, and soil moisture levels inside a greenhouse, and adjusting fan speeds, water pump speeds, and window angles accordingly.

## Hardware

- Raspberry Pi Zero W as main control board. We flash this with Raspbian Lite and solder a header onto the GPIO pins
- DHT11 temperature/humidtity sensor
- YL-69 analog soil moisture sensor - this also needs an MCP3008 or similar ADC for the Raspberry Pi to read it, since the Pi doesn't have an onboard ADC
- Fans, pumps, maybe a servo

## Software architecture

All nodes communicate over Redis pubsub. Each sensor has an associated publisher service (for example, [`dht_publisher.py`](sensors/dht_publisher.py)) that read the sensor value from the GPIO pin and publishes it to a `sensor_msgs/<name>` topic on Redis. Consumer nodes subscribe to those `sensor_msgs` topics and do some action - for example, if the temperature is too high, we might turn a fan on. 

## How to run

1. Install Docker on the Raspberry Pi:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $(id -un)
```

2. Install docker-compose to manage all the services

<TODO>

3. Launch the services

```bash
docker-compose up -f greenhouse-compose.yaml -d
```