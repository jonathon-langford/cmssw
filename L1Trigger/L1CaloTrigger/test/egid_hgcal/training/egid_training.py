# Train egid (BDT: xgboost) for hgcal l1t: using shower shape variables
# > Takes as input clusters which pass selection 
# > Trains separately in different eta regions (1.5-2.7 and 2.7-3.0)

#usual imports
import ROOT
import numpy as np
import pandas as pd
import xgboost as xg
import matplotlib.pyplot as plt
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, roc_curve
from os import path, system
import os
import sys
from array import array
from optparse import OptionParser

#Additional functions (if needed)
from root_numpy import tree2array, fill_hist


# Configure options
def get_options():
  parser = OptionParser()
  parser.add_option('--clusteringAlgo', dest='clusteringAlgo', default='Histomaxvardr', help="Clustering algorithm with which to optimise BDT" )
  parser.add_option('--signalType', dest='signalType', default='electron_200PU', help="Input signal type" )
  parser.add_option('--backgroundType', dest='backgroundType', default='neutrino_200PU', help="Input background type" )
  parser.add_option('--bdtConfig', dest='bdtConfig', default='baseline', help="BDT config (accepted values: baseline/full)" )
  parser.add_option('--reweighting', dest='reweighting', default=1, type='int', help="Boolean to perform re-weighting of clusters to equalise signal and background [yes=1 (default), no=0]" )
  parser.add_option('--trainParams',dest='trainParams', default=None, help='Comma-separated list of colon-separated pairs corresponding to (hyper)parameters for the training')
  return parser.parse_args()

# HARDCODED: input variables to BDT for different configs. Specify config in options. To try new BDT with different inputs variables, then add another key to dict
egid_vars = {"electron_200PU_vs_neutrino_200PU_baseline":['cl3d_coreshowerlength','cl3d_firstlayer','cl3d_maxlayer','cl3d_srrmean'],'electron_200PU_vs_neutrino_200PU_full':['cl3d_coreshowerlength','cl3d_showerlength','cl3d_firstlayer','cl3d_maxlayer','cl3d_szz','cl3d_srrmean','cl3d_srrtot','cl3d_seetot','cl3d_spptot']}

# Define eta regions for different trainings
eta_regions = {"low":[1.5,2.7],"high":[2.7,3.0]}


#Function to train xgboost model for HGCal L1T egid
def train_egid():

  (opt,args) = get_options()
  print "~~~~~~~~~~~~~~~~~~~~~~~~ egid TRAINING ~~~~~~~~~~~~~~~~~~~~~~~~"

  #Set numpy random seed
  np.random.seed(123456)

  # Training and validation fractions
  trainFrac = 0.9
  validFrac = 0.1

  #Define BDT name
  bdt_name = "%s_vs_%s_%s"%(opt.signalType,opt.backgroundType,opt.bdtConfig)
  # Check if input vars for BDT name are defined
  if bdt_name in egid_vars: print " --> Training BDT: %s"%bdt_name
  else:
    print " --> [ERROR] Input variables for BDT %s are not defined. Add key to egid_vars dict. Leaving..."%bdt_name
    print "~~~~~~~~~~~~~~~~~~~~~ egid TRAINING (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1)

  #Dictionaries for sig+bkg type mappings
  treeMap = {"electron":"e_sig","photon":"g_sig","pion":"pi_bkg","neutrino":"pu_bkg"}
  procMap = {"electron":"signal", "photon":"signal", "pion":"background", "neutrino":"background"}

  # Add input files to map
  procFileMap = {}
  procFileMap[ opt.signalType.split("_")[0] ] = "%s/cl3d_selection/%s/%s_%s_train.root"%(os.environ['HGCAL_L1T_BASE'],opt.signalType,opt.signalType,opt.clusteringAlgo)
  procFileMap[ opt.backgroundType.split("_")[0] ] = "%s/cl3d_selection/%s/%s_%s_train.root"%(os.environ['HGCAL_L1T_BASE'],opt.backgroundType,opt.backgroundType,opt.clusteringAlgo)
  procs = procFileMap.keys()

  # Check if models and frames directories exist
  if not os.path.isdir("./models"):
    print " --> Making ./models directory to store trained egid models"
    os.system("mkdir models")
  if not os.path.isdir("./frames"):
    print " --> Making ./frames directory to store pandas dataFrames"
    os.system("mkdir frames")

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # EXTRACT DATAFRAMES FROM INPUT SELECTED CLUSTERS
  trainTotal = None
  trainFrames = {}
  #extract the trees: turn them into arrays
  for proc,fileName in procFileMap.iteritems():
    trainFile = ROOT.TFile("%s"%fileName)
    trainTree = trainFile.Get( treeMap[proc] )
    #initialise new tree with only relevant variables
    _file = ROOT.TFile("tmp.root","RECREATE")
    _tree = ROOT.TTree("tmp","tmp")
    _vars = {}
    for var in egid_vars[bdt_name]:
      _vars[ var ] = array( 'f', [-1.] )
      _tree.Branch( '%s'%var, _vars[ var ], '%s/F'%var )
    #Also add cluster eta to do eta splitting
    _vars['cl3d_eta'] = array( 'f', [-999.] )
    _tree.Branch( 'cl3d_eta', _vars['cl3d_eta'], 'cl3d_eta/F' )  

    #loop over events in tree and add to tmp tree
    for ev in trainTree:
      for var in egid_vars[bdt_name]: _vars[ var ][0] = getattr( ev, '%s'%var )
      _vars['cl3d_eta'][0] = getattr( ev, 'cl3d_eta' )
      _tree.Fill()
  
    #Convert tmp tree to pandas dataFrame and delete tmp files
    trainFrames[proc] = pd.DataFrame( tree2array( _tree ) )
    del _file
    del _tree
    os.system('rm tmp.root')

    #Add columns to dataframe to labl clusters
    trainFrames[proc]['proc'] = procMap[ proc ]
    print " --> Extracted %s dataFrame from file: %s"%(proc,fileName)

  #Create one total frame: i.e. concatenate signal and bkg
  trainList = []
  for proc in procs: trainList.append( trainFrames[proc] )
  trainTotal = pd.concat( trainList, sort=False )
  del trainFrames
  print " --> Created total dataFrame: signal (%s) and background (%s)"%(opt.signalType,opt.backgroundType)

  # Save dataFrames as pkl file
  pd.to_pickle( trainTotal, "./frames/%s.pkl"%bdt_name )

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # TRAIN MODEL: loop over different eta regions
  print ""
  for reg in eta_regions:

    print " ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print " --> Training for %s eta region: %2.1f < |eta| < %2.1f"%(reg,eta_regions[reg][0],eta_regions[reg][1])

    #Impose eta cuts
    train_reg = trainTotal[ abs(trainTotal['cl3d_eta'])>eta_regions[reg][0] ]
    train_reg = train_reg[ abs(train_reg['cl3d_eta'])<=eta_regions[reg][1] ]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # REWEIGHTING: 
    if opt.reweighting:
      print " --> Reweighting: equalise signal and background samples (same sum of weights)"
      sum_sig = len( train_reg[ train_reg['proc'] == "signal" ].index )
      sum_bkg = len( train_reg[ train_reg['proc'] == "background" ].index )
      weights = list( map( lambda a: (sum_sig+sum_bkg)/sum_sig if a == "signal" else (sum_sig+sum_bkg)/sum_bkg, train_reg['proc'] ) )
      train_reg['weight'] = weights 
    else:
      print " --> No reweighting: assuming same S/B as in input ntuples"
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # CONFIGURE DATASETS: shuffle to get train and validation
    print " --> Configuring training and validation datasets"
    label_encoder = LabelEncoder()
    theShape = train_reg.shape[0]  
    theShuffle = np.random.permutation( theShape )
    egid_trainLimit = int(theShape*trainFrac)
    egid_validLimit = int(theShape*validFrac)
  
    #Set up dataFrames for training BDT
    egid_X = train_reg[ egid_vars[bdt_name] ].values
    egid_y = label_encoder.fit_transform( train_reg['proc'].values )
    if opt.reweighting: egid_w = train_reg['weight'].values

    #Peform shuffle
    egid_X = egid_X[theShuffle]
    egid_y = egid_y[theShuffle]
    if opt.reweighting: egid_w = egid_w[theShuffle]

    #Define training and validation sets
    egid_train_X, egid_valid_X, dummy_X = np.split(egid_X, [egid_trainLimit, egid_validLimit+egid_trainLimit] )
    egid_train_y, egid_valid_y, dummy_y = np.split(egid_y, [egid_trainLimit, egid_validLimit+egid_trainLimit] )
    if opt.reweighting: egid_train_w, egid_valid_w, dummy_w = np.split(egid_w, [egid_trainLimit, egid_validLimit+egid_trainLimit] )
 
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # BUILDING THE MODEL
    if opt.reweighting:
      training_egid = xg.DMatrix( egid_train_X, label=egid_train_y, weight=egid_train_w, feature_names=egid_vars[bdt_name] )
      validation_egid = xg.DMatrix( egid_valid_X, label=egid_valid_y, weight=egid_valid_w, feature_names=egid_vars[bdt_name] )
    else:
      training_egid = xg.DMatrix( egid_train_X, label=egid_train_y, feature_names=egid_vars[bdt_name] )
      validation_egid = xg.DMatrix( egid_valid_X, label=egid_valid_y, feature_names=egid_vars[bdt_name] )

    # extract training hyper-parameters for model from input option
    trainParams = {}
    trainParams['objective'] = 'binary:logistic'
    trainParams['nthread'] = 1
    paramExt = ''
    if opt.trainParams:
      paramExt = '__'
      for paramPair in trainParams:
        param = paramPair.split(":")[0]
        value = paramPair.split(":")[1]
        trainParams[param] = value
        paramExt += '%s)%s__'%(param_value)
      paramExt = paramExt[:-2]

    # Train the model
    print " --> Training the model: %s"%trainParams
    egid = xg.train( trainParams, training_egid )
    print " --> Done."

    # Save the model
    egid.save_model( './models/egid_%s_%s_%seta.model'%(bdt_name,opt.clusteringAlgo,reg) )
    print " --> Model saved: ./models/egid_%s_%s_%seta.model"%(bdt_name,opt.clusteringAlgo,reg)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # CHECKING PERFORMANCE OF MODEL: using trainig and validation sets
    egid_train_predy = egid.predict( training_egid )
    egid_valid_predy = egid.predict( validation_egid )

    print "    *************************************************"
    print "    --> Performance: in %s eta region (%2.1f < |eta| < %2.1f)"%(reg,eta_regions[reg][0],eta_regions[reg][1])
    print "      * Training set   ::: AUC = %5.4f"%roc_auc_score( egid_train_y, egid_train_predy )
    print "      * Validation set ::: AUC = %5.4f"%roc_auc_score( egid_valid_y, egid_valid_predy )
    print "    *************************************************"
    print ""

  #END OF LOOP OVER ETA REGIONS
  print "~~~~~~~~~~~~~~~~~~~~~ egid TRAINING (END) ~~~~~~~~~~~~~~~~~~~~~"
# END OF TRAINING FUNCTION

# Main function for running program
if __name__ == "__main__": train_egid()
