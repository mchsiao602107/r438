#ifndef R438GATESCHEDULECONFIGURATOR_H_
#define R438GATESCHEDULECONFIGURATOR_H_

#include "inet/linklayer/configurator/gatescheduling/base/GateScheduleConfiguratorBase.h"

#include <fstream>
#include <string>

namespace inet
{
    class INET_API r438GateScheduleConfigurator : public GateScheduleConfiguratorBase
    {
        protected:

            // Override this function to implement self-defined scheduling algorithm.
            virtual Output *computeGateScheduling(const Input& input) const override;

            // Set GCL schedule for a specific (switch, port, queue).
            Output::Schedule *set_gcl_schedule(char* device_id, int port_id, int queue_id, Input::Port* port) const;
    };
}

#endif
