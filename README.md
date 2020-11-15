# shimmer-listener

This is a heavily modified version of the script that can be found inside the 
BluetoothMaster subfolder of the [tinyos shimmer apps repository](https://github.com/ShimmerResearch/tinyos-shimmer).

This small library acts as an extension that is capable of pairing with multiple motes communicating 
accel/gyro data via the BluetoothMaster TinyOS app.

## Contents

- [shimmer-listener](#shimmer-listener)
  - [Contents](#contents)
  - [Installation](#installation)
    - [Windows](#windows)
    - [Debian-like](#debian-like)
  - [Usage](#usage)
    - [shimmer-to-nodered](#shimmer-to-nodered)

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

Before running an application, your machine must be discoverable in the bluetooth network:

```bash
sudo hciconfig hci0 piscan
```

This is an example of the simplest application that just prints the incoming DataTuples:

```python
from shimmer_listener import bt_init, bt_listen, bt_close, DataTuple

def process_data(data: DataTuple) -> None:
    print(data.as_dict())

if __name__ == "__main__":       
    bt_init()
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

