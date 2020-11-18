# shimmer-listener

This is a project that started from the idea of having a general library that interacted with shimmer apps for tinyos, 
inspired from the python demo scripts that can be found inside some of the sub-directories of the 
[tinyos shimmer apps repository](https://github.com/ShimmerResearch/tinyos-shimmer).

## Contents

- [About][#about]
- [Installation](#installation)
    - [Windows](#windows)
    - [Debian-like](#debian-like)
- [Usage](#usage)
    - [shimmer-to-nodered](#shimmer-to-nodered)

## About

This library allows you to connect to a Shimmer2 mote via Bluetooth both in Master and Slave mode, interacting with it 
via the shimmer-apps precedently introduced (even if it's possible to create custom interactions).

For now, there's only support for the BluetoothMasterTest app for Master-mode motes. For what concerns Slave-mode motes, 
you can use strings identifying the particular app in the initialization process to make the library understand which 
protocol to use to interpret and unpack the incoming data.

The received data can be handled via a data processing function that has to be passed at init time, where you define 
what to do with each instance of incoming data.

## Installation

### Windows

You need to have Microsoft Visual C++ installed in order to build a wheel for pybluez during the installation process.

Get [Visual Studio Installer](https://visualstudio.microsoft.com/it/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16) here, go to Workloads and install the whole Build Tools for C++ suite, which is the first option in the top left corner.

Then, you can just:
```bash
pip install .
```

### Debian-like

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

The script was compiled from the instructions contained in these two stackoverflow responses and the full credit 
for it goes to the authors of these answers. If something is not working, I advise you to directly 
refer to these two links.

- [Compatibility mode](https://stackoverflow.com/a/46810116)
- [Setting permissions](https://stackoverflow.com/a/42306883)


## Usage

If you are on a debian-like system and you're using the slave-mode, your machine must be discoverable in the bluetooth 
network by using:

```bash
sudo hciconfig hci0 piscan
```

This is an example of the simplest application that just prints the incoming data instances in Master Mode, with 
a slave mote that runs the simple_accel app:

```python
from shimmer_listener import bt_init, bt_listen, bt_close, BtMode

def process_data(data):
    print(data)


if __name__ == "__main__":       
    bt_init(mode=BtMode.MASTER, node_app="simple_accel")

    try:
        bt_listen(process=process_data)
    except KeyboardInterrupt:
        bt_close()
```

You can take a look at the **to_nodered** module for a practical example.

### shimmer-to-nodered

The library can be integrated in a nodered flow by using a tcp node listening on a given port. 
You can then use the **shimmer-to-nodered** script to forward the data received through bluetooth by the shimmer 
to the nodered instance:

```bash
shimmer-to-nodered -p <port>
```
