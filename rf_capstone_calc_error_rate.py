"""This script is an attempt to calculate error rates for the rf_capstone_v3.py script.

USAGE:
    1. Follow the 'Calculate BER / Packet Loss' instructions in the rf_capstone_v3.py docstring.
    2. python rf_capstone_calc_error_rate.py
    3. ***** TO DO: DON'T DO NOW... ls command to `head` the top ./devops/files/error.log
"""

# Standard Imports
from dataclasses import dataclass
from typing import Final
# Third Party Imports
# Local Imports

USER1_ENV_VAR: Final[str] = 'USER1_OUTPUT'        # User 1 output environment variable
USER2_ENV_VAR: Final[str] = 'USER2_OUTPUT'        # User 2 output environment variable
SENDING_NEEDLE: Final[str] = '[TX] Sending - '    # The "I sent a message" needle
RECEIVING_NEEDLE: Final[str] = '[RX] Received: '  # The "I received a message" needle


@dataclass
class PacketStats():
    """Contains stats on packet loss."""
    sent: int
    recv: int
    lost: float


def calc_packet_loss(sender: List[str], receiver: List[str]) -> PacketStats:
    """Calculate the packet loss from sender to receiver as a percentage."""
    # LOCAL VARIABLES
    sent_packets = 0  # The number of packets sent
    recv_packets = 0  # The number of received packets
    loss = 100.0      # Percent packet loss

    # CALC IT
    # Count sent packets
    for sent_line in sender:
        if SENDING_NEEDLE in sent_line:
            sent_packets += 1
    # Count recv packets
    for recv_line in receiver:
        if RECEIVING_NEEDLE in recv_line:
            recv_packets += 1
    # Calc it
    if sent_packets > 0:
        loss = recv_packets / sent_packets * 100
    if recv_packets > sent_packets:
        raise RuntimeError(f'There is something fishy in this exchange: recv {recv_packets} > '
                           f'sent {sent_packets}')

    # DONE
    return PacketStats(sent=sent_packets, recv=recv_packets, lost=loss)


def fetch_env_var(env_var: str) -> str:
    """Fetch an environment variable."""
    env_val = os.getenv(env_var)
    if env_val is None:
        raise RuntimeError(f'The "{env_var}" does not exist')
    if not env_val:
        raise RuntimeError(f'The "{env_var}" environment variable is empty')
    return env_val


def print_packet_loss(sender: int, receiver: int, results: PacketStats) -> None:
    """SPOT to print packet loss stats."""
    print(f'User {sender} sent {results.sent} packets, user {receiver} received {results.recv}: '
          f'{results.lost:.2f}% packet loss.')


def read_env_var(env_var: str) -> List[str]:
    """Read a file found in the given environment variable into a list of strings."""
    # LOCAL VARIABLES
    file_cont = []                     # File contents
    filename = fetch_env_var(env_var)  # The output filename

    # READ IT
    file_cont = read_file(filename)

    # DONE
    return file_cont


def read_file(filename: str) -> List[str]:
    """Read a file into a list of strings."""
    # LOCAL VARIABLES
    file_cont = []  # File contents

    # READ IT
    with open(filename, 'r', encoding='ascii') as file:
        file_cont = [line.strip() for line in file]

    # DONE
    return file_cont


def main() -> None:
    """do_it()."""
    # LOCAL VARIABLES
    user1 = read_env_var(USER1_ENV_VAR)
    user2 = read_env_var(USER2_ENV_VAR)
    # user1 = read_file('devops/files/rf_capstone_user1.out')  # OFFLINE TESTING
    # user2 = read_file('devops/files/rf_capstone_user2.out')  # OFFLINE TESTING
    packet_loss_1to2 = calc_packet_loss(sender=user1, receiver=user2)  # User 1 --> User 2
    packet_loss_2to1 = calc_packet_loss(sender=user2, receiver=user1)  # User 2 --> User 1

    # CALCULATE IT
    # User 1 --> User 2
    print_packet_loss(1, 2, packet_loss_1to2)
    # User 2 --> User 1
    print_packet_loss(2, 1, packet_loss_2to1)


if __name__ == '__main__':
    main()
