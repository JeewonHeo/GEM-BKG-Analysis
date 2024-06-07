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
typedef std::tuple<int, int, int, int> Key4;
typedef std::tuple<int, int, int, int, int> Key5;

class gemBackground : public edm::one::EDAnalyzer<edm::one::WatchRuns> {
public:
  explicit gemBackground(const edm::ParameterSet&);
  ~gemBackground() override;

  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

private:
  bool maskChamberWithError(const GEMDetId& chamber_id, const edm::Handle<GEMVFATStatusCollection>, const edm::Handle<GEMOHStatusCollection>);
  virtual void analyze(const edm::Event&, const edm::EventSetup&) override;
  virtual void beginJob() override;
  virtual void endJob() override;

  virtual void beginRun(edm::Run const&, edm::EventSetup const&) override;
  virtual void endRun(edm::Run const&, edm::EventSetup const&) override;
  // ----------member data ---------------------------
  edm::EDGetTokenT<GEMOHStatusCollection> oh_status_collection_;
  edm::EDGetTokenT<GEMVFATStatusCollection> vfat_status_collection_;
  edm::EDGetTokenT<GEMRecHitCollection> gemRecHits_;
  edm::EDGetTokenT<OnlineLuminosityRecord> onlineLumiRecord_;
  edm::ESGetToken<GEMGeometry, MuonGeometryRecord> hGEMGeom_;
  edm::ESGetToken<GEMGeometry, MuonGeometryRecord> hGEMGeomRun_;
  edm::EDGetTokenT<TCDSRecord> tcdsRecord_;

  TH1D* n_event_;
  std::map<Key4,TH2D*> digi_occ_others_;

  edm::Service<TFileService> fs_;

  TTree *t_rec_hits;
  long b_event, b_eventTime, b_luminosityBlock;
  float b_instLumi;
	int b_bunchId, b_orbitNumber;
  int b_flower_event, b_big_cluster_event;

  int hit_region, hit_layer, hit_chamber, hit_ieta, hit_chamber_error;
  int hit_first_strip, hit_cluster_size;
  uint32_t hit_zsMask;
  uint32_t hit_existVFATs;

  std::vector<int> b_region, b_layer, b_chamber, b_ieta, b_chamber_error;
  std::vector<int> b_first_strip, b_cluster_size;
  std::vector<uint32_t> b_zsMask;
  std::vector<uint32_t> b_existVFATs;
  // uint32_t b_missing_vfat;
  std::map<Key5, long> n_hits_each_eta;



};

gemBackground::gemBackground(const edm::ParameterSet& iConfig)
  : hGEMGeom_(esConsumes()),
	  hGEMGeomRun_(esConsumes<edm::Transition::BeginRun>()) {
  oh_status_collection_ = consumes<GEMOHStatusCollection>(iConfig.getParameter<edm::InputTag>("OHInputLabel"));
  vfat_status_collection_ = consumes<GEMVFATStatusCollection>(iConfig.getParameter<edm::InputTag>("VFATInputLabel"));
  gemRecHits_ = consumes<GEMRecHitCollection>(iConfig.getParameter<edm::InputTag>("gemRecHits"));
  onlineLumiRecord_ = consumes<OnlineLuminosityRecord>(iConfig.getParameter<edm::InputTag>("onlineMetaDataDigis"));
  tcdsRecord_ = consumes<TCDSRecord>(iConfig.getParameter<edm::InputTag>("tcdsRecord"));

  t_rec_hits = fs_->make<TTree>("rec_hits", "gem_rec_hits");
  #define BRANCH_(name, suffix) t_rec_hits->Branch(#name, & b_##name, #name "/" #suffix);
	// #define BRANCH_V(name, suffix) t_rec_hits->Branch(#name, & b_##name, #name "/" #suffix);
	#define BRANCH_V_(name, type) t_rec_hits->Branch(#name, "vector<"#type">", & b_##name );
  BRANCH_(event, l);
  BRANCH_(eventTime, l);
  BRANCH_(luminosityBlock, l);
  BRANCH_(instLumi, F);
  BRANCH_(bunchId, I);
  BRANCH_(orbitNumber, I);
  BRANCH_(big_cluster_event, I);
  BRANCH_(flower_event, I);

  BRANCH_V_(region, Int_t);
  BRANCH_V_(layer, Int_t);
  BRANCH_V_(chamber, Int_t);
  BRANCH_V_(ieta, Int_t);
  BRANCH_V_(first_strip, Int_t);
  BRANCH_V_(cluster_size, Int_t);
  BRANCH_V_(chamber_error, Int_t);
  BRANCH_V_(zsMask, uint32_t);
  BRANCH_V_(existVFATs, uint32_t);
  // BRANCH_(missing_vfat, I);
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
  b_luminosityBlock = iEvent.id().luminosityBlock();

  for (auto chamber: GEMGeometry_->chambers()) {
    GEMDetId chamber_id = chamber->id();
    if (chamber_id.station() != 1)
      continue;

    hit_chamber_error = maskChamberWithError(chamber_id, vfat_status_collection, oh_status_collection);
    for (auto eta_part: chamber->etaPartitions()) {
      GEMDetId eta_part_id = eta_part->id();
      hit_region = eta_part_id.region();
      hit_layer = eta_part_id.layer();
      hit_chamber = eta_part_id.chamber();
      hit_ieta = eta_part_id.ieta();
      auto range = gemRecHits->get(eta_part_id);
      for (auto iter = oh_status_collection->begin(); iter != oh_status_collection->end(); iter++) {
        const auto [oh_id, oh_range] = (*iter);
        if (oh_id != chamber_id) continue;
        for (auto oh_status = oh_range.first; oh_status != oh_range.second; oh_status++) {
          // auto tmp = oh_status->missingVFATs();
          // b_missing_vfat = oh_status->missingVFATs();
          hit_zsMask = oh_status->zsMask();
          hit_existVFATs = oh_status->existVFATs();
          // if (tmp) {
          // std::cout << eta_part_id << tmp << std::endl;
          // }
        }
      }
      Key4 key4(hit_region, 1, hit_layer, hit_chamber);
      for (auto rechit = range.first; rechit != range.second; ++rechit) {
        hit_first_strip = rechit->firstClusterStrip();
        hit_cluster_size = rechit->clusterSize();

				b_region.push_back(hit_region);
				b_layer.push_back(hit_layer);
				b_chamber.push_back(hit_chamber);
				b_ieta.push_back(hit_ieta);
				b_chamber_error.push_back(hit_chamber_error);
				b_first_strip.push_back(hit_first_strip);
        b_cluster_size.push_back(hit_cluster_size);
				b_zsMask.push_back(hit_zsMask);
				b_existVFATs.push_back(hit_existVFATs);

        if (b_flower_event == 0) {
          for (int s=hit_first_strip ; s<(hit_first_strip+hit_cluster_size) ; s++) {
            digi_occ_others_[key4]->Fill(s, hit_ieta);
          }
        }
      }  // hits
    }  // eta partition
  }  // chambers
  t_rec_hits->Fill();

	// Reset
  b_instLumi = -1;
  b_bunchId = -1;
  b_orbitNumber = -1;
  b_eventTime = -1;
  b_event = -1;
  b_luminosityBlock = -1;

	b_region.clear();
	b_layer.clear();
	b_chamber.clear();
	b_ieta.clear();
	b_chamber_error.clear();
	b_first_strip.clear();
  b_cluster_size.clear();
	b_zsMask.clear();
	b_existVFATs.clear();
}


// ------------ method called once each job just before starting event loop  ------------
void gemBackground::beginJob() {
  n_event_ = fs_->make<TH1D>("events", "Events", 2, -0.5, 1.5);
}

// ------------ method called once each job just after ending the event loop  ------------
void gemBackground::endJob() {
}

void gemBackground::beginRun(const edm::Run& run, const edm::EventSetup& iSetup) {
  edm::ESHandle<GEMGeometry> hGEMGeom;
  hGEMGeom = iSetup.getHandle(hGEMGeomRun_);

  const GEMGeometry* GEMGeometry_ = &*hGEMGeom;

  for (auto station : GEMGeometry_->stations()) {
    int st = station->station();
    int re = station->region();
    int nEta = st==2 ? 16 : 8;
    const char* re_str = re==1?"P":"M";
    for (auto superChamber : station->superChambers()) {
      for (auto chamber : superChamber->chambers()) {
        int ch = chamber->id().chamber();
        int la = chamber->id().layer();
        const char* ls = chamber->id().chamber()%2==0?"L":"S";
        Key4 key4(re,st,la,ch);
        digi_occ_others_[key4]= fs_->make<TH2D>(Form("occ_GE%d1-%s-%dL%d-%s", st, re_str, ch, la, ls),
                                               Form("GE%d1_%s_ch%d_L%d (others); Strip; iEta", st, re_str, ch, la),
                                               384,-0.5,383.5,
                                               nEta,0.5,nEta+0.5);
      }
    }
  }
}


void gemBackground::endRun(const edm::Run& run, const edm::EventSetup& iSetup) {
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
