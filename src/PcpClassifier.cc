#include "inet/linklayer/common/PcpTag_m.h"
#include "inet/queueing/function/PacketClassifierFunction.h"

namespace inet {

static int classifyPacketByPcp(Packet *packet)
{
    const auto& pcpInd = packet->findTag<PcpInd>();
    if (pcpInd != nullptr) {
        int pcp = pcpInd->getPcp();
        // TSN streams are allocated to pcp 0 & 1 => expressMacLayer
        if (pcp == 0 || pcp == 1)
            return 0;
        // AVB streams are allocated to pcp 7 => preemptableMacLayer
        else
            return 1;
    }
    else
        return 0;
}

Register_Packet_Classifier_Function(PacketPcpIndClassifier, classifyPacketByPcp);

} // namespace inet
