#!/bin/bash

# The following file was written with help from ChatGPT
agent1=$1
agent2=$2
num_games=${3:-50}  # default to 50 games

wins_agent1=0
wins_agent2=0
log_dir="logs/${agent1}_vs_${agent2}"
mkdir -p $log_dir



for (( i=1; i<=num_games; i++ )); do
  log_file="$log_dir/${i}.log"
  if (( i % 2 )); then  # randomly assign colors
    result=$(python -m referee -l $log_file $agent1 $agent2)
    WINNER=$(grep -oP 'winner:\K\w+' $log_file)
    if [ "$WINNER" == "RED" ]; then
        ((wins_agent1++))
    elif [ "$WINNER" == "BLUE" ]; then
        ((wins_agent2++))
    fi

  else
    result=$(python -m referee -l $log_file $agent2 $agent1)
    WINNER=$(grep -oP 'winner:\K\w+' $log_file)
    if [ "$WINNER" == "RED" ]; then
        ((wins_agent2++))
    elif [ "$WINNER" == "BLUE" ]; then
        ((wins_agent1++))
    fi
  fi

  # write log output
  
done

# write summary file
mkdir -p "tests"
summary_file="tests/${agent1}_vs_${agent2}_summary.txt"
echo "${agent1} wins: ${wins_agent1}" > $summary_file
echo "${agent2} wins: ${wins_agent2}" >> $summary_file