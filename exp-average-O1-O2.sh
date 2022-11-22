#!/bin/bash
n=200
summation_round_1_rust_O1=0
summation_round_1_sim_O1=0
summation_round_1_rust_O2=0
summation_round_1_sim_O2=0
summation_round_2_rust_O1=0
summation_round_2_sim_O1=0
summation_round_2_rust_O2=0
summation_round_2_sim_O2=0

echo "Execute $n times of all-the-way-script.sh"
for ((i=0; i<$n; i++))
do	
	echo "iter $i: "
	./all-the-way-script.sh $i 2>/dev/null 1>/dev/null

    rust_O1=$(cat sim-round-1-result | tail -n 4 | head -n 1 | awk '{print $6}')
    sim_O1=$(cat sim-round-1-result | tail -n 4 | head -n 1 | awk '{print $9}')
    rust_O2=$(cat sim-round-1-result | tail -n 3 | head -n 1 | awk '{print $6}')
    sim_O2=$(cat sim-round-1-result | tail -n 3 | head -n 1 | awk '{print $9}')
    echo "Round-1: "
    echo "Rust O1: ${rust_O1}, Sim O1: ${sim_O1}"
    echo "Rust O2: ${rust_O2}, Sim O2: ${sim_O2}"
    summation_round_1_rust_O1=$(echo "scale=6 ; ${summation_round_1_rust_O1} + ${rust_O1}" | bc)
    summation_round_1_sim_O1=$(echo "scale=6 ; ${summation_round_1_sim_O1} + ${sim_O1}" | bc)
    summation_round_1_rust_O2=$(echo "scale=6 ; ${summation_round_1_rust_O2} + ${rust_O2}" | bc)
    summation_round_1_sim_O2=$(echo "scale=6 ; ${summation_round_1_sim_O2} + ${sim_O2}" | bc)
    
    rust_O1=$(cat sim-round-2-result | tail -n 4 | head -n 1 | awk '{print $6}')
    sim_O1=$(cat sim-round-2-result | tail -n 4 | head -n 1 | awk '{print $9}')
    rust_O2=$(cat sim-round-2-result | tail -n 3 | head -n 1 | awk '{print $6}')
    sim_O2=$(cat sim-round-2-result | tail -n 3 | head -n 1 | awk '{print $9}')
    echo "Round-2: "
    echo "Rust O1: ${rust_O1}, Sim O1: ${sim_O1}"
    echo "Rust O2: ${rust_O2}, Sim O2: ${sim_O2}"
    summation_round_2_rust_O1=$(echo "scale=6 ; ${summation_round_2_rust_O1} + ${rust_O1}" | bc)
    summation_round_2_sim_O1=$(echo "scale=6 ; ${summation_round_2_sim_O1} + ${sim_O1}" | bc)
    summation_round_2_rust_O2=$(echo "scale=6 ; ${summation_round_2_rust_O2} + ${rust_O2}" | bc)
    summation_round_2_sim_O2=$(echo "scale=6 ; ${summation_round_2_sim_O2} + ${sim_O2}" | bc)

    echo ""
done

echo "Average Result of Round-1: "
echo "Rust O1: $(echo "scale=6 ; ${summation_round_1_rust_O1} / ${n}" | bc), Sim O1: $(echo "scale=6 ; ${summation_round_1_sim_O1} / ${n}" | bc)"
echo "Rust O2: $(echo "scale=6 ; ${summation_round_1_rust_O2} / ${n}" | bc), Sim O2: $(echo "scale=6 ; ${summation_round_1_sim_O2} / ${n}" | bc)"
echo ""
echo "Average Result of Round-2: "
echo "Rust O1: $(echo "scale=6 ; ${summation_round_2_rust_O1} / ${n}" | bc), Sim O1: $(echo "scale=6 ; ${summation_round_2_sim_O1} / ${n}" | bc)"
echo "Rust O2: $(echo "scale=6 ; ${summation_round_2_rust_O2} / ${n}" | bc), Sim O2: $(echo "scale=6 ; ${summation_round_2_sim_O2} / ${n}" | bc)"
