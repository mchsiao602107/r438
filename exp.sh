#!/bin/bash
n=10
O1_gt_zero_cnt_round_1=0
O2_gt_zero_cnt_round_1=0
O1_gt_zero_cnt_round_2=0
O2_gt_zero_cnt_round_2=0

rm -f exp_round_2_results

echo "Execute $n times of all-the-way-script.sh"
for ((i=0; i<$n; i++))
do	
	if [[ $(($i % $(($n / 10)))) -eq 0 ]];then
		echo "iter $i..."
	fi
	./all-the-way-script.sh $i 2>/dev/null 1>/dev/null

	# Check round-1 results
	O1_sim=$(cat sim-round-1-result | tail -n 4 | head -n 1 | awk '{print $9}')
	O2_sim=$(cat sim-round-1-result | tail -n 3 | head -n 1 | awk '{print $9}')
	if [[ $O1_sim -ne 0 ]];then
		((O1_gt_zero_cnt_round_1++))
	fi
	if [[ $O2_sim -ne 0 ]];then
		((O2_gt_zero_cnt_round_1++))
	fi

	# Check round-2 results
	O1_sim=$(cat sim-round-2-result | tail -n 4 | head -n 1 | awk '{print $9}')
	O2_sim=$(cat sim-round-2-result | tail -n 3 | head -n 1 | awk '{print $9}')
	if [[ $O1_sim -ne 0 ]];then
		((O1_gt_zero_cnt_round_2++))
	fi
	if [[ $O2_sim -ne 0 ]];then
		((O2_gt_zero_cnt_round_2++))
	fi

	# Show round-2 results
	cat sim-round-2-result | tail -n 4
	echo ""
done

echo -e "\nSummary of O1/O2 (sim) after $n times of all-the-way-script.sh"
echo "---round 1---"
echo "O1 > 0:" $O1_gt_zero_cnt_round_1 "times"
echo "O2 > 0:" $O2_gt_zero_cnt_round_1 "times"
echo "---round 2---"
echo "O1 > 0:" $O1_gt_zero_cnt_round_2 "times"
echo "O2 > 0:" $O2_gt_zero_cnt_round_2 "times"