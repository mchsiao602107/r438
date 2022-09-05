"""Check schedulability using the statistic of meanBitLifeTimePerPacket & stream deadline(period)"""
import re
import argparse
import sys

result_sca_file = '../simulations/results/General-#0.sca'
result_vec_file = '../simulations/results/General-#0.vec'
rust_result_file = '../rust-result'

dst_app_stream_info_mapping = dict()
stream_id_queue_id_mapping = dict()
vector_id_dst_app_mapping = dict()

dst_app_delay_gt_deadline = []
dst_app_without_stats = []
vector_id_delay_gt_deadline = []

O1_rust, O1_sim = 0, 0 # non-schedulable TSN stream count
O2_rust, O2_sim = 0, 0 # non-schedulable AVB stream count
O3_rust = 0 # rerouted background stream count (rust has computed it already)
O4_rust, O4_sim = 0.0, 0.0 # sum of AVB stream worst-case delays (max(meanBitLifeTimePerPacket))

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="show output vector", action="store_true", default=False)
parser.add_argument("round_number", nargs=1, type=int)
args = parser.parse_args()

round_number = int(args.round_number[0])
if round_number not in [1, 2]:
    print("[error] invalid round number")
    sys.exit(1)

"""Read rust result"""
with open(rust_result_file, "rt") as my_file:
    lines = my_file.readlines()
    line_iter = iter(lines)
    for line in line_iter:
        float_pattern = r"([0-9]+[.][0-9]+)"
        int_pattern = r"([0-9]+)[.][0-9]+"
        obj_output_pattern = rf"^.*objectives\s\[{int_pattern}, {int_pattern}, {int_pattern}, {float_pattern}\]$"
        obj_re_result = re.search(obj_output_pattern, line)
        # check which round is it
        if obj_re_result:
            # skip 1 newline
            next(line_iter)
            round_re_result = re.search(r"^--- #([0-9]).*$", next(line_iter))
            if round_re_result:
                current_round = int(round_re_result[1])
                if current_round != round_number:
                    continue
                else:
                    O1_rust = int(obj_re_result[1])
                    O2_rust = int(obj_re_result[2])
                    O3_rust = int(obj_re_result[3])
                    O4_rust = float(obj_re_result[4])
                    break

"""Read omnetpp simulation result"""
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
            elif stream_info['type'] == 'tsn' and stream_info['max'] >= stream_info['period']:
                O1_sim += 1
                dst_app_delay_gt_deadline.append(dst_app)
            elif stream_info['type'] == 'avb':
                O4_sim += stream_info['max']
                if stream_info['max'] >= 2e-3:
                    O2_sim += 1
                    dst_app_delay_gt_deadline.append(dst_app)

        # Store mapping of stream_id -> queue_id.
        re_result = re.findall(r'pcp: ([\d]+), name: \\\"([^\\]+)\\\"', line)
        if re_result:
            for pcp, stream in re_result:
                stream_id = stream.split('-')[1]
                stream_id_queue_id_mapping[stream_id] = pcp

# Store output vector of meanBitLifeTimePerPacket for streams that fail to meet deadline.
if args.verbose:
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

"""Print stream info if max(meanBitLifeTimePerPacket) >= deadline."""
if not len(dst_app_delay_gt_deadline):
    print("All streams have max(meanBitLifeTimePerPacket) < deadline.")
else:
    print("Streams with max(meanBitLifeTimePerPacket) >= deadline:")
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
        if args.verbose:
            print('\t#\tEvent\tTime\t\tValue')
            for i in range(stream_info['count']):
                print('\t' + str(i) + '\t' + stream_info['output_vector'][i])

print()

"""Print streams without stats of meanBitLifeTimePerPacket."""
if not len(dst_app_without_stats):
    print("All streams have stats of meanBitLifeTimePerPacket.")
else:
    print("Streams without stats of meanBitLifeTimePerPacket:")
    for dst_app in dst_app_without_stats:
        print("{}-{}, queue: {}, period: {:.4f}us".format(
            dst_app_stream_info_mapping[dst_app]['type'],
            dst_app_stream_info_mapping[dst_app]['stream_id'],
            stream_id_queue_id_mapping[dst_app_stream_info_mapping[dst_app]['stream_id']],
            dst_app_stream_info_mapping[dst_app]['period'] * 1e6
        ))

print()

"""Print objectives from rust & simulation result"""
print("O1 (non-schedulable TSN stream count): {} (rust) / {} (sim)".format(O1_rust, O1_sim))
print("O2 (non-schedulable AVB stream count): {} (rust)/ {} (sim)".format(O2_rust, O2_sim))
print("O3 (rust rerouted background stream count): {} (rust) / *".format(O3_rust))
print("O4 (sum of max e2e delay of AVB streams): {:.2f}ms (rust) / {:.2f}ms (sim)".format(O4_rust, O4_sim * 1e3))