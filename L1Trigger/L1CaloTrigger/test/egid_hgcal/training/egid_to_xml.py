# Script for converting eid xgboost model to xml file (to be used directly in TPG software)

#usual imports
import numpy as np
import xgboost as xg
import pickle
import pandas as pd
import ROOT as r
from root_numpy import tree2array, testdata, list_branches, fill_hist
from os import system, path
import os
import sys
from optparse import OptionParser

# Extract input variables to BDT from egid_training.py: if BDT config not defined there then will fail
from egid_training import egid_vars

# Configure options
def get_options():
  parser = OptionParser()
  parser.add_option('--clusteringAlgo', dest='clusteringAlgo', default='Histomaxvardr', help="Clustering algorithm with which to optimise BDT" )
  parser.add_option('--signalType', dest='signalType', default='electron_200PU', help="Input signal type" )
  parser.add_option('--backgroundType', dest='backgroundType', default='neutrino_200PU', help="Input background type" )
  parser.add_option('--bdtConfig', dest='bdtConfig', default='baseline', help="BDT config (accepted values: baseline/full)" )
  return parser.parse_args()

(opt,args) = get_options()

# Function to convert model into xml
def egid_to_xml():

  print "~~~~~~~~~~~~~~~~~~~~~~~~ egid TO XML ~~~~~~~~~~~~~~~~~~~~~~~~"

  #Define BDT name
  bdt_name = "%s_vs_%s_%s"%(opt.signalType,opt.backgroundType,opt.bdtConfig)
  # Check if model exists
  if not os.path.exists("./models/egid_%s_%s_loweta.model"%(bdt_name,opt.clusteringAlgo)):
    print " --> [ERROR] No model exists for this BDT: ./models/egid_%s_%s_loweta.model. Train first! Leaving..."%(bdt_name,opt.clusteringAlgo)
    print "~~~~~~~~~~~~~~~~~~~~~ egid TRAINING (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1)
  
  elif not os.path.exists("./models/egid_%s_%s_higheta.model"%(bdt_name,opt.clusteringAlgo)):
    print " --> [ERROR] No model exists for this BDT: ./models/egid_%s_%s_higheta.model. Train first! Leaving..."%(bdt_name,opt.clusteringAlgo)
    print "~~~~~~~~~~~~~~~~~~~~~ egid TRAINING (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1) 

  # Check if input vars for BDT name are defined
  if not bdt_name in egid_vars: 
    print " --> [ERROR] Input variables for BDT %s are not defined. Add key to egid_vars dict. Leaving..."%bdt_name
    print "~~~~~~~~~~~~~~~~~~~~~ egid TO XML (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1)

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # LOOP OVER ETA REGIONS
  for reg in ['low','high']:
  
    print " --> Loading model for %s eta region: ./models/egid_%s_%s_%seta.model"%(reg,bdt_name,opt.clusteringAlgo,reg)    
    egid = xg.Booster()
    egid.load_model( "./models/egid_%s_%s_%seta.model"%(bdt_name,opt.clusteringAlgo,reg) )
 
    #Define name of xml file to save
    if not os.path.isdir("./xml"):
      print " --> Making ./xml directory to store models as xml files"
      os.system("mkdir xml")
    f_xml = "./xml/egid_%s_%s_%seta.xml"%(bdt_name,opt.clusteringAlgo,reg)

    # Convert to xml: using mlglue.tree functions
    from mlglue.tree import tree_to_tmva, BDTxgboost, BDTsklearn
    target_names = ['background','signal']
    # FIXME: add options for saving BDT with user specified hyperparams
    bdt = BDTxgboost( egid, egid_vars[bdt_name], target_names, kind='binary', max_depth=6, learning_rate=0.3 )
    bdt.to_tmva( f_xml )

    print " --> Converted to xml: ./xml/egid_%s_%s_%seta.xml"%(bdt_name,opt.clusteringAlgo,reg)
  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # END OF LOOP OVER ETA REGIONS
  print "~~~~~~~~~~~~~~~~~~~~~ egid TO XML (END) ~~~~~~~~~~~~~~~~~~~~~"
# END OF TO_XML FILE

# Main function for running program
if __name__ == "__main__": egid_to_xml()
