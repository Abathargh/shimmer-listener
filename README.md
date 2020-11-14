# shimmer-listener

This is a heavily modified version of the script that can be found inside the 
BluetoothMaster subfolder of the [tinyos shimmer apps repository](https://github.com/ShimmerResearch/tinyos-shimmer).

This small library acts as an extension that is capable of pairing with multiple motes communicating 
accel/gyro data via the BluetoothMaster TinyOS app.

## Contents

- [Installation](#Installation)
- [Usage](#Usage)
    - [shimmer-to-nodered](#shimmer-to-nodered)

## Installation

The library uses pybluez, so you will probably have to install **libbluetooth-dev**.

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

You can take a look at the shimmer-to-nodered script in the **scripts** folder for a practical example.

### shimmer-to-nodered

The library can be integrated in a nodered flow by using a tcp node listening on a given port. 
You can then use the **shimmer-to-nodered** script to forward the data received through bluetooth by the shimmer 
to the nodered instance:

```bash
shimmer-to-nodered -p <port>
```

