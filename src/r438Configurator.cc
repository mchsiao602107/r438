#include "r438Configurator.h"

namespace inet
{
    // Register this module to be used in omnetpp.
    Define_Module(r438Configurator);

    r438Configurator::Output *r438Configurator::computeGateScheduling(const Input& input) const
    {
        // TODO 1: Generate text files for forwarding tables.
        // TODO 2: Return Output() as GCL schedules.
        // --------------------------------------------------

        // GCL schedules for all ports of all switches.
        auto output = new Output();

        // Iterate through all ports of all switches.
        for (auto port : input.ports) {
            // Iterate through all queues of a port.
            for (int gate_index = 0; gate_index < port->numGates; gate_index ++) {

            }
        }


        return output;
    }
}
