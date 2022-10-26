#!/usr/bin/bash

# Get the absolue path of INET_workspace
INET_workspace=$(dirname $(dirname $(readlink -f "$0")))

# Get the name of inet
INET=$(ls -l "${INET_workspace}" | grep inet | awk '{print $9}')

# Remove statistics of previous simulation.
rm -rf "${INET_workspace}"/r438/simulations/results 
rm -f "${INET_workspace}"/r438/simulations/General.anf
rm "${INET_workspace}"/r438/simulations/stream_production_offset_relay_switch/*

# Run rust code to generate all required text files.
cp "$INET_workspace"/r438/rust/*.rs "$INET_workspace"/r08922075/adams-ants-v1.3.2/src/
cp "$INET_workspace"/r438/util/streams/*.yaml "$INET_workspace"/r08922075/adams-ants-v1.3.2/data/streams/
cd "${INET_workspace}"/r08922075/adams-ants-v1.3.2
# Disable warnings
export RUSTFLAGS="-Awarnings"
cargo run --release -- mesh-iso-aud.yaml -t 5 | tee "$INET_workspace"/r438/rust-result >/dev/null

# Sort production offset on relay switches.
cd "${INET_workspace}"/r438/util
python3 sort_stream_production_offset_relay_switch.py

# Run python script to genrate ini files.
cd "${INET_workspace}"/r438/util
python3 generate_ini.py 1
if [[ $? -ne 0 ]] ; then
    exit 1
fi
python3 generate_ini.py 2
if [[ $? -ne 0 ]] ; then
    exit 1
fi

# Run round-1 omnetpp simulation.
cpu_num=$(grep -c 'cpu[0-9]' /proc/stat)
cd "${INET_workspace}"/"$INET" && make MODE=release -j$cpu_num all
cd "${INET_workspace}"/r438/src && make MODE=release all
cd "${INET_workspace}"/r438/simulations
../src/r438 -r 0 -m -u Cmdenv -n .:../src:../../"$INET"/src -l ../../"$INET"/src/INET -f auto-generated-round-1.ini

# Run python script to analyze statistics.
cd "${INET_workspace}"/r438/util
python3 check_stream_schedulability.py 1 > "${INET_workspace}"/r438/sim-round-1-result

# Run round-2 omnetpp simulation.
cpu_num=$(grep -c 'cpu[0-9]' /proc/stat)
cd "${INET_workspace}"/"$INET" && make MODE=release -j$cpu_num all
cd "${INET_workspace}"/r438/src && make MODE=release all
cd "${INET_workspace}"/r438/simulations
../src/r438 -r 0 -m -u Cmdenv -n .:../src:../../"$INET"/src -l ../../"$INET"/src/INET -f auto-generated-round-2.ini

# Run python script to analyze statistics.
cd "${INET_workspace}"/r438/util
python3 check_stream_schedulability.py 2 > "${INET_workspace}"/r438/sim-round-2-result

# Show result.
printf "\nresult of round-1:\n"
printf -- "-------------------\n"
cat "${INET_workspace}"/r438/sim-round-1-result
printf "\nresult of round-2:\n"
printf -- "-------------------\n"
cat "${INET_workspace}"/r438/sim-round-2-result

# Back to r438 directory.
cd "${INET_workspace}"/r438