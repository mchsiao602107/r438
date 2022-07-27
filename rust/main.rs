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

    // Input the second half test case and configure them.
    cnc.input(tsns2, avbs2);
    let stop_cond = scenario.stop_condition();
    let elapsed = cnc.configure(&stop_cond);

    println!("--- #2 elapsed time: {} μs ---", elapsed.as_micros());

    // --------------------------------

    println!("\n*************\n");

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

    // Outcome of all streams.
    /*
    println!("Outcome of all streams.");
    println!("Outcome length: {}", cnc.plan().outcomes.len());
    for i in 0..cnc.plan().outcomes.len() {
        if cnc.plan().outcomes[i].is_scheduled() {
            println!("stream ID: {}, is scheduled: {}, queue: {}", i, cnc.plan().outcomes[i].is_scheduled(), cnc.plan().outcomes[i].used_queue());
        } else {
            println!("stream ID: {}, is scheduled: {}", i, cnc.plan().outcomes[i].is_scheduled());
        }
    }
    println!("\n");
    */

    // Show all ports.
    /*
    println!("All ports.");
    println!("(src, dst, link_id): port_id, reversed_port_id");
    for edge in yaml::load_network(&scenario.network).unwrap().topology().edges().iter() {
        let src = edge.0;
        let dst = edge.1;
        let link_id = edge.2.get_id();
        let link_1 = (src, dst, link_id);
        let link_2 = (dst, src, link_id);
        println!("({}, {}, {}): {}, {}", src, dst, link_id, arc(&link_1), arc(&link_2));
    }
    println!("\n");
    */

    // Schedules.
    // ----------

    // Iterate through each port to construct GCL with all events.
    let plan = &(cnc.plan());
    for gcl_index in 0..plan.allocated_tsns.len() {
        
        let gcl = &(plan.allocated_tsns[gcl_index]);
        let outcomes = &(plan.outcomes);

        // Construct GCL schedule in one hyper-period.
        let hyperperiod = gcl.hyperperiod();
        let mut gcl_one_hyperperiod_queue_0: Vec<Range<u32>> = Vec::new();
        let mut gcl_one_hyperperiod_queue_1: Vec<Range<u32>> = Vec::new();
        for event in gcl.inner.iter() {
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

        // Sort.
        for i in 0..gcl_one_hyperperiod_queue_0.len() {
            let mut min_index = i;
            for j in (i + 1)..gcl_one_hyperperiod_queue_0.len() {
                if gcl_one_hyperperiod_queue_0[min_index].start > gcl_one_hyperperiod_queue_0[j].start {
                    min_index = j;
                }
            }
            gcl_one_hyperperiod_queue_0.swap(min_index, i);
        }
        // Minimize length of GCL schedule for queue 0.
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

        // Sort.
        for i in 0..gcl_one_hyperperiod_queue_1.len() {
            let mut min_index = i;
            for j in (i + 1)..gcl_one_hyperperiod_queue_1.len() {
                if gcl_one_hyperperiod_queue_1[min_index].start > gcl_one_hyperperiod_queue_1[j].start {
                    min_index = j;
                }
            }
            gcl_one_hyperperiod_queue_1.swap(min_index, i);
        }
        // Minimize length of GCL schedule for queue 1.
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

        // Write GCL schedule of this port into text files.
        let filename_queue_0 = format!("./gcl_schedules/{}_queue_0.txt", port_id_from_rust_to_omnetpp[gcl_index]);
        let mut file_queue_0 = File::create(filename_queue_0).expect("Cannot create text file for queue 0");
        for i in 0..gcl_one_hyperperiod_queue_0.len() {
            let line = format!("start = {}, end = {}", gcl_one_hyperperiod_queue_0[i].start, gcl_one_hyperperiod_queue_0[i].end);
            file_queue_0.write_all(line.as_bytes()).expect("Cannot write entry into text file for queue 0");
            if i != (gcl_one_hyperperiod_queue_0.len() - 1) {
                file_queue_0.write_all("\n".as_bytes()).expect("Cannot write entry into text file for queue 0");
            }
        }
        let filename_queue_1 = format!("./gcl_schedules/{}_queue_1.txt", port_id_from_rust_to_omnetpp[gcl_index]);
        let mut file_queue_1 = File::create(filename_queue_1).expect("Cannot create text file for queue 1");
        for i in 0..gcl_one_hyperperiod_queue_1.len() {
            let line = format!("start = {}, end = {}", gcl_one_hyperperiod_queue_1[i].start, gcl_one_hyperperiod_queue_1[i].end);
            file_queue_1.write_all(line.as_bytes()).expect("Cannot write entry into text file for queue 1");
            if i != (gcl_one_hyperperiod_queue_1.len() - 1) {
                file_queue_1.write_all("\n".as_bytes()).expect("Cannot write entry into text file for queue 1");
            }
        }
        println!("Port {}: success", gcl_index);
        

        // Check whether the result match that of expand().
        /*
        if gcl_index == 20 {
            
            // Result of queue 0 and queue 1.
            println!("GCL of queue 0 for port {}.", gcl_index);
            println!("Queue 0 length: {}", gcl_one_hyperperiod_queue_0.len());
            for i in 0..gcl_one_hyperperiod_queue_0.len() {
                println!("{}, {}", gcl_one_hyperperiod_queue_0[i].start, gcl_one_hyperperiod_queue_0[i].end);
            }
            println!("\n");
            println!("GCL of queue 1 for port {}", gcl_index);
            println!("Queue 1 length: {}", gcl_one_hyperperiod_queue_1.len());
            for i in 0..gcl_one_hyperperiod_queue_1.len() {
                println!("{}, {}", gcl_one_hyperperiod_queue_1[i].start, gcl_one_hyperperiod_queue_1[i].end);
            }
            println!("\n");

            // Result of expand(), which is queue 0 plus queue 1.
            println!("Result of expand().");
            println!("Length: {}", gcl.expand().len());
            for gcl_entry in gcl.expand().iter() {
                println!("start = {}, end = {}", gcl_entry.start, gcl_entry.end);
            }
            println!("\n");

            break;
        }
        */
    }

    // Routes.
    // -------
}

#[inline]
fn arc(link: &(usize, usize, usize)) -> usize {
    2 * link.2 + (link.0 > link.1) as usize
}