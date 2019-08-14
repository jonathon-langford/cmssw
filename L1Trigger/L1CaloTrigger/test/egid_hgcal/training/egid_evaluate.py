# Script to evaluate newly trained egid(s)
#  > Input: selected clusters in cl3d_selection directory
#  > Output: copy of ntuples + new BDT scores
#  > Can evaluate multiple BDTs, just need xml input

#usual imports
import ROOT
import numpy as np
import pandas as pd
import xgboost as xg
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, roc_curve
from os import path, system
import os
import sys
from array import array

#Additional functions (if needed)
from root_numpy import tree2array, fill_hist

# Extract input variables to BDT from egid_training.py: if BDT config not defined there then will fail
from egid_training import egid_vars, eta_regions

# Define sample to tree mapping
treeMap = {
  "electron":"e_sig",
  "photon":"g_sig",
  "pion":"pi_bkg",
  "neutrino":"pu_bkg"
}

# Configure options
from optparse import OptionParser
def get_options():
  parser = OptionParser()
  parser.add_option('--clusteringAlgo', dest='clusteringAlgo', default='Histomaxvardr', help="Clustering algorithm with which BDT was trained" )
  parser.add_option('--sampleType', dest='sampleType', default='electron_200PU', help="Input sample type" )
  parser.add_option('--bdts', dest='bdts', default='electron_200PU_vs_neutrino_200PU:baseline', help="Comma separated list of BDTs to evaluate. Format is <discrimnator>:<config>,... e.g. electron_200PU_vs_neutrino_200PU:baseline,electron_200PU_vs_neutrino_200PU:full" )
  parser.add_option('--dataset', dest='dataset', default='test', help="Ntuple to evaluate on [test,train,all]" )
  return parser.parse_args()

(opt,args) = get_options()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# FUNCTIONS TO INITIATE AND EVALUATE BDTs

# Initialisation: returns BDT and dict of input variables. Takes xml file name as input
def initialise_egid_BDT( in_xml, in_var_names ):
  # book mva reader with input variables
  in_var = {}
  for var in in_var_names: in_var[var] = array( 'f', [0.] )
  # initialise TMVA reader and add variables
  bdt_ = ROOT.TMVA.Reader()
  for var in in_var_names: bdt_.AddVariable( var, in_var[var] )
  # book mva with xml file
  bdt_.BookMVA( "BDT", in_xml )
  # return initialised BDT and input variables
  return bdt_, in_var

# Evaluation: calculates BDT score for 3D cluster taking bdt as input
def evaluate_egid_BDT( _bdt, _bdt_var, in_cl3d, in_var_names ):
  # Loop over input vars and extract values from tree
  for var in in_var_names: _bdt_var[var][0]=getattr( in_cl3d, "%s"%var ) 
  #return BDT score
  return _bdt.EvaluateMVA("BDT")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def evaluate_egid():

  print "~~~~~~~~~~~~~~~~~~~~~~~~ egid EVALUATE ~~~~~~~~~~~~~~~~~~~~~~~~"

  # Extract bdt names from input list
  bdt_list = []
  for bdt in opt.bdts.split(","): bdt_list.append( "%s_%s"%(bdt.split(":")[0],bdt.split(":")[1]) )

  # Check there is at least one input BDT
  if len(bdt_list) == 0: 
    print " --> [ERROR] No input BDT. Leaving..."
    print "~~~~~~~~~~~~~~~~~~~~~ egid EVALUATE (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1)

  # Check bdts exist (as xml files), if so then add to dict
  model_xmls = {}
  for bdt_name in bdt_list:
    #check if input variables are defined
    if not bdt_name in egid_vars:
      print " --> [ERROR] Input variables for BDT %s are not defined. Add key to egid_vars in training. Leaving..."%bdt_name
      print "~~~~~~~~~~~~~~~~~~~~~ egid EVALUATE (END) ~~~~~~~~~~~~~~~~~~~~~"
      sys.exit(1)
    for reg in ['low','high']:
      if not os.path.exists("./xml/egid_%s_%s_%seta.xml"%(bdt_name,opt.clusteringAlgo,reg)):
        print " --> [ERROR] no xml file for BDT: %s. Leaving..."%bdt_name
        print "~~~~~~~~~~~~~~~~~~~~~ egid EVALUATE (END) ~~~~~~~~~~~~~~~~~~~~~"
        sys.exit(1)
      else:
        # passed checks: add xml to dict
        model_xmls[ "%s_%seta"%(bdt_name,reg) ] = "./xml/egid_%s_%s_%seta.xml"%(bdt_name,opt.clusteringAlgo,reg)

  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # CONFIGURE INPUT NTUPLE
  # Define input ntuple
  f_in_name = "%s/cl3d_selection/%s/%s_%s_%s.root"%(os.environ['HGCAL_L1T_BASE'],opt.sampleType,opt.sampleType,opt.clusteringAlgo,opt.dataset)
  if not os.path.exists( f_in_name ):
    print " --> [ERROR] Input ntuple %s does not exist. Leaving..."%f_in_name
    print "~~~~~~~~~~~~~~~~~~~~~ egid EVALUATE (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1)

  # Extract trees
  f_in = ROOT.TFile.Open( f_in_name )
  t_in = f_in.Get( treeMap[ opt.sampleType.split("_")[0] ] )
  print " --> Input ntuple %s read successfully"%f_in_name

  
  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # CONFIGURE OUTPUT NTUPLE
  if not os.path.isdir("./results"):
    print " --> Making ./results directory"
    os.system("mkdir results")
  if not os.path.isdir("./results/%s"%opt.sampleType):
    print " --> Making ./results/%s directory to store ntuples with evaluated bdts"%opt.sampleType
    os.system("mkdir results/%s"%opt.sampleType)
  f_out_name = "./results/%s/%s_%s_%s_eval.root"%(opt.sampleType,opt.sampleType,opt.clusteringAlgo,opt.dataset)

  # Variables to store in output ntuple
  out_var_names = ['pt','eta','phi','clusters_n','showerlength','coreshowerlength','firstlayer','maxlayer','seetot','seemax','spptot','sppmax','szz','srrtot','srrmax','srrmean','emaxe']
  # Add bdt score from TPG: i.e. one that was calculated in ntuple production
  out_var_names.append( "bdt_tpg" )
  # Add new bdt scores
  for bdt_name in bdt_list: out_var_names.append( "bdt_%s"%bdt_name )

  # Define dict to store output var
  out_var = {}
  for var in out_var_names: out_var[var] = array('f',[0.])
  
  #Open file: check if already exists (if so ask user if they want to rewrite)
  if os.path.exists( f_out_name ):
    recreate = input("Output file %s already exists. Do you want to write over file [yes=1,no=0]:"%f_out_name)
    if not recreate:
      print " --> Move %s to a new folder then run again. Leaving..."%f_out_name
      print "~~~~~~~~~~~~~~~~~~~~~ egid EVALUATE (END) ~~~~~~~~~~~~~~~~~~~~~"
      sys.exit(1)
  
  f_out = ROOT.TFile.Open( f_out_name, "RECREATE" )
  t_out = ROOT.TTree( treeMap[opt.sampleType.split("_")[0]], treeMap[opt.sampleType.split("_")[0]] )
    
  #Add branches to tree
  for var_name, var in out_var.iteritems(): t_out.Branch("cl3d_%s"%var_name, var, "cl3d_%s/F"%var_name) 

  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # INITIALISE BDTS
  bdts = {}
  bdt_input_variables = {} #dict of dicts to store input var for each bdt
  # Loop over bdts
  for b in bdt_list:
    # Loop over eta regions
    for reg in ['low','high']:
      bdts["%s_%seta"%(b,reg)], bdt_input_variables["%s_%seta"%(b,reg)] = initialise_egid_BDT( model_xmls["%s_%seta"%(b,reg)], egid_vars[b] )
      print " --> Initialised BDT (%s) in %s eta region"%(b,reg)

  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # EVALUATE BDTS: + store output variables in tree
  #Loop over clusters in input tree
  for cl3d in t_in:
  
    #evaluate bdts
    for b in bdt_list:
 
      #Low eta region: use low eta bdt
      if(abs(cl3d.cl3d_eta) > eta_regions['low'][0])&(abs(cl3d.cl3d_eta) <= eta_regions['low'][1]):
        out_var["bdt_%s"%b][0] = evaluate_egid_BDT( bdts["%s_loweta"%b], bdt_input_variables["%s_loweta"%b], cl3d, egid_vars[b] )

      #High eta region: use high eta bdt
      elif(abs(cl3d.cl3d_eta) > eta_regions['high'][0])&(abs(cl3d.cl3d_eta) <= eta_regions['high'][1]):
        out_var["bdt_%s"%b][0] = evaluate_egid_BDT( bdts["%s_higheta"%b], bdt_input_variables["%s_higheta"%b], cl3d, egid_vars[b] )

      # Else: outside allowed eta range, give value of -999
      else: out_var["bdt_%s"%b][0] = -999.

    # Add all other variables to output ntuple
    for var in out_var_names[:-1*len(bdt_list)]:
      if "bdt_tpg" in var: out_var[var][0] = getattr(cl3d,"cl3d_bdteg")
      else: out_var[var][0] = getattr(cl3d,"cl3d_%s"%var)

    # Write cluster with new BDT scores to tree
    t_out.Fill()

  #END of loop over clusters
  print " --> Evaluated BDT scores and saved in output: %s"%f_out_name

  # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # CLOSE FILES
  f_in.Close()
  f_out.Write()
  f_out.Close()

  print "~~~~~~~~~~~~~~~~~~~~~ egid EVALUATE (END) ~~~~~~~~~~~~~~~~~~~~~"
# END OF EVALUATION FUNCTION

# Main function for running program
if __name__ == "__main__": evaluate_egid()


