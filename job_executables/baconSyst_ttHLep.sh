#!/bin/bash

#Script to run signal flat ntuple making

#Set up CMS environment
cd /afs/cern.ch/user/j/jolangfo/trilinear/CMSSW_7_4_4/src/EventGen/delphes
eval `scramv1 runtime -sh`

fInput=$1
proc=$2
syst_type=$3
syst_direction=$4

python tri_ttHLep_NtupleMaker_syst_bacon.py -i $fInput -s $proc -u $syst_type -d $syst_direction
