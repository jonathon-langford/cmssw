# Script to automate the submission, check status, resubmission and extraction of ntuples using crab

import os, sys
from optparse import OptionParser

def get_options():
  parser = OptionParser()
  parser.add_option('--mode', dest='mode', default='sub', help="Option: [sub,status,resub,extract,kill]")
  parser.add_option('--numberOfSamples', dest='numberOfSamples', default=1, type='int', help="Number of samples to process (used for submission and extraction only)")
  parser.add_option('--sampleType', dest='sampleType', default='electron_200PU', help="Sample to process, default signal is electron_200PU, default bkg is neutrino_200PU")
  parser.add_option('--storageSite', dest='storageSite', default='T2_UK_London_IC', help="User storage site")
  parser.add_option('--outputPath', dest='outputPath', default='cwd', help="Output path to hold directory containing ntuples") #allows user to save ntuples in eos
  return parser.parse_args()

(opt,args) = get_options()

#Mapping of sample type to dataset: this will need to be updated if moving to new geometry (new datasets)
sampleDict = {
  "electron_0PU":"/SingleE_FlatPt-2to100/PhaseIIMTDTDRAutumn18DR-NoPU_103X_upgrade2023_realistic_v2-v1/FEVT",
  "electron_200PU":"/SingleE_FlatPt-2to100/PhaseIIMTDTDRAutumn18DR-PU200_103X_upgrade2023_realistic_v2-v1/FEVT",
  "neutrino_200PU":"/NeutrinoGun_E_10GeV/PhaseIIMTDTDRAutumn18DR-PU200_103X_upgrade2023_realistic_v2-v1/FEVT"
}

#Total number of files for each sample: use if want all files to be processes
totalFilesDict = {
  "electron_0PU":22,
  "electron_200PU":400,
  "neutrino_200PU":2599
}

#Output dataset tag
datasetTagDict = {
  "electron_0PU":"SingleElectron_FlatPt-2to100_0PU_hgcal_l1t_v9",
  "electron_200PU":"SingleElectron_FlatPt-2to100_0PU_hgcal_l1t_v9",
  "neutrino_200PU":"SingleNeutrino_200PU_hgcal_l1t_v9"
}

# Catch: check using available sample type
if opt.sampleType not in sampleDict: 
  print " --> [ERROR] sample type %s not supported. Exiting..."%opt.sampleType
  sys.exit(1)

#determine number of files to process
if opt.numberOfSamples == -1: N_process = totalFilesDict[opt.sampleType]
elif opt.numberOfSamples > totalFilesDict[opt.sampleType]: N_process = totalFilesDict[opt.sampleType]
else: N_process = opt.numberOfSamples


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# SUBMISSION
if opt.mode == "sub":
  print "~~~~~~~~~~~~~~~~~~~~~~~~ SUBMISSION ~~~~~~~~~~~~~~~~~~~~~~~~"
  print " --> Writing crab submission file"
  
  #determine number of files to process
  if opt.numberOfSamples == -1: print " --> Processing all samples: %g"%N_process
  elif opt.numberOfSamples > totalFilesDict[opt.sampleType]: print " --> [WARNING] Trying to process %g samples. Only %g exist, processing all samples"%(opt.numberOfSamples,N_process)
  else: print " --> Processing %g sample(s)"%N_process

  #write crab submission script
  f_sub_name = "crab_submit_%s_cfg.py"%opt.sampleType
  f_sub = open("%s"%f_sub_name, "w+")
  f_sub.write("from CRABClient.UserUtilities import config\n")
  f_sub.write("config = config()\n\n")
  f_sub.write("config.Debug.scheddName = \'crab3@vocms0198.cern.ch\'\n\n")
  f_sub.write("config.General.requestName = \'%s\'\n"%opt.sampleType)
  f_sub.write("config.General.workArea = \'crab_area\'\n")
  f_sub.write("config.General.transferOutputs = True\n")
  f_sub.write("config.General.transferLogs = True\n\n")
  f_sub.write("config.JobType.pluginName = \'Analysis\'\n")
  f_sub.write("config.JobType.psetName = \'hgcal_l1t_ntupliser_v9_cfg.py\'\n")
  f_sub.write("config.JobType.maxMemoryMB = 2500\n\n")
  f_sub.write("config.Data.inputDataset = \'%s\'\n"%sampleDict[opt.sampleType])
  f_sub.write("config.Data.inputDBS = \'global\'\n")
  f_sub.write("config.Data.splitting = \'FileBased\'\n")
  f_sub.write("config.Data.unitsPerJob = 1\n")
  f_sub.write("NJOBS = %g\n"%N_process)
  f_sub.write("config.Data.totalUnits = config.Data.unitsPerJob * NJOBS\n")
  f_sub.write("config.Data.outLFNDirBase = \'/store/user/%s/\'\n"%os.environ['USER'])
  f_sub.write("config.Data.publication = True\n")
  f_sub.write("config.Data.outputDatasetTag = \'%s\'\n\n"%datasetTagDict[opt.sampleType])
  f_sub.write("config.Site.storageSite = \'%s\'"%opt.storageSite)
  f_sub.close()

  #Check if submission already exists: if so then ask user if want to delete previous submission
  if os.path.isdir("./crab_area/crab_%s"%opt.sampleType):
    delete = input(" --> Submission %s already exists. Do you want to delete previous submission [yes=1,no=0]:"%opt.sampleType)
    if delete:
      print " --> Deleting previous submission"
      os.system("rm -Rf crab_area/crab_%s"%opt.sampleType)
    else:
      print " --> Keeping previous submission. Leaving..."
      print "~~~~~~~~~~~~~~~~~~~~~ SUBMISSION (END) ~~~~~~~~~~~~~~~~~~~~~~"
      sys.exit(1)

  #Submit file to crab server
  print " --> Submitting to crab server..."
  os.system("crab submit -c crab_submit_%s_cfg.py"%opt.sampleType)
  print "~~~~~~~~~~~~~~~~~~~~~ SUBMISSION (END) ~~~~~~~~~~~~~~~~~~~~~~"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# STATUS
elif opt.mode == "status":
  print "~~~~~~~~~~~~~~~~~~~~~~~~ STATUS ~~~~~~~~~~~~~~~~~~~~~~~~"
  
  #check if crab submission exists
  if os.path.isdir("./crab_area/crab_%s"%opt.sampleType):
    print " --> Checking the status of submission: %s"%opt.sampleType
    os.system("crab status -d crab_area/crab_%s/"%opt.sampleType) 
  else:
    print " --> [ERROR] No submission for %s. Use the sub option first"%opt.sampleType
    print "~~~~~~~~~~~~~~~~~~~~~ STATUS (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1)
  print "~~~~~~~~~~~~~~~~~~~~~ STATUS (END) ~~~~~~~~~~~~~~~~~~~~~"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# RESUBMIT
elif opt.mode == "resub":
  print "~~~~~~~~~~~~~~~~~~~~~~~~ RESUBMISSION ~~~~~~~~~~~~~~~~~~~~~~~~"
  
  #check if crab submission exists
  if os.path.isdir("./crab_area/crab_%s"%opt.sampleType):
    print " --> Re-submitting failed jobs for submission: %s"%opt.sampleType
    os.system("crab resubmit -d crab_area/crab_%s/"%opt.sampleType) 
  else:
    print " --> [ERROR] No submission for %s. Use the sub option first"%opt.sampleType
    print "~~~~~~~~~~~~~~~~~~~~~ RESUBMISSION (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1)
  print "~~~~~~~~~~~~~~~~~~~~~ RESUBMISSION (END) ~~~~~~~~~~~~~~~~~~~~~"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# KILL
elif opt.mode == "kill":
  print "~~~~~~~~~~~~~~~~~~~~~~~~ KILL ~~~~~~~~~~~~~~~~~~~~~~~~"
  
  #check if crab submission exists
  if os.path.isdir("./crab_area/crab_%s"%opt.sampleType):
    kill = input(" --> Are you sure you want to kill all jobs for %s [yes=1,no=0]:"%opt.sampleType)
    if kill: 
      print " --> Killing all jobs for submission: %s"%opt.sampleType
      os.system("crab kill -d crab_area/crab_%s/"%opt.sampleType)
    else:
      print " --> Leaving..."
      print "~~~~~~~~~~~~~~~~~~~~~ KILL (END) ~~~~~~~~~~~~~~~~~~~~~"
      sys.exit(1)
  else:
    print " --> [ERROR] No submission for %s. Use the sub option first"%opt.sampleType
    print "~~~~~~~~~~~~~~~~~~~~~ KILL (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1)
  print "~~~~~~~~~~~~~~~~~~~~~ KILL (END) ~~~~~~~~~~~~~~~~~~~~~"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# EXTRACTION OF NTUPLES
elif opt.mode == "extract":
  print "~~~~~~~~~~~~~~~~~~~~~~~~ EXTRACTION ~~~~~~~~~~~~~~~~~~~~~~~~"
  
  #check if crab submission exists
  if os.path.isdir("./crab_area/crab_%s"%opt.sampleType):
    extract = input(" --> Only use this mode when all crab jobs have finished. Have they finished [yes=1,no=0]:")
    if extract:
      print " --> Extracting ntuples for submission: %s"%opt.sampleType
      #Crab only allows user to extract 500 ntuples at a time: therefore if N_process > 500 do multiple times
      if N_process/500 > 0:
        # FIXME: this should be parallelized as takes a long time for a lot of samples!
        for jobblock in range(0,N_process/500+1):
          jobids = ""
          #For final block:
          if jobblock == N_process/500:
            for jobid in range(1,N_process%500+1): jobids += "%g,"%(500*jobblock+jobid)
          else:
            for jobid in range(1,501): jobids += "%g,"%(500*jobblock+jobid)
          jobids = jobids[:-1] #remove last comma
          os.system("crab getoutput -d crab_area/crab_%s/ --jobids %s\n"%(opt.sampleType,jobids))
      else: 
        os.system("crab getoutput -d crab_area/crab_%s/"%opt.sampleType)

      #If no ntuples to receive then leave
      if not os.path.exists("crab_area/crab_%s/results/ntuple_1.root"%opt.sampleType):
        print " --> No ntuples in folder. Leaving..."
        print "~~~~~~~~~~~~~~~~~~~~~ EXTRACTION (END) ~~~~~~~~~~~~~~~~~~~~~"  
        sys.exit(1) 

      #Check if path to place output directory exists
      if opt.outputPath == "cwd": outputPath = os.environ['PWD']
      else: 
        #Check if path exists
        if os.path.isdir( opt.outputPath ): outputPath = opt.outputPath
        else:
          print " --> [ERROR] path %s does not exist. Ntuples will remain in crab_area/crab_%s/results"%(opt.outputPath,opt.sampleType)
          print "~~~~~~~~~~~~~~~~~~~~~ EXTRACTION (END) ~~~~~~~~~~~~~~~~~~~~~"  
          sys.exit(1)

      # Check if directory already exists
      if os.path.isdir("%s/%s"%(outputPath,opt.sampleType)):
        move = input("Output directory already exists. Do you want to move ntuples anyway [yes=1,no=0]:")
        if move:
          print " --> Moving ntuples to %s/%s"%(outputPath,opt.sampleType)
          os.system("mv crab_area/crab_%s/results/ntuple*.root %s/%s"%(opt.sampleType,outputPath,opt.sampleType))
        else:
          print "Ntuples will remain in crab_area/crab_%s/results"%opt.sampleType
      # if not then make directory and move ntuples there
      else:
        os.system("mkdir %s/%s"%(outputPath,opt.sampleType))
        print " --> Moving ntuples to %s/%s"%(outputPath,opt.sampleType)
        os.system("mv crab_area/crab_%s/results/ntuple*.root %s/%s"%(opt.sampleType,outputPath,opt.sampleType))
        
    else:
      print " --> Leaving"
      print "~~~~~~~~~~~~~~~~~~~~~ EXTRACTION (END) ~~~~~~~~~~~~~~~~~~~~~"  
      sys.exit(1)
  else:
    print " --> [ERROR] No submission for %s. Use the sub option first"%opt.sampleType
    print "~~~~~~~~~~~~~~~~~~~~~ EXTRACTION (END) ~~~~~~~~~~~~~~~~~~~~~"
    sys.exit(1)
  print "~~~~~~~~~~~~~~~~~~~~~ EXTRACTION (END) ~~~~~~~~~~~~~~~~~~~~~"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
else:
  print " --> [ERROR] mode %s is not supported. Please use [sub,status,resub,kill,extract]"
  sys.exit(1)
