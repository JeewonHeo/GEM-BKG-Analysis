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
typedef std::tuple<int, int, int, int, int> Key5;

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
  edm::Service<TFileService> fs_;

  TTree *t_rec_hits;
  float b_instLumi;
  long b_event, b_eventTime;
  int b_bunchId, b_orbitNumber;
  int b_region, b_layer, b_chamber, b_ieta, b_chamber_error;
  int b_first_strip, b_cluster_size;
  int b_flower_event;
  int b_big_cluster_event;
  // uint32_t b_missing_vfat;
  uint32_t b_zsMask;
  uint32_t b_existVFATs;
  std::map<Key5, long> n_hits_each_eta;
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
  BRANCH_(flower_event, I);
  // BRANCH_(missing_vfat, I);
  BRANCH_(zsMask, I);
  BRANCH_(existVFATs, I);
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

  /* Woohyeon's method */
  for (auto etaPart : GEMGeometry_->etaPartitions()) {
    auto etaPartId = etaPart->id();

    int re = etaPartId.region();
    int st = etaPartId.station();
    int la = etaPartId.layer();
    int ch = etaPartId.chamber();
    int et = etaPartId.ieta();

    Key5 key5(re, st, la, ch, et);

    n_hits_each_eta[key5] = 0;
  }

  for (const GEMRecHit& cluster : *gemRecHits) {
    GEMDetId hit_Id = cluster.gemId();

    // ++n_clusters;
    // n_hits += cluster.clusterSize();

    int re = hit_Id.region();
    int st = hit_Id.station();
    int la = hit_Id.layer();
    int ch = hit_Id.chamber();
    int et = hit_Id.ieta();

    Key5 key5(re, st, la, ch, et);

    n_hits_each_eta[key5] += cluster.clusterSize();
  }

  long maxVal = 0;
  b_big_cluster_event = 0;
  for (const auto& entry : n_hits_each_eta) {
    long val = entry.second;
    if (val > maxVal) {
      maxVal = val;
    }
  }
  if (maxVal > 48) {
    b_big_cluster_event = 1;
  }
  /* */

  b_flower_event = 0;
  /* Laurant's method */
  for (size_t i = 0; i < max_trigger; ++i) {
    long l1a_diff = 3564 * (record->getOrbitNr() - record->getL1aHistoryEntry(i).getOrbitNr())
        + record->getBXID() - record->getL1aHistoryEntry(i).getBXID();

    if ((l1a_diff > 150) && (l1a_diff < 200)) {
      std::cout << "Flower event!!!" << std::endl;
      b_flower_event = 1;
      // return;
    }
  }
  /* */

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

    b_chamber_error = maskChamberWithError(chamber_id, vfat_status_collection, oh_status_collection);
    for (auto eta_part: chamber->etaPartitions()) {
      GEMDetId eta_part_id = eta_part->id();
      b_region = eta_part_id.region();
      b_layer = eta_part_id.layer();
      b_chamber = eta_part_id.chamber();
      b_ieta = eta_part_id.ieta();
      auto range = gemRecHits->get(eta_part_id);
      for (auto iter = oh_status_collection->begin(); iter != oh_status_collection->end(); iter++) {
        const auto [oh_id, oh_range] = (*iter);
        if (oh_id != chamber_id) continue;
        for (auto oh_status = oh_range.first; oh_status != oh_range.second; oh_status++) {
          auto tmp = oh_status->missingVFATs();
          // b_missing_vfat = oh_status->missingVFATs();
          b_zsMask = oh_status->zsMask();
          b_existVFATs = oh_status->existVFATs();
          // if (tmp) {
          // std::cout << eta_part_id << tmp << std::endl;
          // }
        }
      }
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

}

//define this as a plug-in
DEFINE_FWK_MODULE(gemBackground);
