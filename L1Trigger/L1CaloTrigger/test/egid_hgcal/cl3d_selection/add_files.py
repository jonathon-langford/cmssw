# Python script for hadd-ing files for input sample type
# Combines files to have: full (100%), train (90%) and test (10%)

import ROOT
import sys
import os
from optparse import OptionParser

print "~~~~~~~~~~~~~~~~~~~~~~~~ ADD FILES ~~~~~~~~~~~~~~~~~~~~~~~~"

def get_options():
  parser = OptionParser()
  parser = OptionParser( usage="python add_files.py --sampleType=<sampleType>" )
  parser.add_option("--sampleType", dest='sampleType', default='electron_200PU', help="Sample to process, default signal is electron_200PU, default bkg is neutrino_200PU")
  parser.add_option("--clusteringAlgo", dest="clusteringAlgo", default="Histomaxvardr", help="Clustering algorithm used in ntuple production")
  parser.add_option("--deleteIndividualFiles", dest="deleteIndividualFiles", default=0, type="int", help="Delete individual files after hadding [1=yes,0=no (default)]")
  return parser.parse_args()

(opt,args) = get_options()

#Check if directory exists:
if not os.path.isdir("./%s"%opt.sampleType):
  print " --> [ERROR] Directory %s does not exist. Try running the cl3d selection first"
  print "~~~~~~~~~~~~~~~~~~~~~ ADD FILES (END) ~~~~~~~~~~~~~~~~~~~~~"
  sys.exit(1)

#Get number of files in folder and separate into test and train sample sizes
N_files = len(next(os.walk('./%s'%opt.sampleType))[2])
if N_files == 0:
  print " --> [ERROR] %s is empty. No files to add"%opt.sampleType
  print "~~~~~~~~~~~~~~~~~~~~~ ADD FILES (END) ~~~~~~~~~~~~~~~~~~~~~"
  sys.exit(1)
N_test = int(0.1*N_files)
N_train = int(N_files-N_test)

print " --> Making all (%g), test (%g) and train (%g) samples"%(N_files,N_test,N_train)

#first add all files for full
os.system('mkdir %s/all'%opt.sampleType)
os.system('hadd %s/all/%s_%s_all.root %s/%s_%s_*.root'%(opt.sampleType,opt.sampleType,opt.clusteringAlgo,opt.sampleType,opt.sampleType,opt.clusteringAlgo))

#make test and train samples
os.system('mkdir %s/test %s/train'%(opt.sampleType,opt.sampleType))
os.system('for fileNum in {1..%g}; do mv %s/%s_%s_${fileNum}.root %s/train; done'%(N_train,opt.sampleType,opt.sampleType,opt.clusteringAlgo,opt.sampleType))
os.system('mv %s/%s_%s_*.root %s/test'%(opt.sampleType,opt.sampleType,opt.clusteringAlgo,opt.sampleType))
os.system('hadd %s/%s_%s_train.root %s/train/*.root'%(opt.sampleType,opt.sampleType,opt.clusteringAlgo,opt.sampleType))  
os.system('hadd %s/%s_%s_test.root %s/test/*.root'%(opt.sampleType,opt.sampleType,opt.clusteringAlgo,opt.sampleType))
os.system('mv %s/all/%s_%s_all.root %s/'%(opt.sampleType,opt.sampleType,opt.clusteringAlgo,opt.sampleType))
os.system('rm -Rf %s/all'%opt.sampleType)
print " --> Successfully made files"

if opt.deleteIndividualFiles:
  print " --> Deleting individual files..."
  os.system('rm -Rf %s/train'%opt.sampleType)
  os.system('rm -Rf %s/test'%opt.sampleType)

print "~~~~~~~~~~~~~~~~~~~~~ ADD FILES (END) ~~~~~~~~~~~~~~~~~~~~~"
