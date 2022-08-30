#include "r438GateScheduleConfigurator.h"

namespace inet
{
    // Register this module to be used in omnetpp.
    Define_Module(r438GateScheduleConfigurator);

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

                    // Queue 7 only opens when interval is long enough for a MTU-sized AVB frame (1500B).
                    // 12 us = 1500B * 8 / 1Gbps.
                    if ((end - start) <= 12)
                        continue;

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
