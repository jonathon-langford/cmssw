import FWCore.ParameterSet.Config as cms

quantize_proc = cms.PSet(ProcessorName  = cms.string('HGCalQuantizedClusterProcessor'),
    RandomString = cms.string("HONK")
)

hgcalQuantizedClusterProducer = cms.EDProducer(
    "HGCalQuantizedClusterProducer",
    Multiclusters = cms.InputTag('hgcalBackEndLayer2Producer:HGCalBackendLayer2Processor3DClustering'),
    ProcessorParameters = quantize_proc.clone()
)

