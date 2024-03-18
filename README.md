# toshiba-ac-tuya-mqtt

Simple python script to create a gateway using Tuya IR emitter device to control Toshiba AC Appliance.

This builds on top of Paho MQTT, Tinytuya and Toshiba-AC.

https://github.com/tyge68/toshiba-ac

Toshiba IR code is computed directly in the code, meaning that the IR device needs to be defined in Tuya App but there is no need to add the AC device itself

# How to use

Configuration is performed in `config.json` file. An example file is given, juste rename and fill the data.

## MQTT Topic

The Tuya device is configured using the topic as follows:

```
MQTT_TOPIC_PREFIX/DEVICE_ID/DEVICE_KEY_ALMOST_AS_BASE64/set
```

Device ID and key shall be found using other means (see all tuya related documentation).

The key shall be encoded in base64. However, due to the fact that some base64 characters are not allowed in topic names, all `+` characters shall be replaced by `!`.

For instance the following :

```
home/toshiba_ac/bfe5db22febf00458edaqf/UihWTyA7Y1sjBVRHXWp4Iw==/set
```

## MQTT Message
MQTT message shall have the following format:

```
{"mode": "heating", "fan":"auto", "temp":"22 °C"}
```

Mode can be:
- `heating`
- `cooling`
- `drying`
- `auto`

Fan can be a value from 1 to 6. Any other value will be considered as "auto"

Temperature needs to be in Celsius. The unit is not necessary but will be remove if present in the payload.

A "unit" key could be present (optional) to separate A and B devices.

Special mode is also optional with the `special_mode` key:
- `hipower`
- `eco`
