"""Parse the CLI arguments."""

# Standard Imports
import argparse
import random
# Third Party Imports
# Local Imports
from protoroad.constants import BROADCAST_ADDR, NULL_ADDR

_MIN_ADDR: Final[int] = NULL_ADDR + 1


def parse_args() -> argparse.Namespace:
    """Parse the command line arguments."""
    # LOCAL VARIABLES
    parser = argparse.ArgumentParser(prog="protoroad",
                                     description="Half-duplex BPSK text chat over USRP radios.")
    args = None  # Parsed arguments

    # DEFINE THEM
    parser.add_argument(
        "--serial", default=None, help="USRP serial number (default: the first B2xx UHD finds)")
    parser.add_argument(
        "--address", type=int, default=None,
        help=f"This node's address, {_MIN_ADDR}-{BROADCAST_ADDR - 1} (default: random)")
    parser.add_argument(
        "--peer", type=int, default=BROADCAST_ADDR,
        help=f"Destination address, {_MIN_ADDR}-{BROADCAST_ADDR} "
             f"(default: {BROADCAST_ADDR}, broadcast)")
    parser.add_argument("--debug", action="store_true", help="Verbose logging")

    # PARSE AND VALIDATE THEM
    args = parser.parse_args()
    if args.address is None:
        args.address = _generate_address()
    elif not NULL_ADDR < args.address < BROADCAST_ADDR:
        parser.error(f"--address must be {_MIN_ADDR}-{BROADCAST_ADDR - 1}")
    if not NULL_ADDR < args.peer <= BROADCAST_ADDR:
        parser.error(f"--peer must be {_MIN_ADDR}-{BROADCAST_ADDR}")

    # DONE
    return args


def _generate_address() -> int:
    """Generate a pseudo-random node address in [0, BROADCAST_ADDR) (never broadcast)."""
    return random.randrange(_MIN_ADDR, BROADCAST_ADDR)
