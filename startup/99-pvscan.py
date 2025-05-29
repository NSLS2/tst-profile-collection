print(f"Loading file {__file__!r} ...")

from ophyd_async.core import Device, Signal, SignalRW
from typing import Dict, Optional, Any
import pprint

devices = [g for g in globals().values() if isinstance(g, Device)]
# TODO make a dict for stray signals
# Tuples of the source and type to capture the dtype which is presently missing
# from our PV list


def walk_signals(
    device: Device, path_prefix: Optional[str] = ""
) -> Dict[str, Signal[Any]]:
    """Retrieve all SignalRWs from a device.

    Stores retrieved signals with their dotted attribute paths in a dictionary. Used as
    part of saving and loading a device.

    Parameters
    ----------
    device : Device
        Ophyd device to retrieve read-write signals from.

    path_prefix : str
        For internal use, leave blank when calling the method.

    Returns
    -------
    SignalRWs : dict
        A dictionary matching the string attribute path of a SignalRW with the
        signal itself.

        See Also
    --------
    :func:`ophyd_async.core.get_signal_values`
    :func:`ophyd_async.core.save_to_yaml`

    """

    if not path_prefix:
        path_prefix = ""

    signals: Dict[str, Signal[Any]] = {}
    for attr_name, attr in device.children():
        dot_path = f"{path_prefix}{attr_name}"
        # if type(attr) is Signal:
        if isinstance(attr, Signal):
            signals[dot_path] = attr
        attr_signals = walk_signals(attr, path_prefix=dot_path + ".")
        signals.update(attr_signals)
    return signals


pvs = {
    device.name: {
        signal.name: signal.source
        for signal in walk_signals(device).values()
        if isinstance(signal, Signal)
    }
    for device in devices
}

pvs2 = {
    f"{device.name}.{signal.name}": signal.source
    for device in devices
    for signal in walk_signals(device).values()
}

pprint.pprint(pvs2)

# pvs = {
#     device.name: {
#         signal[0]: signal[1].source
#         for signal in device.children()
#         if isinstance(signal[1], Signal)
#     }
#     for device in devices
# }
