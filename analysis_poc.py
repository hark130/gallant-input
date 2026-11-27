"""Proof of concept (PoC) code to analyze an offline corpus of sampled FHSS bursts.

USAGE:
    python analysis_poc.py
"""

# Standard Imports
from pathlib import Path
from typing import Final
# Third Party Imports
# Local Imports
from burst_corpus import load_corpus
from gallant_input.data_analysis import (find_dense_repeat, find_dense_repeats,
                                         find_repeats, find_stream_lcd)

CORPUS_FILENAME: Final[Path] = Path() / "data" / "fhss_corpus.json"


def main() -> None:
    """do_it()."""
    repeat_window = 40  # Length of un-decoded preamble(?) repeated in each channel
    common_substr = "11001101"  # Manual inspection indicates that *all* channels contain this
    corpus = load_corpus(CORPUS_FILENAME.absolute())
    streams = [record.bits for record in corpus.records if record.bits]
    # print(f"STREAMS: {streams}")  # DEBUGGING
    num_streams = 0  # TESTING (to limit the for loop while I tweak analysis)

    # Find a common preifx
    print(f"Common prefix: {find_stream_lcd(streams)}")
    # Identify repeats
    for record in corpus.records:
        # Temp var update
        _channel = record.channel if record.channel is not None else 0  # Temp channel number
        _repeat_dict = find_repeats(record.bits, win_len=repeat_window)
        _max_len = len(max(_repeat_dict, key=len))  # Length of the longest key in the repeat dict
        _all_longest = [key for key in _repeat_dict if len(key) == _max_len]
        _dense_repeats = find_dense_repeats(record.bits)
        print(f"DENSE REPEATS: {_dense_repeats}")  # DEBUGGING
        _dense_repeat = [repeat for repeat in _dense_repeats
                         if repeat[0].startswith(common_substr)]
        # Channel analysis
        # find_dense_repeat() helps highlight repeated strings
        print(f"Channel #{_channel:02d} dense repeat: "
              f"{_dense_repeat[0] if _dense_repeat else 'None'}")
        print(f"Channel #{_channel:02d} repeats for window length {repeat_window}: ")
        for long_key in _all_longest:
            if long_key.startswith(common_substr):
                print(f"\t{long_key}")
        # TESTING
        num_streams += 1
        if num_streams >= 3:
            break  # TESTING


if __name__ == "__main__":
    main()
