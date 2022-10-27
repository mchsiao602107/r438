#include "r438PeriodicGate.h"

namespace inet {
    namespace queueing {
        // Register this module to be used in omnetpp.
        Define_Module(r438PeriodicGate);

        void r438PeriodicGate::handleMessage(cMessage *message) {
            if (message == changeTimer) {
                // Schedule change-timer before process change-timer.
                scheduleChangeTimer();
                processChangeTimer();
            }
            else
                throw cRuntimeError("Unknown message");
        }
    }
}