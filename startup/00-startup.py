# Make ophyd listen to pyepics.
print(f"Loading file {__file__!r} ...")

import asyncio
import datetime
import logging
import os
import subprocess
import time as ttime
import warnings
from logging.handlers import SysLogHandler, TimedRotatingFileHandler
from pathlib import Path

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import epicscorelibs.path.pyepics
import nslsii
import redis
from bluesky.callbacks.broker import post_run, verify_files_saved
from bluesky.callbacks.tiled_writer import TiledWriter
from bluesky.plans import count, scan
from bluesky.run_engine import RunEngine, autoawait_in_bluesky_event_loop
from bluesky_queueserver import is_re_worker_active
from IPython import get_ipython
from ophyd.sim import det, motor
from redis_json_dict import RedisJSONDict
from tiled.client import from_uri
from tiled.server import SimpleTiledServer

DEBUG = True

if DEBUG:
    RE = RunEngine()
else:
    RE = RunEngine(RedisJSONDict(redis.Redis("info.tst.nsls2.bnl.gov"), prefix=""))

if not is_re_worker_active():
    autoawait_in_bluesky_event_loop()


tiled_server = SimpleTiledServer()
tiled_client = from_uri(tiled_server.uri)
tiled_writer = TiledWriter(tiled_client)
RE.subscribe(tiled_writer)


def dump_doc_to_stdout(name, doc):
    print("========= Emitting Doc =============")
    print(f"{name = }")
    print(f"{doc = }")
    print("============ Done ============")


RE.subscribe(dump_doc_to_stdout)


LOG_FILE_FORMAT = (
    "[%(levelname)1.1s %(asctime)s.%(msecs)03d %(name)s"
    "  %(module)s:%(lineno)d] %(message)s"
)
# No timestamp: syslog adds it. The logger name becomes the "app" label in Loki.
SYSLOG_FORMAT = "%(name)s[%(process)s]: %(levelname)s - %(module)s:%(lineno)d] %(message)s"


def configure_tst_logging():
    """Log to a local rotating file and, where available, to syslog.

    Syslog is forwarded to log.nsls2.bnl.gov and shipped to Loki, where the
    "TST" logger shows up as app="TST" for this host.
    """
    # bluesky, ophyd, caproto and nslsii loggers: file (BLUESKY_LOG_FILE or
    # the appdirs default) plus syslog. configure_base() does this on other
    # beamlines, but this profile does not call it.
    bluesky_log_path = nslsii.configure_bluesky_logging(ipython=get_ipython())
    tst_log_path = Path(bluesky_log_path).parent / "tst-profile.log"

    tst_logger = logging.getLogger("TST")
    tst_logger.setLevel(logging.DEBUG)
    tst_logger.propagate = False

    file_handler = TimedRotatingFileHandler(
        str(tst_log_path), when="W0", backupCount=10
    )
    file_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    file_handler.setFormatter(
        logging.Formatter(fmt=LOG_FILE_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    )
    tst_logger.addHandler(file_handler)

    if Path("/dev/log").exists():
        syslog_handler = SysLogHandler(address="/dev/log")
        syslog_handler.setLevel(logging.INFO)
        syslog_handler.setFormatter(logging.Formatter(fmt=SYSLOG_FORMAT))
        tst_logger.addHandler(syslog_handler)

    print(f"TST profile log file: '{tst_log_path}'")
    return tst_logger


logger = configure_tst_logging()
logger.info("Starting TST profile (DEBUG=%s)", DEBUG)


def log_run_documents(name, doc):
    if name == "start":
        logger.info(
            "Run start: uid=%s scan_id=%s plan_name=%s",
            doc["uid"],
            doc.get("scan_id"),
            doc.get("plan_name"),
        )
    elif name == "stop":
        level = logging.INFO if doc["exit_status"] == "success" else logging.WARNING
        logger.log(
            level,
            "Run stop: uid=%s exit_status=%s num_events=%s reason=%r",
            doc["run_start"],
            doc["exit_status"],
            doc.get("num_events"),
            doc.get("reason"),
        )


RE.subscribe(log_run_documents)


def now():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


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

RUNNING_IN_NSLS2_CI = os.environ.get("RUNNING_IN_NSLS2_CI", "NO") == "YES" or DEBUG

if RUNNING_IN_NSLS2_CI:
    print("Running in CI, using mock mode when initializing devices...")

file_loading_timer = FileLoadingTimer()
