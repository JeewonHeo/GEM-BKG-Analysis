import os
import csv
import sys
import yaml
import ROOT
import math
import numpy as np
from array import array
import matplotlib.pyplot as plt
import mplhep as hep

hep.style.use("CMS")
ROOT.gROOT.SetBatch(True)
# ROOT.gStyle.SetOptFit(1111)
ROOT.Math.MinimizerOptions.SetDefaultMinimizer("Minuit2")

radius = {
    1: [241.398, 227.973],
    2: [221.943, 211.268],
    3: [204.137, 195.862],
    4: [187.98, 181.755],
    5: [173.148, 168.698],
    6: [159.642, 156.691],
    7: [147.211, 145.559],
    8: [135.854, 135.303]
}

# parlimit = False
parlimit = True

ieta_eta = {
        'even-L1': [1.55, 1.62, 1.71, 1.78, 1.86, 1.94, 2.02, 2.09, 2.17],
        'even-L2': [1.56, 1.63, 1.71, 1.79, 1.87, 1.94, 2.03, '2.10', 2.18],
        'odd-L1': [1.61, 1.68, 1.75, 1.82, '1.90', 1.96, 2.04, 2.11, 2.18],
        'odd-L2': [1.62, 1.69, 1.76, 1.83, '1.90', 1.97, 2.04, 2.11, 2.19],
        }

with open('../analysis/txt/fill_info.yaml', 'r') as f:
    fill_info = yaml.load(f, Loader=yaml.CLoader)
intg_lumi = fill_info['intg_lumi']

with open('../analysis/txt/ge11-eta.yaml', 'r') as y:
    eta_pos = yaml.load(y, Loader=yaml.CLoader)

def main():
    file_path = sys.argv[-2]
    fill_number = int(sys.argv[-1])
    print(fill_number)
    ieta_color = [
        "#3f90da",
        "#ffa90e",
        "#bd1f01",
        "#94a4a2",
        "#832db6",
        "#a96b59",
        "#e76300",
        "#b9ac70",
        ]
    ieta_color.reverse()

    if not os.path.isdir(f"{file_path}/fit"):
        os.makedirs(f"{file_path}/fit")
    if not os.path.isdir(f"{file_path}/fit_values"):
        os.makedirs(f"{file_path}/fit_values")
    # f = ROOT.TFile(f"{file_path}/histos.root", "r")
    f = ROOT.TFile(f"{file_path}/histos_95_ieta.root", "r")

    xevenarr = array('f')
    xoddarr = array('f')
    xallarr = array('f')

    for i in range(0, 251):
        xallarr.append(i)
    for i in radius.values():
        xoddarr.append(i[1])
        xevenarr.append(i[0])

    fit_f = {}
    r_inst_lumi = 1.5
    for region in [-1, 1]:
        region_str = 'M' if region == -1 else 'P'
        for layer in [1, 2]:
            gs = {}
            yarr = {}
            yerrarr = {}
            for chamber in ['even', 'odd']:
                hs = {}
                yarr[chamber] = array('f')
                xerrarr = array('f')
                yerrarr[chamber] = array('f')
                for ieta in range(1, 9):
                    hs[ieta] = f.Get(f"h_{region}_{layer}_{ieta}_{chamber}")
                fig, ax = plt.subplots()
                instlumix = np.linspace(0, 3, 100)
                for icolor, ieta in zip(ieta_color, range(1, 9)):
                    instlumi = []
                    instlumierr = []
                    rate = []
                    rateerr = []
                    for ibin in range(1, hs[ieta].GetNbinsX()+1):
                        if hs[ieta].GetBinContent(ibin) == 0: continue
                        instlumi.append(hs[ieta].GetBinCenter(ibin))
                        instlumierr.append(hs[ieta].GetBinWidth(ibin)/2)
                        rate.append(hs[ieta].GetBinContent(ibin))
                        rateerr.append(hs[ieta].GetBinError(ibin))

                    print(f'{"*"*80}\n{region_str}, {layer}, {chamber}, {ieta}')
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"] = ROOT.TF1("myfunc", "[0] + [1]*x", 0, 1000)
                    if parlimit: fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].SetParLimits(0, 0, 1000)
                    fit_result = hs[ieta].Fit(fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"], 'FS')
                    br_15 = fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"](r_inst_lumi) # - fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].GetParameters()[0]
                    fit_par = fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].GetParameters()
                    err = fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].GetParErrors()
                    cov = fit_result.GetCovarianceMatrix()
                    print("FITERR: ", err[0], err[1], cov[0][1])
                    xerrarr.append(0)
                    # prop_err = (err[0]**2 + (err[1] * r_inst_lumi)**2 + 2 * r_inst_lumi * cov[0][1])**0.5
                    prop_err = err[0] + err[1] * r_inst_lumi
                    print(prop_err)
                    yerrarr[chamber].append(prop_err)
                    yarr[chamber].append(br_15)
                    ratef = lambda x: fit_par[0] + fit_par[1] * x
                    ax.plot(instlumix, ratef(instlumix), color=icolor)
                    ax.errorbar(instlumi, rate, xerr=instlumierr, yerr=rateerr, fmt='^', #ecolor='black',
                                label=f"i$\eta$ = {ieta} ({ieta_eta[f'{chamber}-L{layer}'][ieta-1]} < |$\eta$| <{ieta_eta[f'{chamber}-L{layer}'][ieta]})",
                                color=icolor)

                with open(f"{file_path}/fit_values/GE11-{region_str}-L{layer}-{chamber}.txt", 'w') as txt:
                    writer = csv.writer(txt, delimiter='\t')
                    writer.writerow(['eta'] + list(eta_pos[chamber][f'L{layer}'].values()))
                    writer.writerow(['values'] + list(np.array(yarr[chamber])))
                    writer.writerow(['values+uncrt'] + list(np.array(yarr[chamber])+np.array(yerrarr[chamber])))
                    writer.writerow(['values-uncrt'] + list(np.array(yarr[chamber])-np.array(yerrarr[chamber])))

                if region < 0: reg_str = '-1'
                else: reg_str ='+1'
                if chamber=='even': ch_str = 'long type'
                else: ch_str = 'short type'
                leg = ax.legend(title=f"GE{reg_str}/1 Layer {layer} {ch_str}")
                leg._legend_box.align = "left"
                ax.set_xlabel('Instantaneous Luminosity [$10^{34}cm^{-2}s^{-1}$]')
                ax.set_ylabel('Hit Rate [Hz / $cm^{2}$]')
                hep.cms.text(text='Preliminary')#, loc=2)#, ax=ax)
                hep.cms.lumitext(text=f'{intg_lumi[fill_number]} $\mathrm{{fb}}^{{-1}}$ (13.6 TeV)') #  7.98 \ifb
                plt.text(0.6, 0.85, f"Fill {fill_number}", transform=plt.gca().transAxes, fontsize=25)
                # plt.text(0.3, 0.75, r"Hit rate at L = 1.5 x 10$^{34}$ cm$^{-2}$s$^{-1}$", transform=plt.gca().transAxes, fontsize=25)
                # plt.text(0.3, 0.8, f"GE{region}/1 layer {layer}", transform=plt.gca().transAxes, fontsize=25)
                plt.xlim(0, 2.5)
                plt.ylim(0, 2000)
                # plt.savefig(f"{file_path}/fit/fit_{region_str}_L{layer}_{chamber}.pdf")# _{chamber}.png")
                plt.savefig(f"{file_path}/fit/fit_{region_str}_L{layer}_{chamber}.png")# _{chamber}.png")
                plt.clf()
 
                fig, ax = plt.subplots()
                xarr = xevenarr if chamber == 'even' else xoddarr
                if chamber == 'odd':
                    gs[chamber] = ROOT.TGraphErrors(8, xarr, yarr[chamber], xerrarr, yerrarr[chamber])
                else:
                    gs[chamber] = ROOT.TGraphErrors(8, xarr, yarr[chamber], xerrarr, yerrarr[chamber])
                if chamber == 'odd':
                    r_fit_odd = ROOT.TF1("rfunc", "expo(0)", 1, -1)
                    odd_fit_result = gs['odd'].Fit(r_fit_odd, 'S')
                    odd_f_par = r_fit_odd.GetParameters()
                    # odd_f_err = r_fit_odd.GetParErrors()
                    odd_p0_err_dn = odd_fit_result.LowerError(0)
                    odd_p0_err_up  = odd_fit_result.UpperError(0)
                    odd_p1_err_dn = odd_fit_result.LowerError(1)
                    odd_p1_err_up  = odd_fit_result.UpperError(1)
                else:
                    r_fit_even = ROOT.TF1("rfunc", "expo(0)", 1, -1)
                    even_fit_result = gs['even'].Fit(r_fit_even, 'S')
                    even_f_par = r_fit_even.GetParameters()
                    # even_f_err = r_fit_even.GetParErrors()
                    even_p0_err_dn = even_fit_result.LowerError(0)
                    even_p0_err_up  = even_fit_result.UpperError(0)
                    even_p1_err_dn = even_fit_result.LowerError(1)
                    even_p1_err_up  = even_fit_result.UpperError(1)
                    
                gs[chamber].SetTitle(f"GE11-{region_str}-L{layer}")# -{chamber}")
                gs[chamber].GetXaxis().SetTitle("R [cm]")
                gs[chamber].GetYaxis().SetTitle(r"Hit Rate [Hz / cm^{2}]")
            odd_f = np.vectorize(lambda x: math.exp(odd_f_par[0] + odd_f_par[1] * x))
            even_f = np.vectorize(lambda x: math.exp(even_f_par[0] + even_f_par[1] * x))
            odd_lower_f = np.vectorize(lambda x: math.exp((odd_f_par[0] - odd_p0_err_dn) + (odd_f_par[1] - odd_p1_err_dn) * x))
            odd_upper_f = np.vectorize(lambda x: math.exp((odd_f_par[0] + odd_p0_err_up) + (odd_f_par[1] + odd_p1_err_up) * x))
            even_lower_f = np.vectorize(lambda x: math.exp((even_f_par[0] - even_p0_err_dn) + (even_f_par[1] - even_p1_err_dn) * x))
            even_upper_f = np.vectorize(lambda x: math.exp((even_f_par[0] + even_p0_err_up) + (even_f_par[1] + even_p1_err_up) * x))
            fig, ax = plt.subplots()
            xarrs = np.array(xallarr)
            ax.errorbar(xevenarr, yarr['even'], yerr=yerrarr['even'], fmt='^', color='blue', label='long type', markersize=10, ecolor='black')
            ax.errorbar(xoddarr, yarr['odd'], yerr=yerrarr['odd'], fmt='v', color='red', label='short type', markersize=10, ecolor='black')
            ax.plot(xarrs, odd_f(xarrs), color='red', alpha=0.8)
            ax.plot(xarrs, even_f(xarrs), color='blue', alpha=0.8)
            ax.fill_between(xarrs, odd_lower_f(xarrs), odd_upper_f(xarrs), color='red', alpha=0.1)
            ax.fill_between(xarrs, even_lower_f(xarrs), even_upper_f(xarrs), color='blue', alpha=0.1)
            ax.legend()
            ax.set_xlabel('R [cm]')
            ax.set_ylabel('Hit Rate [Hz / $cm^{2}$]')
            hep.cms.text(text='Preliminary')#, loc=2)#, ax=ax)
            # hep.cms.lumitext(text='pp data, 2024 (13.6 TeV)') #  7.98 \ifb
            hep.cms.lumitext(text=f'{intg_lumi[fill_number]} $\mathrm{{fb}}^{{-1}}$ (13.6 TeV)') #  7.98 \ifb
            plt.text(0.3, 0.85, f"Fill {fill_number}", transform=plt.gca().transAxes, fontsize=25)
            plt.text(0.3, 0.75, r"L = 1.5 x 10$^{34}$ cm$^{-2}$s$^{-1}$", transform=plt.gca().transAxes, fontsize=25)
            if region < 0: reg_str = '-1'
            else: reg_str ='+1'
            plt.text(0.3, 0.8, f"GE{reg_str}/1 Layer {layer}", transform=plt.gca().transAxes, fontsize=25)
            plt.xlim(125, 250)
            plt.ylim(0, 1500)
            plt.savefig(f"{file_path}/fit/GE11_{region_str}_L{layer}.png")# _{chamber}.png")
            # plt.savefig(f"{file_path}/fit/GE11_{region_str}_L{layer}.pdf")# _{chamber}.png")
            plt.clf()
if __name__=='__main__':
    main()
