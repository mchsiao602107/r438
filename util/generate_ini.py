import yaml

name_mapping = {"3": "es_1", "4": "es_3", "5": "es_5",
                "6": "s_1", "7": "s_5", "8": "s_9",
                "9": "s_2", "10": "s_6", "11": "s_10",
                "12": "s_3", "13": "s_7", "14": "s_11",
                "15": "s_4", "16": "s_8", "17": "s_12",
                "0": "es_2", "1": "es_4", "2": "es_6",}

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
        my_file.write('{}.{}.app[{}].display-name = "TSN"\n'.format(network_name, source, app_counts[source]))
        my_file.write('{}.{}.app[{}].io.destAddress = "{}"\n'.format(network_name, source, app_counts[source], destination))
        my_file.write('{}.{}.app[{}].io.destPort = {}\n'.format(network_name, source, app_counts[source], udp_port_number))
        my_file.write('{}.{}.app[{}].source.packetNameFormat = "%M-%m-%c"\n'.format(network_name, source, app_counts[source]))
        my_file.write('{}.{}.app[{}].source.packetLength = {}B\n'.format(network_name, source, app_counts[source], frame_size))
        my_file.write('{}.{}.app[{}].source.productionInterval = {}us\n'.format(network_name, source, app_counts[source], period))

        # Destination application.
        my_file.write('{}.{}.app[{}].typename = "UdpSinkApp"\n'.format(network_name, destination, app_counts[destination]))
        my_file.write('{}.{}.app[{}].display-name = "TSN"\n'.format(network_name, destination, app_counts[destination]))
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
        my_file.write('{}.{}.app[{}].display-name = "AVB"\n'.format(network_name, source, app_counts[source]))
        my_file.write('{}.{}.app[{}].io.destAddress = "{}"\n'.format(network_name, source, app_counts[source], destination))
        my_file.write('{}.{}.app[{}].io.destPort = {}\n'.format(network_name, source, app_counts[source], udp_port_number))
        my_file.write('{}.{}.app[{}].source.packetNameFormat = "%M-%m-%c"\n'.format(network_name, source, app_counts[source]))
        my_file.write('{}.{}.app[{}].source.packetLength = {}B\n'.format(network_name, source, app_counts[source], frame_size))
        my_file.write('{}.{}.app[{}].source.productionInterval = {}us\n'.format(network_name, source, app_counts[source], period))

        # Destination application.
        my_file.write('{}.{}.app[{}].typename = "UdpSinkApp"\n'.format(network_name, destination, app_counts[destination]))
        my_file.write('{}.{}.app[{}].display-name = "AVB"\n'.format(network_name, destination, app_counts[destination]))
        my_file.write('{}.{}.app[{}].io.localPort = {}\n'.format(network_name, destination, app_counts[destination], udp_port_number))
        my_file.write("\n")

        app_counts[source] += 1
        app_counts[destination] += 1
        udp_port_number += 1
           
    # Forwarding table.
    # ----------------
    # my_file.write('{}.macForwardingTableConfigurator.typename = ""\n'.format(network_name))
    # for i in range(1, 13):
    #     my_file.write('{}.s_{}.macTable.forwardingTableFile = "forwarding_table_s_{}.txt"\n'.format(network_name, i, i))
    # my_file.write("\n")

    # Scheduling.
    # -----------
    my_file.write('*.gateScheduleConfigurator.typename = "r438Configurator"\n')
    my_file.write('*.gateScheduleConfigurator.gateCycleDuration = {}us\n'.format(data["scale"]["hyperperiod"]))
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
