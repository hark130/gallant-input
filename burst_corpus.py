"""Save and load a burst corpus: one record per detected burst, for offline analysis.

Run the slow DSP once (detect, estimate frequency, resolve channel, demodulate), save the
results, and then iterate on analysis against the saved file in milliseconds.

BurstRecord:  One burst: where it is in the capture, its channel/frequency, and its bits.
BurstCorpus:  Every BurstRecord from one capture, plus the capture's metadata and the settings
              that produced it (so a result can be reproduced later).
save_corpus() / load_corpus(): JSON round trip.  Saving is atomic: a crash mid-write can't
              leave a truncated corpus behind.

    Typical usage example:

    corpus = BurstCorpus(capture="fhss_915mhz_26msps.iq", samp_rate=26e6, center_freq=915e6,
                         symbol_rate=250e3, params={"on_db": 8.0, "off_db": 4.0})
    corpus.records.append(BurstRecord(number=1, start=270_100, stop=478_653, channel=13,
                                      freq_hz=909.2023e6, residual_hz=2.3e3, bits="0101..."))
    save_corpus(corpus, "fhss_corpus.json")
    ...
    corpus = load_corpus("fhss_corpus.json")
    streams = [record.bits for record in corpus.records]  # Ready for data_analysis
"""

# Standard Imports
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Final, List
import json
import os
import re
import tempfile
# Third Party Imports
# Local Imports

SCHEMA_VERSION: Final[int] = 1  # Bump when the file layout changes incompatibly
BITS_REGEX: Final[re.Pattern] = re.compile(r"[01]*")  # A valid bit string: only "0"s and "1"s


@dataclass(frozen=True)
class BurstRecord:
    """One detected burst.  Indices are absolute samples: the half-open interval [start, stop)."""

    number: int          # Burst number, in detection order (1-based)
    start: int           # Absolute index of the burst's first sample
    stop: int            # Absolute index one past the burst's last sample
    channel: int | None  # Resolved channel number (None if it didn't resolve)
    freq_hz: float       # Estimated absolute center frequency (Hz)
    residual_hz: float   # Estimated frequency minus the channel's frequency (Hz)
    bits: str = ""       # Demodulated bits as "0"/"1" characters ("" if not demodulated)

    def __post_init__(self):
        """Validate, and normalize bytes bits (e.g., b"0101" from a modem) to str."""
        # LOCAL VARIABLES
        bits = self.bits  # Bits, normalized to str

        # NORMALIZE IT
        if isinstance(bits, bytes):
            bits = bits.decode("ascii")
            object.__setattr__(self, "bits", bits)  # Frozen dataclass: set via object

        # VALIDATE IT
        for name in ("number", "start", "stop"):
            _validate_int(getattr(self, name), name)
        if self.stop <= self.start:
            raise ValueError(f"stop ({self.stop}) must be > start ({self.start})")
        if self.channel is not None:
            _validate_int(self.channel, "channel")
        _validate_float(self.freq_hz, "freq_hz")
        _validate_float(self.residual_hz, "residual_hz")
        if not isinstance(bits, str):
            raise TypeError(f"bits must be str or bytes, got {type(bits)}")
        if not BITS_REGEX.fullmatch(bits):
            raise ValueError("bits may only contain '0' and '1' characters")


@dataclass
class BurstCorpus:
    """Every BurstRecord from one capture, plus the capture's metadata."""

    capture: str                 # Capture file name (or a live source's description)
    samp_rate: float             # Sample rate of the capture (samples per second)
    center_freq: float           # Tuned center frequency of the capture (Hz)
    symbol_rate: float           # Symbol rate used to demodulate (symbols per second)
    params: Dict[str, Any] = field(default_factory=dict)  # Settings that produced this corpus
    records: List[BurstRecord] = field(default_factory=list)  # One per burst, in order
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_record(self, record: BurstRecord) -> None:
        """Add a burst record to the internal list."""
        self.records.append(record)

    def get_start_sec(self, record: BurstRecord) -> float:
        """Return a record's start time (seconds from the start of the capture)."""
        return record.start / self.samp_rate

    def get_duration_sec(self, record: BurstRecord) -> float:
        """Return a record's duration (seconds)."""
        return (record.stop - record.start) / self.samp_rate


def load_corpus(path: Path | str) -> BurstCorpus:
    """Load a burst corpus saved by save_corpus().

    Args:
        path: The JSON file to read.

    Returns:
        The corpus, with every record re-validated.

    Raises:
        OSError: The file couldn't be read.
        TypeError: Bad data type in the file.
        ValueError: Bad value in the file, or an unsupported schema version.
    """
    # LOCAL VARIABLES
    raw = None     # The parsed JSON document
    corpus = None  # The rebuilt BurstCorpus

    # READ IT
    with open(path, "r", encoding="utf-8") as in_file:
        raw = json.load(in_file)

    # VALIDATE IT
    if not isinstance(raw, dict):
        raise TypeError(f"{path} must hold a JSON object, not {type(raw).__name__}")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path} has schema version {raw.get('schema_version')}, "
                         f"but this code reads version {SCHEMA_VERSION}")

    # REBUILD IT
    corpus = BurstCorpus(capture=raw["capture"], samp_rate=float(raw["samp_rate"]),
                         center_freq=float(raw["center_freq"]),
                         symbol_rate=float(raw["symbol_rate"]), params=dict(raw["params"]),
                         records=[BurstRecord(**entry) for entry in raw["records"]],
                         created=raw["created"])

    # DONE
    return corpus


def save_corpus(corpus: BurstCorpus, path: str) -> None:
    """Save a burst corpus as JSON, atomically.

    The corpus is written to a temporary file in the same directory, then renamed over path.
    Readers (and a crash) only ever see the old file or the complete new one.

    Args:
        corpus: The corpus to save.
        path: The JSON file to write (overwritten if it exists).

    Raises:
        OSError: The file couldn't be written.
        TypeError: Bad data type (e.g., a params value JSON can't represent).
    """
    # LOCAL VARIABLES
    document = None                                     # The JSON-ready dictionary
    directory = os.path.dirname(os.path.abspath(path))  # Where path (and temp file) live
    temp_fd = -1                                        # Temporary file's descriptor
    temp_path = ""                                      # Temporary file's path

    # INPUT VALIDATION
    if not isinstance(corpus, BurstCorpus):
        raise TypeError(f"corpus must be a BurstCorpus, got {type(corpus)}")

    # CONVERT IT (plain Python types only, so numpy scalars can't sneak into the JSON)
    document = {"schema_version": SCHEMA_VERSION, "capture": str(corpus.capture),
                "samp_rate": float(corpus.samp_rate), "center_freq": float(corpus.center_freq),
                "symbol_rate": float(corpus.symbol_rate), "created": str(corpus.created),
                "params": corpus.params,
                "records": [_convert_record(record) for record in corpus.records]}

    # SAVE IT
    temp_fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as out_file:
            json.dump(document, out_file, indent=1)
        os.replace(temp_path, path)  # Atomic on POSIX and Windows
    except BaseException:
        if os.path.exists(temp_path):
            os.remove(temp_path)  # Don't leave a partial temp file behind
        raise


def _convert_record(record: BurstRecord) -> Dict[str, Any]:
    """Convert a BurstRecord to a dict of plain Python types for JSON."""
    # LOCAL VARIABLES
    entry = asdict(record)  # Field name -> value

    # CONVERT IT
    for name in ("number", "start", "stop"):
        entry[name] = int(entry[name])
    if entry["channel"] is not None:
        entry["channel"] = int(entry["channel"])
    entry["freq_hz"] = float(entry["freq_hz"])
    entry["residual_hz"] = float(entry["residual_hz"])

    # DONE
    return entry


def _validate_float(value: float, name: str) -> None:
    """Validate a real number (int, float, or numpy scalar) on behalf of this module."""
    if isinstance(value, bool) or not hasattr(value, "__float__"):
        raise TypeError(f"{name} must be a real number, got {type(value)}")


def _validate_int(value: int, name: str) -> None:
    """Validate an integer (int or numpy integer) on behalf of this module."""
    if isinstance(value, bool) or not hasattr(value, "__index__"):
        raise TypeError(f"{name} must be an integer, got {type(value)}")
