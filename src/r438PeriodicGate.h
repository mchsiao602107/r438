#ifndef r438PERIODICGATE_H_
#define r438PERIODICGATE_H_

#include "inet/queueing/gate/PeriodicGate.h"

namespace inet {
    namespace queueing {

        class INET_API r438PeriodicGate : public PeriodicGate
        {
            protected:

                // Override this to function.
                virtual void handleMessage(cMessage *message) override;
        };
    
    } // namespace queueing,
} // namespace inet

#endif