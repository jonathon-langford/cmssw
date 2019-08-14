# Python script for cluster selection: gen-matching + selection cuts

import ROOT
import sys
import os
import math
from array import array
from optparse import OptionParser

print "~~~~~~~~~~~~~~~~~~~~~~~~ Cl3D Selection ~~~~~~~~~~~~~~~~~~~~~~~~"

def get_options():
  parser = OptionParser()
  parser = OptionParser( usage="usage: python hgcal_l1t_cl3d_selection.py <options>" )
  parser.add_option("--sampleType", dest='sampleType', default='electron_200PU', help="Sample to process, default signal is electron_200PU, default bkg is neutrino_200PU")
  parser.add_option("--inputPath", dest="inputPath", default="%s/ntuples"%os.environ['HGCAL_L1T_BASE'], help="Path to directories which hold input ntuples")
  parser.add_option("--fileNumber", dest="fileNumber", default=1, type="int", help="Input ntuple number")
  parser.add_option("--maxEvents", dest="maxEvents", default=-1, type="int", help="Maximum number of events to process")
  parser.add_option("--clusteringAlgo", dest="clusteringAlgo", default="Histomaxvardr", help="Clustering algorithm used in ntuple production")
  # IF want to process with a different clustering alg: need to change the cms config script in ntuples/ directory
  return parser.parse_args()

(opt,args) = get_options()

# Mapping to extract TDirectory for different clustering algo
# Add full chain name if using a different alg
clusteringAlgoDirDict = {"gen":"Floatingpoint8ThresholdDummyHistomaxvardrGenclustersntuple","Histomaxvardr":"Floatingpoint8ThresholdDummyHistomaxvardrGenclustersntuple","Histomaxvardr_stc":"Floatingpoint8SupertriggercellDummyHistomaxvardrClustersntuple"}

# Mapping: sample type to pdgid used for gen matching
pdgIdDict = {
  "electron":[11],
  "photon":[22],
  "pion":[211],
  "neutrino":[]
}
pdgid = pdgIdDict[ opt.sampleType.split("_")[0] ]

#Check: clustering exists in dir
clusteringAlgo = opt.clusteringAlgo
if clusteringAlgo not in clusteringAlgoDirDict:
  print " --> [ERROR] not configured for %s clustering. Leaving..."%clusteringAlgo  
  print "~~~~~~~~~~~~~~~~~~~~ Cl3D Selection (END) ~~~~~~~~~~~~~~~~~~~~"
  sys.exit(1)

# Check: if ntuple exists
if os.path.exists("%s/%s/ntuple_%g.root"%(opt.inputPath,opt.sampleType,opt.fileNumber)):
  print " --> Processing %s/%s/ntuple_%g.root"%(opt.inputPath,opt.sampleType,opt.fileNumber)
  f_in_name = "%s/%s/ntuple_%g.root"%(opt.inputPath,opt.sampleType,opt.fileNumber)
  print " --> Clustering algorithm: %s"%clusteringAlgo
  print " --> Events to be processed: %g"%opt.maxEvents
else:
  print " --> [ERROR] %s/%s/ntuple_%g.root does not exist. Leaving..."%(opt.inputPath,opt.sampleType,opt.fileNumber)
  print "~~~~~~~~~~~~~~~~~~~~ Cl3D Selection (END) ~~~~~~~~~~~~~~~~~~~~"
  sys.exit(1)

# Open trees to read from
f_in = ROOT.TFile.Open( f_in_name )
gen_tree = f_in.Get("%s/HGCalTriggerNtuple"%clusteringAlgoDirDict["gen"])
cl3d_tree = f_in.Get("%s/HGCalTriggerNtuple"%clusteringAlgoDirDict[clusteringAlgo])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CLASS DEFINITIONS

# class for 3d cluster variable: only initiate if cl3d passes selection
class Cluster3D:

  #Constructor method: takes event and cluster number as input
  def __init__(self, _event, _ncl3d):
    #initialise TLorentzVector
    _p4 = ROOT.TLorentzVector()
    _p4.SetPtEtaPhiE( _event.cl3d_pt[_ncl3d], _event.cl3d_eta[_ncl3d], _event.cl3d_phi[_ncl3d], _event.cl3d_energy[_ncl3d] )
    self.P4 = _p4
    self.clusters_n       = _event.cl3d_clusters_n[_ncl3d]
    self.showerlength     = _event.cl3d_showerlength[_ncl3d]
    self.coreshowerlength = _event.cl3d_coreshowerlength[_ncl3d]
    self.firstlayer       = _event.cl3d_firstlayer[_ncl3d]
    self.maxlayer         = _event.cl3d_maxlayer[_ncl3d]
    self.seetot           = _event.cl3d_seetot[_ncl3d]
    self.seemax           = _event.cl3d_seemax[_ncl3d]
    self.spptot           = _event.cl3d_spptot[_ncl3d]
    self.sppmax           = _event.cl3d_sppmax[_ncl3d]
    self.szz              = _event.cl3d_szz[_ncl3d]
    self.srrtot           = _event.cl3d_srrtot[_ncl3d]
    self.srrmax           = _event.cl3d_srrmax[_ncl3d]
    self.srrmean          = _event.cl3d_srrmean[_ncl3d]
    self.emaxe            = _event.cl3d_emaxe[_ncl3d]
    self.bdteg            = _event.cl3d_bdteg[_ncl3d]
    self.quality          = _event.cl3d_quality[_ncl3d]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# FUNCTION DEFINITIONS

#function to fill tree
def fill_cl3d( _cl3d, _out_var ):
  _out_var['pt'][0] = _cl3d.P4.Pt()
  _out_var['eta'][0] = _cl3d.P4.Eta()
  _out_var['phi'][0] = _cl3d.P4.Phi()
  _out_var['clusters_n'][0] = _cl3d.clusters_n
  _out_var['showerlength'][0] = _cl3d.showerlength
  _out_var['coreshowerlength'][0] = _cl3d.coreshowerlength
  _out_var['firstlayer'][0] = _cl3d.firstlayer
  _out_var['maxlayer'][0] = _cl3d.maxlayer
  _out_var['seetot'][0] = _cl3d.seetot
  _out_var['seemax'][0] = _cl3d.seemax
  _out_var['spptot'][0] = _cl3d.spptot
  _out_var['sppmax'][0] = _cl3d.sppmax
  _out_var['szz'][0] = _cl3d.szz
  _out_var['srrtot'][0] = _cl3d.srrtot
  _out_var['srrmax'][0] = _cl3d.srrmax
  _out_var['srrmean'][0] = _cl3d.srrmean
  _out_var['emaxe'][0] = _cl3d.emaxe
  _out_var['bdteg'][0] = _cl3d.bdteg
  _out_var['quality'][0] = _cl3d.quality
  out_tree.Fill()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CONFIGURE OUTPUT
print " --> Configuring output ntuple"

#Check if output dir exists
if not os.path.isdir( "%s/cl3d_selection/%s"%(os.environ['HGCAL_L1T_BASE'],opt.sampleType) ):
  print " --> Making directory: %s/cl3d_selection/%s"%(os.environ['HGCAL_L1T_BASE'],opt.sampleType)
  os.system("mkdir %s/cl3d_selection/%s"%(os.environ['HGCAL_L1T_BASE'],opt.sampleType) )
  
# Create output file name
f_out_name = "%s/cl3d_selection/%s/%s_%s_%g.root"%(os.environ['HGCAL_L1T_BASE'],opt.sampleType,opt.sampleType,clusteringAlgo,opt.fileNumber)
print " --> Creating output file: %s"%f_out_name
f_out = ROOT.TFile( f_out_name, "RECREATE" )

# Initialise ttree and define output variables
sampleToTreeDict = {
  "electron":"e_sig",
  "photon":"g_sig",
  "pion":"pu_sig",
  "neutrino":"pu_bkg"
}
out_tree = ROOT.TTree( sampleToTreeDict[opt.sampleType.split("_")[0]], sampleToTreeDict[opt.sampleType.split("_")[0]] )
out_var_names = ['pt','eta','phi','clusters_n','showerlength','coreshowerlength','firstlayer','maxlayer','seetot','seemax','spptot','sppmax','szz','srrtot','srrmax','srrmean','emaxe','bdteg','quality']
out_var = {}
for var in out_var_names: out_var[var] = array('f',[0.])
#Create branches in output tree
for var_name, var in out_var.iteritems(): out_tree.Branch( "cl3d_%s"%var_name, var, "cl3d_%s/F"%var_name )

print " --> Output configured"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CL3D SELECTION: loop over events and write clusters passing selection to output file
for ev_idx in range(cl3d_tree.GetEntries()):

  if ev_idx == opt.maxEvents: break
  if opt.maxEvents == -1:
    if ev_idx % 100 == 0: print "    --> Processing event: %g/%g"%(ev_idx+1,cl3d_tree.GetEntries())
  else:
    if ev_idx % 100 == 0: print "    --> Processing event: %g/%g"%(ev_idx+1,opt.maxEvents)

  #Extract event info from both gen and cluster tree
  gen_tree.GetEntry( ev_idx )
  cl3d_tree.GetEntry( ev_idx )

  #Extract number of gen particles + cl3d in event
  N_gen = gen_tree.gen_n
  N_cl3d = cl3d_tree.cl3d_n

  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # GEN-MATCHED CLUSTERS
  if opt.sampleType.split("_")[0] in ['electron','photon','pion']:

    #Loop over gen-e/gamma in event
    for gen_idx in range( N_gen ):
      if abs( gen_tree.gen_pdgid[gen_idx] ) in pdgid:
        #define TLorentzVector for gen particle
        gen_p4 = ROOT.TLorentzVector()
        gen_p4.SetPtEtaPhiE( gen_tree.gen_pt[gen_idx], gen_tree.gen_eta[gen_idx], gen_tree.gen_phi[gen_idx], gen_tree.gen_energy[gen_idx] )
        # require gen e/g/pi pT > 20 GeV
        if gen_p4.Pt() < 20.: continue

        # loop overi 3d clusters: save index of max pt cluster if in 
        cl3d_genMatched_maxpt_idx = -1
        cl3d_genMatched_maxpt = -999
        for cl3d_idx in range( N_cl3d ):
          #requre that cluster pt > 10 GeV
          if cl3d_tree.cl3d_pt[cl3d_idx] < 10.: continue
          #define TLorentxVector for cl3d
          cl3d_p4 = ROOT.TLorentzVector()
          cl3d_p4.SetPtEtaPhiE( cl3d_tree.cl3d_pt[cl3d_idx], cl3d_tree.cl3d_eta[cl3d_idx], cl3d_tree.cl3d_phi[cl3d_idx], cl3d_tree.cl3d_energy[cl3d_idx] )
          #Require cluster to be dR < 0.2 within gen particle
          if cl3d_p4.DeltaR( gen_p4 ) < 0.2:
            #If pT of cluster is > present max then set 
            if cl3d_p4.Pt() > cl3d_genMatched_maxpt:
               cl3d_genMatched_maxpt = cl3d_p4.Pt()
               cl3d_genMatched_maxpt_idx = cl3d_idx

        # if cl3d idx has been set then add fill cluster to tree
        if cl3d_genMatched_maxpt_idx >= 0:
          cl3d = Cluster3D( cl3d_tree, cl3d_genMatched_maxpt_idx )
          fill_cl3d( cl3d, out_var )

  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  #BACKGROUND CLUSTERS: PU
  else:

    #Loop over 3d clusters: if pT > 20 GeV then fill as background
    for cl3d_idx in range(0, N_cl3d ):

      if cl3d_tree.cl3d_pt[cl3d_idx] > 20.:
        cl3d = Cluster3D( cl3d_tree, cl3d_idx )
        fill_cl3d( cl3d, out_var )

  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# END OF EVENTS LOOP

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
f_out.Write()
f_out.Close()
print "~~~~~~~~~~~~~~~~~~~~ Cl3D Selection (END) ~~~~~~~~~~~~~~~~~~~~"
