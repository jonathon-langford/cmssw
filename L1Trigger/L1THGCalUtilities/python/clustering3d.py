import FWCore.ParameterSet.Config as cms

binSums = cms.vuint32(13,               #0
                      11, 11, 11,       # 1 - 3
                      9, 9, 9,          # 4 - 6
                      7, 7, 7, 7, 7, 7, # 7 - 12
                      5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,  # 13 - 27
                      3, 3, 3, 3, 3, 3, 3, 3  # 28 - 35
                      )


def create_distance(process, inputs,
        distance=0.01
        ):
    producer = process.hgcalBackEndLayer2Producer.clone() 
    producer.ProcessorParameters.C3d_parameters.dR_multicluster = cms.double(distance)
    producer.ProcessorParameters.C3d_parameters.type_multicluster = cms.string('dRC3d')
    producer.InputCluster = cms.InputTag('{}:HGCalBackendLayer1Processor2DClustering'.format(inputs))
    return producer


def create_dbscan(process, inputs,
        distance=0.005,
        min_points=3
        ):
    producer = process.hgcalBackEndLayer2Producer.clone() 
    producer.ProcessorParameters.C3d_parameters.dist_dbscan_multicluster = cms.double(distance)
    producer.ProcessorParameters.C3d_parameters.minN_dbscan_multicluster = cms.uint32(min_points)
    producer.ProcessorParameters.C3d_parameters.type_multicluster = cms.string('DBSCANC3d')
    producer.InputCluster = cms.InputTag('{}:HGCalBackendLayer1Processor2DClustering'.format(inputs))
    return producer


def create_histoMax(process, inputs,
        distance = 0.01,
        nBins_R = 36,
        nBins_Phi = 216,
        binSumsHisto = binSums,                        
        ):
    producer = process.hgcalBackEndLayer2Producer.clone() 
    producer.ProcessorParameters.C3d_parameters.dR_multicluster = cms.double(distance)
    producer.ProcessorParameters.C3d_parameters.nBins_R_histo_multicluster = cms.uint32(nBins_R)
    producer.ProcessorParameters.C3d_parameters.nBins_Phi_histo_multicluster = cms.uint32(nBins_Phi)
    producer.ProcessorParameters.C3d_parameters.binSumsHisto = binSumsHisto
    producer.ProcessorParameters.C3d_parameters.type_multicluster = cms.string('HistoMaxC3d')
    producer.InputCluster = cms.InputTag('{}:HGCalBackendLayer1Processor2DClustering'.format(inputs))
    return producer


def create_histoInterpolatedMax(process, inputs,
        distance = 0.01,
        nBins_R = 36,
        nBins_Phi = 216,
        binSumsHisto = binSums,
        ):
    producer = create_histoMax( process, distance, nBins_R, nBins_Phi, binSumsHisto )    
    producer.ProcessorParameters.C3d_parameters.type_multicluster = cms.string('HistoInterpolatedMaxC3d')
    return producer

def create_histoInterpolatedMax1stOrder(process, inputs):
    producer = custom_3dclustering_histoInterpolatedMax( process )    
    producer.ProcessorParameters.C3d_parameters.neighbour_weights=cms.vdouble(  0    , 0.25, 0   ,
                                                   0.25 , 0   , 0.25,
                                                   0    , 0.25, 0
                                                )
    return producer



def create_histoInterpolatedMax2ndOrder(process, inputs):
    producer = custom_3dclustering_histoInterpolatedMax( process )    
    producer.ProcessorParameters.C3d_parameters.neighbour_weights=cms.vdouble( -0.25, 0.5, -0.25,
                                                   0.5 , 0  ,  0.5 ,
                                                  -0.25, 0.5, -0.25
                                                )
    return producer



def create_histoThreshold(process, inputs,
        threshold = 20.,
        distance = 0.01,
        nBins_R = 36,
        nBins_Phi = 216,
        binSumsHisto = binSums,
        ):
    producer = process.hgcalBackEndLayer2Producer.clone() 
    producer.ProcessorParameters.C3d_parameters.threshold_histo_multicluster = cms.double(threshold)
    producer.ProcessorParameters.C3d_parameters.dR_multicluster = cms.double(distance)
    producer.ProcessorParameters.C3d_parameters.nBins_R_histo_multicluster = cms.uint32(nBins_R)
    producer.ProcessorParameters.C3d_parameters.nBins_Phi_histo_multicluster = cms.uint32(nBins_Phi)
    producer.ProcessorParameters.C3d_parameters.binSumsHisto = binSumsHisto
    producer.ProcessorParameters.C3d_parameters.type_multicluster = cms.string('HistoThresholdC3d')
    producer.InputCluster = cms.InputTag('{}:HGCalBackendLayer1Processor2DClustering'.format(inputs))
    return producer
