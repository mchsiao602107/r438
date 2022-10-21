import os
from parse import parse

target_dir = "../simulations/stream_production_offset_relay_switch/"
for filename in os.listdir(target_dir):

    # Read all lines from a file.
    lines = list()
    with open(target_dir + filename, "r") as my_file:
        for line in my_file:
            stream_id, offset, period = tuple(parse("stream ID: {}, offset: {}, period: {}\n", line))
            lines.append([int(stream_id), int(offset)])

    # Sort lines by production offset of flows.
    lines_sorted = sorted(lines, key=lambda item: item[1])
    
    # Write the sorted result.
    with open(target_dir + filename, "w") as my_file:
        for stream_id, offset in lines_sorted:
            my_file.write("stream ID: {}, offset: {}\n".format(stream_id, offset))
            