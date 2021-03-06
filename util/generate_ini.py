import yaml
import re

name_mapping = {"3": "es_1", "4": "es_3", "5": "es_5",
                "6": "s_1", "7": "s_5", "8": "s_9",
                "9": "s_2", "10": "s_6", "11": "s_10",
                "12": "s_3", "13": "s_7", "14": "s_11",
                "15": "s_4", "16": "s_8", "17": "s_12",
                "0": "es_2", "1": "es_4", "2": "es_6",}

# *********************************************
# How to handle non-schedulable avb's queue ID?
# *********************************************
stream_id_queue_id_mapping = dict()
filename = "./stream_id_queue_id_mapping/stream_id_queue_id_mapping.txt"
with open(filename, "rt") as my_file:
    while True:
        line = my_file.readline()
        if not line:
            break
        stream_id = str(re.findall(r"stream ID: ([\d]+)", line)[0])
        is_scheduled = str(re.findall(r"is scheduled: ([\w]+)", line)[0])
        if is_scheduled == "true":
            queue_id = str(re.findall(r"queue: ([\d]+)", line)[0])
        else:
            queue_id = 7
        stream_id_queue_id_mapping[stream_id] = queue_id

# Read yaml file for streams.
filename = "./streams/mesh-iso40-aud20-01-a.yaml"
with open(filename, "rt") as my_file:
    data = yaml.safe_load(my_file)

# Generate .ini file.
filename = "../simulations/auto-generated.ini"
network_name = "partial_mesh"
with open(filename, "wt") as my_file:

    # General settings.
    # -----------------
    my_file.write("[General]\n")
    my_file.write("network = {}\n".format(network_name))
    my_file.write("sim-time-limit = 5s\n")
    my_file.write("*.*.eth[*].bitrate = 1Gbps\n")
    my_file.write("\n")

    # Gate schedule visualizer.
    # -------------------------
    my_file.write("**.displayGateSchedules = true\n")
    my_file.write('**.gateFilter = "**.eth[0].**"\n')
    my_file.write("**.gateScheduleVisualizer.height = 10\n")
    my_file.write('**.gateScheduleVisualizer.placementHint = "left"\n')
    my_file.write("\n")

    # Number of applications.
    # -----------------------
    num_source_applications = {"es_1": 0, "es_2": 0, "es_3": 0, "es_4": 0, "es_5": 0, "es_6": 0}
    num_destination_applications = {"es_1": 0, "es_2": 0, "es_3": 0, "es_4": 0, "es_5": 0, "es_6": 0}
    for stream in data["tsns"] + data["avbs"]:
        num_source_applications[name_mapping[str(stream["src"])]] += 1
        num_destination_applications[name_mapping[str(stream["dst"])]] += 1
    for es in ["es_1", "es_2", "es_3", "es_4", "es_5", "es_6"]:
        if num_source_applications[es] + num_destination_applications[es] > 0:
            my_file.write("{}.{}.numApps = {}\n".format(network_name, es, num_source_applications[es] + num_destination_applications[es]))
        if num_source_applications[es] > 0:
            my_file.write("{}.{}.hasOutgoingStreams = true\n".format(network_name, es))
        if num_destination_applications[es] > 0:
            my_file.write("{}.{}.hasIncomingStreams = true\n".format(network_name, es))
    my_file.write("\n")    
    
    # Enable egress traffic shaping on end stations.
    # ----------------------------------------------
    my_file.write("{}.es_*.hasEgressTrafficShaping = true\n".format(network_name))
    my_file.write("\n")
    
    # Enable switching.
    # -----------------
    my_file.write("{}.s_*.hasIncomingStreams = true\n".format(network_name))
    my_file.write("{}.s_*.hasOutgoingStreams = true\n".format(network_name))
    my_file.write("{}.s_*.hasEgressTrafficShaping = true\n".format(network_name))
    my_file.write("\n")

    # Make gates initially open.
    # --------------------------
    #my_file.write("partial_mesh.es_*.eth[*].macLayer.queue.transmissionGate[*].initiallyOpen = true\n")
    #my_file.write("partial_mesh.s_*.eth[*].macLayer.queue.transmissionGate[*].initiallyOpen = true\n")
    #my_file.write("\n")
    
    # Application settings.
    # ---------------------
    app_counts = {"es_1": 0, "es_2": 0, "es_3": 0, "es_4": 0, "es_5": 0, "es_6": 0}
    udp_port_number = 5000

    # TSN streams.
    for stream in data["tsns"]:
        source, destination = name_mapping[str(stream["src"])], name_mapping[str(stream["dst"])]
        frame_size, period = stream["size"], stream["period"]

        # Source application.
        my_file.write('{}.{}.app[{}].typename = "UdpSourceApp"\n'.format(network_name, source, app_counts[source]))
        my_file.write('{}.{}.app[{}].display-name = "tsn-{}-src"\n'.format(network_name, source, app_counts[source], udp_port_number - 5000))
        my_file.write('{}.{}.app[{}].io.destAddress = "{}"\n'.format(network_name, source, app_counts[source], destination))
        my_file.write('{}.{}.app[{}].io.destPort = {}\n'.format(network_name, source, app_counts[source], udp_port_number))
        my_file.write('{}.{}.app[{}].source.packetNameFormat = "%M-%m-%c"\n'.format(network_name, source, app_counts[source]))
        my_file.write('{}.{}.app[{}].source.packetLength = {}B\n'.format(network_name, source, app_counts[source], frame_size))
        my_file.write('{}.{}.app[{}].source.productionInterval = {}us\n'.format(network_name, source, app_counts[source], period))

        # Destination application.
        my_file.write('{}.{}.app[{}].typename = "UdpSinkApp"\n'.format(network_name, destination, app_counts[destination]))
        my_file.write('{}.{}.app[{}].display-name = "tsn-{}-dst"\n'.format(network_name, destination, app_counts[destination], udp_port_number - 5000))
        my_file.write('{}.{}.app[{}].io.localPort = {}\n'.format(network_name, destination, app_counts[destination], udp_port_number))
        my_file.write("\n")

        app_counts[source] += 1
        app_counts[destination] += 1
        udp_port_number += 1
    
    # AVB streams.
    for stream in data["avbs"]:
        source = name_mapping[str(stream["src"])]
        destination = name_mapping[str(stream["dst"])]
        frame_size = stream["size"]
        period = stream["period"]

        # Source application.
        my_file.write('{}.{}.app[{}].typename = "UdpSourceApp"\n'.format(network_name, source, app_counts[source]))
        my_file.write('{}.{}.app[{}].display-name = "avb-{}-src"\n'.format(network_name, source, app_counts[source], udp_port_number - 5000))
        my_file.write('{}.{}.app[{}].io.destAddress = "{}"\n'.format(network_name, source, app_counts[source], destination))
        my_file.write('{}.{}.app[{}].io.destPort = {}\n'.format(network_name, source, app_counts[source], udp_port_number))
        my_file.write('{}.{}.app[{}].source.packetNameFormat = "%M-%m-%c"\n'.format(network_name, source, app_counts[source]))
        my_file.write('{}.{}.app[{}].source.packetLength = {}B\n'.format(network_name, source, app_counts[source], frame_size))
        my_file.write('{}.{}.app[{}].source.productionInterval = {}us\n'.format(network_name, source, app_counts[source], period))

        # Destination application.
        my_file.write('{}.{}.app[{}].typename = "UdpSinkApp"\n'.format(network_name, destination, app_counts[destination]))
        my_file.write('{}.{}.app[{}].display-name = "avb-{}-dst"\n'.format(network_name, destination, app_counts[destination], udp_port_number - 5000))
        my_file.write('{}.{}.app[{}].io.localPort = {}\n'.format(network_name, destination, app_counts[destination], udp_port_number))
        my_file.write("\n")

        app_counts[source] += 1
        app_counts[destination] += 1
        udp_port_number += 1

    # PCP to gate index mapping.
    # --------------------------
    # 1. "PcpTrafficClassClassifier.mapping" for switches.
    my_file.write("*.switch.eth[*].macLayer.queue.classifier.mapping = [[0, 0, 0, 0, 0, 0, 0, 0],\n")
    my_file.write("                                                     [0, 0, 0, 0, 0, 1, 1, 1],\n")
    my_file.write("                                                     [0, 0, 0, 1, 1, 2, 2, 2],\n")
    my_file.write("                                                     [0, 0, 0, 1, 1, 2, 3, 3],\n")
    my_file.write("                                                     [0, 1, 1, 2, 2, 3, 4, 4],\n")
    my_file.write("                                                     [0, 1, 1, 2, 2, 3, 4, 5],\n")
    my_file.write("                                                     [0, 1, 2, 3, 3, 4, 5, 6],\n")
    my_file.write("                                                     [0, 1, 2, 3, 4, 5, 6, 7]]\n")
    my_file.write("\n")
    
    # 2. "bridging.streamIdentifier.identifier.mapping" and "bridging.streamCoder.encoder.mapping" for sender.
    udp_port_number = 5000
    stream_to_udp_mapping = {"es_1": str(), "es_2": str(), "es_3": str(), "es_4": str(), "es_5": str(), "es_6": str()}
    stream_to_pcp_mapping = {"es_1": str(), "es_2": str(), "es_3": str(), "es_4": str(), "es_5": str(), "es_6": str()}
    for stream in data["tsns"]:
        source = name_mapping[str(stream["src"])]
        line = '{{stream: "tsn-{}", packetFilter: expr(udp.destPort == {})}}'.format(udp_port_number - 5000, udp_port_number)
        if not stream_to_udp_mapping[source]:
            stream_to_udp_mapping[source] = line
        else:
            stream_to_udp_mapping[source] += ",\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t" + line
        line = '{{stream: "tsn-{}", pcp: {}}}'.format(udp_port_number - 5000, stream_id_queue_id_mapping[str(udp_port_number - 5000)])
        if not stream_to_pcp_mapping[source]:
            stream_to_pcp_mapping[source] = line
        else:
            stream_to_pcp_mapping[source] += ",\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t" + line
        udp_port_number += 1
    for stream in data["avbs"]:
        source = name_mapping[str(stream["src"])]
        line = '{{stream: "avb-{}", packetFilter: expr(udp.destPort == {})}}'.format(udp_port_number - 5000, udp_port_number)
        if not stream_to_udp_mapping[source]:
            stream_to_udp_mapping[source] = line
        else:
            stream_to_udp_mapping[source] += ",\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t" + line
        line = '{{stream: "avb-{}", pcp: {}}}'.format(udp_port_number - 5000, stream_id_queue_id_mapping[str(udp_port_number - 5000)])
        if not stream_to_pcp_mapping[source]:
            stream_to_pcp_mapping[source] = line
        else:
            stream_to_pcp_mapping[source] += ",\n\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t" + line
        udp_port_number += 1
    for es, lines in stream_to_udp_mapping.items():
        my_file.write("{}.{}.bridging.streamIdentifier.identifier.mapping = [{}]\n".format(network_name, es, lines))
    my_file.write("\n")
    for es, lines in stream_to_pcp_mapping.items():
        my_file.write("{}.{}.bridging.streamCoder.encoder.mapping = [{}]\n".format(network_name, es, lines))
    my_file.write("\n")
    

    # Forwarding table.
    # ----------------
    # my_file.write('{}.macForwardingTableConfigurator.typename = ""\n'.format(network_name))
    # for i in range(1, 13):
    #     my_file.write('{}.s_{}.macTable.forwardingTableFile = "forwarding_table_s_{}.txt"\n'.format(network_name, i, i))
    # my_file.write("\n")

    # Routing and FRER.
    # -----------------
    my_file.write('*.macForwardingTableConfigurator.typename = ""\n')
    my_file.write('*.*.hasStreamRedundancy = true\n')
    my_file.write('*.*.bridging.streamRelay.typename = "StreamRelayLayer"\n')
    my_file.write('*.*.bridging.streamCoder.typename = "StreamCoderLayer"\n')
    my_file.write('*.streamRedundancyConfigurator.typename = "StreamRedundancyConfigurator"\n')
    my_file.write('*.streamRedundancyConfigurator.configuration = [\n')

    # Add routes for TSN streams.
    with open("./routes_tsn_avb/routes_tsn.txt", "rt") as routes_tsn_file:
        while True:
            line = routes_tsn_file.readline()
            if not line:
                break

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

            # Add only first half of streams.
            # expr(udp.destPort == {})
            if stream_id < 60:
                my_file.write('\t{{pcp: {}, name: "{}", packetFilter: "*", source: "{}", destination: "{}", trees: [[[{}]], [[{}]]]}},\n'.format(
                    stream_id_queue_id_mapping[str(stream_id)],
                    "tsn-" + str(stream_id),
                    #5000 + stream_id,
                    route_1_mapped[0],
                    route_1_mapped[-1],
                    route_1_mapped_string,
                    route_2_mapped_string
                ))
    
    # Add routes for AVB streams.
    with open("./routes_tsn_avb/routes_avb.txt", "rt") as routes_avb_file:
        while True:
            line = routes_avb_file.readline()
            if not line:
                break

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

            # Add only first half of streams.
            if stream_id < 60:
                if stream_id == 59:
                    my_file.write('\t{{pcp: {}, name: "{}", packetFilter: "*", source: "{}", destination: "{}", trees: [[[{}]], [[{}]]]}}]\n'.format(
                        stream_id_queue_id_mapping[str(stream_id)],
                        "avb-" + str(stream_id),
                        #5000 + stream_id,
                        route_1_mapped[0],
                        route_1_mapped[-1],
                        route_1_mapped_string,
                        route_2_mapped_string
                    ))
                else:
                    my_file.write('\t{{pcp: {}, name: "{}", packetFilter: "*", source: "{}", destination: "{}", trees: [[[{}]], [[{}]]]}},\n'.format(
                        stream_id_queue_id_mapping[str(stream_id)],
                        "avb-" + str(stream_id),
                        #5000 + stream_id,
                        route_1_mapped[0],
                        route_1_mapped[-1],
                        route_1_mapped_string,
                        route_2_mapped_string
                    ))

    my_file.write("\n")

    # Scheduling.
    # -----------
    my_file.write('*.gateScheduleConfigurator.typename = "r438Configurator"\n')
    my_file.write('*.gateScheduleConfigurator.gateCycleDuration = {}us\n'.format(data["scale"]["hyperperiod"]))
    """
    my_file.write('*.gateScheduleConfigurator.configuration = \n')
    
    count = 0
    app_counts = {"es_1": 0, "es_2": 0, "es_3": 0, "es_4": 0, "es_5": 0, "es_6": 0}
    for stream in data["tsns"]:
        source, destination = name_mapping[str(stream["src"])], name_mapping[str(stream["dst"])]
        frame_size, period, deadline = stream["size"], stream["period"], stream["deadline"]
        
        if count == 0:
            my_file.write('\t[{{pcp: 7, gateIndex: 7, application: "app[{}]", source: "{}", destination: "{}", packetLength: {}B, packetInterval: {}us, maxLatency: {}us}},\n'.format(app_counts[source], source, destination, frame_size, period, deadline))
        else:
            my_file.write('\t {{pcp: 7, gateIndex: 7, application: "app[{}]", source: "{}", destination: "{}", packetLength: {}B, packetInterval: {}us, maxLatency: {}us}},\n'.format(app_counts[source], source, destination, frame_size, period, deadline))
        count += 1

        app_counts[source] += 1
        app_counts[destination] += 1
    
    count = 0
    for stream in data["avbs"]:
        source, destination = name_mapping[str(stream["src"])], name_mapping[str(stream["dst"])]
        frame_size, period, deadline = stream["size"], stream["period"], stream["deadline"]
        
        if count == len(data["avbs"]) - 1:
            my_file.write('\t {{pcp: 5, gateIndex: 5, application: "app[{}]", source: "{}", destination: "{}", packetLength: {}B, packetInterval: {}us, maxLatency: {}us}}]\n'.format(app_counts[source], source, destination, frame_size, period, deadline))
        else:
            my_file.write('\t {{pcp: 5, gateIndex: 5, application: "app[{}]", source: "{}", destination: "{}", packetLength: {}B, packetInterval: {}us, maxLatency: {}us}},\n'.format(app_counts[source], source, destination, frame_size, period, deadline))
        count += 1

        app_counts[source] += 1
        app_counts[destination] += 1

    my_file.write('\n')
    """
