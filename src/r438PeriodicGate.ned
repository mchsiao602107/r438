package r438;

import inet.queueing.gate.PeriodicGate;
import inet.queueing.contract.IPacketGate;

simple r438PeriodicGate extends PeriodicGate like IPacketGate
{
    parameters:
    
	    // Explicitly specify the C++ class, which is defined in inet namespace.
	    @class(inet::queueing::r438PeriodicGate);
}