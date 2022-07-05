#ifndef R438CONFIGURATOR_H_
#define R438CONFIGURATOR_H_

#include "inet/linklayer/configurator/gatescheduling/base/GateScheduleConfiguratorBase.h"

namespace inet
{
    class INET_API r438Configurator : public GateScheduleConfiguratorBase
    {
        protected:

            // Override this function to implement self-defined scheduling algorithm.
            virtual Output *computeGateScheduling(const Input& input) const override;

            // Function to implement self-defined routing algorithm.
    };
}

#endif
