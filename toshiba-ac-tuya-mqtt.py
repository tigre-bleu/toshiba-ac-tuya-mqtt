#!/usr/bin/env python3

import paho.mqtt.client as mqtt
from tinytuya import Contrib
from toshiba_ac.generator import IRCodeGenerator, UnitType, ModeType, SpecialModeType, FanType
import time
import json
import base64
import os
import sys

# MQTT Config
with open( os.path.dirname(os.path.realpath(sys.argv[0])) + '/config.json') as f:
    conf = json.load(f)

MQTT_SERVER = conf["server"]
MQTT_PORT = int(conf["port"])
MQTT_TOPIC_PREFIX = conf["topic_prefix"]
MQTT_TOPIC_STATUS = MQTT_TOPIC_PREFIX + "status"
MQTT_TOPIC_CMD_SUFFIX = "set"

# Tuya IR Device
class Device():
    def __init__(self, tuya_id, tuya_key):
        print(f"New device %s with key %s" % (tuya_id, tuya_key))
        self.head = "010ED80000000000030015004000AB"
        ip = "Auto" # We rely on tinytuya to get the right IP
        self.device = Contrib.IRRemoteControlDevice(tuya_id, ip, tuya_key)

    def send(self, code):
        self.device.send_key(self.head, code)

# Device Manager
class DeviceManager():
    def __init__(self):
        self.devices = {}

    def create_device(self, id, key):
        self.devices[id] = Device(id, key)
        return self.devices[id]

    def get_device(self, id, key):
        if id in self.devices.keys():
            return self.devices[id]
        else:
            return self.create_device(id, key)

def get_mode(mode):
	if mode == "auto" :
		return ModeType.AutoMode
	elif mode == "cooling":
		return ModeType.CoolingMode
	elif mode == "drying":
		return ModeType.DryinggMode
	elif mode == "heating":
		return ModeType.HeatingMode
	else:
		return ModeType.PwrOffMode

def get_special_mode(special_mode):
	if special_mode == None :
		return SpecialModeType.NoSpecialMode
	elif special_mode == "hipower" :
		return SpecialModeType.HiPowerSpecialMode
	elif special_mode == "eco" :
		return SpecialModeType.EcoSpecialMode
	else:
		return SpecialModeType.NoSpecialMode

def get_fan(fan):
	if fan == "1" :
		return FanType.Fan1
	elif fan == "2":
		return FanType.Fan2
	elif fan == "3":
		return FanType.Fan3
	elif fan == "4":
		return FanType.Fan4
	elif fan == "5":
		return FanType.Fan5
	elif fan == "6":
		return FanType.Fan6
	else:
		return FanType.FanAuto

def get_unit(unit):
	if unit is None:
		return UnitType.UnitA
	elif unit == "b":
		return UnitType.UnitB
	else:
		return UnitType.UnitB

def send_command(emitter, mode, fan, temp_celsius, unit=None, special_mode=None):

    mode = get_mode(mode)
    special_mode = get_special_mode(special_mode)
    fan = get_fan(fan)
    temp_celsius = int(float(temp_celsius))
    unit = get_unit(unit)

    # Generate a Toshiba AC code
    generated = generator.make_mode_fan_temp(unit, mode, special_mode, fan, temp_celsius)[0].split(" ")

    # Build raw IR code
    t = ["01$$0048"]
    t = t + [part[2::] for part in generated]
    t.append("@$")
    
    key = "".join(t)
    
    # Send code
    emitter.send(key)


# Create MQTT client
def on_connect(mqttc, userdata, flags, rc):
    print("MQTT Client Connected")
    (result, mid)=mqttc.subscribe(MQTT_TOPIC_PREFIX + "#")

def on_subscribe(mqttc, userdata, mid, granted_qos):
    mqttc.publish(MQTT_TOPIC_STATUS, 'online')

def on_message(mqttc, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')

    id = topic.replace(MQTT_TOPIC_PREFIX, "").split("/")[0]
    key = base64.b64decode(topic.replace(MQTT_TOPIC_PREFIX, "").split("/")[1].replace("!", "+")).decode('utf-8')
    cmd = json.loads(payload)
    print(f"%s : %s" % (id, cmd))
    
    mode = cmd["mode"]
    fan = cmd["fan"]
    temp_celsius = cmd["temp"].replace(" °C", "").replace("°C", "").replace("°c", "")
    if "unit" in cmd.keys():
        unit = cmd["unit"]  
    else:
        unit = None
    if "special_mode" in cmd.keys():
        special_mode = cmd["special_mode"]
    else:
        special_mode = None

    device = device_manager.get_device(id, key)
    send_command(device, mode, fan, temp_celsius, unit, special_mode)


def start_mqtt():

    # MQTT
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_subscribe = on_subscribe

    mqttc.will_set(MQTT_TOPIC_STATUS, payload="offline", qos=0, retain=True)
    mqttc.connect(MQTT_SERVER, MQTT_PORT, 60)
    mqttc.loop_forever()

if __name__ == '__main__':

    # Create a Toshiba AC code generator
    generator = IRCodeGenerator()

    # Create a manager for all future devices
    device_manager = DeviceManager()

    start_mqtt()


