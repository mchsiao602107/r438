use std::fmt::Write;
use std::sync::{Arc, Weak};
use std::time::{Duration, Instant};

use crate::algo::{Algorithm, StopCond, OSACO, RO, SPF};
use crate::plan::Plan;
use crate::route::discover::{Grossi, GrossiExtendDetour, Konen};
use crate::route::Network;
use crate::schedule::Evaluator;
use crate::stream::{FlowTable, AVB, TSN};

/// A component that models the centralized TSN network controller.
///
/// `CNC` acts as an interface for user to feed in the setup such as network
/// topology and stream flow table. The setup will forward to the routing
/// algorithm. CNC then receives the result and prints it out.
pub struct CNC {
    algorithm: Box<dyn Algorithm>,
    flowtable: Arc<FlowTable>,
    //plan: Plan,
    pub plan: Plan,
    verbose: bool,
    objectives: [f64; 4],
}

impl CNC {
    /// Constructs a new `CNC`, with an empty flowtable.
    ///
    /// `CNC` takes a static network to initialize.
    /// Dynamic networks are not supported yet.
    pub fn new(algo: &str, network: Network) -> Self {
        let network = Arc::new(network);
        let plan = Plan::new(Arc::downgrade(&network));

        CNC {
            algorithm: build_algorithm(algo, network),
            flowtable: Arc::new(FlowTable::new()),
            plan,
            verbose: true,
            objectives: [f64::INFINITY; 4],
        }
    }

    /// Gets the current routing and scheduling decision.
    pub fn plan(&mut self) -> &mut Plan {
        &mut self.plan
    }

    /// Gets the current objectives with respect to the decision.
    pub fn objs(&self) -> [f64; 4] {
        self.objectives
    }

    /// Sets the random seed to the heuristic routing algorithms.
    pub fn with_random_seed(mut self, seed: u64) -> Self {
        self.algorithm.seed(seed);
        self
    }

    /// Sets if CNC reports the results after configurations.
    pub fn with_verbosity(mut self, verbose: bool) -> Self {
        self.verbose = verbose;
        self
    }

    /// Pushes new streams into flow table and marked them inputs.
    ///
    /// Their candidate routes are discovered upon the push.
    ///
    /// # Panics
    ///
    /// Panics if there are other pointers sharing the flow table.
    pub fn input(&mut self, tsns: Vec<TSN>, avbs: Vec<AVB>) {
        self.plan.flowtable = Weak::new();
        assert_eq!(Arc::weak_count(&self.flowtable), 0);

        let algorithm = &mut self.algorithm; // can mutate its hashmap
        let flowtable = Arc::get_mut(&mut self.flowtable).unwrap();

        flowtable.append_with_routing(tsns, avbs, |s, t, r| {
            algorithm.candidate_routes(s, t, r).to_vec()
        });

        self.plan.resize(flowtable.len());
        self.plan.flowtable = Arc::downgrade(&self.flowtable);
    }

    /// Executes configuration to decide routes and schedules.
    ///
    /// For the input streams, new routes and schedules may be decided; For
    /// the background streams, they can be rerouted or rescheduled. All input
    /// streams are promoted to backgrounds streams after the configuration.
    pub fn configure(&mut self, stop_cond: &StopCond) -> Duration {
        let prev_run = self.plan.clone();

        let now = Instant::now();
        let mut this_run = self.algorithm.run(prev_run, stop_cond);
        let elapsed = now.elapsed();

        // Swap in `this_run` and swap out `prev_run` at same time.
        this_run.confirm_selections();
        let prev_run = std::mem::replace(&mut self.plan, this_run);

        self.objectives = self.plan.evaluate_with(&prev_run);
        if self.verbose {
            self.show_result(&prev_run).unwrap();
        }

        drop(prev_run);

        self.plan.flowtable = Weak::new();
        let flowtable = Arc::get_mut(&mut self.flowtable).unwrap();
        flowtable.promote_inputs_to_backgrounds();
        self.plan.flowtable = Arc::downgrade(&self.flowtable);

        elapsed
    }

    /// Reports the routing results.
    ///
    /// The previous routing plan is compared against to show if some background
    /// streams are rerouted.
    fn show_result(&self, prev_run: &Plan) -> anyhow::Result<()> {
        const FEASIBLE: [&str; 2] = ["failed", "ok"];
        const REROUTED: [&str; 2] = ["", "*"];

        let this_run = &self.plan;
        let backgrounds = self.flowtable.backgrounds();
        let mut msg = String::new();

        writeln!(msg, "TSN streams")?;

        // --------------------------
        use std::fs::File;
        use std::io::prelude::*;
        let filename_tsn = "./routes_tsn_avb/routes_tsn.txt";
        let mut file_tsn = File::create(filename_tsn).expect("Cannot open file for tsn routes.");

        for nth in self.flowtable.tsns() {
            let kth = this_run.selection(nth).now();
            let route = self.flowtable.candidate(nth, kth);

            let is_feasible = this_run.outcome(nth).is_scheduled();
            let is_rerouted = backgrounds.contains(&nth)
                && this_run.selection(nth).now() != prev_run.selection(nth).future();

            writeln!(
                msg,
                "- stream #{:02} {}, with route #{}{} {:?}",
                nth, FEASIBLE[is_feasible as usize], kth, REROUTED[is_rerouted as usize], route
            )?;

            // --------------------------
            let line = format!("- stream #{:02} {}, with route #{}{} {:?}\n", nth, FEASIBLE[is_feasible as usize], kth, REROUTED[is_rerouted as usize], route);
            file_tsn.write_all(line.as_bytes()).expect("Cannot write file for tsn routes.");
        }

        writeln!(msg, "AVB streams")?;

        // --------------------------
        let filename_avb = "./routes_tsn_avb/routes_avb.txt";
        let mut file_avb = File::create(filename_avb).expect("Cannot open file for avb routes.");

        for nth in self.flowtable.avbs() {
            let kth = this_run.selection(nth).now();
            let route = self.flowtable.candidate(nth, kth);
            let wcd = this_run
                .evaluate_avb_wcd(nth, kth)
                .div_duration_f64(Duration::MICROSECOND);
            let max = self.flowtable.avb_spec(nth).deadline as f64;

            let is_feasible = this_run.outcome(nth).is_scheduled() && wcd <= max;
            let is_rerouted = backgrounds.contains(&nth)
                && this_run.selection(nth).now() != prev_run.selection(nth).future();

            writeln!(
                msg,
                "- stream #{:02} {} ({:02.0}%), with route #{}{} {:?}",
                nth,
                FEASIBLE[is_feasible as usize],
                100.0 * wcd / max,
                kth,
                REROUTED[is_rerouted as usize],
                route
            )?;

            // --------------------------
            let line = format!("- stream #{:02} {} ({:02.0}%), with route #{}{} {:?}\n", nth, FEASIBLE[is_feasible as usize], 100.0 * wcd / max, kth, REROUTED[is_rerouted as usize], route);
            file_avb.write_all(line.as_bytes()).expect("Cannot write file for avb routes.");
        }

        let objs = self.objectives;
        let weights = [2744.0, 72.2, 19.0, 0.001];
        let cost = itertools::izip!(&objs, &weights)
            .map(|(x, y)| x * y)
            .sum::<f64>();

        writeln!(
            msg,
            "the solution has cost {:.2} and objectives {:.2?}",
            cost, objs
        )?;
        println!("{}", msg);

        Ok(())
    }
}

/// Initializes the routing algorithm from the name.
///
/// The algorithm is boxed to fulfill dynamic dispatch. This allows CLI swaps
/// the algorithms.
fn build_algorithm(name: &str, network: Arc<Network>) -> Box<dyn Algorithm> {
    match name {
        "osaco" => Box::new(OSACO::<GrossiExtendDetour>::new(network)),
        "osaco+g" => Box::new(OSACO::<Grossi>::new(network)),
        "osaco+k" => Box::new(OSACO::<Konen>::new(network)),
        "ro" => Box::new(RO::new(network)),
        "spf" => Box::new(SPF::new(network)),
        _ => panic!("only these algorithms allowed: osaco, osaco+g, osaco+k, ro, spf"),
    }
}
