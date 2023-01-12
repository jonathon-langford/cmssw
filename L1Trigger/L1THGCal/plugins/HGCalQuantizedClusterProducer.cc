#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/stream/EDProducer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Utilities/interface/ESGetToken.h"

#include "DataFormats/L1THGCal/interface/HGCalCluster.h"
#include "DataFormats/L1THGCal/interface/HGCalMulticluster.h"

#include "Geometry/Records/interface/CaloGeometryRecord.h"
#include "L1Trigger/L1THGCal/interface/HGCalTriggerGeometryBase.h"

#include "L1Trigger/L1THGCal/interface/HGCalProcessorBase.h"

#include <memory>
#include <utility>

class HGCalQuantizedClusterProducer : public edm::stream::EDProducer<> {
public:
  HGCalQuantizedClusterProducer(const edm::ParameterSet&);
  ~HGCalQuantizedClusterProducer() override {}

  void beginRun(const edm::Run&, const edm::EventSetup&) override;
  void produce(edm::Event&, const edm::EventSetup&) override;

private:
  // inputs
  edm::EDGetToken multiclusters_token_;
  edm::ESHandle<HGCalTriggerGeometryBase> triggerGeometry_;
  edm::ESGetToken<HGCalTriggerGeometryBase, CaloGeometryRecord> triggerGeomToken_;

  std::unique_ptr<HGCalQuantizedClusterProcessorBase> quantizeProcess_;
};

DEFINE_FWK_MODULE(HGCalQuantizedClusterProducer);

HGCalQuantizedClusterProducer::HGCalQuantizedClusterProducer(const edm::ParameterSet& conf) 
    : triggerGeomToken_(esConsumes<HGCalTriggerGeometryBase, CaloGeometryRecord, edm::Transition::BeginRun>()) {

  // Input multicluster token
  multiclusters_token_ = consumes<l1t::HGCalMulticlusterBxCollection>(conf.getParameter<edm::InputTag>("Multiclusters"));

  //setup quantization parameters
  const edm::ParameterSet& quantizeParamConfig = conf.getParameterSet("ProcessorParameters");
  const std::string& quantizeProcessorName = quantizeParamConfig.getParameter<std::string>("ProcessorName");
  quantizeProcess_ = std::unique_ptr<HGCalQuantizedClusterProcessorBase>{
      HGCalQuantizedClusterFactory::get()->create(quantizeProcessorName, quantizeParamConfig)};

  produces<l1t::HGCalMulticlusterBxCollection>(quantizeProcess_->name());
}

void HGCalQuantizedClusterProducer::beginRun(const edm::Run& /*run*/, const edm::EventSetup& es) {
  triggerGeometry_ = es.getHandle(triggerGeomToken_);
  backendProcess_->setGeometry(triggerGeometry_.product());
}

void HGCalQuantizedClusterProducer::produce(edm::Event& e, const edm::EventSetup& es) {

  std::cout << "[HGCalQuantizedClusterProducer] Here" << std::endl;

  // Output collections
  l1t::HGCalMulticlusterBxCollection qmulticlusters_out;

  // Input collection
  edm::Handle<l1t::HGCalMulticlusterBxCollection> multiclusters_in;

  e.getByToken(multiclusters_token_, multiclusters_in);

  // Run quantization module
  quantizeProcess_->run(multiclusters_in, qmulticlusters_out);

  e.put(std::make_unique<l1t::HGCalMulticlusterBxCollection>(std::move(qmulticlusters_out)), quantizeProcess_->name());
}
