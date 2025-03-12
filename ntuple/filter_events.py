import os
import ROOT
import argparse
from array import array
from tqdm import tqdm
# sys.path.append('/home/jheo/gem-background/git/jheo/gem-background/cmssw/flower/backgorund')
from background import get_on_vfats, select_hot_strips_with_analyzed
ROOT.gROOT.SetBatch(True)

def filter_rechits(file_path, out_path, run_number, hot_strips, bad_chambers, off_bx):
    f = ROOT.TFile.Open(file_path)
    # gem_bkg_dir = f.gemBackground
    rec_hits = f.rec_hits
    tot_events = rec_hits.GetEntries()
    print(f"{tot_events = }")
    out_file = ROOT.TFile.Open(out_path, "RECREATE")
    tree = ROOT.TTree("rec_hits", "gem_rec_hits")
    ran = [60, 0, 30000]
    h_instlumi = ROOT.TH1F("instlumi", "instlumi", *ran)
    h_bxon = ROOT.TH1F("bx_on", "bx_on", *ran)
    h_bxoff = ROOT.TH1F("bx_off", "bx_off", *ran)
    h_bunchcross = ROOT.TH1F("BXID", "BXID", 3600, 0, 3600)
    # h_events = #gem_bkg_dir.Get("events")
    h_bad_chamber = {
            "PL1": ROOT.TH2D("bad_chamber_PL1", "bad chamber GE1/1-P-L1", 36, 0.5, 36.5, *ran),
            "PL2": ROOT.TH2D("bad_chamber_PL2", "bad chamber GE1/1-P-L2", 36, 0.5, 36.5, *ran),
            "ML1": ROOT.TH2D("bad_chamber_ML1", "bad chamber GE1/1-M-L1", 36, 0.5, 36.5, *ran),
            "ML2": ROOT.TH2D("bad_chamber_ML2", "bad chamber GE1/1-M-L2", 36, 0.5, 36.5, *ran),
            "PL1_on": ROOT.TH2D("bad_chamber_PL1_on", "bad chamber GE1/1-P-L1_on", 36, 0.5, 36.5, *ran),
            "PL2_on": ROOT.TH2D("bad_chamber_PL2_on", "bad chamber GE1/1-P-L2_on", 36, 0.5, 36.5, *ran),
            "ML1_on": ROOT.TH2D("bad_chamber_ML1_on", "bad chamber GE1/1-M-L1_on", 36, 0.5, 36.5, *ran),
            "ML2_on": ROOT.TH2D("bad_chamber_ML2_on", "bad chamber GE1/1-M-L2_on", 36, 0.5, 36.5, *ran),
            "PL1_off": ROOT.TH2D("bad_chamber_PL1_off", "bad chamber GE1/1-P-L1_off", 36, 0.5, 36.5, *ran),
            "PL2_off": ROOT.TH2D("bad_chamber_PL2_off", "bad chamber GE1/1-P-L2_off", 36, 0.5, 36.5, *ran),
            "ML1_off": ROOT.TH2D("bad_chamber_ML1_off", "bad chamber GE1/1-M-L1_off", 36, 0.5, 36.5, *ran),
            "ML2_off": ROOT.TH2D("bad_chamber_ML2_off", "bad chamber GE1/1-M-L2_off", 36, 0.5, 36.5, *ran),
            }

    h_2d = {}
    for re in ['M', "P"]:
        for la in [1, 2]:
            h_2d[f"{re}_L{la}"] = ROOT.TH2D(f"GE{re}/1-L{la}", f"GE{re}1L{la}", 36, 1, 37, 8, 1, 9)

    a_event = array('L', [0])
    a_event_time = array('L', [0])
    a_lumi_block = array('l', [0])
    a_instLumi = array('f', [0])
    a_bunchId = array('i', [0])

    a_region = array('i', [0])
    a_layer = array('i', [0])
    a_chamber = array('i', [0])
    a_ieta = array('i', [0])
    a_first_strip= array('i', [0])
    a_cluster_size= array('i', [0])
    a_scale = array("f", [0])
    a_scale_chamber = array("f", [0])

    v_region = ROOT.std.vector('int')()
    v_layer = ROOT.std.vector('int')()
    v_chamber = ROOT.std.vector('int')()
    v_ieta = ROOT.std.vector('int')()
    v_first_strip = ROOT.std.vector('int')()
    v_cluster_size = ROOT.std.vector('int')()
    v_scale = ROOT.std.vector('float')()
    v_scale_chamber = ROOT.std.vector('float')()

    tree.Branch("event", a_event, "event/L")
    tree.Branch("eventTime", a_event_time, "eventTime/L")
    tree.Branch("luminosityBlock", a_lumi_block, "luminosityBlock/I")
    tree.Branch("instLumi", a_instLumi, "instLumi/F")
    tree.Branch("bunchId", a_bunchId, "bunchId/I")

    tree.Branch("region", v_region)
    tree.Branch("layer", v_layer)
    tree.Branch("chamber", v_chamber)
    tree.Branch("ieta", v_ieta)
    tree.Branch("first_strip", v_first_strip)
    tree.Branch("cluster_size", v_cluster_size)
    tree.Branch("scale", v_scale)
    tree.Branch("scale_chamber", v_scale_chamber)

    event_per_sec = 10**9 / (8 * 25)  # 1event / 8bx * 1bx / 25ns
    area = {
        1: [829.832, 672.621],
        2: [762.952, 623.335],
        3: [582.477, 487.737],
        4: [536.375, 452.607],
        5: [412.741, 357.334],
        6: [380.546, 331.901],
        7: [294.870, 263.171],
        8: [272.121, 244.628]
        }
    event_num = 0
    for event in tqdm(rec_hits, total=tot_events):
        v_region.clear(); v_layer.clear(); v_chamber.clear(); v_ieta.clear();
        v_first_strip.clear(); v_cluster_size.clear();
        v_scale.clear(); v_scale_chamber.clear();
        flower_event = event.flower_event
        if flower_event: continue

        # big_cluster_event = event.big_cluster_event
        # if big_cluster_event: continue

        event_num = event.event
        inst_lumi = event.instLumi
        bunch_id = event.bunchId

        h_instlumi.Fill(inst_lumi)
        h_bunchcross.Fill(bunch_id)
        if bunch_id not in off_bx:
            h_bxon.Fill(inst_lumi)
        else:
            h_bxoff.Fill(inst_lumi)

        # chamber_err = event.chamber_error
        # if bunch_id not in off_bx: continue

        a_instLumi[0] = inst_lumi
        a_event[0] = event_num
        a_event_time[0] = event.eventTime
        a_lumi_block[0] = event.luminosityBlock
        a_bunchId[0] = bunch_id

        bad_ch_in_evt = {
                f'{reg}-L{lyr}': [0]*36 for reg in ["M", "P"] for lyr in [1, 2]
                } 
        vec_lst = [event.region, event.layer, event.chamber, event.ieta,
                   event.first_strip, event.cluster_size, event.activatedVFATs,
                   # event.first_strip, event.cluster_size, event.chamber_error,
                   # event.zsMask, event.existVFATs]
                   ]
        for vecs in zip(*vec_lst):
            region, layer, chamber, ieta, first_strip, cluster_size, activatedVFATs = vecs
            region_str = "M" if region == -1 else "P"
            # if chamber_err:
            #     bad_ch_in_evt[f"{region_str}-L{layer}"][chamber-1] = 1
            #     continue

            # on_vfats = get_on_vfats(zsMask, existVFATs)
            on_vfats = get_on_vfats(activatedVFATs)
            for tmp_ieta in range(1, 9):
                if len(on_vfats[tmp_ieta]) == 0:
                    bad_ch_in_evt[f"{region_str}-L{layer}"][chamber-1] = 1
                    continue

            gem_label = f"GE11-{region_str}-L{layer}"
            if bad_chambers[gem_label][chamber-1]:
                bad_ch_in_evt[f"{region_str}-L{layer}"][chamber-1] = 1
                continue
            
            # hit_label = f"{gem_label}-{chamber}"
            # bad_strips = hot_strips[hit_label][ieta]

            # hit_cluster = [digi for digi in range(first_strip, first_strip + cluster_size)]
            # include_hot_strip = False
            # for digi in hit_cluster:
            #     if digi in bad_strips:
            #         include_hot_strip = True
            #         break
            # if include_hot_strip: continue


        for vecs in zip(*vec_lst):
            region, layer, chamber, ieta, first_strip, cluster_size, activatedVFATs = vecs
            region_str = "M" if region == -1 else "P"
            if bad_ch_in_evt[f"{region_str}-L{layer}"][chamber-1] != 0:
                continue


            gem_label = f"GE11-{region_str}-L{layer}"
            if bad_chambers[gem_label][chamber-1]: continue

            
            hit_label = f"{gem_label}-{chamber}"
            bad_strips = hot_strips[hit_label][ieta]

            # if (first_strip in bad_strips) and (cluster_size == 1):
            #     # print(region, layer, chamber, first_strip, cluster_size, bad_strips)
            #     continue

            hit_cluster = [digi for digi in range(first_strip, first_strip + cluster_size)]
            include_hot_strip = False
            for digi in hit_cluster:
                if digi in bad_strips:
                    include_hot_strip = True
                    break
            if include_hot_strip: continue


            # on_vfats = get_on_vfats(zsMask, existVFATs)
            on_vfats = get_on_vfats(activatedVFATs)
            on_strips = [digi for section in on_vfats[ieta] \
                    for digi in range(section*128, 128 + section*128)]
            good_on_strips = [digi for digi in on_strips if digi not in bad_strips]
            good_strip_ratio = len(good_on_strips) / 384

            # on_strips = [digi for section in on_vfats[ieta] \
            #         for digi in range(section*128, 128 + section*128)]
            # bad_strips = [digi for digi in bad_strips if digi in on_strips]

            # good_strip_ratio = 1 - len(bad_strips) / (128 * len(on_vfats[ieta]))
            # on_vfats = get_on_vfats(zsMask, existVFATs)
            # good_strip_ratio = len(on_vfats[ieta]) / 3 #- len(bad_strips) / (128 * len(on_vfats[ieta]))

            good_eta_part_area = area[ieta][chamber%2] * good_strip_ratio
            scale = event_per_sec / good_eta_part_area if good_strip_ratio != 0 else 0

            good_area_chamber = 0
            for tmp_ieta in range(1, 9):
                # on_strips = [digi for section in on_vfats[tmp_ieta] \
                #         for digi in range(section*128, 128 + section*128)]
                # bad_strips = [digi for digi in bad_strips if digi in on_strips]

                # good_strip_ratio = 1 - len(bad_strips) / (128 * len(on_vfats[tmp_ieta]))
                # good_strip_ratio = 1# - len(bad_strips) / (128 * len(on_vfats[tmp_ieta]))

                on_strips = [digi for section in on_vfats[ieta] \
                        for digi in range(section*128, 128 + section*128)]
                good_on_strips = [digi for digi in on_strips if digi not in bad_strips]
                good_strip_ratio = len(good_on_strips) / 384
                good_area_chamber += area[tmp_ieta][chamber%2] * good_strip_ratio

            scale_chamber = event_per_sec / good_area_chamber if good_area_chamber != 0 else 0

            h_2d[f"{region_str}_L{layer}"].Fill(chamber, ieta)
            a_region[0] = region
            a_layer[0] = layer
            a_chamber[0] = chamber
            a_ieta[0] = ieta
            a_first_strip[0] = first_strip
            a_cluster_size[0] = cluster_size
            a_scale[0] = scale
            a_scale_chamber[0] = scale_chamber

            v_region.push_back(a_region[0])
            v_layer.push_back(a_layer[0])
            v_chamber.push_back(a_chamber[0])
            v_ieta.push_back(a_ieta[0])
            v_first_strip.push_back(a_first_strip[0])
            v_cluster_size.push_back(a_cluster_size[0])
            v_scale.push_back(a_scale[0])
            v_scale_chamber.push_back(a_scale_chamber[0])

        for r in ['M', 'P']:
            for l in [1, 2]:
                for ch, i in enumerate(bad_ch_in_evt[f"{r}-L{l}"]):
                    if i != 0: 
                        h_bad_chamber[f"{r}L{l}"].Fill(ch+1, inst_lumi)
                        if bunch_id not in off_bx:
                            h_bad_chamber[f"{r}L{l}_on"].Fill(ch+1, inst_lumi)
                        else:
                            h_bad_chamber[f"{r}L{l}_off"].Fill(ch+1, inst_lumi)
        tree.Fill()

    # out_file.WriteObject(h_events, "events")
    out_file.WriteObject(h_bad_chamber["PL1"], "bad_chamber_PL1")
    out_file.WriteObject(h_bad_chamber["PL2"], "bad_chamber_PL2")
    out_file.WriteObject(h_bad_chamber["ML1"], "bad_chamber_ML1")
    out_file.WriteObject(h_bad_chamber["ML2"], "bad_chamber_ML2")
    out_file.WriteObject(h_bad_chamber["PL1_on"], "bad_chamber_PL1_on")
    out_file.WriteObject(h_bad_chamber["PL2_on"], "bad_chamber_PL2_on")
    out_file.WriteObject(h_bad_chamber["ML1_on"], "bad_chamber_ML1_on")
    out_file.WriteObject(h_bad_chamber["ML2_on"], "bad_chamber_ML2_on")
    out_file.WriteObject(h_bad_chamber["PL1_off"], "bad_chamber_PL1_off")
    out_file.WriteObject(h_bad_chamber["PL2_off"], "bad_chamber_PL2_off")
    out_file.WriteObject(h_bad_chamber["ML1_off"], "bad_chamber_ML1_off")
    out_file.WriteObject(h_bad_chamber["ML2_off"], "bad_chamber_ML2_off")
    out_file.WriteObject(h_instlumi, "instLumi")
    out_file.WriteObject(h_bxon, "bx_on")
    out_file.WriteObject(h_bxoff, "bx_off")
    out_file.WriteObject(h_bunchcross, "bunchCross")
    for histo in h_2d:
        out_file.WriteObject(h_2d[histo], histo)
    tree.Write()
    del tree
    out_file.Close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='get hits')
    parser.add_argument('--input_path', type=str,
            default="/eos/user/j/jheo/ZeroBias/8754_367416-v1/230705_093329/0000/histo_1.root")
    parser.add_argument('--output_path', type=str,
            default='filtered_hits/')
    parser.add_argument('--output_name', type=str,
            default='test.root')
    parser.add_argument('--dqm_path', type=str,
            default='/hdfs/user/jheo/dqm/')
    parser.add_argument('--run_number', type=int, default=359691)
    parser.add_argument('--fill', type=int, default=8754)
    parser.add_argument('--run_era', type=str, default="Run2022E")
    args = parser.parse_args()

    lumitxt = '/users/jheo/GEM-BKG-Analysis/analysis/txt/fill_8754_bunch.txt'
    with open(lumitxt) as f:
        lines = f.readlines()
        bxs = [line.split('\t') for line in lines][2:]
        off_bx = [int(bx[0]) for bx in bxs if float(bx[2])==0 or float(bx[3])==0]

    # with open('/home/jheo/gem-background/git/jheo/gem-background/cmssw/flower/bunch/InstLumi_8220_AVG_Lumi_HIGH.txt') as f:
    # # with open('/home/jheo/gem-background/git/jheo/gem-background/cmssw/flower/bunch/InstLumi_8456_AVG_uncrt.txt') as f:
    #     lines = f.readlines()
    #     bxs = [line.split('\t') for line in lines][2:]
    #     off_bx = [int(bx[0]) for bx in bxs if not float(bx[1])]

    if not os.path.isdir(args.output_path):
        os.makedirs(args.output_path)
    # hot_strips, bad_chambers = select_hot_strips_with_analyzed(args.dqm_path, '/store/user/jheo/ZeroBias/wlumimask', args.run_number, args.fill, args.run_era)
    # hot_strips, bad_chambers = select_hot_strips_with_analyzed(args.dqm_path, '/hdfs/store/user/jheo/ZeroBias', args.run_number, args.fill, args.run_era)
    hot_strips, bad_chambers = select_hot_strips_with_analyzed(args.dqm_path, '/users/jheo/GEM-BKG-Analysis/ntuple/gem_ntuple', args.run_number, args.fill, args.run_era)
    filter_rechits(args.input_path, f"{args.output_path}/{args.output_name}", args.run_number, hot_strips, bad_chambers, off_bx)
