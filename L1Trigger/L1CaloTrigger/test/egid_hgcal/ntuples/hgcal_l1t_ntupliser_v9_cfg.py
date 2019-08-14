import FWCore.ParameterSet.Config as cms 
from Configuration.StandardSequences.Eras import eras
from Configuration.ProcessModifiers.convertHGCalDigisSim_cff import convertHGCalDigisSim

# For old samples use the digi converter
process = cms.Process('DIGI',eras.Phase2C4)

# import of standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('Configuration.Geometry.GeometryExtended2023D35Reco_cff')
process.load('Configuration.Geometry.GeometryExtended2023D35_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.Generator_cff')
process.load('IOMC.EventVertexGenerators.VtxSmearedHLLHC14TeV_cfi')
process.load('GeneratorInterface.Core.genFilterSummary_cff')
process.load('Configuration.StandardSequences.SimIdeal_cff')
process.load('Configuration.StandardSequences.Digi_cff')
process.load('Configuration.StandardSequences.SimL1Emulator_cff')
process.load('Configuration.StandardSequences.DigiToRaw_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(10)
)

# Input source
process.source = cms.Source("PoolSource",
       fileNames = cms.untracked.vstring('/store/mc/PhaseIIMTDTDRAutumn18DR/NeutrinoGun_E_10GeV/FEVT/PU200_103X_upgrade2023_realistic_v2-v1/280000/13B217C2-4935-CE45-BBF7-EC843AFA3D8D.root'),
       inputCommands=cms.untracked.vstring(
           'keep *',
           'drop l1tEMTFHit2016Extras_simEmtfDigis_CSC_HLT',
           'drop l1tEMTFHit2016Extras_simEmtfDigis_RPC_HLT',
           'drop l1tEMTFHit2016s_simEmtfDigis__HLT',
           'drop l1tEMTFTrack2016Extras_simEmtfDigis__HLT',
           'drop l1tEMTFTrack2016s_simEmtfDigis__HLT',
           )
       )

process.options = cms.untracked.PSet(

)

# Production Info
process.configurationMetadata = cms.untracked.PSet(
    version = cms.untracked.string('$Revision: 1.20 $'),
    annotation = cms.untracked.string('SingleElectronPt10_cfi nevts:10'),
    name = cms.untracked.string('Applications')
)

# Output definition
process.TFileService = cms.Service(
    "TFileService",
    fileName = cms.string("ntuple.root")
    )

# Other statements
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, 'auto:phase2_realistic', '')

# load HGCAL TPG simulation
process.load('L1Trigger.L1THGCal.hgcalTriggerPrimitives_cff')
process.load('L1Trigger.L1THGCalUtilities.hgcalTriggerNtuples_cff')
from L1Trigger.L1THGCalUtilities.hgcalTriggerChains import HGCalTriggerChains
import L1Trigger.L1THGCalUtilities.vfe as vfe
import L1Trigger.L1THGCalUtilities.concentrator as concentrator
import L1Trigger.L1THGCalUtilities.clustering2d as clustering2d
import L1Trigger.L1THGCalUtilities.clustering3d as clustering3d
import L1Trigger.L1THGCalUtilities.customNtuples as ntuple


chains = HGCalTriggerChains()
# Register algorithms
## VFE
chains.register_vfe("Floatingpoint8", lambda p : vfe.create_compression(p, 4, 4, True))
## ECON
chains.register_concentrator("Threshold", concentrator.create_threshold)
chains.register_concentrator("Supertriggercell", concentrator.create_supertriggercell)
## BE1
chains.register_backend1("Dummy", clustering2d.create_dummy)
## BE2
chains.register_backend2("Histomaxvardr", lambda p,i : clustering3d.create_histoMax_variableDr(p,i))
# Register ntuples
# Store gen info only in the reference ntuple
ntuple_list_ref = ['event', 'gen', 'multiclusters']
ntuple_list = ['event', 'multiclusters']
chains.register_ntuple("Genclustersntuple", lambda p,i : ntuple.create_ntuple(p,i, ntuple_list_ref))
chains.register_ntuple("Clustersntuple", lambda p,i : ntuple.create_ntuple(p,i, ntuple_list))

# Register trigger chains
concentrator_algos = ['Threshold','Supertriggercell']
backend_algos = ['Histomaxvardr']
## Make cross product fo ECON and BE algos
import itertools
ch_idx = 0 #add gen info to first chain 
for cc,be in itertools.product(concentrator_algos,backend_algos):
    if ch_idx == 0: chains.register_chain('Floatingpoint8', cc, 'Dummy', be, ntuple='Genclustersntuple')
    else: chains.register_chain('Floatingpoint8', cc, 'Dummy', be, ntuple='Clustersntuple')
    ch_idx += 1

#Add chains to process
process = chains.create_sequences(process)

# Set MinPt threshold in each chain
for ch in chains.chain:
  #Concatenate elements of chain up to backend algo
  ch_str = ""
  for element in ch[:4]: ch_str += element
  #Treat Ref3d and Histomaxvardr separaterly
  if ch[3] == "Histomaxvardr": 
    pset = getattr(process,ch_str).ProcessorParameters.C3d_parameters.histoMax_C3d_clustering_parameters
  else: 
    print "[ERROR] Backend alg %s not supported. Exiting..."%ch[3]
    sys.exit(1)
  #Set minPt threshold
  pset.minPt_multicluster = cms.double(10.)

# Remove towers from sequence
process.hgcalTriggerPrimitives.remove(process.hgcalTowerMap)
process.hgcalTriggerPrimitives.remove(process.hgcalTower)

process.hgcl1tpg_step = cms.Path(process.hgcalTriggerPrimitives)
process.ntuple_step = cms.Path(process.hgcalTriggerNtuples)

# Schedule definition
process.schedule = cms.Schedule(process.hgcl1tpg_step,process.ntuple_step)

# Add early deletion of temporary data products to reduce peak memory need
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
# End adding early deletion

