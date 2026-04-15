import asyncio
from secrets import secrets

LOCATION_NAMES = {
    "n_stairs": "North Side Stairwell",
    "s_stairs": "South Side Stairwell",
    "level_a":  "Level A Elevator",
    "level_1":  "Level 1 Elevator",
    "l_well":   "L Well",
}

JINGLE_FILES = {
    "n_stairs": "n_stairs.jingle",
    "s_stairs": "s_stairs.jingle",
    "level_a":  "level_a.jingle",
    "level_1":  "tron.jingle",
    "l_well":   "l_well.jingle",
}

JINGLE_BOOT = "tron.jingle"
JINGLE_ACK  = "ack.jingle"


class App:
    def __init__(self, mqtt_client, jingle, lcd, backlight, ack):
        self.mqtt     = mqtt_client
        self.jingle   = jingle
        self.lcd      = lcd
        self.backlight = backlight
        self.ack      = ack

        self.current_location = None
        self.location_loops   = {}

        self.mqtt.on_message = self._on_message

    # Display

    def _show_location(self, location_code, name):
        location = LOCATION_NAMES.get(location_code, location_code)
        self.lcd.clear()
        self.lcd.message = (
            "Name:\n"
            f"{name[:20]}\n"
            "Location:\n"
            f"{location[:20]}"
        )

    # Jingle Jangle

    async def _loop_jingle(self, file, location_code):
        while location_code in self.location_loops:
            try:
                await self.jingle.play(file)
            except FileNotFoundError:
                print(f"[ERROR] Missing jingle: {file}")
                break
            except asyncio.CancelledError:
                self.jingle.buzzer.off()
                break
            await asyncio.sleep(0)

    def _stop_all_jingles(self):
        for loc, task in list(self.location_loops.items()):
            task.cancel()
            del self.location_loops[loc]
        self.jingle.buzzer.off()

    # MQTT

    def _on_message(self, client, topic, msg):
        msg_str = msg.decode() if isinstance(msg, bytes) else str(msg)

        if topic == "letmein2/req":
            self.current_location = msg_str

        elif topic == "letmein2/name":
            if self.current_location is None:
                return

            self.backlight.value = True
            self._show_location(self.current_location, msg_str)

            file = JINGLE_FILES.get(self.current_location)
            if file and self.current_location not in self.location_loops:
                task = asyncio.create_task(
                    self._loop_jingle(file, self.current_location)
                )
                self.location_loops[self.current_location] = task

    # Ackkkkkk

    async def _handle_ack(self):
        while True:
            if self.ack.value:
                print("[INPUT] Button pressed!")
                self._stop_all_jingles()
                await asyncio.sleep(0.5)

                self.lcd.clear()
                self.lcd.message = "CHOMMMMMMMMMMMMMMMMM"
                await asyncio.sleep(2)

                self.lcd.clear()
                self.backlight.value = False
                self.mqtt.publish("letmein2/ack", secrets["location"])
                await asyncio.sleep(1)

            await asyncio.sleep(0.05)

    # Moop

    async def _mqtt_loop(self):
        while True:
            self.mqtt.loop()
            await asyncio.sleep(0)

    async def _run(self):
        try:
            await self.jingle.play(JINGLE_BOOT)
        except FileNotFoundError:
            print("[WARN] Missing boot jingle")

        await asyncio.gather(
            self._mqtt_loop(),
            self._handle_ack(),
        )

    def launch(self):
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            print("Exiting...")
            self._stop_all_jingles()
            self.lcd.clear()
            self.backlight.value = False
