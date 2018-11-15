#!/bin/bash

#Script to run signal flat ntuple making

#Set up CMS environment
cd /afs/cern.ch/user/j/jolangfo/trilinear/CMSSW_7_4_4/src/EventGen/delphes
eval `scramv1 runtime -sh`

fInput=$1
proc=$2

python tri_GEN_acceptance_bacon.py -i $fInput -s $proc
