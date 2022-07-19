#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "L1Trigger/L1THGCal/interface/HGCalAlgoWrapperBase.h"

#include "DataFormats/L1THGCal/interface/HGCalCluster.h"
#include "DataFormats/L1THGCal/interface/HGCalMulticluster.h"

#include "L1Trigger/L1THGCal/interface/backend_emulator/HGCalHistoClusteringImpl_SA.h"
#include "L1Trigger/L1THGCal/interface/backend_emulator/HGCalHistoClusteringConfig_SA.h"
#include "L1Trigger/L1THGCal/interface/backend_emulator/HGCalTriggerCell_SA.h"
#include "L1Trigger/L1THGCal/interface/backend_emulator/HGCalCluster_SA.h"
#include "DataFormats/ForwardDetId/interface/HGCalTriggerBackendDetId.h"

#include "FWCore/MessageLogger/interface/MessageLogger.h"

#include "Geometry/Records/interface/CaloGeometryRecord.h"
#include "L1Trigger/L1THGCal/interface/HGCalTriggerGeometryBase.h"
#include "L1Trigger/L1THGCal/interface/HGCalTriggerTools.h"

class HGCalHistoClusteringWrapper : public HGCalHistoClusteringWrapperBase {
public:
  HGCalHistoClusteringWrapper(const edm::ParameterSet& conf);
  ~HGCalHistoClusteringWrapper() override {}

  void configure(
      const std::tuple<const HGCalTriggerGeometryBase* const, const edm::ParameterSet&, const unsigned int, const int>& configuration) override;

  void process(const std::vector<std::vector<edm::Ptr<l1t::HGCalCluster>>>& inputClusters,
               std::pair<l1t::HGCalMulticlusterBxCollection&, l1t::HGCalClusterBxCollection&>&
                   outputMulticlustersAndRejectedClusters) const override;

private:
  void convertCMSSWInputs(const std::vector<std::vector<edm::Ptr<l1t::HGCalCluster>>>& clustersPtrs,
                          l1thgcfirmware::HGCalTriggerCellSAPtrCollections& clusters_SA) const;
  void convertAlgorithmOutputs( l1thgcfirmware::HGCalClusterSAPtrCollection& clusterSums, l1thgcfirmware::HGCalTriggerCellSAPtrCollection& unclusteredTCs, l1t::HGCalMulticlusterBxCollection& multiClusters_out, const std::vector<std::vector<edm::Ptr<l1t::HGCalCluster>>>& inputClustersPtrs ) const;

  void clusterizeHisto( l1thgcfirmware::HGCalTriggerCellSAPtrCollections& triggerCells_in_SA, l1thgcfirmware::HGCalTriggerCellSAPtrCollection& clusteredTCs, l1thgcfirmware::HGCalTriggerCellSAPtrCollection& unclusteredTCs, l1thgcfirmware::CentroidHelperPtrCollection& prioritizedMaxima, l1thgcfirmware::CentroidHelperPtrCollection& readoutFlags,
  l1thgcfirmware::HGCalClusterSAPtrCollection& clusterSums ) const;

  void setGeometry(const HGCalTriggerGeometryBase* const geom) { triggerTools_.setGeometry(geom); }

  HGCalTriggerTools triggerTools_;

  l1thgcfirmware::ClusterAlgoConfig theConfiguration_;

  l1thgcfirmware::HGCalHistoClusteringImplSA theAlgo_;

  edm::ESHandle<HGCalTriggerGeometryBase> triggerGeometry_;
};

HGCalHistoClusteringWrapper::HGCalHistoClusteringWrapper(const edm::ParameterSet& conf)
    : HGCalHistoClusteringWrapperBase(conf),
      theConfiguration_(),
      theAlgo_(theConfiguration_) {}

void HGCalHistoClusteringWrapper::convertCMSSWInputs(const std::vector<std::vector<edm::Ptr<l1t::HGCalCluster>>>& clustersPtrs, l1thgcfirmware::HGCalTriggerCellSAPtrCollections& clusters_SA ) const {

  // Convert trigger cells to format required by emulator
  l1thgcfirmware::HGCalTriggerCellSAPtrCollections clusters_SA_perSector60(3, l1thgcfirmware::HGCalTriggerCellSAPtrCollection() );
  unsigned iSector60 = 0;

  for (const auto& sector60 : clustersPtrs) {
    unsigned iCluster = 0;
    for (const auto& cluster : sector60) {
      const GlobalPoint& position = cluster->position();
      double x = position.x();
      double y = position.y();
      double z = position.z();
      unsigned int digi_rOverZ = ( std::sqrt(x * x + y * y) / std::abs(z) ) * theConfiguration_.rOverZNValues()/ theConfiguration_.rOverZRange();

      if (z > 0)
        x = -x;
      double phi = std::atan2(y, x);
      // Rotate phi to sector 0
      auto sector = theConfiguration_.sector();
      if (sector == 1) {
        if (phi < M_PI and phi > 0)
          phi = phi - (2. * M_PI / 3.);
        else
          phi = phi + (4. * M_PI / 3.);
      } else if (sector == 2) {
        phi = phi + (2. * M_PI / 3.);
      }

      // Ignore TCs that are outside of the nominal 180 degree S2 sector
      // Assume these cannot be part of a cluster found within the central 120 degrees of the S2 sector?
      if ( phi < 0 || phi > M_PI ) {
        continue;
      }

      unsigned int digi_phi = ( phi ) * theConfiguration_.phiNValues() / theConfiguration_.phiRange();
      unsigned int digi_energy = ( cluster->pt() ) * theConfiguration_.ptDigiFactor();

      // The existing S2 firmware is assuming the TCs on one S1->S2 link originate from
      // a 60 degree region of a S1 sector, and the links from one 60 degree region
      // are grouped together (the first 24 links are for 0-60 degrees etc. )
      // But some of the TCs in the S1 emulation fall outside of the 60 degree region
      // For now, assign these TCs to the 60 degree sector that the S2 emulation is expecting them to be in.
      unsigned tcSector60 = iSector60;
      unsigned int minSectorPhi = iSector60 * 648;
      unsigned int maxSectorPhi = (iSector60 + 1) * 648;
      if ( digi_phi < minSectorPhi ) {
        tcSector60 -= 1;
      }
      else if ( digi_phi > maxSectorPhi ) {
        tcSector60 += 1;
      }

      clusters_SA_perSector60[tcSector60].emplace_back( 
                                            std::make_shared<l1thgcfirmware::HGCalTriggerCell>(
                                              true,
                                              true,
                                              digi_rOverZ,
                                              digi_phi,
                                              triggerTools_.layerWithOffset(cluster->detId()),
                                              digi_energy
                                          ) );
      clusters_SA_perSector60[tcSector60].back()->setCmsswIndex( std::pair<int, int>{iSector60, iCluster} );
      ++iCluster;
    }
    ++iSector60;
  }

  // Distribute trigger cells to links and frames
  // Current firmware expects trigger cells from each S1 FPGA are ordered by r/z in time (r/z increase with frame number), and links from same 60 degree sector are grouped together
  // As first (optimistic) step, all trigger cells within a 60 degree sector are combined and sorted in r/z
  // Ultimately, links/ordering in time should come from S1 emulation
  // Sort by r/z in each 60 degree sector
  for (auto& clusters : clusters_SA_perSector60) {
    std::sort(clusters.begin(), clusters.end(), [](l1thgcfirmware::HGCalTriggerCellSAPtr a, l1thgcfirmware::HGCalTriggerCellSAPtr b) { return a->rOverZ()<b->rOverZ(); });
  }

  // Distribute to links
  clusters_SA.clear();
  clusters_SA.resize( 212, l1thgcfirmware::HGCalTriggerCellSAPtrCollection() ); // Magic numbers
  for ( auto& clusters : clusters_SA ) {
    clusters.resize(72, l1thgcfirmware::HGCalTriggerCellSAPtr( std::make_shared<l1thgcfirmware::HGCalTriggerCell>() ) ); // Magic numbers
  }
  iSector60 = 0;
  for (const auto& sector60 : clusters_SA_perSector60) {
    unsigned iCluster = 0;
    for ( const auto& cluster : sector60 ) {
      // Leave first two frames empty
      unsigned frame = 2 + iCluster / 24; // Magic numbers
      unsigned link = iCluster % 24 + iSector60 * 24; // Magic numbers
      if ( frame >= 212 ) break; // Magic numbers
      clusters_SA[frame][link] = cluster;
      ++iCluster;
    }
    ++iSector60;
  }
}

void HGCalHistoClusteringWrapper::convertAlgorithmOutputs( l1thgcfirmware::HGCalClusterSAPtrCollection& clusterSums, l1thgcfirmware::HGCalTriggerCellSAPtrCollection& unclusteredTCs,
l1t::HGCalMulticlusterBxCollection& multiClusters_out, const std::vector<std::vector<edm::Ptr<l1t::HGCalCluster>>>& inputClustersPtrs
 ) const {
  for ( const auto& cluster : clusterSums ) {

    // Convert from digitised quantities
    if ( cluster->w() == 0 || cluster->e() == 0 ) continue;
    double phi = ( cluster->wphi() / cluster->w() ) * theConfiguration_.phiRange() / theConfiguration_.phiNValues();
    double pt = cluster->e() / theConfiguration_.ptDigiFactor();

    if ( pt < 0.5 ) continue; // Add (or take) cut threshold to config

    double rOverZ = ( cluster->wroz() / cluster->w() ) * theConfiguration_.rOverZRange() / theConfiguration_.rOverZNValues();
    double eta = -1.0 * std::log( tan( atan( rOverZ ) / 2 ) );
    eta *= theConfiguration_.zSide();

    auto sector = theConfiguration_.sector();
    if (sector == 1) {
      phi += (2. * M_PI / 3.);
    } else if (sector == 2) {
      phi = phi + (4. * M_PI / 3.);
    }
    if ( theConfiguration_.zSide() == 1 ) {
      phi = M_PI - phi;
    }
    phi -= ( phi > M_PI ) ? 2 * M_PI : 0;

    math::PtEtaPhiMLorentzVector clusterP4(pt, eta, phi, 0.);

    l1t::HGCalMulticluster multicluster;
    multicluster.setP4(clusterP4);
    // std::cout << "Got a cluster : " << cluster->e() << " " << cluster->constituents().size() << " " << multicluster.pt() << " " << multicluster.eta() << " " << multicluster.phi()  << " " << rOverZ << " " << phi << " " << eta << std::endl;
    for ( const auto& tc : cluster->constituents() ) {
      const auto& tc_cmssw = inputClustersPtrs.at(tc->cmsswIndex().first).at(tc->cmsswIndex().second);
      // Add tc as constituent, but don't update any other properties of the multicluster i.e. leave them unchanged from those calculated by the emulator
      multicluster.addConstituent( tc_cmssw, false, 0. );
    }

    double emIntFraction = 1.0 * cluster->e_em() / cluster->e();
    multicluster.saveEnergyInterpretation(l1t::HGCalMulticluster::EnergyInterpretation::EM, emIntFraction * multicluster.energy() );

    double emCoreIntFraction = 1.0 * cluster->e_em_core() / cluster->e();
    multicluster.saveEnergyInterpretation(l1t::HGCalMulticluster::EnergyInterpretation::EM_CORE, emCoreIntFraction * multicluster.energy() );

    double emHEarlyIntFraction = 1.0 * cluster->e_h_early() / cluster->e();
    multicluster.saveEnergyInterpretation(l1t::HGCalMulticluster::EnergyInterpretation::H_EARLY, emHEarlyIntFraction * multicluster.energy() );

    multiClusters_out.push_back(0, multicluster);

    // Set cluster shower shape properties
    multicluster.showerLength( cluster->ShowerLen() );
    multicluster.coreShowerLength( cluster->CoreShowerLen() );
    multicluster.firstLayer( cluster->FirstLayer() );
    multicluster.Sigma_E_Quotient( cluster->Sigma_E_Quotient() );
    multicluster.Sigma_E_Fraction( cluster->Sigma_E_Fraction() );
    multicluster.Mean_z_Quotient( cluster->Mean_z_Quotient() );
    multicluster.Mean_z_Fraction( cluster->Mean_z_Fraction() );
    multicluster.Mean_phi_Quotient( cluster->Mean_phi_Quotient() );
    multicluster.Mean_phi_Fraction( cluster->Mean_phi_Fraction() );
    multicluster.Mean_eta_Quotient( cluster->Mean_eta_Quotient() );
    multicluster.Mean_eta_Fraction( cluster->Mean_eta_Fraction() );
    multicluster.Mean_roz_Quotient( cluster->Mean_roz_Quotient() );
    multicluster.Mean_roz_Fraction( cluster->Mean_roz_Fraction() );
    multicluster.Sigma_z_Quotient( cluster->Sigma_z_Quotient() );
    multicluster.Sigma_z_Fraction( cluster->Sigma_z_Fraction() );
    multicluster.Sigma_phi_Quotient( cluster->Sigma_phi_Quotient() );
    multicluster.Sigma_phi_Fraction( cluster->Sigma_phi_Fraction() );
    multicluster.Sigma_eta_Quotient( cluster->Sigma_eta_Quotient() );
    multicluster.Sigma_eta_Fraction( cluster->Sigma_eta_Fraction() );
    multicluster.Sigma_roz_Quotient( cluster->Sigma_roz_Quotient() );
    multicluster.Sigma_roz_Fraction( cluster->Sigma_roz_Fraction() );
    multicluster.E_EM_over_E_Quotient( cluster->E_EM_over_E_Quotient() );
    multicluster.E_EM_over_E_Fraction( cluster->E_EM_over_E_Fraction() );
    multicluster.E_EM_core_over_E_EM_Quotient( cluster->E_EM_core_over_E_EM_Quotient() );
    multicluster.E_EM_core_over_E_EM_Fraction( cluster->E_EM_core_over_E_EM_Fraction() );
    multicluster.E_H_early_over_E_Quotient( cluster->E_H_early_over_E_Quotient() );
    multicluster.E_H_early_over_E_Fraction( cluster->E_H_early_over_E_Fraction() );
  }
}

void HGCalHistoClusteringWrapper::process(
    const std::vector<std::vector<edm::Ptr<l1t::HGCalCluster>>>&
        inputClusters,
    std::pair<l1t::HGCalMulticlusterBxCollection&, l1t::HGCalClusterBxCollection&>&
        outputMulticlustersAndRejectedClusters) const {

  l1thgcfirmware::HGCalTriggerCellSAPtrCollections triggerCells_in_SA;
  convertCMSSWInputs(inputClusters, triggerCells_in_SA);

  l1thgcfirmware::HGCalTriggerCellSAPtrCollection clusteredTCs_out_SA;
  l1thgcfirmware::HGCalTriggerCellSAPtrCollection unclusteredTCs_out_SA;
  l1thgcfirmware::CentroidHelperPtrCollection prioritizedMaxima_out_SA;
  l1thgcfirmware::CentroidHelperPtrCollection readoutFlags_out_SA;
  l1thgcfirmware::HGCalClusterSAPtrCollection clusterSums_out_SA;
  clusterizeHisto(triggerCells_in_SA, clusteredTCs_out_SA, unclusteredTCs_out_SA, prioritizedMaxima_out_SA, readoutFlags_out_SA, clusterSums_out_SA);
  
  convertAlgorithmOutputs( clusterSums_out_SA, unclusteredTCs_out_SA, outputMulticlustersAndRejectedClusters.first, inputClusters );
}

void HGCalHistoClusteringWrapper::clusterizeHisto( l1thgcfirmware::HGCalTriggerCellSAPtrCollections& triggerCells_in_SA, l1thgcfirmware::HGCalTriggerCellSAPtrCollection& clusteredTCs, l1thgcfirmware::HGCalTriggerCellSAPtrCollection& unclusteredTCs, l1thgcfirmware::CentroidHelperPtrCollection& prioritizedMaxima, l1thgcfirmware::CentroidHelperPtrCollection& readoutFlags, l1thgcfirmware::HGCalClusterSAPtrCollection& clusterSums ) const {

  theAlgo_.runAlgorithm( triggerCells_in_SA, clusteredTCs, unclusteredTCs, prioritizedMaxima, readoutFlags, clusterSums );
}

void HGCalHistoClusteringWrapper::configure(
    const std::tuple<const HGCalTriggerGeometryBase* const, const edm::ParameterSet&, const unsigned int, const int>& configuration) {
  setGeometry(std::get<0>(configuration));

  theConfiguration_.setSector( std::get<2>(configuration) );
  theConfiguration_.setZSide( std::get<3>(configuration) );

  const edm::ParameterSet pset = std::get<1>(configuration).getParameterSet("C3d_parameters").getParameterSet("histoMax_C3d_clustering_parameters").getParameterSet("layer2FwClusteringParameters");

  theConfiguration_.setVariablePhiWidth( pset.getParameter<bool>("variablePhiWidth"));
  theConfiguration_.setClusterizerOffset( pset.getParameter<unsigned int>("clusterizerOffset"));
  theConfiguration_.setStepLatencies( pset.getParameter<std::vector<unsigned int>>("stepLatencies"));
  theConfiguration_.setCClocks( pset.getParameter<unsigned int>("cClocks") );
  theConfiguration_.setCInputs( pset.getParameter<unsigned int>("cInputs") );
  theConfiguration_.setCInputs2( pset.getParameter<unsigned int>("cInputs2") );
  theConfiguration_.setCInt( pset.getParameter<unsigned int>("cInt") );
  theConfiguration_.setCColumns( pset.getParameter<unsigned int>("cColumns") );
  theConfiguration_.setCRows( pset.getParameter<unsigned int>("cRows") );
  theConfiguration_.setROverZHistOffset( pset.getParameter<unsigned int>("rOverZHistOffset") );
  theConfiguration_.setROverZBinSize( pset.getParameter<unsigned int>("rOverZBinSize") );
  theConfiguration_.setClusterizerMagicTime( pset.getParameter<unsigned int>("clusterizerMagicTime") );
  theConfiguration_.setNBinsCosLUT( pset.getParameter<unsigned int>("nBinsCosLUT") );
  theConfiguration_.setDepths( pset.getParameter<std::vector<unsigned int>>("depths"));
  theConfiguration_.setTriggerLayers( pset.getParameter<std::vector<unsigned int>>("triggerLayers"));
  theConfiguration_.setLayerWeights_E( pset.getParameter<std::vector<unsigned int>>("layerWeights_E"));
  theConfiguration_.setLayerWeights_E_EM( pset.getParameter<std::vector<unsigned int>>("layerWeights_E_EM"));
  theConfiguration_.setLayerWeights_E_EM_core( pset.getParameter<std::vector<unsigned int>>("layerWeights_E_EM_core"));
  theConfiguration_.setLayerWeights_E_H_early( pset.getParameter<std::vector<unsigned int>>("layerWeights_E_H_early"));
  theConfiguration_.setCorrection( pset.getParameter<unsigned int>("correction") );
  theConfiguration_.setSaturation( pset.getParameter<unsigned int>("saturation") );
  const edm::ParameterSet thresholdParams = pset.getParameterSet("thresholdMaximaParams");
  theConfiguration_.setThresholdParams( thresholdParams.getParameter<unsigned int>("a"), thresholdParams.getParameter<unsigned int>("b"), thresholdParams.getParameter<int>("c") );
  theConfiguration_.initializeLUTs();

  // const edm::ParameterSet digitizationPset = pset.getParameterSet("digiParams");
  const edm::ParameterSet digitizationPset = std::get<1>(configuration).getParameterSet("C3d_parameters").getParameterSet("histoMax_C3d_clustering_parameters").getParameterSet("layer2FwClusteringParameters").getParameterSet("digiParams");

  theConfiguration_.setROverZRange( digitizationPset.getParameter<double>("rOverZRange"));
  theConfiguration_.setROverZNValues( digitizationPset.getParameter<double>("rOverZNValues"));
  theConfiguration_.setPhiRange( digitizationPset.getParameter<double>("phiRange"));
  theConfiguration_.setPhiNValues( digitizationPset.getParameter<double>("phiNValues"));
  theConfiguration_.setPtDigiFactor( digitizationPset.getParameter<double>("ptDigiFactor"));
  

};

DEFINE_EDM_PLUGIN(HGCalHistoClusteringWrapperBaseFactory, HGCalHistoClusteringWrapper, "HGCalHistoClusteringWrapper");
