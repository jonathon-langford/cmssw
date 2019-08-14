#!/bin/bash

# Set up environment
export HGCAL_L1T_BASE=$1
cd $HGCAL_L1T_BASE

#Script to run the HGCal L1T cluster definition
cd cl3d_selection
eval `scramv1 runtime -sh`

#Input to cl3d selection
sample_type=$2
input_path=$3
file_number=$4
clustering_algo=$5

# Run selection
python hgcal_l1t_cl3d_selection.py --sampleType $sample_type --inputPath $input_path --fileNumber $file_number --clusteringAlgo $clustering_algo 
