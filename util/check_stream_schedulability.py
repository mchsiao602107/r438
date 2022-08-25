"""Check schedulability using the statistic of meanBitLifeTimePerPacket & stream deadline(period)"""
import re

result_sca_file = '../simulations/results/General-#0.sca'
result_vec_file = '../simulations/results/General-#0.vec'

dst_app_stream_info_mapping = dict()
stream_id_queue_id_mapping = dict()
vector_id_dst_app_mapping = dict()

dst_app_delay_gt_deadline = []
dst_app_without_stats = []
vector_id_delay_gt_deadline = []

with open(result_sca_file, "rt") as my_file:
    while True:
        line = my_file.readline()
        if not line:
            break

        # Store stream type & id & period from the content of ini file.
        re_result = re.search(r"config .+productionInterval (.+)us", line)
        if re_result:
            period = int(re_result[1]) / 1e6 # unit is us
            # skip 2 lines: [initialProductionOffset, dst_app typename]
            my_file.readline()
            my_file.readline()
            re_result = re.search(r"config (.+).+display-name (.+)", my_file.readline())
            dst_app, stream = re_result[1], re_result[2]
            dst_app_stream_info_mapping[dst_app] = {}
            dst_app_stream_info_mapping[dst_app]['type'] = stream.split('-')[0]
            dst_app_stream_info_mapping[dst_app]['stream_id'] = stream.split('-')[1]
            dst_app_stream_info_mapping[dst_app]['period'] = period

        # Store stats of meanBitLifeTimePerPacket.
        re_result = re.search(r"statistic (.+).sink meanBitLifeTimePerPacket:histogram", line)
        if re_result:
            dst_app = re_result[1]
            stream_info = dst_app_stream_info_mapping[dst_app]
            stream_info['count'] = int(re.search(r"field count ([\d]+)", my_file.readline())[1])
            stream_info['mean'] = float(re.search(r"field mean (.+)", my_file.readline())[1])
            stream_info['stddev'] = float(re.search(r"field stddev (.+)", my_file.readline())[1])
            stream_info['min'] = float(re.search(r"field min (.+)", my_file.readline())[1])
            stream_info['max'] = float(re.search(r"field max (.+)", my_file.readline())[1])
            # Store streams that fail to meet deadline & the ones without stats.
            if dst_app_stream_info_mapping[dst_app]['count'] == 0:
                dst_app_without_stats.append(dst_app)
            # TSN streams: deadline == period, AVB streams: deadline == 2000us
            elif stream_info['type'] == 'tsn' and stream_info['max'] > stream_info['period'] or \
                 stream_info['type'] == 'avb' and stream_info['max'] > 2e-3:
                dst_app_delay_gt_deadline.append(dst_app)

        # Store mapping of stream_id -> queue_id.
        re_result = re.findall(r'pcp: ([\d]+), name: \\\"([^\\]+)\\\"', line)
        if re_result:
            for pcp, stream in re_result:
                stream_id = stream.split('-')[1]
                stream_id_queue_id_mapping[stream_id] = pcp

# Store output vector of meanBitLifeTimePerPacket for streams that fail to meet deadline.
with open(result_vec_file, "rt") as my_file:
    while True:
        line = my_file.readline()
        if not line:
            break

        # Store vector_id to locate the output vector.
        vector_declaration_pattern = r"^vector ([\d]+) (.+)\.sink meanBitLifeTimePerPacket:vector ETV$"
        re_result = re.search(vector_declaration_pattern, line)
        if re_result:
            vector_id, dst_app = int(re_result[1]), re_result[2]
            if dst_app in dst_app_delay_gt_deadline:
                vector_id_delay_gt_deadline.append(vector_id)
                vector_id_dst_app_mapping[vector_id] = dst_app

        # Store output vector.
        id_event_time_value_pattern = r"^([\d]+)\t([\d]+)\t(.+)\t(.+)$"
        re_result = re.search(id_event_time_value_pattern, line)
        if re_result:
            vector_id = int(re_result[1])
            if vector_id in vector_id_delay_gt_deadline:
                dst_app = vector_id_dst_app_mapping[vector_id]
                count = dst_app_stream_info_mapping[dst_app]['count']
                event, time, value = int(re_result[2]), float(re_result[3]), float(re_result[4])
                if 'output_vector' not in dst_app_stream_info_mapping[dst_app].keys():
                    dst_app_stream_info_mapping[dst_app]['output_vector'] = []
                dst_app_stream_info_mapping[dst_app]['output_vector'].append("{}\t{:.4f}us\t{:.4f}us".format(event, time * 1e6, value*1e6))

# print(dst_app_stream_info_mapping)

# Print stream info if max(meanBitLifeTimePerPacket) > deadline.
print("Streams with max(meanBitLifeTimePerPacket) > deadline:")
for dst_app in dst_app_delay_gt_deadline:
    stream_info = dst_app_stream_info_mapping[dst_app]
    if stream_info['type'] == 'tsn':
        print("{}-{}, {}, queue: {}, period: {:.0f}us, max: {:.4f}us, mean: {:.4f}us".format(
            stream_info['type'],
            stream_info['stream_id'],
            dst_app,
            stream_id_queue_id_mapping[stream_info['stream_id']],
            stream_info['period'] * 1e6,
            stream_info['max'] * 1e6,
            stream_info['mean'] * 1e6,
        ))
    elif stream_info['type'] == 'avb':
        print("{}-{}, {}, max: {:.4f}us(> 2000us)".format(
            stream_info['type'],
            stream_info['stream_id'],
            dst_app,
            stream_info['max'] * 1e6,
        ))
    print('#\tEvent\tTime\t\tValue')
    for i in range(stream_info['count']):
        print(str(i) + '\t' + stream_info['output_vector'][i])

# Print streams without stats of meanBitLifeTimePerPacket.
print("\nStreams without stats of meanBitLifeTimePerPacket:")
for dst_app in dst_app_without_stats:
    print("{}-{}, queue: {}, period: {:.4f}us".format(
        dst_app_stream_info_mapping[dst_app]['type'],
        dst_app_stream_info_mapping[dst_app]['stream_id'],
        stream_id_queue_id_mapping[dst_app_stream_info_mapping[dst_app]['stream_id']],
        dst_app_stream_info_mapping[dst_app]['period'] * 1e6
    ))
