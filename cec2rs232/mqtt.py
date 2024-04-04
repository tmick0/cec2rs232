import asyncio
import logging
import json

import aiomqtt

logger = logging.getLogger(__name__)

class mqtt_interface (object):

    def __init__(self, driver, loop, server, port, username, password, name, topic, discovery):
        self.driver = driver
        self.loop = loop
        self.name = name
        self.discovery = discovery

        self.server = server
        self.port = port
        self.username = username
        self.password = password

        self.topic = topic
        self.commands = {
            "volume_up": driver.volume_up,
            "volume_down": driver.volume_down,
            "toggle_mute": driver.toggle_mute,
            "mute_on": driver.mute_on,
            "mute_off": driver.mute_off,
            "power_on": driver.power_on,
            "power_off": driver.power_off
        }
    
    async def connect(self):
        logger.info(f"connecting to {self.server}:{self.port}")

        async def advertise_loop():
            while True:
                await self.advertise(client)
                await asyncio.sleep(15)

        client = aiomqtt.Client(self.server, port=self.port, username=self.username, password=self.password)

        while True:
            advertise_task = None
            try:
                async with client:
                    await client.subscribe(f"{self.topic}/command", qos=1)
                    logger.info(f"connected to {self.server}")
                    if self.discovery:
                        advertise_task = self.loop.create_task(advertise_loop())
                    async for msg in client.messages:
                        logger.info(msg.payload)
                        command = msg.payload.decode()
                        if command in self.commands:
                            self.commands[command]()
                        
            except aiomqtt.MqttError as e:
                if advertise_task:
                    advertise_task.cancel()
                    try:
                        await advertise_task
                    except asyncio.CancelledError:
                        pass
                logger.warning("connection failed or lost, will retry")
                logger.exception(e)
                await asyncio.sleep(5)


    async def run(self):
        await self.connect() 

    async def advertise(self, client):
        prefix = f"homeassistant/button/{self.name}"
        for o in self.commands.keys():
            config = {
                "name": f"{self.name} {o}",
                "command_topic": f"{self.topic}/command",
                "payload_press": o,
                "unique_id": f"{self.name}_{o}",
                "device": {
                    "name": self.name,
                    "identifiers": [self.name]
                }
            }
            logger.info(f"publishing {o} entity")
            await client.publish(f"{prefix}/{o}/config", payload=json.dumps(config), qos=1)


