# shimmer-listener

## THIS PROJECT IS ARCHIVED, PLEASE FEEL FREE TO CONTACT ME IF YOU WISH TO BE A MAINTAINER OR FORK IT.

This is a project that started from the idea of having a general library that interacted with shimmer apps for tinyos, 
inspired from the python demo scripts that can be found inside the sub-directories of the 
[tinyos shimmer apps repository](https://github.com/ShimmerResearch/tinyos-shimmer).

## Contents

- [shimmer-listener](#shimmer-listener)
  - [Contents](#contents)
  - [About](#about)
    - [Presentation protocol](#presentation-protocol)
  - [Installation](#installation)
    - [Windows](#windows)
    - [Debian-like](#debian-like)
  - [Usage](#usage)
    - [Documentation](#documentation)
    - [Bt Master example](#bt-master-example)
    - [Callbacks](#callbacks)
  - [Console Scripts](#console-scripts)
    - [shimmer-printer](#shimmer-printer)
    - [shimmer-btslave](#shimmer-btslave)

  
## About

This library allows you to connect to a Shimmer2 mote via Bluetooth both in Master and Slave mode, interacting with it 
via the shimmer-apps precedently introduced (even if it's possible to create custom interactions).

For now, there's only support for the BluetoothMasterTest app for Master-mode motes. For what concerns Slave-mode motes, 
a small initialization protocol (the **presentation** protocol) is used to let the master node know about the data format 
used by the mote.

The received data can be handled via a data processing function that has to be passed at init time, where you define 
what to do with each instance of incoming data (more on this in the example below).

### Presentation protocol

The presentation protocol is just a small protocol through which a BT Slave Shimmer describes the data frames that 
are to be expected when a BT Master initiates a connection. Its structure is the following:

```c
#define MAX_FMT_LEN 10
#define MAX_STR_LEN 10
#define MAX_KEY_NUM 10

typedef char key_string[MAX_STR_LEN];

typedef struct {
    uint8_t framesize;
    uint8_t chunklen;
    char format[MAX_FMT_LEN];
    key_string keys[MAX_KEY_NUM];
} frameinfo;
```

To let your nesC app implement this protocol, just copy this C snippet into a header file or directly into the 
nesC app implementation, create an instance of frameinfo containing your metadata and send it as the first Bluetooth 
message (in Bluetooth.connectionMade).

The struct fields refer to:

- **framesize**, the size of a single frame, meaning the buffer size that you periodically forward to the BT Master.
- **chunklen**, the size of one chunk of the frame, a contiguous unit of related data packed into the frame.
- **format**, the format of the data packed into the chunk, this refers to the [python 3 struct library format](https://docs.python.org/3/library/struct.html#format-characters).
- **keys**, a list of keys describing each sensed data packed into a chunk.

**e.g.**

A Shimmer2r streaming accelerometer + battery data, packs the data as four 16 bit instances in an 8 B chunk. A full 
buffer is 120 B wide, containing a total of 15 8 B chunks.

Then we'll have:

- framesize = 120 B
- chunklen = 8 B
- format = "hhhh" (h = short int aka 2 B integer in python struct terms)
- keys = {"accel_x", "accel_y", "accel_z", "batt"}

## Installation

If you have any problems installing or building a version of pybluez for your target platform, I have a repository hosting some pre-compiled wheels for different python version and platforms, [you can find the wheels here](https://github.com/Abathargh/pybluez-wheels/).

### Windows

You need to have Microsoft Visual C++ installed in order to build a wheel for pybluez during the installation process.

Get [Visual Studio Installer](https://visualstudio.microsoft.com/it/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16) here, go to Workloads and install the whole Build Tools for C++ suite, which is the first option in the top left corner.

Then, you can just:
```bash
pip install .
```

**IMPORTANT**

During testing on Win10 with Python 3.7 and 3.8, using pybluez 0.23, strange runtime errors (OSError) started popping out. For now, if this happens, the only thing that seems to work 100% of the times is installing by cloning the repository and using the setup.py script as suggested by @demanbart in [this comment](https://github.com/pybluez/pybluez/issues/180#issuecomment-397547920):

```bash
git clone https://github.com/pybluez/pybluez
cd pybluez
python setup.py install
```

### Debian-like

**N.B. Ubuntu for Raspberry Pi**

When trying to make the library work on Ubuntu 20.10 for Raspberry Pi, 
you should just install the following package:

```bash
sudo apt install pi-bluetooth
```

This was tested using a Rpi 4.

**Other Debian-like**

The library uses pybluez, so you will probably have to install **libbluetooth-dev** and **bluez**.
On debian-like:

```bash
sudo apt install libbluetooth-dev bluez
```

Clone the repo or download a pre-built wheel from the release section, then:

```bash
pip install . # if you cloned the repo
pip install <wheel-name>.whl # if you downloaded the wheel
```


In order to run the program you have to set bluez to run in compatibility mode, add your user to the bluetooth 
group and modify some other setting. I put everything in the set_bt.sh script so that you can just execute:

```bash
chmod +x setup_bt.sh
sudo ./setup_bt.sh
```

The script is based on the instructions contained in these two stackoverflow responses, and the full credit
for it goes to the authors of these answers. If something is not working, I advise you to directly 
refer to these two links.

- [Compatibility mode](https://stackoverflow.com/a/46810116)
- [Setting permissions](https://stackoverflow.com/a/42306883)


## Usage

If you are on a debian-like system, your machine will be discoverable in the bluetooth 
network by using:

```bash
sudo hciconfig hci0 piscan
```

### Documentation

Full documentation is accessible at https://abathargh.github.io/shimmer-listener.

### Bt Master example

This is an example of the simplest application that just prints the incoming data instances in Master Mode, with 
a slave mote that runs its app that implements the shimmer-listener presentation protocol:

```python
from shimmer_listener import bt_init, bt_listen, bt_close, BtMode

def process_data(mac, data):
    print(f"Data from {mac}: {data}")

bt_init(mode=BtMode.MASTER)

try:
    bt_listen(message_handle=process_data)
except KeyboardInterrupt:
    bt_close()
```

You can take a look at the **Examples** directory and at the **_console_scripts** module for some practical examples.

### Callbacks

A series of callbacks can be used and set as properties to intercept certain events:

- **on_connect(mac: str, info: frameinfo) -> None**
  
    Called when a mote identified by **mac** succesfully connects. All the information
    regarding the exchanged data format, obtained through *the presentation protocol* are
    accessible via **info**.

- **on_message(mac: str, frame: Dict[str, Any]) -> None**
  
    Called when a message is received from a mote identified by **mac**. The message is
    returned as a dict with the keys previously obtained from the *presentation protocol*.

- **on_disconnect(mac: str, lost: bool) -> None**
  
    Called when a mote identified by **mac** disconnects. If **lost** is true, the disconnect
    event happened because the connection has been lost.

```python
from shimmer_listener import bt_init, bt_listen, BtMode

def on_connect(mac, info):
    print(f"BT MAC {mac}: received presentation frame, {info}")

def on_disconnect(mac, lost):
    if lost:
        print(f"BT MAC {mac}: connection lost")
    else:
        print(f"BT MAC {mac}: disconnecting")

def on_message(mac, data):
    print(f"BT MAC {mac}: got {data}")

bt_init(mode=BtMode.MASTER)
bt_listen(connect_handle=on_connect, message_handle=on_message,
          disconnect_handle=on_disconnect)
```

## Console Scripts

The following executable applications are shipped with the library and can be used once you install it.

### shimmer-printer

This is am executable that can be used to quickly check if your devices successfully work with the app. It just prints 
every data frame it receives.

```bash
shimmer-printer
```

### shimmer-btslave

A simple application encapsulating the original example of the btMasterTest TinyOS app. By using it, 
you start an app as a slave device connecting to the shimmer (in this case, the BT Master).

```bash
shimmer-btslave
```
