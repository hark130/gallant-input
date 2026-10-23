"""Defines the LinkStats class: count what the link delivered, missed, and ignored.

Why?  Without counts, "it seems to work" is all you can say about a run.  LinkStats turns a
run into numbers: frames received per sender, frames that never arrived (sequence-number
gaps), duplicates, sender restarts, frames ignored, and bursts the receiver couldn't decode.

Sequence numbers come from each sender's single counter (shared across every destination),
so LinkStats must see every valid frame from other nodes, BEFORE address filtering.
Otherwise frames a sender addressed to someone else would look like losses.
"""

# Standard Imports
from dataclasses import dataclass
# Third Party Imports
# Local Imports
from protoroad.frame_info import FrameInfo, measure_seq_nums, START_SEQ_NUM


@dataclass
class SenderStats:
    """What one sender's frames looked like from here."""

    received: int = 0     # Valid frames heard from this sender (any destination)
    missed: int = 0       # Frames skipped in its sequence (never heard)
    duplicates: int = 0   # Repeats of the previous sequence number
    restarts: int = 0     # Times its sequence jumped back to START_SEQ_NUM (sender restarted)
    last_seq: int | None = None  # Most recent sequence number heard


class LinkStats:
    """Accumulate per-sender loss statistics plus receiver-wide counts; report at exit.

    Not thread-safe by design: record from the RX thread, report after joining it.
    """

    def __init__(self):
        """Class ctor."""
        self._senders: dict[int, SenderStats] = {}  # Keyed by src address
        self.accepted = 0                           # Frames for us (or broadcast)
        self.ignored = 0                            # Valid frames not for us, or our own

    def record_frame(self, frame: FrameInfo) -> None:
        """Account for one valid frame from another node (call BEFORE address filtering).

        The sequence distance from this sender's previous frame says what happened:
            0       -> a duplicate of the previous frame
            1       -> the next frame, in order (including the wrap from 255 back to 1)
            n > 1   -> n - 1 frames went missing in between...
                       ...unless seq is START_SEQ_NUM: then the sender most likely restarted
                       (a jump back to the start can't be told apart from losing frames up
                       to the wrap, so it's counted as a restart, not as losses)
        """
        # LOCAL VARIABLES
        sender = self._senders.setdefault(frame.src, SenderStats())  # This sender's stats
        distance = 0                                                 # seq steps since last

        # CLASSIFY IT
        sender.received += 1
        if sender.last_seq is not None:
            distance = measure_seq_nums(sender.last_seq, frame.seq)
            if distance == 0:
                sender.duplicates += 1
            elif distance > 1:
                if frame.seq == START_SEQ_NUM:
                    sender.restarts += 1
                else:
                    sender.missed += distance - 1
        sender.last_seq = frame.seq

    def record_routing(self, accepted: bool) -> None:
        """Count a frame as accepted (for us, or broadcast) or ignored (own, or for others)."""
        if accepted:
            self.accepted += 1
        else:
            self.ignored += 1

    def report(self, bursts_detected: int = 0, bursts_undecoded: int = 0,
               overflows: int = 0) -> str:
        """Summarize the run as printable lines.

        Args:
            bursts_detected: [OPTIONAL] Bursts the burst detector found (FrameReceiver).
            bursts_undecoded: [OPTIONAL] Of those, how many didn't produce a valid frame:
                noise, collisions, or frames too damaged to trust.
            overflows: [OPTIONAL] Times the radio dropped samples (Radio.overflows).
        """
        # LOCAL VARIABLES
        lines = []                                                  # Report lines
        received = sum(s.received for s in self._senders.values())  # Valid frames, all senders
        missed = sum(s.missed for s in self._senders.values())      # Gaps, all senders

        # SUMMARIZE IT
        lines.append(f"Bursts detected: {bursts_detected}, undecoded: {bursts_undecoded}, "
                     f"radio overflows: {overflows}")
        lines.append(f"Frames from others: {received} (accepted {self.accepted}, "
                     f"ignored {self.ignored}), missed: {missed}"
                     + (f" ({100 * missed / (received + missed):.1f}% loss)"
                        if received + missed else ""))
        for src in sorted(self._senders):
            sender = self._senders[src]
            lines.append(f"  Src #{src}: received {sender.received}, missed {sender.missed}, "
                         f"duplicates {sender.duplicates}, restarts {sender.restarts}")

        # DONE
        return "\n".join(lines)
