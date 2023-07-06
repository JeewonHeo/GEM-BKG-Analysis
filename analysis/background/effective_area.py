import ROOT

def bin2dec(digits):
    on_lst = []
    for i in range(24):
        if int(bin(digits)[-1]):
            on_lst.append(i)
    return on_lst


def get_on_vfats(hit):
    on_vfat_dict = {ieta: [] for ieta in range(1, 9)}
    zs_msk = bin2dec(hit.zsMask)
    exist_vfats = bin2dec(hit.existVFATs)
    on_vfat = zs_msk + exist_vfats

    if len(set(on_vfat)) != len(zs_msk) + len(exist_vfats):
        print(on_vfat)

    for vfat in on_vfat:
        ieta = 8 - vfat % 8
        vfat_section = vfat // 8
        on_vfat_dict[ieta].append(vfat_section)

    return on_vfat_dict


if __name__ == '__main__':
    test_path = "/eos/user/j/jheo/ZeroBias/8754_367416-v1/230705_093329/0000/histo_8.root"
    import ROOT as r
    f = r.TFile.Open(test_path)
    rec_hits = f.gemBackground.rec_hits

    for hit in rec_hits:
        get_on_vfats(hit)
