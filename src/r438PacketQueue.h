#ifndef r438PACKETQUEUE_H_
#define r438PACKETQUEUE_H_

#include "inet/queueing/queue/PacketQueue.h"

namespace inet {
    namespace queueing {

        class INET_API r438PacketQueue : public PacketQueue
        {
            protected:

                int order_count;
                int order_streams[500];
                int eligible_stream_index;

                int buffer_count;
                Packet *stream_buffer[500];

                // Override this to read information about flow reordering.
                virtual void initialize(int stage) override;
                // Override this to support flow reordering before enqueuing frames into FIFO queue.
                virtual void pushPacket(Packet *packet, cGate *gate) override;
        };
    
    } // namespace queueing,
} // namespace inet

#endif
