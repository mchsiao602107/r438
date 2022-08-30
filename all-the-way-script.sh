# Run rust code to generate all required text files.
cd ~/omnetpp-6.0/INET_workspace/r08922075/adams-ants-v1.3.2
cargo run --release -- mesh-iso-aud.yaml

# Run python script to genrate auto-generated.ini.
cd ~/omnetpp-6.0/INET_workspace/r438/util
python3 generate_ini.py

# Remove statistics of previous simulation.
rm -rf ~/omnetpp-6.0/INET_workspace/r438/simulations/results 
rm -f ~/omnetpp-6.0/INET_workspace/r438/simulations/General.anf

# Run omnetpp simulation.
cpu_num=$(grep -c 'cpu[0-9]' /proc/stat)
cd ~/omnetpp-6.0/INET_workspace/inet && make MODE=release -j$cpu_num all
cd ~/omnetpp-6.0/INET_workspace/r438/src && make MODE=release all
cd ~/omnetpp-6.0/INET_workspace/r438/simulations
../src/r438 -r 0 -m -u Cmdenv -n .:../src:../../inet/examples:../../inet/showcases:../../inet/src:../../inet/tests/validation:../../inet/tests/networks:../../inet/tutorials -l ../../inet/src/INET -f auto-generated.ini

# Run python script to analyze statistics.
printf "\nResult of round-1 simulation: \n\n"
cd ~/omnetpp-6.0/INET_workspace/r438/util
python3 check_stream_schedulability.py

# Back to r438 directory.
cd ~/omnetpp-6.0/INET_workspace/r438
