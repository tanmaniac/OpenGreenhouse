# Notes from setting up Greenhouse on Raspberry Pi Zero W

## Docker installation

You can't use the Docker repo to install `docker` on Raspberry Pi - instead had to use convenience script:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $(id -un)
```

**Docker's architecture detection is a little flaky** so running something like `docker run --rm hello-world` doesn't work out of the box. We have to instead specify the `arm32v6` images.

## Running redis

Apparently this helps:

```bash
echo "vm.overcommit_memory=1" | sudo tee -a /etc/sysctl.conf
```

A basic instance:

```bash
docker run --name redis -d -p 127.0.0.1:6379:6379 \
                           --restart unless-stopped \
                           arm32v6/redis:5-alpine \
                           --appendonly yes \
                           --maxmemory 256mb \
                           --tcp-backlog 128
```

Get redis-cli:

```bash
sudo apt install redis-tools
```

## Temparature and humidity sensor

The temperature and humidity sensor we're using is a generic variant of the Adafruit DHT11, which transmits serial data over a single GPIO pin. This means we need some kind of driver library to decode the signal; luckily Adafruit provides one (with Python bindings!): https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/python-setup

```bash
sudo apt install -y python3-pip libgpiod2
pip3 install -U RPI.GPIO adafruit-blinka 
pip3 install -U adafruit-circuitpython-dht
``` 