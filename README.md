# cec2rs232

## Overview

This project aims to turn a Raspberry Pi into a bridge between the HDMI CEC standard
and arbitrary control protocols for audio systems.

The intent is to automate powering up and controlling volume of certain hifi systems
as you would a dedicated home theater receiver.

RS-232 and IR controls are supported. RS-232 requires a USB adapter, while IR can be
controlled via GPIO.

## Installation

It is assumed that the Raspberry Pi is not doing anything important so it is suitable
to install cec2rs232 globally and run it as root. The package is available from pip:

```
sudo pip install cec2rs232
```

Copy `cec2rs232.example.json` to `/etc/cec2rs232/cec2rs232.json`. Edit it as needed.

Then you can have it run as a service using the provided systemd file:

```
sudo cp systemd/cec2rs232.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cec2rs232
sudo systemctl start cec2rs232
```

This will start the process and ensure it starts again at boot.

## Supported televisions

The intent is to support any TV with CEC capabilities. However, the project was originally
developed using a Samsung TU7000 and therefore may unintentionally be designed against its
quirks. Please report any problems you experience with another model of television and an
attempt will be made to add support.

## Supported audio devices

### Cambridge Audio CXA61/81

These two integrated amplifiers support controlling power, source, and mute status over RS-232 but
require IR for volume controls.

A 3.5mm TRS can be connected to the IR In port on the back of the amp instead of using an actual IR
transmitter. In this case, connect the GPIO pin to the tip and ground to the sleeve. The ring need
not be connected.

#### Driver name:

`cambridge_cxa61`

#### Parameters:

| Name          | Type               | Description                                                         |
|---------------|--------------------|---------------------------------------------------------------------|
| `serial_port` | string             | Path to serial device, e.g. "/dev/ttyUSB0"                          |
| `ir_gpio_pin` | integer            | GPIO pin number driving the IR transmitter                          |
| `tv_source`   | string (optional)  | Source to activate when TV turns on, e.g. "D2". Omit to not change. |

### Others

Please feel free to make a pull request to add support for other devices.

## Dependencies

Bindings for libCEC are required: `sudo apt install python3-cec`.

If using a virtual environment, specify `--system-site-packages` so the native libcec can be used.

Pigpiod is required: `sudo apt install pigpiod && sudo systemctl enable pigpiod && sudo systemctl start pigpiod`.

Other dependencies should be brought in automatically by pip.

## License and attribution

Released under the terms of the [MIT License](LICENSE.md).
