package r438;

import inet.linklayer.configurator.gatescheduling.base.GateScheduleConfiguratorBase;
import inet.linklayer.configurator.gatescheduling.contract.IGateScheduleConfigurator;

simple r438Configurator extends GateScheduleConfiguratorBase like IGateScheduleConfigurator
{
	parameters:
	    // Explicitly specify the C++ class, which is defined in inet namespace.
	    @class(inet::r438Configurator);
}