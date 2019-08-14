# HGCal L1T egid setup script

# Setup environment
source /cvmfs/cms.cern.ch/crab3/crab.sh
export HGCAL_L1T_BASE=$PWD

#set up grid proxy
voms-proxy-init --rfc --voms cms
