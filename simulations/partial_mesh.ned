package r438.simulations;

import inet.common.scenario.ScenarioManager;
import inet.networks.base.TsnNetworkBase;
import inet.node.tsn.TsnDevice;
import inet.node.tsn.TsnSwitch;

network partial_mesh extends TsnNetworkBase
{
    @display("bgb=1224.2101,943.306");

    types:

        channel ethernet_link extends ned.DatarateChannel
        {
            datarate = 1Gbps;
            
            // Propagation delay, bit error rate, and packet error rate.
            //delay = 100ns;
            // ber = 0;
            // per = 0;
        }

    submodules:

        scenario_manager: ScenarioManager {
            @display("p=100,800;is=s");
        }

		// 6 end stations.
        es_1: TsnDevice {
            @display("p=496.22797,132.57999");
        }
        es_2: TsnDevice {
            @display("p=994.35,132.57999");
        }
        es_3: TsnDevice {
            @display("p=496.22797,232.96199");
        }
        es_4: TsnDevice {
            @display("p=994.35,232.96199");
        }
        es_5: TsnDevice {
            @display("p=496.22797,331.44998");
        }
        es_6: TsnDevice {
            @display("p=994.35,331.44998");
        }

        // 12 switches.
        s_1: TsnSwitch {
            @display("p=594.71594,132.57999");
        }
        s_2: TsnSwitch {
            @display("p=695.09796,132.57999");
        }
        s_3: TsnSwitch {
            @display("p=795.48,132.57999");
        }
        s_4: TsnSwitch {
            @display("p=893.96796,132.57999");
        }
        s_5: TsnSwitch {
            @display("p=594.71594,232.96199");
        }
        s_6: TsnSwitch {
            @display("p=695.09796,232.96199");
        }
        s_7: TsnSwitch {
            @display("p=795.48,232.96199");
        }
        s_8: TsnSwitch {
            @display("p=893.96796,232.96199");
        }
        s_9: TsnSwitch {
            @display("p=594.71594,331.44998");
        }
        s_10: TsnSwitch {
            @display("p=695.09796,331.44998");
        }
        s_11: TsnSwitch {
            @display("p=795.48,331.44998");
        }
        s_12: TsnSwitch {
            @display("p=893.96796,331.44998");
        }

    connections:

        // Horizontal links.
        es_1.ethg++ <--> ethernet_link <--> s_1.ethg++;
        s_1.ethg++ <--> ethernet_link <--> s_2.ethg++;
        s_2.ethg++ <--> ethernet_link <--> s_3.ethg++;
        s_3.ethg++ <--> ethernet_link <--> s_4.ethg++;
        s_4.ethg++ <--> ethernet_link <--> es_2.ethg++;
        es_3.ethg++ <--> ethernet_link <--> s_5.ethg++;
        s_5.ethg++ <--> ethernet_link <--> s_6.ethg++;
        s_6.ethg++ <--> ethernet_link <--> s_7.ethg++;
        s_7.ethg++ <--> ethernet_link <--> s_8.ethg++;
        s_8.ethg++ <--> ethernet_link <--> es_4.ethg++;
        es_5.ethg++ <--> ethernet_link <--> s_9.ethg++;
        s_9.ethg++ <--> ethernet_link <--> s_10.ethg++;
        s_10.ethg++ <--> ethernet_link <--> s_11.ethg++;
        s_11.ethg++ <--> ethernet_link <--> s_12.ethg++;
        s_12.ethg++ <--> ethernet_link <--> es_6.ethg++;

        // Vertical links.
        s_1.ethg++ <--> ethernet_link <--> s_5.ethg++;
        s_5.ethg++ <--> ethernet_link <--> s_9.ethg++;
        s_2.ethg++ <--> ethernet_link <--> s_6.ethg++;
        s_6.ethg++ <--> ethernet_link <--> s_10.ethg++;
        s_3.ethg++ <--> ethernet_link <--> s_7.ethg++;
        s_7.ethg++ <--> ethernet_link <--> s_11.ethg++;
        s_4.ethg++ <--> ethernet_link <--> s_8.ethg++;
        s_8.ethg++ <--> ethernet_link <--> s_12.ethg++;
}
