import os, sys
from optparse import OptionParser

print "~~~~~~~~~~~~~~~~~~~~~~~~ Cl3D Selection Submission ~~~~~~~~~~~~~~~~~~~~~~~~"

def get_options():
  parser = OptionParser()
  parser.add_option('--sampleType', dest='sampleType', default='electron_200PU', help="Sample to process, default signal is electron_200PU, default bkg is neutrino_200PU" )
  parser.add_option("--inputPath", dest="inputPath", default="%s/ntuples"%os.environ['HGCAL_L1T_BASE'], help="Path to directories which hold input ntuples")
  parser.add_option('--clusteringAlgo', dest='clusteringAlgo', default='Histomaxvardr', help="Clustering algorithm" )
  parser.add_option('--numberOfFiles', dest='numberOfFiles', default=-1, type="int", help="Number of files to process" )
  parser.add_option('--queue', dest='queue', default='microcentury', help="HTCondor Queue" )
  return parser.parse_args()

(opt,args) = get_options()

#Total number of files for each sample: use if want all files to be processes
totalFilesDict = {
  "electron_0PU":22,
  "electron_200PU":400,
  "neutrino_200PU":2599
}

#Define path and 
path = "%s/cl3d_selection"%os.environ['HGCAL_L1T_BASE']
f_sub_name = "submit_%s_%s.sub"%(opt.sampleType,opt.clusteringAlgo)
sub_handle = "%s_%s_$(procID)"%(opt.sampleType,opt.clusteringAlgo)

print " --> Submitting cl3d selection for %s"%opt.sampleType
if opt.numberOfFiles == -1:
  print " --> Processing all files: %g"%totalFilesDict[opt.sampleType]
  N_process = totalFilesDict[opt.sampleType]
elif opt.numberOfFiles > totalFilesDict[opt.sampleType]:
  print " --> [WARNING] only %g files exist. Processing all files"%totalFilesDict[opt.sampleType]
  N_process = totalFilesDict[opt.sampleType]
else:
  print " --> Processing %g files"%opt.numberOfFiles
  N_process = opt.numberOfFiles

#Create condor submission file
print " --> Creating HTCondor submission file: %s"%f_sub_name
f_sub = open("%s"%f_sub_name,"w+")
f_sub.write("plusone = $(Process) + 1\n")
f_sub.write("procID = $INT(plusone,%d)\n\n")
f_sub.write("executable          = %s/run.sh\n"%path)
f_sub.write("arguments           = %s %s %s $(procID) %s\n"%(os.environ['HGCAL_L1T_BASE'],opt.sampleType,opt.inputPath,opt.clusteringAlgo))
f_sub.write("output              = %s/jobs/out/%s.out\n"%(path,sub_handle))
f_sub.write("error               = %s/jobs/err/%s.err\n"%(path,sub_handle))
f_sub.write("log                 = %s/jobs/log/%s.log\n"%(path,sub_handle))
f_sub.write("+JobFlavour         = \"%s\"\n"%opt.queue)
f_sub.write("queue %s\n"%N_process)
f_sub.close()

print "      plusone = $(Process) + 1"
print "      procID = $INT(plusone,%d)"
print "      executable          = %s/run.sh"%path
print "      arguments           = %s %s %s $(procID) %s"%(os.environ['HGCAL_L1T_BASE'],opt.sampleType,opt.inputPath,opt.clusteringAlgo)
print "      output              = %s/jobs/out/%s.out"%(path,sub_handle)
print "      error               = %s/jobs/err/%s.err"%(path,sub_handle)
print "      log                 = %s/jobs/log/%s.log"%(path,sub_handle)
print "      +JobFlavour         = \"%s\""%opt.queue
print "      queue %s"%N_process

print " --> Submitting..."
os.system('condor_submit %s'%f_sub_name)
print " --> Deleting submission file"
os.system('rm %s'%f_sub_name)

print "~~~~~~~~~~~~~~~~~~~~~ Cl3D Selection Submission (END)~~~~~~~~~~~~~~~~~~~~~~"
