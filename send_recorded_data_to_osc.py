#!/usr/bin/env python
# NOTE: only supports a single (1) sensor recording at the moment
import argparse
import datetime
import json
import os
import time

import pandas
from pythonosc import udp_client

_ROOT_DIR = os.path.dirname(__file__)
_DATA_DIR = os.path.join(_ROOT_DIR, "data")

# Example header
# OpenSignals Text File Format
# {"00:07:80:79:6F:DB": {"sensor": ["ECG"], "device name": "00:07:80:79:6F:DB", "column": ["nSeq", "DI", "PORT1_CHN1"], "sync interval": 2, "time": "10:29:43.249", "comments": "", "device connection": "BTH00:07:80:79:6F:DB", "channels": [1], "keywords": "", "convertedValues": 0, "mode": 0, "digital IO": [0, 1], "firmware version": 773, "device": "channeller", "position": 0, "sampling rate": 1000, "label": ["PORT1_CHN1"], "resolution": [16], "date": "2018-7-5", "special": [{}, {}, {}, {}, {}, {}, {}]}}
# EndOfHeader

_START_HEADER_MARKER = "# OpenSignals Text File Format. Version 1\n"
_END_HEADER_MARKER = "# EndOfHeader\n"
_FORMAT_PREFIX = "# "


def get_data(file_path: str) -> tuple[dict, pandas.DataFrame]:
    """Parses a .txt file produced by opensignal, following this format: https://support.pluxbiosignals.com/knowledge-base/opensignals-sensor-file-specifications-txt-format/
    return a list of one or more tuples, one for each recorded sensor, with a
    dict containing metadata from a sensor, and a pandas dataframe for the
    sensor readings.
    """
    with open(file_path) as file:
        parse_format_line: bool = False
        format_data: dict | None = None
        for line in file:
            if parse_format_line:
                format_data = json.loads(line.lstrip(_FORMAT_PREFIX))
                break
            if line == _START_HEADER_MARKER:
                parse_format_line = True
            if line == _END_HEADER_MARKER:
                break
        assert format_data != None, f"Did not find format header, please check if {file_path} is specification compliant."

        # The header is a dict with key mac address and value format data.
        # {"00:07:80:8C:AD:4F": {...}, ...}
        # NOTE: this only supports one sensor currently
        format_data = next(iter(format_data.values()))
        assert format_data != None, f"Did not find format header content, please check if {file_path} is specification compliant."
        # resolution is in bytes, values are stored as unsigned integers,
        # e.g. resolution '16' is equivalent to uint 16 with a maximum value of 2^16-1 = 65535
        format_data['limit'] = pow(2, format_data['resolution'][0]) - 1

        # pandas does not allow (?) naming the first column, which contains the values. So snap off the first value.
        names = format_data['column'][1:]
        dtype = {name: int for name in names}
        data: pandas.DataFrame = pandas.read_csv(file_path, skiprows=[0,1,2], sep=r'\s+', names=format_data['column'][1:], dtype=dtype)
        return format_data, data


def playback_data_osc(osc_client: udp_client.SimpleUDPClient,
                      format_and_data: tuple[dict, pandas.DataFrame],
                      desired_frequency: int,
                      loop_enabled: bool):
    """Uses opensignal pandas data frame(s) and companion meta data, as
    constructed by get_data to playback recorded data, real time via osc at the
    desired frequency. Typically sensor reading sampling / frequecy is in the
    range of 1000+ while playback, especially for video may want specify
    something more in the range of 30 or 60 as these are common frame per
    second rates.
    """
    desired_interval = 1.0 / float(desired_frequency)
    desired_delta = datetime.timedelta(seconds=desired_interval)

    format_data, data_frame = format_and_data

    # Resample the data_frame to desired frequency
    input_frequency = format_data["sampling rate"]
    input_interval = 1.0 / float(input_frequency)
    input_delta = datetime.timedelta(seconds=input_interval)
    index = pandas.timedelta_range(start='0 nanoseconds', periods=len(data_frame.index), freq=input_delta)
    processed_data_frame = data_frame.set_index(index)
    processed_data_frame = processed_data_frame.resample(desired_delta).min()

    # Not the most beautiful or accurate way of doing this, but good enough.
    index = 0
    limit = format_data['limit']
    while True:
        start = time.perf_counter()
        try:
            value = processed_data_frame.iloc[index, 1]
            # TODO: pre-calculate this as an optimisation
            normalised_value = value / limit
        except IndexError:
            if loop_enabled:
                index = 0
                continue
            break
        print(normalised_value)
        osc_client.send_message("/sensor", normalised_value)
        index += 1
        time.sleep(max(desired_interval-(time.perf_counter()-start),0))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=41235,
        help="The port the OSC server is listening on")
    parser.add_argument("--data-file-path", type=str, default=os.path.join(_DATA_DIR, "breath-short.txt"),
        help="Path to txt file that stores the opensensor data")
    parser.add_argument('--no-loop', action=argparse.BooleanOptionalAction, help="Do not loop data.")
    args = parser.parse_args()

    osc_client = udp_client.SimpleUDPClient(args.ip, args.port)
    format_and_data = get_data(args.data_file_path)
    loop_enabled = args.no_loop is None
    playback_data_osc(osc_client=osc_client, format_and_data=format_and_data, desired_frequency=30, loop_enabled=loop_enabled)
