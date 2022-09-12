#ifndef R438GATESCHEDULECONFIGURATOR_H_
#define R438GATESCHEDULECONFIGURATOR_H_

#include "inet/linklayer/configurator/gatescheduling/base/GateScheduleConfiguratorBase.h"
#include "inet/queueing/gate/PeriodicGate.h"

#include <fstream>
#include <string>

namespace inet
{
    class INET_API r438GateScheduleConfigurator : public GateScheduleConfiguratorBase
    {
        protected:

            // Override this function to implement self-defined scheduling algorithm.
            virtual Output *computeGateScheduling(const Input& input) const override;

            // Override these to locate ".macLayer.expressMacLayer.queue".
            virtual void addPorts(Input& input) const override;
            virtual void configureGateScheduling() override;

            // Set GCL schedule for a specific (switch, port, queue).
            Output::Schedule *set_gcl_schedule(char* device_id, int port_id, int queue_id, Input::Port* port) const;
    };
}

#endif
