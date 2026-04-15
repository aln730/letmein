import board, busio, digitalio, wifi, socketpool, ssl, asyncio
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_character_lcd.character_lcd as characterlcd
import adafruit_pcf8574
from secrets import *
from jingles import Jingle
from app import App

def main():
    # Acckkkkk
    ack = digitalio.DigitalInOut(board.GP15)
    ack.direction = digitalio.Direction.INPUT
    ack.pull = digitalio.Pull.DOWN

    # LCD
    i2c = busio.I2C(scl=board.GP17, sda=board.GP16)
    pcf = adafruit_pcf8574.PCF8574(i2c, address=0x27)
    backlight = pcf.get_pin(3)
    backlight.switch_to_output(False)
    lcd = characterlcd.Character_LCD(
        pcf.get_pin(0), pcf.get_pin(2), pcf.get_pin(4),
        pcf.get_pin(5), pcf.get_pin(6), pcf.get_pin(7),
        20, 4
    )
    lcd.clear()

    # Jingle Jangle
    jingle = Jingle(board.GP14)

    location = secrets["location"]
    if not location:
        print("Location not set! Please set location in secrets.")
        return

    print(f"Connecting to {secrets['ssid']}")
    print('mac address:', "%02x:%02x:%02x:%02x:%02x:%02x" % tuple(map(int, wifi.radio.mac_address)))
    wifi.radio.connect(secrets['ssid'], secrets['password'])
    print(f"Connected! IP: {wifi.radio.ipv4_address}")
    pool = socketpool.SocketPool(wifi.radio)

    # MQTT
    mqtt_client = MQTT.MQTT(
        broker=secrets["broker"],
        port=secrets["port"],
        socket_pool=pool,
        ssl_context=ssl.create_default_context(),
    )
    print(f"Connecting to MQTT broker: {mqtt_client.broker}")
    mqtt_client.connect()
    mqtt_client.subscribe("letmein2/req")
    mqtt_client.subscribe("letmein2/name")
    mqtt_client.subscribe(mqtt_ack_topic)

    app = App(mqtt_client, jingle, lcd, backlight, ack)
    app.launch()

if __name__ == "__main__":
    main()
