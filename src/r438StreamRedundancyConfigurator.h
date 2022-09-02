#ifndef r438STREAMREDUNDANCYCONFIGURATOR_H_
#define r438STREAMREDUNDANCYCONFIGURATOR_H_

#include "inet/linklayer/configurator/StreamRedundancyConfigurator.h"

namespace inet {

class INET_API r438StreamRedundancyConfigurator : public StreamRedundancyConfigurator
{
  protected:
    std::map<std::pair<std::string, int>, int> nextVlanIds; // maps network node name and streamId from streamName to next available VLAN ID

	// Override this function to assign vlanId according to streamId.
    virtual void computeStreamEncodings(cValueMap *streamConfiguration) override;
};

} // namespace inet

#endif
