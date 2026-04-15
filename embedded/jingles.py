import asyncio, time
from buzzer import Buzzer

class Jingle:
    def __init__(self, pin):
        self.buzzer = Buzzer(pin)

    # Big sad, can't use async play on sync functions like main()
    # probably for the best...
    def boot_sync(self):
        self.buzzer.on()
        self.buzzer.note("C4")
        time.sleep(0.1)
        self.buzzer.note("F4")
        time.sleep(0.2)
        self.buzzer.off()

    async def play(self, file):
        """Play a jingle file asynchronously."""
        with open(f"aud_jingles/{file}") as jingle_file:
            self.buzzer.on()
            for action in jingle_file:
                line = action.split('#', 1)[0].strip()
                if not line:
                    continue
                try:
                    note, duration_str = line.split(None, 1) 
                    duration = float(duration_str)
                except ValueError:
                    print("bro what")
                    continue

                if note.lower() == "rest":
                    self.buzzer.off()
                    await asyncio.sleep(duration)
                    self.buzzer.on()
                elif note.isdigit():
                    # Try playing as hz
                    hz = int(note)
                    self.buzzer.hz(hz)
                    await asyncio.sleep(duration)
                else:
                    # play a specified note
                    self.buzzer.note(note)
                    await asyncio.sleep(duration)

            self.buzzer.off()
