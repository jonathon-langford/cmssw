#include "L1Trigger/L1THGCal/interface/HGCalProcessorBase.h"

#include "DataFormats/L1THGCal/interface/HGCalCluster.h"
#include "DataFormats/L1THGCal/interface/HGCalMulticluster.h"

#include <utility>

class HGCalQuantizedClusterProcessor : public HGCalQuantizedClusterProcessorBase {
public:
  HGCalQuantizedClusterProcessor(const edm::ParameterSet& conf) : HGCalQuantizedClusterProcessorBase(conf) {
    randomString = conf.getParameter<std::string>("RandomString");
  }

  void run(const edm::Handle<l1t::HGCalMulticlusterBxCollection>& collHandle,
           l1t::HGCalMulticlusterBxCollection& qcluster_output) override {

    /* create a persistent vector of pointers to the input clusters */
    std::vector<edm::Ptr<l1t::HGCalMulticluster>> multiclusters_in;
    for (unsigned i = 0; i < collHandle->size(); ++i) {
      edm::Ptr<l1t::HGCalMulticluster> ptr(collHandle, i);
      multiclusters_in.push_back(ptr);
    }

    // DEBUG: Output random string to check if in processor
    std::cout << "[HGCalQuantizedClusterProcessor] " << randomString << std::endl;

    for (auto& multicluster : multiclusters_in) {
      // Do processing here
      qcluster_output.push_back(0, *multicluster);
    }
  }

private:
  std::string randomString;
};

DEFINE_EDM_PLUGIN(HGCalQuantizedClusterFactory,
                  HGCalQuantizedClusterProcessor,
                  "HGCalQuantizedClusterProcessor");
