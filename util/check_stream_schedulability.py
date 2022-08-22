"""Check schedulability using the statistic of meanBitLifeTimePerPacket & stream deadline(period)"""
import re

result_sca_file = '../simulations/results/General-#0.sca'
dst_app_stream_info_mapping = dict()
stream_id_queue_id_mapping = dict()
dst_app_without_stats = []

with open(result_sca_file, "rt") as my_file:
    while True:
        line = my_file.readline()
        if not line:
            break

        # Store stream type & id & period from the content of ini file.
        re_result = re.findall(r"config .+productionInterval (.+)us", line)
        if re_result:
            period = int(re_result[0]) / 1e6 # unit is us
            # skip 2 lines: [initialProductionOffset, dst_app typename]
            my_file.readline()
            my_file.readline()
            re_result = re.search(r"config (.+).+display-name (.+)", my_file.readline())
            dst, stream = re_result[1], re_result[2]
            dst_app_stream_info_mapping[dst] = {}
            dst_app_stream_info_mapping[dst]['type'] = stream.split('-')[0]
            dst_app_stream_info_mapping[dst]['stream_id'] = stream.split('-')[1]
            dst_app_stream_info_mapping[dst]['period'] = period

        # Store stats of meanBitLifeTimePerPacket.
        re_result = re.search(r"statistic (.+).sink meanBitLifeTimePerPacket:histogram", line)
        if re_result:
            dst = re_result[1]
            dst_app_stream_info_mapping[dst]['count'] = int(re.search(r"field count ([\d]+)", my_file.readline())[1])
            dst_app_stream_info_mapping[dst]['mean'] = float(re.search(r"field mean (.+)", my_file.readline())[1])
            dst_app_stream_info_mapping[dst]['stddev'] = float(re.search(r"field stddev (.+)", my_file.readline())[1])
            dst_app_stream_info_mapping[dst]['min'] = float(re.search(r"field min (.+)", my_file.readline())[1])
            dst_app_stream_info_mapping[dst]['max'] = float(re.search(r"field max (.+)", my_file.readline())[1])
            if dst_app_stream_info_mapping[dst]['count'] == 0:
                dst_app_without_stats.append(dst)

        # Store mapping of stream_id -> queue_id.
        re_result = re.findall(r'pcp: ([\d]+), name: \\\"([^\\]+)\\\"', line)
        if re_result:
            for pcp, stream in re_result:
                stream_id = stream.split('-')[1]
                stream_id_queue_id_mapping[stream_id] = pcp

# print(dst_app_stream_info_mapping)

# Print stream info if max(meanBitLifeTimePerPacket) > deadline.
print("Streams with max(meanBitLifeTimePerPacket) > deadline")
for dst_app, stream_info in dst_app_stream_info_mapping.items():
    if stream_info['type'] == 'tsn':
        if stream_info['max'] > stream_info['period']: # deadline == period
            print("{}-{}, {}, queue: {}, period: {}, max: {}, mean: {}".format(
                stream_info['type'],
                stream_info['stream_id'],
                dst_app,
                stream_id_queue_id_mapping[stream_info['stream_id']],
                format(stream_info['period'], '.1e'),
                format(stream_info['max'], '.1e'),
                format(stream_info['mean'], '.1e')
            ))
    elif stream_info['type'] == 'avb':
        if stream_info['max'] > 2e-3: # deadline == 2000us
            print("{}-{}, {}, max: {}(> 2000us)".format(
                stream_info['type'],
                stream_info['stream_id'],
                dst_app,
                format(stream_info['max'], '.1e'),
            ))

# Print streams without stats of meanBitLifeTimePerPacket.
print("\nStreams without stats of meanBitLifeTimePerPacket:")
for dst in dst_app_without_stats:
    print("{}-{}, queue: {}, period: {}".format(
        dst_app_stream_info_mapping[dst]['type'],
        dst_app_stream_info_mapping[dst]['stream_id'],
        stream_id_queue_id_mapping[dst_app_stream_info_mapping[dst]['stream_id']],
        dst_app_stream_info_mapping[dst]['period']
    ))