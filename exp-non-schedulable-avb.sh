#!/bin/bash
n=200
summation_round_1=0
summation_round_2=0

echo "Execute $n times of all-the-way-script.sh"
for ((i=0; i<$n; i++))
do	
	echo "iter $i: "
	./all-the-way-script.sh $i 2>/dev/null 1>/dev/null

    O2_rust=$(cat sim-round-1-result | tail -n 3 | head -n 1 | awk '{print $6}')
    O2_sim=$(cat sim-round-1-result | tail -n 3 | head -n 1 | awk '{print $9}')
    if [[ ${O2_rust} -eq 0 ]] ; then
        echo "round-1 ratio = 0"
    else
        ratio=$(echo "scale=6 ; ${O2_sim} / ${O2_rust}" | bc)
        summation_round_1=$(echo "scale=6 ; ${summation_round_1} + ${ratio}" | bc)
        echo "round-1 ratio = ${ratio}"
    fi
    
    O2_rust=$(cat sim-round-2-result | tail -n 3 | head -n 1 | awk '{print $6}')
    O2_sim=$(cat sim-round-2-result | tail -n 3 | head -n 1 | awk '{print $9}')
    if [[ ${O2_rust} -eq 0 ]] ; then
        echo "round-2 ratio = 0"
    else
        ratio=$(echo "scale=6 ; ${O2_sim} / ${O2_rust}" | bc)
        summation_round_2=$(echo "scale=6 ; ${summation_round_2} + ${ratio}" | bc)
        echo "round-2 ratio = ${ratio}"
    fi

    echo ""
done

echo "Average Ratio after ${n} Runs: "
echo "Round-1 Ratio: $(echo "scale=6 ; ${summation_round_1} / ${n}" | bc)"
echo "Round-2 Ratio: $(echo "scale=6 ; ${summation_round_2} / ${n}" | bc)"
