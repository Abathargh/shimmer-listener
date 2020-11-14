#! /usr/bin/env bash

dbus_bluez="/etc/systemd/system/dbus-org.bluez.service"
cat $dbus_bluez | sed -e "s/<ExecStart=\/usr\/lib\/bluetooth\/bluetoothd>/ExecStart=\/usr\/lib\/bluetooth\/bluetoothd -C/" > "$dbus_bluez".tmp && mv "$dbus_bluez".tmp dbus_bluez
sdptool add SP
usermod -G bluetooth -a "${USER}"
chgrp bluetooth /var/run/sdp

systemctl daemon-reload
service bluetooth restart

echo -e "[Unit]\nDescrption=Monitor /var/run/sdp\n\n[Install]\n\nWantedBy=bluetooth.service\n\n[Path]\nPathExists=/var/run/sdp\nUnit=var-run-sdp.service" > /etc/systemd/system/var-run-sdp.path
echo -e "[Unit]\nDescription=Set permission of /var/run/sdp\n\n[Install]\nRequiredBy=var-run-sdp.path\n\n[Service]\nType=simple\nExecStart=/bin/chgrp bluetooth /var/run/sdp" > /etc/systemd/system/var-run-sdp.service

systemctl daemon-reload
systemctl enable var-run-sdp.path
systemctl enable var-run-sdp.service
systemctl start var-run-sdp.path

