def bin2dec(digits):
    on_lst = []
    for i in range(24):
        try:
            if int(bin(digits)[-(i+1)]):
                on_lst.append(i)
        except:
            break
    return on_lst


def get_on_vfats(activatedVFATs): # zsMask, existVFATs):
    on_vfat_dict = {ieta: [] for ieta in range(1, 9)}
    on_vfat = bin2dec(activatedVFATs)

    for vfat in on_vfat:
        ieta = 8 - vfat % 8
        vfat_section = vfat // 8
        on_vfat_dict[ieta].append(vfat_section)

    return on_vfat_dict


if __name__ == '__main__':
    test_path = "/store/user/jheo/ZeroBias/histo_9701_381484-2024.root"
    import ROOT as r
    f = r.TFile.Open(test_path)
    rec_hits = f.gemBackground.rec_hits

    count = 0
    for event in rec_hits:
        vec_lst = [event.region, event.layer, event.chamber, event.ieta,
                   event.first_strip, event.cluster_size, event.chamber_error,
                   event.zsMask, event.existVFATs]
        for vecs in zip(*vec_lst):
            region, layer, chamber, ieta, first_strip, cluster_size, chamber_err, zsMask, existVFATs = vecs
            if first_strip != 383: continue
            print(first_strip)

            num_on_vfats = sum([len(i) for i in get_on_vfats(zsMask, existVFATs).values()])
            # if (num_on_vfats == 24): continue
            # if (num_on_vfats == 0): continue
            print(region, layer, chamber)
            print(zsMask, existVFATs)
            print(get_on_vfats(zsMask, existVFATs))
            count += 1
        if count > 10: break

