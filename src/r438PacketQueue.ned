package r438;

import inet.queueing.queue.PacketQueue;
import inet.queueing.contract.IPacketQueue;

simple r438PacketQueue extends PacketQueue like IPacketQueue
{
    parameters:
    
    	int round_number = default(1);
    
	    // Explicitly specify the C++ class, which is defined in inet namespace.
	    @class(inet::queueing::r438PacketQueue);
}