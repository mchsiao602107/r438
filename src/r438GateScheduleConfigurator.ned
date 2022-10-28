package r438;

import inet.linklayer.configurator.gatescheduling.base.GateScheduleConfiguratorBase;
import inet.linklayer.configurator.gatescheduling.contract.IGateScheduleConfigurator;

simple r438GateScheduleConfigurator extends GateScheduleConfiguratorBase like IGateScheduleConfigurator
{
	parameters:
	    // Explicitly specify the C++ class, which is defined in inet namespace.
	    @class(inet::r438GateScheduleConfigurator);  
	    
	    // Round number to read corresponding gcl schedule text files.
	    int round_number = default(1); 

	    bool frame_preemption_enabled = default(false);
}