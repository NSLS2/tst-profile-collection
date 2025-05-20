print(f"Loading file {__file__!r} ...")

from ophyd_async.core import Device, Signal

devices = [g for g in globals().values() if isinstance(g, Device)]

pvs = {
    device.name: {
        signal[0]: signal[1].source
        for signal in device.children()
        if isinstance(signal[1], Signal)
    }
    for device in devices
}

print("Devices", devices)
print("PVs", pvs)
