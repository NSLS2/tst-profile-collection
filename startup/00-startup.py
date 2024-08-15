# Make ophyd listen to pyepics.
print(f"Loading file {__file__!r} ...")

import asyncio
import datetime
import logging
import os
import subprocess
import time as ttime
import warnings

import epicscorelibs.path.pyepics
import nslsii
import ophyd.signal
import redis
from bluesky.callbacks.broker import post_run, verify_files_saved
from bluesky.callbacks.tiled_writer import TiledWriter
from bluesky.run_engine import RunEngine, call_in_bluesky_event_loop
from databroker.v0 import Broker
from IPython import get_ipython
from redis_json_dict import RedisJSONDict
from tiled.client import from_uri

ophyd.signal.EpicsSignal.set_defaults(connection_timeout=5)
# See docstring for nslsii.configure_base() for more details
# this command takes away much of the boilerplate for setting up a profile
# (such as setting up best-effort callback, etc)


nslsii.configure_base(
    get_ipython().user_ns,
    Broker.named("temp"),
    pbar=True,
    bec=True,
    magics=True,
    mpl=True,
    epics_context=False,
)

RE.unsubscribe(0)

event_loop = asyncio.get_event_loop()
RE = RunEngine(loop=event_loop)
RE.subscribe(bec)

tiled_client = from_uri("http://localhost:8000", api_key=os.getenv("TILED_API_KEY", ""))
tw = TiledWriter(tiled_client)
RE.subscribe(tw)
# db = Broker()

import json


class JSONWriter:
    """Writer for a JSON array"""

    def __init__(self, filepath):
        self.file = open(filepath, "w")
        self.file.write("[\n")

    def __call__(self, name, doc):
        json.dump({"name": name, "doc": doc}, self.file, default=str)
        if name == "stop":
            self.file.write("\n]")
            self.file.close()
        else:
            self.file.write(",\n")


# This is needed for ophyd-async to enable 'await <>' instead of 'asyncio.run(<>)':
get_ipython().run_line_magic("autoawait", "call_in_bluesky_event_loop")

# PandA does not produce any data for plots for now.
bec.disable_plots()
bec.disable_table()


def dump_doc_to_stdout(name, doc):
    print("========= Emitting Doc =============")
    print(f"{name = }")
    print(f"{doc = }")
    print("============ Done ============")


RE.subscribe(dump_doc_to_stdout)


def now():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


jlw = JSONWriter(f"/tmp/export-docs-{now()}.json")
# RE.subscribe(jlw)


class FileLoadingTimer:

    def __init__(self):
        self.start_time = 0
        self.loading = False

    def start_timer(self, filename):
        if self.loading:
            raise Exception("File already loading!")

        print(f"Loading {filename}...")
        self.start_time = ttime.time()
        self.loading = True

    def stop_timer(self, filename):

        elapsed = ttime.time() - self.start_time
        print(f"Done loading {filename} in {elapsed} seconds.")
        self.loading = False


# EpicsSignalBase.set_defaults(timeout=10, connection_timeout=10)

# At the end of every run, verify that files were saved and
# print a confirmation message.
# RE.subscribe(post_run(verify_files_saved, db), 'stop')

# Uncomment the following lines to turn on verbose messages for
# debugging.
ophyd.logger.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)


RE.md = RedisJSONDict(redis.Redis("info.tst.nsls2.bnl.gov"), prefix="")


warnings.filterwarnings("ignore")


def warmup_hdf5_plugins(detectors):
    """
    Warm-up the hdf5 plugins.
    This is necessary for when the corresponding IOC restarts we have to trigger one image
    for the hdf5 plugin to work correctly, else we get file writing errors.
    Parameter:
    ----------
    detectors: list
    """
    for det in detectors:
        _array_size = det.hdf5.array_size.get()
        if 0 in [_array_size.height, _array_size.width] and hasattr(det, "hdf5"):
            print(
                f"\n  Warming up HDF5 plugin for {det.name} as the array_size={_array_size}..."
            )
            det.hdf5.warmup()
            print(
                f"  Warming up HDF5 plugin for {det.name} is done. array_size={det.hdf5.array_size.get()}\n"
            )
        else:
            print(
                f"\n  Warming up of the HDF5 plugin is not needed for {det.name} as the array_size={_array_size}."
            )


def show_env():
    # this is not guaranteed to work as you can start IPython without hacking
    # the path via activate
    proc = subprocess.Popen(["conda", "list"], stdout=subprocess.PIPE)
    out, err = proc.communicate()
    a = out.decode("utf-8")
    b = a.split("\n")
    print(b[0].split("/")[-1][:-1])


TST_PROPOSAL_DIR_ROOT = "/nsls2/data/tst/legacy/mock-proposals"


file_loading_timer = FileLoadingTimer()
