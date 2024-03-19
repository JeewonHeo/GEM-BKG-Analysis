def bin2dec(digits):
    on_lst = []
    for i in range(24):
        try:
            if int(bin(digits)[-(i+1)]):
                on_lst.append(i)
        except:
            break
    return on_lst


def get_on_vfats(zsMask, existVFATs):
    on_vfat_dict = {ieta: [] for ieta in range(1, 9)}
    zs_msk = bin2dec(zsMask)
    exist_vfats = bin2dec(existVFATs)
    on_vfat = zs_msk + exist_vfats

    if len(set(on_vfat)) != len(zs_msk) + len(exist_vfats):
        print(on_vfat)

    for vfat in on_vfat:
        ieta = 8 - vfat % 8
        vfat_section = vfat // 8
        on_vfat_dict[ieta].append(vfat_section)

    return on_vfat_dict


if __name__ == '__main__':
    test_path = "/store/user/jheo/ZeroBias/histo_8754_367413.root"
    import ROOT as r
    f = r.TFile.Open(test_path)
    rec_hits = f.gemBackground.rec_hits

    count = 0
    for hit in rec_hits:
        num_on_vfats = sum([len(i) for i in get_on_vfats(hit.zsMask, hit.existVFATs).values()])
        if (num_on_vfats == 24): continue
        if (num_on_vfats == 0): continue
        print(hit.region, hit.layer, hit.chamber)
        print(hit.zsMask + hit.existVFATs)
        print(get_on_vfats(hit.zsMask, hit.existVFATs))
        count += 1
        if count == 10: break
