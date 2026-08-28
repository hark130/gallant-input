"""This script is an attempt to calculate error rates for the rf_capstone_v3.py script.

USAGE:
    1. Follow the 'Calculate BER / Packet Loss' instructions in the rf_capstone_v3.py docstring.
    2. python rf_capstone_calc_error_rate.py
    3. ***** TO DO: DON'T DO NOW... ls command to `head` the top ./devops/files/error.log
    4. Save the files with:
cp "$USER1_OUTPUT" ./devops/files/$(date +%Y%m%d_%H%M%S)_rf_capstone_user1.out
cp "$USER2_OUTPUT" ./devops/files/$(date +%Y%m%d_%H%M%S)_rf_capstone_user2.out

"""

# Standard Imports
from dataclasses import dataclass
from typing import Final
import os
# Third Party Imports
# Local Imports

USER1_ENV_VAR: Final[str] = 'USER1_OUTPUT'        # User 1 output environment variable
USER2_ENV_VAR: Final[str] = 'USER2_OUTPUT'        # User 2 output environment variable
SENDING_NEEDLE: Final[str] = '[TX] Sending - '    # The "I sent a message" needle
RECEIVING_NEEDLE: Final[str] = '[RX] Received: '  # The "I received a message" needle
FIELD_NEEDLE_PRE: Final[str] = '[CFT] Found preamble'  # The "I found a preamble" needle
FIELD_NEEDLE_SYN: Final[str] = '[CFT] Found syncword'  # The "I found a syncword" needle
FIELD_NEEDLE_LEN: Final[str] = '[CFT] Found DATA_LEN'  # The "I found a valid DATA_LEN" needle


@dataclass
class PacketStats():
    """Contains stats on packet loss."""
    sent: int
    recv: int
    lost: float


@dataclass
class FieldStats():
    """Contains stats on packet loss."""
    sent: int        # Total packets sent
    recv_pre: int    # Correlated preambles
    recv_syn: int    # Valid syncwords
    recv_len: int    # Valid DATA_LEN field count
    recv_frame: int  # Completely valid frame (checksum passed)


def calc_field_loss(sender: List[str], receiver: List[str]) -> FieldStats:
    """Calculate loss rate, by field, from sender to receiver."""
    # LOCAL VARIABLES
    sent_packets = 0  # The number of packets sent
    recv_preambles = 0  # Total preambles found
    recv_syncwords = 0  # Total syncwords found
    recv_data_len = 0   # Total number of valid DATA_LEN fields
    recv_frame = 0      # Total valid frames received (checksum passed)

    # CALC IT
    # Count sent packets
    sent_packets = calc_sent_packets(sender)
    # Count received preambles
    recv_preambles = _count_it(haystack=receiver, needle=FIELD_NEEDLE_PRE)
    # Count received syncwords
    recv_syncwords = _count_it(haystack=receiver, needle=FIELD_NEEDLE_SYN)
    # Count received data_len
    recv_data_len = _count_it(haystack=receiver, needle=FIELD_NEEDLE_LEN)
    # Count received frames
    recv_frame = calc_recv_packets(receiver)

    # DONE
    return FieldStats(sent=sent_packets, recv_pre=recv_preambles, recv_syn=recv_syncwords,
                      recv_len=recv_data_len, recv_frame=recv_frame)


def calc_packet_loss(sender: List[str], receiver: List[str]) -> PacketStats:
    """Calculate the packet loss from sender to receiver as a percentage."""
    # LOCAL VARIABLES
    sent_packets = 0  # The number of packets sent
    recv_packets = 0  # The number of received packets
    loss = 100.0      # Percent packet loss

    # CALC IT
    # Count sent packets
    sent_packets = calc_sent_packets(sender)
    # Count recv packets
    for recv_line in receiver:
        if RECEIVING_NEEDLE in recv_line:
            recv_packets += 1
    # Calc it
    if sent_packets > 0:
        loss = (sent_packets - recv_packets) / sent_packets * 100
    if recv_packets > sent_packets:
        raise RuntimeError(f'There is something fishy in this exchange: recv {recv_packets} > '
                           f'sent {sent_packets}')

    # DONE
    return PacketStats(sent=sent_packets, recv=recv_packets, lost=loss)


def calc_recv_packets(receiver: List[str]) -> int:
    """Count the number of packets the receiver received."""
    # LOCAL VARIABLES
    recv_packets = 0  # The number of received packets

    # CALC IT
    # Count recv packets
    recv_packets = _count_it(haystack=receiver, needle=RECEIVING_NEEDLE)

    # DONE
    return recv_packets


def calc_sent_packets(sender: List[str]) -> int:
    """Count the number of packets the sender sent."""
    # LOCAL VARIABLES
    sent_packets = 0  # The number of packets sent

    # CALC IT
    # Count sent packets
    sent_packets = _count_it(haystack=sender, needle=SENDING_NEEDLE)

    # DONE
    return sent_packets


def fetch_env_var(env_var: str) -> str:
    """Fetch an environment variable."""
    env_val = os.getenv(env_var)
    if env_val is None:
        raise RuntimeError(f'The "{env_var}" does not exist')
    if not env_val:
        raise RuntimeError(f'The "{env_var}" environment variable is empty')
    return env_val


def print_avg_packet_loss(user1: PacketStats, user2: PacketStats) -> None:
    """SPOT to print average packet loss stats."""
    print(f'Average: {(user1.lost + user2.lost) / 2:.2f}% packet loss.')


def print_field_loss(sender: int, receiver: int, results: FieldStats) -> None:
    """SPOT to print loss-by-field stats."""
    # LOCAL VARIABLES
    preamble_loss = 0
    syncword_loss = 0
    data_len_loss = 0
    frame_loss = 0

    # CALCULATE
    if results.sent > 0:
        preamble_loss = (results.sent - results.recv_pre) / results.sent * 100
        syncword_loss = (results.sent - results.recv_syn) / results.sent * 100
        data_len_loss = (results.sent - results.recv_len) / results.sent * 100
        frame_loss = (results.sent - results.recv_frame) / results.sent * 100

        # FIELD LOSS
        print()
        print(f'User {sender} sent {results.sent} packets.  Of those packets, user {receiver} received:'
              f'\n\t{results.recv_pre} preambles ({preamble_loss:.2f}% loss)'
              f'\n\t{results.recv_syn} syncwords ({syncword_loss:.2f}% loss)'
              f'\n\t{results.recv_len} DATA_LENs ({data_len_loss:.2f}% loss)'
              f'\n\t{results.recv_frame} frames ({frame_loss:.2f}% loss)')

        # FALSE POSITIVES?!
        if results.recv_pre > results.sent:
            print(f'User {receiver} has received {results.recv_pre - results.sent} extra preambles')
        if results.recv_syn > results.sent:
            print(f'User {receiver} has received {results.recv_syn - results.sent} extra syncwords?')
        if results.recv_len > results.sent:
            print(f'User {receiver} has received {results.recv_len - results.sent} extra DATA_LENs?!')
        if results.recv_frame > results.sent:
            print(f'User {receiver} has received {results.recv_frame - results.sent} extra frames?!?!')
    else:
        print(f'User {sender} has not yet sent any packets')


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
    with open(filename, 'r', encoding='utf-8') as file:
        file_cont = [line.strip() for line in file]

    # DONE
    return file_cont


def _count_it(haystack: List[str], needle: str) -> int:
    """Count the occurrences of the needle in the haystack."""
    # LOCAL VARIABLES
    count = 0

    # COUNT IT
    for straw in haystack:
        if needle in straw:
            count += 1

    # DONE
    return count


def main() -> None:
    """do_it()."""
    # LOCAL VARIABLES
    user1 = read_env_var(USER1_ENV_VAR)
    user2 = read_env_var(USER2_ENV_VAR)
    # user1 = read_file('devops/files/rf_capstone_user1.out')  # OFFLINE TESTING
    # user2 = read_file('devops/files/rf_capstone_user2.out')  # OFFLINE TESTING
    packet_loss_1to2 = calc_packet_loss(sender=user1, receiver=user2)  # User 1 --> User 2
    packet_loss_2to1 = calc_packet_loss(sender=user2, receiver=user1)  # User 2 --> User 1
    field_loss_1to2 = calc_field_loss(sender=user1, receiver=user2)  # User 1 --> User 2
    field_loss_2to1 = calc_field_loss(sender=user2, receiver=user1)  # User 2 --> User 1

    # CALCULATE IT
    print()
    # 1. Packet Loss
    # User 1 --> User 2
    print_packet_loss(1, 2, packet_loss_1to2)
    # User 2 --> User 1
    print_packet_loss(2, 1, packet_loss_2to1)
    # Average
    print_avg_packet_loss(packet_loss_1to2, packet_loss_2to1)
    # 2. Field Loss
    print()
    # User 1 --> User 2
    print_field_loss(1, 2, field_loss_1to2)
    # User 2 --> User 1
    print_field_loss(2, 1, field_loss_2to1)

    # DONE
    print()


if __name__ == '__main__':
    main()
