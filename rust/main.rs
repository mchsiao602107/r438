use adams_ants::util::{args, yaml};
use adams_ants::CNC;
use docopt::Docopt;

// ------------------------
use std::ops::Range;
use prepona::provide::Edges;
use prepona::prelude::Edge;
use std::fs::File;
use std::io::prelude::*;

const USAGE: &str = "
Usage:
    adams_ants [options] <scenario>
    adams_ants --help

Options:
    -h, --help             Display this message
    -a, --algo NAME        Override CNC algorithm to calculate routing sets
    -s, --seed NUM         Override random seed for OSACO and RO algorithm
    -b, --background FILE  Override background streams file
    -i, --input FILE       Override input streams file
    -t, --timeout NUM      Override timeout per configuration (in seconds)
";

fn main() {

    // parse command line arguments.
    let argv = std::env::args();
    let args: args::Args = Docopt::new(USAGE)
        .and_then(|d| d.argv(argv).deserialize())
        .unwrap_or_else(|e| e.exit());

    // Load the scenario file to obtain network and streams.
    // command line arguments may override default settings.
    let scenario = yaml::load_scenario(&args.arg_scenario)
        .unwrap()
        .override_by_args(args);

    let network = yaml::load_network(&scenario.network).unwrap();
    let (tsns1, avbs1) = yaml::load_streams(&scenario.streams.background).unwrap();
    let (tsns2, avbs2) = yaml::load_streams(&scenario.streams.input).unwrap();

    // Setup CNC to initialize the routing algorithm.
    let mut cnc = CNC::new(&scenario.algorithm.name, network)
        .with_random_seed(scenario.algorithm.seed)
        .with_verbosity(scenario.verbose);

    // Input the first half test case and configure them.
    cnc.input(tsns1, avbs1);
    let stop_cond = scenario.stop_condition();
    let elapsed = cnc.configure(&stop_cond);

    println!("--- #1 elapsed time: {} μs ---", elapsed.as_micros());

    // --------------------------------

    // Mapping from rust port ID to omnetpp port ID.
    let port_id_from_rust_to_omnetpp = ["es_1_port_0", "s_1_port_0", "es_3_port_0",
                                        "s_5_port_0", "es_5_port_0", "s_9_port_0",
                                        "s_1_port_1", "s_2_port_0", "s_5_port_1",
                                        "s_6_port_0", "s_9_port_1", "s_10_port_0",
                                        "s_2_port_1", "s_3_port_0", "s_6_port_1",
                                        "s_7_port_0", "s_10_port_1", "s_11_port_0",
                                        "s_3_port_1", "s_4_port_0", "s_7_port_1",
                                        "s_8_port_0", "s_11_port_1", "s_12_port_0",
                                        "es_2_port_0", "s_4_port_1", "es_4_port_0",
                                        "s_8_port_1", "es_6_port_0", "s_12_port_1",
                                        "s_1_port_2", "s_5_port_2", "s_5_port_3",
                                        "s_9_port_2", "s_2_port_2", "s_6_port_2",
                                        "s_6_port_3", "s_10_port_2", "s_3_port_2",
                                        "s_7_port_2", "s_7_port_3", "s_11_port_2",
                                        "s_4_port_2", "s_8_port_2", "s_8_port_3", "s_12_port_2"];

    // Collect initial production offset on end stations.
    let filename = format!("../../r438/util/stream_initial_production_offset/stream_initial_production_offset_round_1.txt");
    let mut my_file = File::create(filename).expect("Cannot open file");
    let plan = &(cnc.plan());
    for gcl_index in 0..plan.allocated_tsns.len() {
        let gcl = &(plan.allocated_tsns[gcl_index]);
        let outcomes = &(plan.outcomes);
        if gcl_index == 0 || gcl_index == 2 || gcl_index == 4 || gcl_index == 24 || gcl_index == 26 || gcl_index == 28 {
            for event in gcl.inner.iter() {
                let line = format!("stream ID: {}, initial production offset: {}\n", event.value, event.start);
                my_file.write_all(line.as_bytes()).expect("Cannot write.");
            }
        } 
    }

    // Collect production offset on relay switches.
    let plan = &(cnc.plan());
    for gcl_index in 0..plan.allocated_tsns.len() {
        let gcl = &(plan.allocated_tsns[gcl_index]);
        let hyperperiod = gcl.hyperperiod();
        let outcomes = &(plan.outcomes);
        if gcl_index == 6 || gcl_index == 30 || gcl_index == 19 || gcl_index == 42 || gcl_index == 8 || gcl_index == 31 || gcl_index == 32 || gcl_index == 21 || gcl_index == 43 || gcl_index == 44 || gcl_index == 10 || gcl_index == 33 || gcl_index == 23 || gcl_index == 45 {
            let filename = format!("../../r438/simulations/stream_production_offset_relay_switch/{}_queue_0_round_1.txt", port_id_from_rust_to_omnetpp[gcl_index]);
            let mut my_file = File::create(filename).expect("Cannot open file");
            for event in gcl.inner.iter() {
                if outcomes[event.value].is_scheduled() && outcomes[event.value].used_queue() == 0 {
                    for i in 0..hyperperiod / event.period {
                        let line = format!("stream ID: {}, offset: {}, period: {}\n", event.value, event.start + event.period * i, event.period);
                        my_file.write_all(line.as_bytes()).expect("Cannot write.");
                    }
                }
            }
            let filename = format!("../../r438/simulations/stream_production_offset_relay_switch/{}_queue_1_round_1.txt", port_id_from_rust_to_omnetpp[gcl_index]);
            let mut my_file = File::create(filename).expect("Cannot open file");
            for event in gcl.inner.iter() {
                if outcomes[event.value].is_scheduled() && outcomes[event.value].used_queue() == 1 {
                    for i in 0..hyperperiod / event.period {
                        let line = format!("stream ID: {}, offset: {}, period: {}\n", event.value, event.start + event.period * i, event.period);
                        my_file.write_all(line.as_bytes()).expect("Cannot write.");
                    }
                }
            }
        } 
    }

    // Store stream ID to queue ID mapping.
    let mut my_file = File::create("../../r438/util/stream_id_queue_id_mapping/stream_id_queue_id_mapping_round_1.txt").expect("Cannot create text file");
    for i in 0..cnc.plan().outcomes.len() {
        let mut line;
        if cnc.plan().outcomes[i].is_scheduled() {
            line = format!("stream ID: {}, is scheduled: {}, queue: {}\n", i, cnc.plan().outcomes[i].is_scheduled(), cnc.plan().outcomes[i].used_queue());
        } else {
            line = format!("stream ID: {}, is scheduled: {}\n", i, cnc.plan().outcomes[i].is_scheduled());
        }
        my_file.write_all(line.as_bytes()).expect("Cannot write entry");
    }

    // Iterate through each port to construct GCL with all events.
    let plan = &(cnc.plan());
    for gcl_index in 0..plan.allocated_tsns.len() {
        
        let gcl = &(plan.allocated_tsns[gcl_index]);
        let outcomes = &(plan.outcomes);

        let hyperperiod = gcl.hyperperiod();
        let mut gcl_one_hyperperiod_queue_0: Vec<Range<u32>> = Vec::new();
        let mut gcl_one_hyperperiod_queue_1: Vec<Range<u32>> = Vec::new();
        for event in gcl.inner.iter() {
            println!("[DEBUG_round-1] tsn-{}, {}, queue {}", event.value, port_id_from_rust_to_omnetpp[gcl_index], outcomes[event.value].used_queue());
            if outcomes[event.value].is_scheduled(){
                for i in 0..hyperperiod / event.period {
                    println!("{} - {}, ", event.start + event.period * i, event.end + event.period * i );
                }
            }

            if outcomes[event.value].is_scheduled() && outcomes[event.value].used_queue() == 0 {
                for i in 0..hyperperiod / event.period {
                    gcl_one_hyperperiod_queue_0.push(Range { start: event.start + event.period * i, end: event.end + event.period * i });
                }
            } else if outcomes[event.value].is_scheduled() && outcomes[event.value].used_queue() == 1 {
                for i in 0..hyperperiod / event.period {
                    gcl_one_hyperperiod_queue_1.push(Range { start: event.start + event.period * i, end: event.end + event.period * i });
                }
            } 
        }

        for i in 0..gcl_one_hyperperiod_queue_0.len() {
            let mut min_index = i;
            for j in (i + 1)..gcl_one_hyperperiod_queue_0.len() {
                if gcl_one_hyperperiod_queue_0[min_index].start > gcl_one_hyperperiod_queue_0[j].start {
                    min_index = j;
                }
            }
            gcl_one_hyperperiod_queue_0.swap(min_index, i);
        }
        
        // let mut is_entry_changed = true;
        // while is_entry_changed {
        //     is_entry_changed = false;
        //     for i in 0..gcl_one_hyperperiod_queue_0.len() {
        //         for j in (i + 1)..gcl_one_hyperperiod_queue_0.len() {
        //             if gcl_one_hyperperiod_queue_0[i].end == gcl_one_hyperperiod_queue_0[j].start {
        //                 let new_entry = Range { start: gcl_one_hyperperiod_queue_0[i].start, end: gcl_one_hyperperiod_queue_0[j].end };
        //                 gcl_one_hyperperiod_queue_0.remove(j);
        //                 gcl_one_hyperperiod_queue_0.remove(i);
        //                 gcl_one_hyperperiod_queue_0.insert(i, new_entry);
        //                 is_entry_changed = true;
        //                 break;
        //             }
        //         }
        //         if is_entry_changed {
        //             break;
        //         }
        //     }
        // }

        for i in 0..gcl_one_hyperperiod_queue_1.len() {
            let mut min_index = i;
            for j in (i + 1)..gcl_one_hyperperiod_queue_1.len() {
                if gcl_one_hyperperiod_queue_1[min_index].start > gcl_one_hyperperiod_queue_1[j].start {
                    min_index = j;
                }
            }
            gcl_one_hyperperiod_queue_1.swap(min_index, i);
        }
        
        // let mut is_entry_changed = true;
        // while is_entry_changed {
        //     is_entry_changed = false;
        //     for i in 0..gcl_one_hyperperiod_queue_1.len() {
        //         for j in (i + 1)..gcl_one_hyperperiod_queue_1.len() {
        //             if gcl_one_hyperperiod_queue_1[i].end == gcl_one_hyperperiod_queue_1[j].start {
        //                 let new_entry = Range { start: gcl_one_hyperperiod_queue_1[i].start, end: gcl_one_hyperperiod_queue_1[j].end };
        //                 gcl_one_hyperperiod_queue_1.remove(j);
        //                 gcl_one_hyperperiod_queue_1.remove(i);
        //                 gcl_one_hyperperiod_queue_1.insert(i, new_entry);
        //                 is_entry_changed = true;
        //                 break;
        //             }
        //         }
        //         if is_entry_changed {
        //             break;
        //         }
        //     }
        // }

        let filename_queue_0 = format!("../../r438/simulations/gcl_schedules/{}_queue_0_round_1.txt", port_id_from_rust_to_omnetpp[gcl_index]);
        let mut file_queue_0 = File::create(filename_queue_0).expect("Cannot create text file for queue 0");
        for i in 0..gcl_one_hyperperiod_queue_0.len() {
            let line = format!("start = {}, end = {}", gcl_one_hyperperiod_queue_0[i].start, gcl_one_hyperperiod_queue_0[i].end);
            file_queue_0.write_all(line.as_bytes()).expect("Cannot write entry into text file for queue 0");
            if i != (gcl_one_hyperperiod_queue_0.len() - 1) {
                file_queue_0.write_all("\n".as_bytes()).expect("Cannot write entry into text file for queue 0");
            }
        }
        
        let filename_queue_1 = format!("../../r438/simulations/gcl_schedules/{}_queue_1_round_1.txt", port_id_from_rust_to_omnetpp[gcl_index]);
        let mut file_queue_1 = File::create(filename_queue_1).expect("Cannot create text file for queue 1");
        for i in 0..gcl_one_hyperperiod_queue_1.len() {
            let line = format!("start = {}, end = {}", gcl_one_hyperperiod_queue_1[i].start, gcl_one_hyperperiod_queue_1[i].end);
            file_queue_1.write_all(line.as_bytes()).expect("Cannot write entry into text file for queue 1");
            if i != (gcl_one_hyperperiod_queue_1.len() - 1) {
                file_queue_1.write_all("\n".as_bytes()).expect("Cannot write entry into text file for queue 1");
            }
        }
        
        let filename_queue_7 = format!("../../r438/simulations/gcl_schedules/{}_queue_7_round_1.txt", port_id_from_rust_to_omnetpp[gcl_index]);
        let mut file_queue_7 = File::create(filename_queue_7).expect("Cannot create text file for queue 7");
        for i in 0..gcl.expand().len() {
            let mut line;
            if i == 0 {
                if gcl.expand()[i].start == 0 {
                    continue;
                } else {
                    line = format!("start = {}, end = {}", 0, gcl.expand()[i].start);
                }
            } else if i == (gcl.expand().len() - 1) {
                line = format!("start = {}, end = {}\nstart = {}, end = {}", gcl.expand()[i - 1].end, gcl.expand()[i].start, gcl.expand()[i].end, hyperperiod);
            } else {
                line = format!("start = {}, end = {}", gcl.expand()[i - 1].end, gcl.expand()[i].start);
            }

            file_queue_7.write_all(line.as_bytes()).expect("Cannot write entry into text file for queue 7");
            if i != (gcl.expand().len() - 1) {
                file_queue_7.write_all("\n".as_bytes()).expect("Cannot write entry into text file for queue 7");
            }
        }
    }

    // Input the second half test case and configure them.
    cnc.input(tsns2, avbs2);
    let stop_cond = scenario.stop_condition();
    let elapsed = cnc.configure(&stop_cond);

    println!("--- #2 elapsed time: {} μs ---", elapsed.as_micros());

    // --------------------------------

    // Collect initial production offset on end station.
    let filename = format!("../../r438/util/stream_initial_production_offset/stream_initial_production_offset_round_2.txt");
    let mut my_file = File::create(filename).expect("Cannot open file");
    let plan = &(cnc.plan());
    for gcl_index in 0..plan.allocated_tsns.len() {
        let gcl = &(plan.allocated_tsns[gcl_index]);
        let outcomes = &(plan.outcomes);
        if gcl_index == 0 || gcl_index == 2 || gcl_index == 4 || gcl_index == 24 || gcl_index == 26 || gcl_index == 28 {
            for event in gcl.inner.iter() {
                let line = format!("stream ID: {}, initial production offset: {}\n", event.value, event.start);
                my_file.write_all(line.as_bytes()).expect("Cannot write.");
            }
        } 
    }

    // Collect production offset on relay switches.
    let plan = &(cnc.plan());
    for gcl_index in 0..plan.allocated_tsns.len() {
        let gcl = &(plan.allocated_tsns[gcl_index]);
        let hyperperiod = gcl.hyperperiod();
        let outcomes = &(plan.outcomes);
        if gcl_index == 6 || gcl_index == 30 || gcl_index == 19 || gcl_index == 42 || gcl_index == 8 || gcl_index == 31 || gcl_index == 32 || gcl_index == 21 || gcl_index == 43 || gcl_index == 44 || gcl_index == 10 || gcl_index == 33 || gcl_index == 23 || gcl_index == 45 {
            let filename = format!("../../r438/simulations/stream_production_offset_relay_switch/{}_queue_0_round_2.txt", port_id_from_rust_to_omnetpp[gcl_index]);
            let mut my_file = File::create(filename).expect("Cannot open file");
            for event in gcl.inner.iter() {
                if outcomes[event.value].is_scheduled() && outcomes[event.value].used_queue() == 0 {
                    for i in 0..hyperperiod / event.period {
                        let line = format!("stream ID: {}, offset: {}, period: {}\n", event.value, event.start + event.period * i, event.period);
                        my_file.write_all(line.as_bytes()).expect("Cannot write.");
                    }
                }
            }
            let filename = format!("../../r438/simulations/stream_production_offset_relay_switch/{}_queue_1_round_2.txt", port_id_from_rust_to_omnetpp[gcl_index]);
            let mut my_file = File::create(filename).expect("Cannot open file");
            for event in gcl.inner.iter() {
                if outcomes[event.value].is_scheduled() && outcomes[event.value].used_queue() == 1 {
                    for i in 0..hyperperiod / event.period {
                        let line = format!("stream ID: {}, offset: {}, period: {}\n", event.value, event.start + event.period * i, event.period);
                        my_file.write_all(line.as_bytes()).expect("Cannot write.");
                    }
                }
            }
        } 
    }

    // Store stream ID to queue ID mapping.
    let mut my_file = File::create("../../r438/util/stream_id_queue_id_mapping/stream_id_queue_id_mapping_round_2.txt").expect("Cannot create text file");
    for i in 0..cnc.plan().outcomes.len() {
        let mut line;
        if cnc.plan().outcomes[i].is_scheduled() {
            line = format!("stream ID: {}, is scheduled: {}, queue: {}\n", i, cnc.plan().outcomes[i].is_scheduled(), cnc.plan().outcomes[i].used_queue());
        } else {
            line = format!("stream ID: {}, is scheduled: {}\n", i, cnc.plan().outcomes[i].is_scheduled());
        }
        my_file.write_all(line.as_bytes()).expect("Cannot write entry");
    }

    // Iterate through each port to construct GCL with all events.
    let plan = &(cnc.plan());
    for gcl_index in 0..plan.allocated_tsns.len() {
        
        let gcl = &(plan.allocated_tsns[gcl_index]);
        let outcomes = &(plan.outcomes);

        let hyperperiod = gcl.hyperperiod();
        let mut gcl_one_hyperperiod_queue_0: Vec<Range<u32>> = Vec::new();
        let mut gcl_one_hyperperiod_queue_1: Vec<Range<u32>> = Vec::new();
        for event in gcl.inner.iter() {
            println!("[DEBUG_round-2] tsn-{}, {}, queue {}", event.value, port_id_from_rust_to_omnetpp[gcl_index], outcomes[event.value].used_queue());
            if outcomes[event.value].is_scheduled(){
                for i in 0..hyperperiod / event.period {
                    println!("{} - {}, ", event.start + event.period * i, event.end + event.period * i );
                }
            }

            if outcomes[event.value].is_scheduled() && outcomes[event.value].used_queue() == 0 {
                for i in 0..hyperperiod / event.period {
                    gcl_one_hyperperiod_queue_0.push(Range { start: event.start + event.period * i, end: event.end + event.period * i });
                }
            } else if outcomes[event.value].is_scheduled() && outcomes[event.value].used_queue() == 1 {
                for i in 0..hyperperiod / event.period {
                    gcl_one_hyperperiod_queue_1.push(Range { start: event.start + event.period * i, end: event.end + event.period * i });
                }
            } 
        }

        for i in 0..gcl_one_hyperperiod_queue_0.len() {
            let mut min_index = i;
            for j in (i + 1)..gcl_one_hyperperiod_queue_0.len() {
                if gcl_one_hyperperiod_queue_0[min_index].start > gcl_one_hyperperiod_queue_0[j].start {
                    min_index = j;
                }
            }
            gcl_one_hyperperiod_queue_0.swap(min_index, i);
        }
        
        let mut is_entry_changed = true;
        while is_entry_changed {
            is_entry_changed = false;
            for i in 0..gcl_one_hyperperiod_queue_0.len() {
                for j in (i + 1)..gcl_one_hyperperiod_queue_0.len() {
                    if gcl_one_hyperperiod_queue_0[i].end == gcl_one_hyperperiod_queue_0[j].start {
                        let new_entry = Range { start: gcl_one_hyperperiod_queue_0[i].start, end: gcl_one_hyperperiod_queue_0[j].end };
                        gcl_one_hyperperiod_queue_0.remove(j);
                        gcl_one_hyperperiod_queue_0.remove(i);
                        gcl_one_hyperperiod_queue_0.insert(i, new_entry);
                        is_entry_changed = true;
                        break;
                    }
                }
                if is_entry_changed {
                    break;
                }
            }
        }

        for i in 0..gcl_one_hyperperiod_queue_1.len() {
            let mut min_index = i;
            for j in (i + 1)..gcl_one_hyperperiod_queue_1.len() {
                if gcl_one_hyperperiod_queue_1[min_index].start > gcl_one_hyperperiod_queue_1[j].start {
                    min_index = j;
                }
            }
            gcl_one_hyperperiod_queue_1.swap(min_index, i);
        }
        
        let mut is_entry_changed = true;
        while is_entry_changed {
            is_entry_changed = false;
            for i in 0..gcl_one_hyperperiod_queue_1.len() {
                for j in (i + 1)..gcl_one_hyperperiod_queue_1.len() {
                    if gcl_one_hyperperiod_queue_1[i].end == gcl_one_hyperperiod_queue_1[j].start {
                        let new_entry = Range { start: gcl_one_hyperperiod_queue_1[i].start, end: gcl_one_hyperperiod_queue_1[j].end };
                        gcl_one_hyperperiod_queue_1.remove(j);
                        gcl_one_hyperperiod_queue_1.remove(i);
                        gcl_one_hyperperiod_queue_1.insert(i, new_entry);
                        is_entry_changed = true;
                        break;
                    }
                }
                if is_entry_changed {
                    break;
                }
            }
        }

        let filename_queue_0 = format!("../../r438/simulations/gcl_schedules/{}_queue_0_round_2.txt", port_id_from_rust_to_omnetpp[gcl_index]);
        let mut file_queue_0 = File::create(filename_queue_0).expect("Cannot create text file for queue 0");
        for i in 0..gcl_one_hyperperiod_queue_0.len() {
            let line = format!("start = {}, end = {}", gcl_one_hyperperiod_queue_0[i].start, gcl_one_hyperperiod_queue_0[i].end);
            file_queue_0.write_all(line.as_bytes()).expect("Cannot write entry into text file for queue 0");
            if i != (gcl_one_hyperperiod_queue_0.len() - 1) {
                file_queue_0.write_all("\n".as_bytes()).expect("Cannot write entry into text file for queue 0");
            }
        }
        
        let filename_queue_1 = format!("../../r438/simulations/gcl_schedules/{}_queue_1_round_2.txt", port_id_from_rust_to_omnetpp[gcl_index]);
        let mut file_queue_1 = File::create(filename_queue_1).expect("Cannot create text file for queue 1");
        for i in 0..gcl_one_hyperperiod_queue_1.len() {
            let line = format!("start = {}, end = {}", gcl_one_hyperperiod_queue_1[i].start, gcl_one_hyperperiod_queue_1[i].end);
            file_queue_1.write_all(line.as_bytes()).expect("Cannot write entry into text file for queue 1");
            if i != (gcl_one_hyperperiod_queue_1.len() - 1) {
                file_queue_1.write_all("\n".as_bytes()).expect("Cannot write entry into text file for queue 1");
            }
        }
        
        let filename_queue_7 = format!("../../r438/simulations/gcl_schedules/{}_queue_7_round_2.txt", port_id_from_rust_to_omnetpp[gcl_index]);
        let mut file_queue_7 = File::create(filename_queue_7).expect("Cannot create text file for queue 7");
        for i in 0..gcl.expand().len() {
            let mut line;
            if i == 0 {
                if gcl.expand()[i].start == 0 {
                    continue;
                } else {
                    line = format!("start = {}, end = {}", 0, gcl.expand()[i].start);
                }
            } else if i == (gcl.expand().len() - 1) {
                line = format!("start = {}, end = {}\nstart = {}, end = {}", gcl.expand()[i - 1].end, gcl.expand()[i].start, gcl.expand()[i].end, hyperperiod);
            } else {
                line = format!("start = {}, end = {}", gcl.expand()[i - 1].end, gcl.expand()[i].start);
            }

            file_queue_7.write_all(line.as_bytes()).expect("Cannot write entry into text file for queue 7");
            if i != (gcl.expand().len() - 1) {
                file_queue_7.write_all("\n".as_bytes()).expect("Cannot write entry into text file for queue 7");
            }
        }
    }

}

#[inline]
fn arc(link: &(usize, usize, usize)) -> usize {
    2 * link.2 + (link.0 > link.1) as usize
}