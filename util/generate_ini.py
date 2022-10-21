import yaml
import re
import sys
import random

# Flags for experimental purposes.
is_avb_disable = True

name_mapping = {"3": "es_1", "4": "es_3", "5": "es_5",
                "6": "s_1", "7": "s_5", "8": "s_9",
                "9": "s_2", "10": "s_6", "11": "s_10",
                "12": "s_3", "13": "s_7", "14": "s_11",
                "15": "s_4", "16": "s_8", "17": "s_12",
                "0": "es_2", "1": "es_4", "2": "es_6",}

# Get the round number from command line.
if len(sys.argv) != 2:
    print("[error] to run this script -> python3 generate_ini.py round_number")
    sys.exit(1)
round_number = int(sys.argv[1])
if round_number not in [1, 2]:
    print("[error] invalid round number")
    sys.exit(1)

# Stream ID to queue ID mapping.
stream_id_queue_id_mapping = dict()
failed_streams = list()
filename = "./stream_id_queue_id_mapping/stream_id_queue_id_mapping_round_{}.txt".format(round_number)
with open(filename, "rt") as my_file:
    for line in my_file:
        stream_id = str(re.findall(r"stream ID: ([\d]+)", line)[0])
        is_scheduled = str(re.findall(r"is scheduled: ([\w]+)", line)[0])
        if is_scheduled == "true":
            queue_id = str(re.findall(r"queue: ([\d]+)", line)[0])
            stream_id_queue_id_mapping[stream_id] = queue_id
        else:
            queue_id = "7"
            stream_id_queue_id_mapping[stream_id] = queue_id
            failed_streams.append(int(stream_id))

# Read yaml file for stream specification.
filename = "./streams/mesh-iso40-aud20-01-a.yaml"
with open(filename, "rt") as my_file:
    data = yaml.safe_load(my_file)
if round_number == 2:
    filename = "./streams/mesh-iso40-aud20-01-b.yaml"
    with open(filename, "rt") as my_file:
        data_2 = yaml.safe_load(my_file)
    data["tsns"].extend(data_2["tsns"])
    data["avbs"].extend(data_2["avbs"])
# Append stream ID for tsn.
stream_id = 0
for stream in data["tsns"]:
    if stream_id == 40:
        stream_id = 60
    stream["stream_id"] = stream_id
    stream_id += 1
# Append stream ID for avb.
stream_id = 40
for stream in data["avbs"]:
    if stream_id == 60:
        stream_id = 100
    stream["stream_id"] = stream_id
    stream_id += 1

# Stream ID to initial production offset mapping.
stream_id_initial_production_offset = dict()
filename = "./stream_initial_production_offset/stream_initial_production_offset_round_{}.txt".format(round_number)
with open(filename, "rt") as my_file:
    for line in my_file:
        stream_id = str(re.findall(r"stream ID: ([\d]+)", line)[0])
        offset = str(re.findall(r"initial production offset: ([\d]+)", line)[0])
        stream_id_initial_production_offset[int(stream_id)] = int(offset)

# Generate .ini file.
filename = "../simulations/auto-generated-round-{}.ini".format(round_number)
network_name = "partial_mesh"
with open(filename, "wt") as my_file:

    # General settings.
    my_file.write("[General]\n")
    my_file.write("network = {}\n".format(network_name))
    my_file.write("sim-time-limit = 6ms\n")
    my_file.write("record-eventlog = false\n")
    my_file.write("**.result-recording-modes = all\n")
    my_file.write("**.cmdenv-log-level = off\n")
    my_file.write("\n")
    my_file.write("*.*.eth[*].bitrate = 1Gbps\n")
    my_file.write("\n")

    # Length of inter-frame gap.
    my_file.write("**.interFrameGapInserter.duration = 0s\n")
    my_file.write("\n")

    # Interface name visualizer.
    my_file.write("**.visualizer.interfaceTableVisualizer.displayInterfaceTables = true\n")
    my_file.write("\n")

    # Frame preemption.
    my_file.write('**.crcMode = "computed"\n')
    my_file.write('**.fcsMode = "computed"\n')
    my_file.write('*.es_*.hasFramePreemption = true\n')
    my_file.write('*.es_*.eth[*].macLayer.queue.typename = ""\n')
    my_file.write('*.es_*.eth[*].macLayer.expressMacLayer.queue.typename = "Ieee8021qTimeAwareShaper"\n')
    my_file.write('*.es_*.eth[*].macLayer.preemptableMacLayer.queue.typename = "Ieee8021qTimeAwareShaper"\n')
    my_file.write('*.es_*.eth[*].macLayer.outboundClassifier.classifierClass = "inet::PacketPcpIndClassifier"\n')
    my_file.write('*.s_*.hasFramePreemption = true\n')
    my_file.write('*.s_*.eth[*].macLayer.queue.typename = ""\n')
    my_file.write('*.s_*.eth[*].macLayer.expressMacLayer.queue.typename = "Ieee8021qTimeAwareShaper"\n')    
    my_file.write('*.s_*.eth[*].macLayer.preemptableMacLayer.queue.typename = "Ieee8021qTimeAwareShaper"\n')
    my_file.write('*.s_*.eth[*].macLayer.outboundClassifier.classifierClass = "inet::PacketPcpIndClassifier"\n')
    my_file.write('\n')
    
    # Support flow reordering on relay switches (edge switches).
    relay_switches = ["s_1", "s_4", "s_5", "s_8", "s_9", "s_12"]
    included_ports = {"s_1": [1, 2], "s_4": [0, 2], "s_5": [1, 2, 3], "s_8": [0, 2, 3], "s_9": [1, 2], "s_12": [0, 2]}
    for relay_switch, ports in included_ports.items():
        for port in ports:
            for queue_id in [0, 1]:
                my_file.write('*.{}.eth[{}].macLayer.expressMacLayer.queue.queue[{}].typename = "r438PacketQueue"\n'.format(relay_switch, port, queue_id))
                my_file.write('*.{}.eth[{}].macLayer.expressMacLayer.queue.queue[{}].round_number = {}\n'.format(relay_switch, port, queue_id, round_number))
    my_file.write('\n')

    # Enable egress traffic shaping on end stations.
    my_file.write("{}.es_*.hasEgressTrafficShaping = true\n".format(network_name))
    my_file.write('\n')

    # Enable switching.
    my_file.write("{}.s_*.hasIncomingStreams = true\n".format(network_name))
    my_file.write("{}.s_*.hasOutgoingStreams = true\n".format(network_name))
    my_file.write("{}.s_*.hasEgressTrafficShaping = true\n".format(network_name))
    my_file.write("\n")
    
    # Application settings.
    app_counts = {"es_1": 0, "es_2": 0, "es_3": 0, "es_4": 0, "es_5": 0, "es_6": 0}
    num_source_applications = {"es_1": 0, "es_2": 0, "es_3": 0, "es_4": 0, "es_5": 0, "es_6": 0}
    num_destination_applications = {"es_1": 0, "es_2": 0, "es_3": 0, "es_4": 0, "es_5": 0, "es_6": 0}
        
    # TSN streams.
    for stream in data["tsns"]:
        source, destination = name_mapping[str(stream["src"])], name_mapping[str(stream["dst"])]
        frame_size, period = stream["size"], stream["period"]
        stream_id = stream["stream_id"]

        # Exclude TSN streams not schedulable by rust.
        if stream_id not in failed_streams:

            num_source_applications[source] += 1
            num_destination_applications[destination] += 1
            
            # Source application.
            my_file.write('{}.{}.app[{}].typename = "UdpSourceApp"\n'.format(network_name, source, app_counts[source]))
            my_file.write('{}.{}.app[{}].display-name = "tsn-{}"\n'.format(network_name, source, app_counts[source], stream_id))
            my_file.write('{}.{}.app[{}].io.destAddress = "{}"\n'.format(network_name, source, app_counts[source], destination))
            my_file.write('{}.{}.app[{}].io.destPort = {}\n'.format(network_name, source, app_counts[source], stream_id + 5000))
            my_file.write('{}.{}.app[{}].source.packetNameFormat = "%M-%m-%c"\n'.format(network_name, source, app_counts[source]))
            my_file.write('{}.{}.app[{}].source.packetLength = {}B\n'.format(network_name, source, app_counts[source], frame_size - 76))
            my_file.write('{}.{}.app[{}].source.productionInterval = {}us\n'.format(network_name, source, app_counts[source], period))
            my_file.write('{}.{}.app[{}].source.initialProductionOffset = {}us\n'.format(network_name, source, app_counts[source], stream_id_initial_production_offset[stream_id]))        
            
            # Destination application.
            my_file.write('{}.{}.app[{}].typename = "UdpSinkApp"\n'.format(network_name, destination, app_counts[destination]))
            my_file.write('{}.{}.app[{}].display-name = "tsn-{}"\n'.format(network_name, destination, app_counts[destination], stream_id))
            my_file.write('{}.{}.app[{}].io.localPort = {}\n'.format(network_name, destination, app_counts[destination], stream_id + 5000))
            my_file.write("\n")

            app_counts[source] += 1
            app_counts[destination] += 1
    
    # AVB streams.
    if not is_avb_disable:
        for stream in data["avbs"]:
            source, destination = name_mapping[str(stream["src"])], name_mapping[str(stream["dst"])]
            frame_size, period = stream["size"], stream["period"]
            stream_id = stream["stream_id"]
            
            num_source_applications[source] += 1
            num_destination_applications[destination] += 1

            # Source application.
            my_file.write('{}.{}.app[{}].typename = "UdpSourceApp"\n'.format(network_name, source, app_counts[source]))
            my_file.write('{}.{}.app[{}].display-name = "avb-{}"\n'.format(network_name, source, app_counts[source], stream_id))
            my_file.write('{}.{}.app[{}].io.destAddress = "{}"\n'.format(network_name, source, app_counts[source], destination))
            my_file.write('{}.{}.app[{}].io.destPort = {}\n'.format(network_name, source, app_counts[source], stream_id + 5000))
            my_file.write('{}.{}.app[{}].source.packetNameFormat = "%M-%m-%c"\n'.format(network_name, source, app_counts[source]))
            my_file.write('{}.{}.app[{}].source.packetLength = {}B\n'.format(network_name, source, app_counts[source], frame_size - 76))
            my_file.write('{}.{}.app[{}].source.productionInterval = {}us\n'.format(network_name, source, app_counts[source], period))
            my_file.write('{}.{}.app[{}].source.initialProductionOffset = {}us\n'.format(network_name, source, app_counts[source], random.randint(0, 10)))

            # Destination application.
            my_file.write('{}.{}.app[{}].typename = "UdpSinkApp"\n'.format(network_name, destination, app_counts[destination]))
            my_file.write('{}.{}.app[{}].display-name = "avb-{}"\n'.format(network_name, destination, app_counts[destination], stream_id))
            my_file.write('{}.{}.app[{}].io.localPort = {}\n'.format(network_name, destination, app_counts[destination], stream_id + 5000))
            my_file.write("\n")

            app_counts[source] += 1
            app_counts[destination] += 1

    # Write actual number of applications.
    for es in ["es_1", "es_2", "es_3", "es_4", "es_5", "es_6"]:
        if num_source_applications[es] + num_destination_applications[es] > 0:
            my_file.write("{}.{}.numApps = {}\n".format(network_name, es, num_source_applications[es] + num_destination_applications[es]))
        if num_source_applications[es] > 0:
            my_file.write("{}.{}.hasOutgoingStreams = true\n".format(network_name, es))
        if num_destination_applications[es] > 0:
            my_file.write("{}.{}.hasIncomingStreams = true\n".format(network_name, es))
    my_file.write("\n")

    # PCP to gate index mapping.
    my_file.write("*.*.eth[*].macLayer.expressMacLayer.queue.classifier.mapping = [[0, 0, 0, 0, 0, 0, 0, 0],\n")
    my_file.write("                                                                [0, 0, 0, 0, 0, 1, 1, 1],\n")
    my_file.write("                                                                [0, 0, 0, 1, 1, 2, 2, 2],\n")
    my_file.write("                                                                [0, 0, 0, 1, 1, 2, 3, 3],\n")
    my_file.write("                                                                [0, 1, 1, 2, 2, 3, 4, 4],\n")
    my_file.write("                                                                [0, 1, 1, 2, 2, 3, 4, 5],\n")
    my_file.write("                                                                [0, 1, 2, 3, 3, 4, 5, 6],\n")
    my_file.write("                                                                [0, 1, 2, 3, 4, 5, 6, 7]]\n")
    my_file.write("\n")
    my_file.write("*.*.eth[*].macLayer.preemptableMacLayer.queue.classifier.mapping = [[0, 0, 0, 0, 0, 0, 0, 0],\n")
    my_file.write("                                                                    [0, 0, 0, 0, 0, 1, 1, 1],\n")
    my_file.write("                                                                    [0, 0, 0, 1, 1, 2, 2, 2],\n")
    my_file.write("                                                                    [0, 0, 0, 1, 1, 2, 3, 3],\n")
    my_file.write("                                                                    [0, 1, 1, 2, 2, 3, 4, 4],\n")
    my_file.write("                                                                    [0, 1, 1, 2, 2, 3, 4, 5],\n")
    my_file.write("                                                                    [0, 1, 2, 3, 3, 4, 5, 6],\n")
    my_file.write("                                                                    [0, 1, 2, 3, 4, 5, 6, 7]]\n")
    my_file.write("\n")

    # Scheduling.
    my_file.write('*.gateScheduleConfigurator.typename = "r438GateScheduleConfigurator"\n')
    my_file.write('*.gateScheduleConfigurator.gateCycleDuration = {}us\n'.format(data["scale"]["hyperperiod"]))
    my_file.write('*.gateScheduleConfigurator.round_number = {}\n'.format(round_number))
    my_file.write("\n")

    # Routing and FRER.
    my_file.write('*.macForwardingTableConfigurator.typename = ""\n')
    my_file.write('*.*.hasStreamRedundancy = true\n')
    my_file.write('*.*.bridging.streamRelay.typename = "StreamRelayLayer"\n')
    my_file.write('*.*.bridging.streamCoder.typename = "StreamCoderLayer"\n')
    my_file.write('*.streamRedundancyConfigurator.typename = "r438StreamRedundancyConfigurator"\n')
    my_file.write('*.streamRedundancyConfigurator.configuration = [\n')

    # Add routes for TSN streams.
    filename = "./routes_tsn_avb/routes_tsn_round_{}.txt".format(round_number) 
    with open(filename, "rt") as routes_tsn_file:
        line = routes_tsn_file.readline()
        while True:

            # Get "stream ID", "pair of routes in rust notation", and "pair of routes in omnetpp notation".
            stream_id = int(re.findall(r"#([\d]+)", line)[0])
            route_1, route_2 = tuple(re.findall(r"\[([,\s\d]+)\]", line))
            route_1_mapped = [name_mapping[node.strip()] for node in route_1.split(",")]
            route_2_mapped = [name_mapping[node.strip()] for node in route_2.split(",")]

            # Exclude TSN streams not schedulable by rust.
            if stream_id in failed_streams:
                line = routes_tsn_file.readline()
                continue
                
            # Convert "pair of routes in omnetpp notation" into format required by "trees".
            route_1_mapped_string = str()
            for i in range(len(route_1_mapped)):
                route_1_mapped_string += ('"' + route_1_mapped[i] + '"')
                if i != len(route_1_mapped) - 1:
                    route_1_mapped_string += ", "
            route_2_mapped_string = str()
            for i in range(len(route_2_mapped)):
                route_2_mapped_string += ('"' + route_2_mapped[i] + '"')
                if i != len(route_2_mapped) - 1:
                    route_2_mapped_string += ", "

            my_file.write('\t{{pcp: {}, name: "{}", packetFilter: "*-{}-*", source: "{}", destination: "{}", trees: [[[{}]], [[{}]]]}}'.format(
                stream_id_queue_id_mapping[str(stream_id)],
                "tsn-" + str(stream_id),
                "tsn-" + str(stream_id),
                route_1_mapped[0],
                route_1_mapped[-1],
                route_1_mapped_string,
                route_2_mapped_string
            ))

            line = routes_tsn_file.readline()
            if not line:
                if is_avb_disable:
                    my_file.write("]")
                else:
                    my_file.write(",\n")
                break
            else:
                my_file.write(",\n")
    
    # Add routes for AVB streams.
    if not is_avb_disable:
        filename = "./routes_tsn_avb/routes_avb_round_{}.txt".format(round_number) 
        with open(filename, "rt") as routes_avb_file:
            line = routes_avb_file.readline()
            while True:

                # Get "stream ID", "pair of routes in rust notation", and "pair of routes in omnetpp notation".
                stream_id = int(re.findall(r"#([\d]+)", line)[0])
                route_1, route_2 = tuple(re.findall(r"\[([,\s\d]+)\]", line))
                route_1_mapped = [name_mapping[node.strip()] for node in route_1.split(",")]
                route_2_mapped = [name_mapping[node.strip()] for node in route_2.split(",")]
                
                # Convert "pair of routes in omnetpp notation" into format required by "trees".
                route_1_mapped_string = str()
                for i in range(len(route_1_mapped)):
                    route_1_mapped_string += ('"' + route_1_mapped[i] + '"')
                    if i != len(route_1_mapped) - 1:
                        route_1_mapped_string += ", "
                route_2_mapped_string = str()
                for i in range(len(route_2_mapped)):
                    route_2_mapped_string += ('"' + route_2_mapped[i] + '"')
                    if i != len(route_2_mapped) - 1:
                        route_2_mapped_string += ", "

                my_file.write('\t{{pcp: {}, name: "{}", packetFilter: "*-{}-*", source: "{}", destination: "{}", trees: [[[{}]], [[{}]]]}}'.format(
                    stream_id_queue_id_mapping[str(stream_id)],
                    "avb-" + str(stream_id),
                    "avb-" + str(stream_id),
                    route_1_mapped[0],
                    route_1_mapped[-1],
                    route_1_mapped_string,
                    route_2_mapped_string
                ))

                line = routes_avb_file.readline()
                if not line:
                    my_file.write("]")
                    break
                else:
                    my_file.write(",\n")
