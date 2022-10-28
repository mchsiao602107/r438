#include "r438GateScheduleConfigurator.h"

namespace inet
{
    // Register this module to be used in omnetpp.
    Define_Module(r438GateScheduleConfigurator);

    void r438GateScheduleConfigurator::addPorts(Input& input) const
    {
        // Check if frame preemption is enabled
        bool frame_preemption_enabled = par("frame_preemption_enabled");

        for (int i = 0; i < topology->getNumNodes(); i++) {
            auto node = (Node *)topology->getNode(i);
            auto networkNode = input.getNetworkNode(node->module);
            for (auto interface : node->interfaces) {
                auto networkInterface = interface->networkInterface;
                if (!networkInterface->isLoopback()) {
                    auto subqueue = networkInterface->findModuleByPath(".macLayer.queue.queue[0]");
                    if (frame_preemption_enabled)
                        subqueue = networkInterface->findModuleByPath(".macLayer.expressMacLayer.queue.queue[0]");
                    auto port = new Input::Port();
                    port->numGates = subqueue != nullptr ? subqueue->getVectorSize() : -1;
                    port->module = interface->networkInterface;
                    port->datarate = bps(interface->networkInterface->getDatarate());
                    port->propagationTime = check_and_cast<cDatarateChannel *>(interface->networkInterface->getTxTransmissionChannel())->getDelay();
                    port->maxPacketLength = B(interface->networkInterface->getMtu());
                    port->guardBand = s(port->maxPacketLength / port->datarate).get();
                    port->maxCycleTime = gateCycleDuration;
                    port->maxSlotDuration = gateCycleDuration;
                    port->startNode = networkNode;
                    networkNode->ports.push_back(port);
                    input.ports.push_back(port);
                }
            }
        }
        for (auto networkNode : input.networkNodes) {
            auto node = check_and_cast<Node *>(topology->getNodeFor(networkNode->module));
            for (auto port : networkNode->ports) {
                auto networkInterface = check_and_cast<NetworkInterface *>(port->module);
                auto link = findLinkOut(findInterface(node, networkInterface));
                auto linkOut = findLinkOut(node, networkInterface->getNodeOutputGateId());
                auto remoteNode = check_and_cast<Node *>(linkOut->getLinkOutRemoteNode());
                port->endNode = *std::find_if(input.networkNodes.begin(), input.networkNodes.end(), [&] (const auto& networkNode) {
                    return networkNode->module == remoteNode->module;
                });
                port->otherPort = *std::find_if(input.ports.begin(), input.ports.end(), [&] (const auto& otherPort) {
                    return otherPort->module == link->destinationInterface->networkInterface;
                });
                ASSERT(port->endNode);
                ASSERT(port->otherPort);
            }
        }
    }

    void r438GateScheduleConfigurator::configureGateScheduling()
    {
        // Check if frame preemption is enabled
        bool frame_preemption_enabled = par("frame_preemption_enabled");

        for (int i = 0; i < topology->getNumNodes(); i++) {
            auto node = (Node *)topology->getNode(i);
            auto networkNode = node->module;
            for (auto interface : node->interfaces) {
                auto queue = interface->networkInterface->findModuleByPath(".macLayer.queue");
                if (queue != nullptr) {
                    for (cModule::SubmoduleIterator it(queue); !it.end(); ++it) {
                        cModule *gate = *it;
                        if (dynamic_cast<queueing::PeriodicGate *>(gate) != nullptr)
                            // Explicitly reference parent's method.
                            GateScheduleConfiguratorBase::configureGateScheduling(networkNode, gate, interface);
                    }
                }
                if (frame_preemption_enabled) {
                    // Configure GCL in express MAC.
                    queue = interface->networkInterface->findModuleByPath(".macLayer.expressMacLayer.queue");
                    if (queue != nullptr) {
                        for (cModule::SubmoduleIterator it(queue); !it.end(); ++it) {
                            cModule *gate = *it;
                            if (dynamic_cast<queueing::PeriodicGate *>(gate) != nullptr)
                                // Explicitly reference parent's method.
                                GateScheduleConfiguratorBase::configureGateScheduling(networkNode, gate, interface);
                        }
                    }
                    // Configure GCL in preemptable MAC.
                    queue = interface->networkInterface->findModuleByPath(".macLayer.preemptableMacLayer.queue");
                    if (queue != nullptr) {
                        for (cModule::SubmoduleIterator it(queue); !it.end(); ++it) {
                            cModule *gate = *it;
                            if (dynamic_cast<queueing::PeriodicGate *>(gate) != nullptr)
                                // Explicitly reference parent's method.
                                GateScheduleConfiguratorBase::configureGateScheduling(networkNode, gate, interface);
                        }
                    }
                }
            }
        }
    }

    r438GateScheduleConfigurator::Output *r438GateScheduleConfigurator::computeGateScheduling(const Input& input) const
    {
        // GCL schedules for all ports of all switches.
        auto output = new Output();

        // Iterate through all ports of all switches.
        for (auto port : input.ports) {

            // Get device ID and port ID for this port.
            char device_id [10];
            int port_id;
            sscanf(port->module->getFullPath().c_str(), "partial_mesh.%[^.].eth[%d]", device_id, &port_id);

            // Set schedule for each queue of this port.
            for (int queue_id = 0; queue_id < port->numGates; queue_id ++) {
                Output::Schedule *schedule = set_gcl_schedule(device_id, port_id, queue_id, port);
                output->gateSchedules[port].push_back(schedule);
            }
        }

        // Set start time for applications.
        for (auto application : input.applications)
            output->applicationStartTimes[application] = 0;

        return output;
    }

    r438GateScheduleConfigurator::Output::Schedule *r438GateScheduleConfigurator::set_gcl_schedule(char* device_id, int port_id, int queue_id, Input::Port* port) const
    {
        Output::Schedule *schedule = new Output::Schedule();

        // Set schedule (gateCycleDuration = 2000 us simtime_t).
        schedule->port = port;
        schedule->gateIndex = queue_id;
        schedule->cycleStart = 0;
        schedule->cycleDuration = gateCycleDuration;

        // Read the round number.
        int round_number = par("round_number").intValue();

        if (queue_id == 0 || queue_id == 1) {
            std::fstream my_file;
            std::string filename = "./gcl_schedules/" + std::string(device_id) + "_port_" + std::to_string(port_id) + "_queue_" + std::to_string(queue_id) + "_round_" + std::to_string(round_number) + ".txt";
            my_file.open(filename, std::ios::in);
            if (my_file.is_open()) {

                EV << "filename = " << filename << endl;

                // Add time slots into schedule.
                std::string line;
                int start, end;
                Output::Slot slot;
                while (getline(my_file, line)) {
                    sscanf(line.c_str(), "start = %d, end = %d", &start, &end);
                    slot.start = SimTime(start, SIMTIME_US);
                    slot.duration = SimTime((end - start), SIMTIME_US);
                    schedule->slots.push_back(slot);
                }
            }
            my_file.close();
        } else if (queue_id == 7) {
            std::fstream my_file;
            std::string filename = "./gcl_schedules/" + std::string(device_id) + "_port_" + std::to_string(port_id) + "_queue_" + std::to_string(queue_id) + "_round_" + std::to_string(round_number) + ".txt";
            my_file.open(filename, std::ios::in);
            if (my_file.is_open()) {
                std::string line;
                int start, end;
                Output::Slot slot;
                while (getline(my_file, line)) {
                    sscanf(line.c_str(), "start = %d, end = %d", &start, &end);

                    // 12 us guard band if no preemption, 2 us if having preemption.
                    // Guard band is not required if using r438PeriodicGate.

                    // if ((end - start) <= 2)
                    //     continue;
                    // else
                    //     end -= 2;

                    slot.start = SimTime(start, SIMTIME_US);
                    slot.duration = SimTime((end - start), SIMTIME_US);
                    schedule->slots.push_back(slot);
                }
            }
            my_file.close();
       } else {
            // Don't add time slots into schedule (always closed).
        }

        return schedule;
    }
}
