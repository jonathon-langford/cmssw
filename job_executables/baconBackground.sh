#!/bin/bash

#Script to run signal flat ntuple making

#Set up proxy
export X509_USER_PROXY=/afs/cern.ch/user/j/jolangfo/voms_proxy/proxy

#Set up CMS environment
cd /afs/cern.ch/user/j/jolangfo/trilinear/CMSSW_7_4_4/src/EventGen/delphes
eval `scramv1 runtime -sh`

fInput=$1
proc=$2

python tri_NtupleMaker_background_bacon.py -i $fInput -p $proc
