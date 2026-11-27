"""Proof of concept (PoC) code to analyze an offline corpus of sampled FHSS bursts.

USAGE:
    python analysis_poc.py
"""

# Standard Imports
from dataclasses import dataclass
from pathlib import Path
from typing import Final
# Third Party Imports
# Local Imports
from burst_corpus import load_corpus
from gallant_input.data_analysis import (compare_streams, find_common_prefix,
                                         find_common_substrings, find_dense_repeat,
                                         find_dense_repeats, find_longest_common_substrings,
                                         find_repeats)
from gallant_input.data_analysis.line_coding import decode_manchester, evaluate_manchester_coding
from gallant_input.data_analysis.manchesterverdict import ManchesterVerdict

CORPUS_FILENAME: Final[Path] = Path() / "data" / "fhss_corpus.json"


@dataclass(frozen=True)
class UniqueChanIden:
    """Unique(?) channel identifier."""

    channel: int | None  # Identified channel number
    binary: str          # That channel's unique(?) binary substr


def main() -> None:
    """do_it()."""
    # repeat_window = 40  # Length of un-decoded preamble(?) repeated in each channel
    repeat_window = 20  # Length of decoded preamble(?) repeated in each channel
    common_substr = "0110011010"  # Manual inspection indicates that *all* channels contain this
    actual_substr = decode_manchester(common_substr, 0)  # Manchester decoded common substring
    corpus = load_corpus(CORPUS_FILENAME.absolute())
    # streams = [record.bits for record in corpus.records if record.bits]
    streams = [record.bits[record.bits.find(common_substr):] for record in corpus.records
               if record.bits and common_substr in record.bits]
    # print(f"STREAMS: {streams}")  # DEBUGGING
    num_streams = 0  # TESTING (to limit the for loop while I tweak analysis)
    chan_binary: List[UniqueChanIden] = []  # Unique(?) channel binary substrings

    # Find a common preifx
    print("Marker in every burst: "
          f"{common_substr in find_common_substrings(streams, len(common_substr))}")
    # print(f"COMMON SUBSTRINGS: {find_common_substrings(streams, len(common_substr))}")  # DEBUGGING
    print(f"Longest common: {find_longest_common_substrings(streams)}")
    # Identify repeats
    _id_units = {}
    for record in corpus.records:
        # Channel analysis
        _channel = record.channel if record.channel is not None else 0  # Temp channel number
        print(f"\nCHANNEL: #{_channel:02d}")

        # 0. Prepare binary
        # _bits = record.bits  # Raw demodulated binary value from the record
        _bits = record.bits[record.bits.find(common_substr):]  # Demod binary value sliced to substr

        # 1. Evaluate the encoding
        _evaluation = evaluate_manchester_coding(_bits, log_findings=False)
        # print(f"Channel #{_channel:02d} Evaluation: {_evaluation.verdict.name} "
        #       f"(offset {_evaluation.best_offset}, illegal pairs {_evaluation.illegal_pairs})")
        if _evaluation.verdict == ManchesterVerdict.MANCHESTER:
            _bits = _evaluation.decoded_bits  # IEEE 802.3 convention: "01" = 1
        _repeat_dict = find_repeats(_bits, win_len=repeat_window)
        _max_len = len(max(_repeat_dict, key=len))  # Length of the longest key in the repeat dict
        _all_longest = [key for key in _repeat_dict if len(key) == _max_len]
        _dense_repeats = find_dense_repeats(_bits)
        _dense_repeat = [repeat for repeat in _dense_repeats
                         if repeat[0].startswith(actual_substr)]


        # 2. find_dense_repeat() helps highlight repeated strings
        # print(f"Channel #{_channel:02d} dense repeat: "
        #       f"{_dense_repeat[0] if _dense_repeat else 'None'}")
        print(f"Channel #{_channel:02d} repeats for window length {repeat_window}: ")
        _long_keys = []
        for long_key in _all_longest:
            if long_key.startswith(actual_substr):
                _long_keys.append(long_key)
                print(f"\t{long_key}")
            if long_key.startswith(actual_substr) and long_key[:10] == long_key[10:]:
                print(f"\tID unit: {long_key[:10]}")
                if _channel in _id_units:
                    if long_key[:10] not in _id_units[_channel]:
                        _id_units[_channel] = _id_units[_channel] + [long_key[:10]]  # Unique add
                else:
                    _id_units[_channel] = [long_key[:10]]
        if len(_long_keys) == 0:
            print(f"Unable to find '{actual_substr}' in Channel #{_channel:02d} burst")
        elif len(_long_keys) > 1:
            print(f"Discarding false positives(?) for Channel #{_channel:02d}")
        else:
            chan_binary.append(UniqueChanIden(channel=_channel, binary=_long_keys[0]))
    for channel, id_list in _id_units.items():
        print(f"Channel #{channel:02d} identified: {id_list}")

        # TESTING
        num_streams += 1
        # if num_streams >= 5:
        #     break  # TESTING

    # COMPARE CHANNEL BINARY SUBSTRINGS
    # Find common prefixes (which is fine now that I've sliced it down to unique channel ids)
    uci_bin_list = [uci.binary for uci in chan_binary]  # List of all unique channel binary strings
    print(f"Common sub-string prefix: {find_common_prefix(uci_bin_list)}")
    # Find duplicates?!
    # for uci_bin in uci_bin_list:
    #     if uci_bin_list.count(uci_bin) > 1:
    #         print(f"Found a duplicate binary substring: {uci_bin}")
    #         for uci in chan_binary:
    #             if uci.binary == uci_bin:
    #                 print(f"Channel #{_channel:02d} contains {uci_bin}")
    # Compare the unique IDs to each other
    for i in range(0, len(chan_binary), 2):
        try:
            first_uci = chan_binary[i]
            second_uci = chan_binary[i+1]
        except IndexError:
            break  # Done
        else:
            print(f"Comparing Channel #{first_uci.channel:02d} to "
                  f"Channel #{second_uci.channel:02d}")
            compare_streams(first_uci.binary, second_uci.binary)


if __name__ == "__main__":
    main()
