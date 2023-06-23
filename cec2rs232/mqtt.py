import asyncio
import socket
import logging
import json
from uuid import uuid4

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class mqtt_interface (object):

    def __init__(self, driver, loop, server, port, username, password, name, discovery):
        self.driver = driver
        self.loop = loop
        self.name = name
        self.discovery = discovery

        self.server = server
        self.port = port

        self.client = mqtt.Client(client_id=uuid4().hex)
        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_close = self.on_socket_close
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        self.prefix = f"homeassistant/button/{name}"
        self.commands = {
            "volume_up": driver.volume_up,
            "volume_down": driver.volume_down,
            "toggle_mute": driver.toggle_mute,
            "mute_on": driver.mute_on,
            "mute_off": driver.mute_off,
            "power_on": driver.power_on,
            "power_off": driver.power_off
        }
        
        self.client.username_pw_set(username, password)
    
    def connect(self):
        self.client.connect(self.server, self.port)

    async def run(self):
        self.connect()

    def on_connect(self, client, userdata, flags, rc):
        if self.discovery:
            for o in self.commands.keys():
                config = {
                    "name": f"{self.name} {o}",
                    "command_topic": f"{self.prefix}/command",
                    "payload_press": o,
                    "unique_id": f"{self.name}_{o}",
                    "device": {
                        "name": self.name,
                        "identifiers": [self.name]
                    }
                }
                self.client.publish(f"{self.prefix}/{o}/config", json.dumps(config))
                logger.info(f"publishing {o} entity")
        self.client.subscribe(f"{self.prefix}/command")
        logger.info(f"connected to {self.server}")

    def on_message(self, client, userdata, msg):
        logger.info(msg.payload)
        command = msg.payload.decode()
        if command in self.commands:
            self.commands[command]()

    def on_disconnect(self, client, userdata, rc):
        logger.info(f"disconnected: {userdata} {rc}")
        self.connect()

    def on_socket_open(self, client, userdata, sock):
        def cb():
            client.loop_read()
        self.loop.add_reader(sock, cb)
        self.misc = self.loop.create_task(self.misc_loop())

    def on_socket_close(self, client, userdata, sock):
        self.loop.remove_reader(sock)
        self.misc.cancel()

    def on_socket_register_write(self, client, userdata, sock):
        def cb():
            client.loop_write()
        self.loop.add_writer(sock, cb)

    def on_socket_unregister_write(self, client, userdata, sock):
        self.loop.remove_writer(sock)

    async def misc_loop(self):
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
