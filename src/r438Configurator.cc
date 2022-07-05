#include "r438Configurator.h"

namespace inet
{
    // Register this module to be used in omnetpp.
    Define_Module(r438Configurator);

    r438Configurator::Output *r438Configurator::computeGateScheduling(const Input& input) const
    {
        // TODO 1: Generate text files for forwarding tables.
        // TODO 2: Return Output() as GCL schedules.
        
        // Reference: AlwaysOpenGateScheduleConfigurator

        // GCL schedules for all ports of all switches.
        auto output = new Output();

        // Iterate through all ports of all switches.
        for (auto port : input.ports) {
            // Iterate through all queues of a port.
            for (int gate_index = 0; gate_index < port->numGates; gate_index ++) {
                
                Output::Schedule *schedule = new Output::Schedule();
                schedule->port = port;
                schedule->gateIndex = gate_index;
                schedule->cycleStart = 0;
                schedule->cycleDuration = gateCycleDuration;

                Output::Slot slot;
                slot.start = 0;
                slot.duration = gateCycleDuration;

                schedule->slots.push_back(slot);
                output->gateSchedules[port].push_back(schedule);
            }
        }

        for (auto application : input.applications)
            output->applicationStartTimes[application] = 0;

        return output;
    }
}
