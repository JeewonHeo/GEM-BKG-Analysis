// -*- C++ -*-
//
// Package:    gem-background/gemBackground
// Class:      gemBackground
//
/**\class gemBackground gemBackground.cc gem-background/gemBackground/plugins/gemBackground.cc

 Description: [one line class summary]

 Implementation:
     [Notes on implementation]
*/
//
// Original Author:  Master student from University of Seoul
//         Created:  Mon, 03 Oct 2022 08:17:53 GMT
//
//


// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/ConsumesCollector.h"
#include "FWCore/Framework/interface/EventSetup.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "FWCore/ServiceRegistry/interface/Service.h"

#include "FWCore/Utilities/interface/InputTag.h"

#include "CommonTools/UtilAlgos/interface/TFileService.h"

#include "DataFormats/GEMDigi/interface/GEMDigiCollection.h"
#include "DataFormats/GEMDigi/interface/GEMOHStatusCollection.h"
#include "DataFormats/GEMDigi/interface/GEMVFATStatusCollection.h"
#include "DataFormats/GEMRecHit/interface/GEMRecHitCollection.h"
#include "DataFormats/MuonDetId/interface/GEMDetId.h"
#include "DataFormats/OnlineMetaData/interface/OnlineLuminosityRecord.h"
#include "DataFormats/TCDS/interface/TCDSRecord.h"

#include "Geometry/Records/interface/MuonGeometryRecord.h"
#include "Geometry/GEMGeometry/interface/GEMGeometry.h"

#include "FWCore/Framework/interface/ESHandle.h"
#include "FWCore/Framework/interface/Run.h"

#include "TFile.h"
#include "TH1D.h"
#include "TH2D.h"
#include "TTree.h"

// class declaration
//

// If the analyzer does not use TFileService, please remove
// the template argument to the base class so the class inherits
// from  edm::one::EDAnalyzer<>
// This will improve performance in multithreaded jobs.


constexpr size_t max_trigger = 16;
typedef std::tuple<int, int> Key2;

class gemBackground : public edm::one::EDAnalyzer<> {
public:
  explicit gemBackground(const edm::ParameterSet&);
  ~gemBackground() override;

  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

private:
  bool maskChamberWithError(const GEMDetId& chamber_id, const edm::Handle<GEMVFATStatusCollection>, const edm::Handle<GEMOHStatusCollection>);
  virtual void analyze(const edm::Event&, const edm::EventSetup&) override;
  virtual void beginJob() override;
  virtual void endJob() override;

  // ----------member data ---------------------------
  edm::EDGetTokenT<GEMOHStatusCollection> oh_status_collection_;
  edm::EDGetTokenT<GEMVFATStatusCollection> vfat_status_collection_;
  edm::EDGetTokenT<GEMRecHitCollection> gemRecHits_;
  edm::EDGetTokenT<OnlineLuminosityRecord> onlineLumiRecord_;
  edm::ESGetToken<GEMGeometry, MuonGeometryRecord> hGEMGeom_;
  edm::EDGetTokenT<TCDSRecord> tcdsRecord_;

  TH1D* n_event_;
  // TH2D* bad_chamber_PL1_;
  // TH2D* bad_chamber_PL2_;
  // TH2D* bad_chamber_ML1_;
  // TH2D* bad_chamber_ML2_;
  edm::Service<TFileService> fs_;

  TTree *t_rec_hits;
  float b_instLumi;
  long b_event, b_eventTime;
  int b_bunchId, b_orbitNumber;
  int b_region, b_layer, b_chamber, b_ieta, b_chamber_error;
  int b_first_strip, b_cluster_size;
  int b_big_cluster_event;
};

gemBackground::gemBackground(const edm::ParameterSet& iConfig)
  : hGEMGeom_(esConsumes()) {
  oh_status_collection_ = consumes<GEMOHStatusCollection>(iConfig.getParameter<edm::InputTag>("OHInputLabel"));
  vfat_status_collection_ = consumes<GEMVFATStatusCollection>(iConfig.getParameter<edm::InputTag>("VFATInputLabel"));
  gemRecHits_ = consumes<GEMRecHitCollection>(iConfig.getParameter<edm::InputTag>("gemRecHits"));
  onlineLumiRecord_ = consumes<OnlineLuminosityRecord>(iConfig.getParameter<edm::InputTag>("onlineMetaDataDigis"));
  tcdsRecord_ = consumes<TCDSRecord>(iConfig.getParameter<edm::InputTag>("tcdsRecord"));

  t_rec_hits = fs_->make<TTree>("rec_hits", "gem_rec_hits");
  #define BRANCH_(name, suffix) t_rec_hits->Branch(#name, & b_##name, #name "/" #suffix);
  BRANCH_(instLumi, F);
  BRANCH_(event, l);
  BRANCH_(eventTime, l);
  BRANCH_(bunchId, I);
  BRANCH_(orbitNumber, I);
  BRANCH_(region, I);
  BRANCH_(layer, I);
  BRANCH_(chamber, I);
  BRANCH_(ieta, I);
  BRANCH_(first_strip, I);
  BRANCH_(cluster_size, I);
  BRANCH_(chamber_error, I);
  BRANCH_(big_cluster_event, I);
}

gemBackground::~gemBackground() {
  // do anything here that needs to be done at desctruction time
  // (e.g. close files, deallocate resources etc.)
  //
  // please remove this method altogether if it would be left empty
}

//
// member functions
//

bool gemBackground::maskChamberWithError(const GEMDetId& chamber_id,
                                         const edm::Handle<GEMVFATStatusCollection> vfat_status_collection,
                                         const edm::Handle<GEMOHStatusCollection> oh_status_collection) {
  const bool mask = true;
  for (auto iter = oh_status_collection->begin(); iter != oh_status_collection->end(); iter++) {
    const auto [oh_id, range] = (*iter);
    if (chamber_id != oh_id) {
      continue;
    }

    for (auto oh_status = range.first; oh_status != range.second; oh_status++) {
      if (oh_status->isBad()) {
        // GEMOHStatus is bad. Mask this chamber.
        return mask;
      }  // isBad
    }  // range
  }  // collection
  for (auto iter = vfat_status_collection->begin(); iter != vfat_status_collection->end(); iter++) {
    const auto [vfat_id, range] = (*iter);
    if (chamber_id != vfat_id.chamberId()) {
      continue;
    }
    for (auto vfat_status = range.first; vfat_status != range.second; vfat_status++) {
      if (vfat_status->isBad()) {
        return mask;
      }  // isBad
    }  // range
  }  // collection
  return not mask;
}


// ------------ method called for each event  ------------
void gemBackground::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup) {
  edm::ESHandle<GEMGeometry> hGEMGeom;
  hGEMGeom = iSetup.getHandle(hGEMGeom_);
  const GEMGeometry* GEMGeometry_ = &*hGEMGeom;

  edm::Handle<GEMRecHitCollection> gemRecHits;
  iEvent.getByToken(gemRecHits_, gemRecHits);

  edm::Handle<GEMVFATStatusCollection> vfat_status_collection;
  iEvent.getByToken(vfat_status_collection_, vfat_status_collection);

  edm::Handle<GEMOHStatusCollection> oh_status_collection;
  iEvent.getByToken(oh_status_collection_, oh_status_collection);

  edm::Handle<OnlineLuminosityRecord> onlineLumiRecord;
  iEvent.getByToken(onlineLumiRecord_, onlineLumiRecord);

  edm::Handle<TCDSRecord> record;
  iEvent.getByToken(tcdsRecord_, record);

  if (!record.isValid() || !gemRecHits.isValid()) {
    std::cout << "Error!" << std::endl;
    return;
  }
  n_event_->Fill(0);

  // float n_clusters = 0;
  // float n_hits = 0;
  // std::vector<std::vector<int>> n_hits_each_chamber(8, std::vector<int>(36, 0)); // giving max nDigis in one chamber
  std::vector<std::vector<int>> n_hits_each_etaPart(8, std::vector<int>(576, 0)); // giving max nDigis in one etaPartition

  for (const GEMRecHit& cluster : *gemRecHits) {
    // ++n_clusters;
    GEMDetId hit_id = cluster.gemId();
    int layer_index = (hit_id.region()+1)/2 + 2*(hit_id.station()-1) + 4*(hit_id.layer()-1);
    // n_hits = cluster.clusterSize();
    // n_hits_each_chamber[layer_index][hit_id.chamber() - 1] += n_hits;
    int eta_index = 16 * (hit_id.chamber() - 1) + hit_id.ieta() - 1;
    n_hits_each_etaPart[layer_index][eta_index] += cluster.clusterSize();
  }

  /*  we don't want to use hit based cut
  if ((n_clusters > 650.) || ((n_clusters - 50.) * (2000. / 600.) > n_hits)) {
    return;
   }
  */

  /* W.Heo's flower event cut
  int max_val = *std::max_element(n_hits_each_chamber[0].begin(),n_hits_each_chamber[0].end());
  for (const auto& row : n_hits_each_chamber) {
    max_val = std::max(max_val, *std::max_element(row.begin(), row.end()));
    if (max_val > 384) return;
  }
  */
  b_big_cluster_event = 0;
  int max_val;
  // for (const auto& row : n_hits_each_chamber) {
  for (const auto& row : n_hits_each_etaPart) {
    max_val = *std::max_element(row.begin(), row.end());
    // if (max_val > 384) return; // big cluster event filter
    if (max_val > 48) {
      b_big_cluster_event = 1; // big cluster event filter
    }
  }


  /*  Laurant's method */
  for (size_t i = 0; i < max_trigger; ++i) {
    long l1a_diff = 3564 * (record->getOrbitNr() - record->getL1aHistoryEntry(i).getOrbitNr())
        + record->getBXID() - record->getL1aHistoryEntry(i).getBXID();

    if ((l1a_diff > 150) && (l1a_diff < 200)) {
      std::cout << "Flower event!!!" << std::endl;
      return;
    }
  }
  /**/
  n_event_->Fill(1);

  b_instLumi = onlineLumiRecord->instLumi();
  b_bunchId = iEvent.bunchCrossing();
  b_orbitNumber = iEvent.orbitNumber();
  b_eventTime = iEvent.time().unixTime();
  b_event = iEvent.id().event();

  for (auto chamber: GEMGeometry_->chambers()) {
    GEMDetId chamber_id = chamber->id();
    if (chamber_id.station() != 1)
      continue;
    /* disabled to keep bad chambers with flag
    if (maskChamberWithError(chamber_id, vfat_status_collection, oh_status_collection)) {
      b_region = chamber_id.region();
      b_layer = chamber_id.layer();
      b_chamber = chamber_id.chamber();
      if (b_region == -1) {
        if (b_layer == 1) bad_chamber_ML1_->Fill(b_chamber, b_instLumi);
        if (b_layer == 2) bad_chamber_ML2_->Fill(b_chamber, b_instLumi);
      } else {
        if (b_layer == 1) bad_chamber_PL1_->Fill(b_chamber, b_instLumi);
        if (b_layer == 2) bad_chamber_PL2_->Fill(b_chamber, b_instLumi);
      }
      continue;
    }
    */
    b_chamber_error = maskChamberWithError(chamber_id, vfat_status_collection, oh_status_collection);
    for (auto eta_part: chamber->etaPartitions()) {
      GEMDetId eta_part_id = eta_part->id();
      b_region = eta_part_id.region();
      b_layer = eta_part_id.layer();
      b_chamber = eta_part_id.chamber();
      b_ieta = eta_part_id.ieta();
      auto range = gemRecHits->get(eta_part_id);
      for (auto rechit = range.first; rechit != range.second; ++rechit) {
        b_first_strip = rechit->firstClusterStrip();
        b_cluster_size = rechit->clusterSize();
        t_rec_hits->Fill();
      }  // hits
    }  // eta partition
  }  // chambers
}


// ------------ method called once each job just before starting event loop  ------------
void gemBackground::beginJob() {
  n_event_ = fs_->make<TH1D>("events", "Events", 2, -0.5, 1.5);
  // bad_chamber_PL1_ = fs_->make<TH2D>("bad_chamber_PL1", "bad chamber GE1/1-L1",
  //                                    36, 0.5, 36.5,
  //                                    30, 0, 30000);
  // bad_chamber_PL2_ = fs_->make<TH2D>("bad_chamber_PL2", "bad chamber GE1/1-L2",
  //                                    36, 0.5, 36.5,
  //                                    30, 0, 30000);
  // bad_chamber_ML1_ = fs_->make<TH2D>("bad_chamber_ML1", "bad chamber GE-1/1-L1",
  //                                    36, 0.5, 36.5,
  //                                    30, 0, 30000);
  // bad_chamber_ML2_ = fs_->make<TH2D>("bad_chamber_ML2", "bad chamber GE-1/1-L2",
  //                                    36, 0.5, 36.5,
  //                                    30, 0, 30000);
}

// ------------ method called once each job just after ending the event loop  ------------
void gemBackground::endJob() {
}

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void gemBackground::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);

  //Specify that only 'tracks' is allowed
  //To use, remove the default given above and uncomment below
  //ParameterSetDescription desc;
  //desc.addUntracked<edm::InputTag>("tracks","ctfWithMaterialTracks");
  //descriptions.addWithDefaultLabel(desc);
}

//define this as a plug-in
DEFINE_FWK_MODULE(gemBackground);
