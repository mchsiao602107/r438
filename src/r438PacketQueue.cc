#include "r438PacketQueue.h"
#include "inet/protocolelement/redundancy/StreamTag_m.h"
#include "inet/common/ModuleAccess.h"
#include <fstream>
#include <string>

namespace inet {
    namespace queueing {
        // Register this module to be used in omnetpp.
        Define_Module(r438PacketQueue);

        void r438PacketQueue::initialize(int stage) {
            PacketQueueBase::initialize(stage);
            if (stage == INITSTAGE_LOCAL) {
                queue.setName("storage");
                producer = findConnectedModule<IActivePacketSource>(inputGate);
                collector = findConnectedModule<IActivePacketSink>(outputGate);
                packetCapacity = par("packetCapacity");
                dataCapacity = b(par("dataCapacity"));
                buffer = findModuleFromPar<IPacketBuffer>(par("bufferModule"), this);
                packetComparatorFunction = createComparatorFunction(par("comparatorClass"));
                if (packetComparatorFunction != nullptr)
                    queue.setup(packetComparatorFunction);
                packetDropperFunction = createDropperFunction(par("dropperClass"));
            }
            else if (stage == INITSTAGE_QUEUEING) {
                checkPacketOperationSupport(inputGate);
                checkPacketOperationSupport(outputGate);
                if (producer != nullptr)
                    producer->handleCanPushPacketChanged(inputGate->getPathStartGate());
            }
            else if (stage == INITSTAGE_LAST)
                updateDisplayString();

            // Read the round number.
            int round_number = par("round_number").intValue();

            // Get switch and port that this queue belongs to.
            int port_id = -1, queue_id = -1;
            char device_id [10] = "";
            sscanf(this->getFullPath().c_str(), "partial_mesh.%[^.].eth[%d].macLayer.queue.queue[%d]", device_id, &port_id, &queue_id);
            // Check expressMacLayer only when frame preemption is enabled
            if (queue_id == -1)
                sscanf(this->getFullPath().c_str(), "partial_mesh.%[^.].eth[%d].macLayer.expressMacLayer.queue.queue[%d]", device_id, &port_id, &queue_id);

            // Get order of flows.
            std::fstream my_file;
            std::string filename = "./stream_production_offset_relay_switch/" + std::string(device_id) + "_port_" + std::to_string(port_id) + "_queue_" + std::to_string(queue_id) + "_round_" + std::to_string(round_number) + ".txt";
            my_file.open(filename, std::ios::in);
            if (my_file.is_open()) {
                std::string line;
                int stream_id, offset;
                this->order_count = 0;
                while (getline(my_file, line)) {
                    sscanf(line.c_str(), "stream ID: %d, offset: %d", &stream_id, &offset);
                    this->order_streams[this->order_count ++] = stream_id;
                }
            }
            else
                throw cRuntimeError("Fail to open file %s", filename.c_str());
            my_file.close();

            // Initialize stream buffer.
            this->buffer_count = 0;
            for (int i = 0; i < 500; i ++)
                this->stream_buffer[i] = nullptr;

            // Set the eligible flow as the first flow in the order.
            this->eligible_stream_index = 0;
        }

        void r438PacketQueue::pushPacket(Packet *packet, cGate *gate) {
            Enter_Method("pushPacket");
            take(packet);
            cNamedObject packetPushStartedDetails("atomicOperationStarted");
            emit(packetPushStartedSignal, packet, &packetPushStartedDetails);
            EV_INFO << "Pushing packet" << EV_FIELD(packet) << EV_ENDL;

            // Get stream ID of the packet.
            int stream_id;
            sscanf(packet->findTag<StreamReq>()->getStreamName(), "tsn-%d", &stream_id);

            EV << "eligible: " << this->order_streams[this->eligible_stream_index] << ", arrived: " << stream_id << endl;

            // Check whether reordering is required.
            if (stream_id == this->order_streams[this->eligible_stream_index]) {
                // Enqueue this packet, and update index of eligible stream.
                queue.insert(packet);
                this->eligible_stream_index = (this->eligible_stream_index + 1) % this->order_count;

                // Check whether buffered packets can be enqueued now.
                bool is_inserted = true;
                while (is_inserted) {
                    is_inserted = false;
                    for (int i = 0; i < this->buffer_count; i ++) {
                        Packet *buffered_packet = this->stream_buffer[i];
                        sscanf(buffered_packet->findTag<StreamReq>()->getStreamName(), "tsn-%d", &stream_id);
                        if (stream_id == this->order_streams[this->eligible_stream_index]) {
                            EV << "Enqueue stream " << stream_id << " from buffered_packet" << endl;
                            is_inserted = true;
                            queue.insert(buffered_packet);
                            this->eligible_stream_index = (this->eligible_stream_index + 1) % this->order_count;
                            for (int j = i + 1; j < this->buffer_count; j ++)
                                this->stream_buffer[j - 1] = this->stream_buffer[j];
                            this->stream_buffer[this->buffer_count - 1] = nullptr;
                            this->buffer_count --;
                            break;
                        }
                    }
                }
            } else {
                // Keep this packet in buffer until its turn.
                this->stream_buffer[this->buffer_count ++] = packet;
            }

            // queue.insert(packet);
            // if (buffer != nullptr)
            //     buffer->addPacket(packet);
            // else if (packetDropperFunction != nullptr) {
            //     while (isOverloaded()) {
            //         auto packet = packetDropperFunction->selectPacket(this);
            //         EV_INFO << "Dropping packet" << EV_FIELD(packet) << EV_ENDL;
            //         queue.remove(packet);
            //         dropPacket(packet, QUEUE_OVERFLOW);
            //     }
            // }
            ASSERT(!isOverloaded());
            if (collector != nullptr && getNumPackets() != 0)
                collector->handleCanPullPacketChanged(outputGate->getPathEndGate());
            cNamedObject packetPushEndedDetails("atomicOperationEnded");
            emit(packetPushEndedSignal, nullptr, &packetPushEndedDetails);
            updateDisplayString();
        }
    }
}
