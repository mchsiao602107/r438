package r438;

import inet.linklayer.configurator.StreamRedundancyConfigurator;
import inet.networklayer.configurator.contract.INetworkConfigurator;

simple r438StreamRedundancyConfigurator extends StreamRedundancyConfigurator like INetworkConfigurator
{
	parameters:
	    // Explicitly specify the C++ class, which is defined in inet namespace.
	    @class(inet::r438StreamRedundancyConfigurator);
}