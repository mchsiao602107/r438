#!/usr/bin/bash

# Get the absolue path of INET_workspace
INET_workspace=$(dirname $(dirname $(readlink -f "$0")))

# Get the name of inet
INET=$(ls -l "${INET_workspace}" | grep inet | awk '{print $9}')

# Run rust code to generate all required text files.
cd "${INET_workspace}"/r08922075/adams-ants-v1.3.2
cargo run --release -- mesh-iso-aud.yaml

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

# Remove statistics of previous simulation.
rm -rf "${INET_workspace}"/r438/simulations/results 
rm -f "${INET_workspace}"/r438/simulations/General.anf

# Run round-1 omnetpp simulation.
cpu_num=$(grep -c 'cpu[0-9]' /proc/stat)
cd "${INET_workspace}"/"$INET" && make MODE=release -j$cpu_num all
cd "${INET_workspace}"/r438/src && make MODE=release all
cd "${INET_workspace}"/r438/simulations
../src/r438 -r 0 -m -u Cmdenv -n .:../src:../../"$INET"/examples:../../"$INET"/showcases:../../"$INET"/src:../../"$INET"/tests/validation:../../"$INET"/tests/networks:../../"$INET"/tutorials -l ../../"$INET"/src/INET -f auto-generated-round-1.ini

# Run python script to analyze statistics.
cd "${INET_workspace}"/r438/util
python3 check_stream_schedulability.py > "${INET_workspace}"/r438/round-1-result

# Run round-2 omnetpp simulation.
cpu_num=$(grep -c 'cpu[0-9]' /proc/stat)
cd "${INET_workspace}"/"$INET" && make MODE=release -j$cpu_num all
cd "${INET_workspace}"/r438/src && make MODE=release all
cd "${INET_workspace}"/r438/simulations
../src/r438 -r 0 -m -u Cmdenv -n .:../src:../../"$INET"/examples:../../"$INET"/showcases:../../"$INET"/src:../../"$INET"/tests/validation:../../"$INET"/tests/networks:../../"$INET"/tutorials -l ../../"$INET"/src/INET -f auto-generated-round-2.ini

# Run python script to analyze statistics.
cd "${INET_workspace}"/r438/util
python3 check_stream_schedulability.py > "${INET_workspace}"/r438/round-2-result

# Show result.
printf "\nresult of round-1:\n"
printf -- "-------------------\n"
cat "${INET_workspace}"/r438/round-1-result
printf "\nresult of round-2:\n"
printf -- "-------------------\n"
cat "${INET_workspace}"/r438/round-2-result

# Back to r438 directory.
cd "${INET_workspace}"/r438
