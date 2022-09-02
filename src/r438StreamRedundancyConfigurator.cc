#include "r438StreamRedundancyConfigurator.h"

namespace inet {
	// Register this module to be used in omnetpp.
	Define_Module(r438StreamRedundancyConfigurator);

	void r438StreamRedundancyConfigurator::computeStreamEncodings(cValueMap *streamConfiguration)
	{
		int pcp = streamConfiguration->containsKey("pcp") ? streamConfiguration->get("pcp").intValue() : -1;
		for (int i = 0; i < topology->getNumNodes(); i++) {
			auto node = (Node *)topology->getNode(i);
			auto networkNode = node->module;
			auto networkNodeName = networkNode->getFullName();
			std::string destinationAddress = streamConfiguration->containsKey("destinationAddress") ? streamConfiguration->get("destinationAddress") : streamConfiguration->get("destination");
			std::string streamName = streamConfiguration->get("name").stringValue();
			// encoding configuration
			auto& stream = streams[streamName];
			auto& streamNode = stream.streamNodes[networkNodeName];
			for (int j = 0; j < streamNode.receivers.size(); j++) {
				auto& receiverNetworkNodeNames = streamNode.receivers[j];
				if (!receiverNetworkNodeNames.empty()) {
					std::string streamNameSuffix;
					for (auto receiverNetworkNodeName : receiverNetworkNodeNames)
						streamNameSuffix += "_" + receiverNetworkNodeName;
					auto outputStreamName = streamNode.distinctReceivers.size() == 1 ? streamName : streamName + streamNameSuffix;
					auto it = std::find_if(node->streamEncodings.begin(), node->streamEncodings.end(), [&] (const StreamEncoding& streamEncoding) {
						return streamEncoding.name == outputStreamName;
					});
					if (it != node->streamEncodings.end())
						continue;

					// Read streamId from streamName
					int streamId;
					if (streamName.substr(0, 3) == "tsn") {
						sscanf(streamName.c_str(), "tsn-%d", &streamId);
					}
					else {
						sscanf(streamName.c_str(), "avb-%d", &streamId);
					}

					// Assign vlanId according to streamId
					auto jt = nextVlanIds.emplace(std::pair<std::string, int>{networkNodeName, streamId}, 2 * streamId);

					int vlanId = jt.first->second++;
					if (vlanId > maxVlanId)
						throw cRuntimeError("Cannot assign VLAN ID in the available range");
					for (int k = 0; k < receiverNetworkNodeNames.size(); k++) {
						auto receiverNetworkNodeName = receiverNetworkNodeNames[k];
						EV_DEBUG << "Assigning VLAN id" << EV_FIELD(streamName) << EV_FIELD(networkNodeName) << EV_FIELD(receiverNetworkNodeName) << EV_FIELD(destinationAddress) << EV_FIELD(vlanId) << EV_ENDL;

						EV << "r438 " << streamName << ", " << networkNodeName << ", " << receiverNetworkNodeName << ", " << vlanId << '\n';

						assignedVlanIds[{networkNodeName, receiverNetworkNodeName, destinationAddress, streamName}] = vlanId;
						StreamEncoding streamEncoding;
						streamEncoding.name = outputStreamName;
						streamEncoding.networkInterface = streamNode.interfaces[j][k];
						streamEncoding.vlanId = vlanId;
						streamEncoding.pcp = pcp;
						streamEncoding.destination = destinationAddress;
						node->streamEncodings.push_back(streamEncoding);
					}
				}
			}
		}
	}

} // namespace inet


