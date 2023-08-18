import os
import csv
import sys
import yaml
import ROOT
import math
import numpy as np
from array import array
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptFit(1111)

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

ieta_eta = [1.56, 1.63, 1.71, 1.79, 1.87, 1.94, 2.03, '2.10', 2.18]

intg_lumi = {
        8220: 0.41,
        8456: 0.67,
        8754: 0.66,
        }
year = {
        8220: 2022,
        8456: 2022,
        8754: 2023,
        }

with open('txt/ge11-eta.yaml', 'r') as y:
    eta_pos = yaml.load(y, Loader=yaml.CLoader)

def main():
    file_path = sys.argv[-1]
    fill_number = int(file_path.split('_')[1])
    print(fill_number)

    if not os.path.isdir(f"{file_path}/fit"):
        os.makedirs(f"{file_path}/fit")
    if not os.path.isdir(f"{file_path}/fit_values"):
        os.makedirs(f"{file_path}/fit_values")
    f = ROOT.TFile(f"{file_path}/histos.root", "r")

    xevenarr = array('f')
    xoddarr = array('f')
    xallarr = array('f')

    for i in range(0, 251):
        xallarr.append(i)
    for i in radius.values():
        xoddarr.append(i[1])
        xevenarr.append(i[0])

    uncrt = {}
    for region in [-1, 1]:
        for layer in [1, 2]:
            for ieta in range(1, 9):
                even_chamber_count = 0
                odd_chamber_count = 0
                even_list = []
                odd_list = []
                for chamber in range(1, 37):
                    h = f.Get(f"h_{region}_{layer}_{chamber}_{ieta}")
                    h_list = np.array([h.GetBinContent(i) for i in range(1, 31)])
                    if sum(h_list) != 0:
                        if chamber % 2 == 0:
                            even_chamber_count += 1
                            even_list.append(h_list)
                        else:
                            odd_chamber_count += 1
                            odd_list.append(h_list)
                even_list = np.array(even_list).T
                odd_list = np.array(odd_list).T
                uncrt[f'{region}_{layer}_{ieta}_even'] = even_list.std(axis=1)
                uncrt[f'{region}_{layer}_{ieta}_odd'] = odd_list.std(axis=1)

    fit_f = {}
    r_inst_lumi = 1.0
    cvs = ROOT.TCanvas('', '', 1200, 900)
    for region in [-1, 1]:
        region_str = 'M' if region == -1 else 'P'
        for layer in [1, 2]:
            gs = {}
            for chamber in ['even', 'odd']:
                hs = {}
                yarr = array('f')
                xerrarr = array('f')
                yerrarr = array('f')
                for ieta in range(1, 9):
                    hs[ieta] = f.Get(f"h_{region}_{layer}_{ieta}_{chamber}")
                    for i in range(1, 21):
                        # hs[ieta].SetBinError(i, uncrt[f'{region}_{layer}_{ieta}_{chamber}'][i-1])
                        break

                for ieta in range(1, 9):
                    # f.Get(f"h_{region}_{layer}_{ieta}_{chamber}") = f.Get(f"h_{region}_{layer}_{ieta}_{chamber}")
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"] = ROOT.TF1("myfunc", "[0] + [1]*x", 0, 1000)
                    _ = hs[ieta].Fit(fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"], 'F')
                    br_15 = fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"](r_inst_lumi)
                    err = fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].GetParErrors()
                    print(f'{region_str}, {layer}, {chamber}, {ieta = }\n{fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].GetParameters()[1]}')
                    xerrarr.append(0)
                    yerrarr.append(err[0] + err[1] * r_inst_lumi)
                    yarr.append(br_15)
    # if not os.path.isdir(f"{file_path}/fit_values"):
                with open(f"{file_path}/fit_values/GE11-{region_str}-L{layer}-{chamber}.txt", 'w') as txt:
                    writer = csv.writer(txt, delimiter='\t')
                    writer.writerow(['eta'] + list(eta_pos[chamber][f'L{layer}'].values()))
                    writer.writerow(['values'] + list(np.array(yarr)))
                    writer.writerow(['values+uncrt'] + list(np.array(yarr)+np.array(yerrarr)))
                    writer.writerow(['values-uncrt'] + list(np.array(yarr)-np.array(yerrarr)))
                print(yarr, yarr + yerrarr)

                # h_tmp = f.Get(f"h_{region}_{layer}_8_{chamber}")
                hs[8].Draw('E')
                hs[8].SetTitle(f"GE11-{region_str}-L{layer}-{chamber}")

                leg = ROOT.TLegend(0.15, 0.55, 0.4, 0.85)
                for ieta in range(1, 9):
                    leg.AddEntry(hs[ieta], r'i_{#eta} = '+f'{ieta} ({ieta_eta[ieta-1]} < '+r'|#eta|'+f' <{ieta_eta[ieta]})','lep')
                    hs[ieta].DrawCopy("E SAME")
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].SetLineColor(hs[ieta].GetLineColor())
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].Draw("same")
                leg.SetFillStyle(0)
                leg.SetBorderSize(0)
                leg.Draw()
                txt = ROOT.TLatex()
                # txt.DrawLatexNDC(0.52, 0.7, f"Hit rate at L = {r_inst_lumi}"+r" x 10^{34}cm^{-2}s^{-1}")
                txt.SetTextFont(61)
                txt.SetTextSize(0.055)
                txt.DrawLatexNDC(0.1, 0.91, "CMS")
                txt.SetTextFont(52)
                txt.SetTextSize(0.03)
                txt.DrawLatexNDC(0.19, 0.91, f"Preliminary")
                txt.SetTextSize(0.025)
                txt.DrawLatexNDC(0.62, 0.91, f"Fill {fill_number}"+\
                        r"#sqrt{s}"+\
                        f" = 13.6 TeV ({year[fill_number]}) {intg_lumi[fill_number]}"+\
                        r"fb^{-1}")
                cvs.SaveAs(f"{file_path}/fit/fit_{region}_{layer}_{chamber}.png")


def main2():
    file_path = sys.argv[-1]
    fill_number = int(file_path.split('_')[1])
    print(fill_number)

    if not os.path.isdir(f"{file_path}/fit"):
        os.makedirs(f"{file_path}/fit")
    if not os.path.isdir(f"{file_path}/fit_values"):
        os.makedirs(f"{file_path}/fit_values")
    f = ROOT.TFile(f"{file_path}/histos.root", "r")

    xevenarr = array('f')
    xoddarr = array('f')
    xallarr = array('f')

    for i in range(0, 251):
        xallarr.append(i)
    for i in radius.values():
        xoddarr.append(i[1])
        xevenarr.append(i[0])

    uncrt = {}
    for region in [-1, 1]:
        for layer in [1, 2]:
            for ieta in range(1, 9):
                even_chamber_count = 0
                odd_chamber_count = 0
                even_list = []
                odd_list = []
                for chamber in range(1, 37):
                    h = f.Get(f"h_{region}_{layer}_{chamber}_{ieta}")
                    h_list = np.array([h.GetBinContent(i) for i in range(1, 31)])
                    if sum(h_list) != 0:
                        if chamber % 2 == 0:
                            even_chamber_count += 1
                            even_list.append(h_list)
                        else:
                            odd_chamber_count += 1
                            odd_list.append(h_list)
                even_list = np.array(even_list).T
                odd_list = np.array(odd_list).T
                uncrt[f'{region}_{layer}_{ieta}_even'] = even_list.std(axis=1)
                uncrt[f'{region}_{layer}_{ieta}_odd'] = odd_list.std(axis=1)

    fit_f = {}
    r_inst_lumi = 1.0
    cvs = ROOT.TCanvas('', '', 1200, 900)
    for region in [-1, 1]:
        region_str = 'M' if region == -1 else 'P'
        for layer in [1, 2]:
            gs = {}
            for chamber in ['even', 'odd']:
                hs = {}
                yarr = array('f')
                xerrarr = array('f')
                yerrarr = array('f')
                for ieta in range(1, 9):
                    hs[ieta] = f.Get(f"h_{region}_{layer}_{ieta}_{chamber}")
                    for i in range(1, 21):
                        # hs[ieta].SetBinError(i, uncrt[f'{region}_{layer}_{ieta}_{chamber}'][i-1])
                        break

                for ieta in range(1, 9):
                    # f.Get(f"h_{region}_{layer}_{ieta}_{chamber}") = f.Get(f"h_{region}_{layer}_{ieta}_{chamber}")
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"] = ROOT.TF1("myfunc", "[0] + [1]*x", 0, 1000)
                    _ = hs[ieta].Fit(fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"], 'F')
                    br_15 = fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"](r_inst_lumi)
                    err = fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].GetParErrors()
                    print(f'{region_str}, {layer}, {chamber}, {ieta = }\n{fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].GetParameters()[1]}')
                    xerrarr.append(0)
                    yerrarr.append(err[0] + err[1] * r_inst_lumi)
                    yarr.append(br_15)
    # if not os.path.isdir(f"{file_path}/fit_values"):
                with open(f"{file_path}/fit_values/GE11-{region_str}-L{layer}-{chamber}.txt", 'w') as txt:
                    writer = csv.writer(txt, delimiter='\t')
                    writer.writerow(['eta'] + list(eta_pos[chamber][f'L{layer}'].values()))
                    writer.writerow(['values'] + list(np.array(yarr)))
                    writer.writerow(['values+uncrt'] + list(np.array(yarr)+np.array(yerrarr)))
                    writer.writerow(['values-uncrt'] + list(np.array(yarr)-np.array(yerrarr)))
                print(yarr, yarr + yerrarr)

                # h_tmp = f.Get(f"h_{region}_{layer}_8_{chamber}")
                hs[8].Draw('E')
                hs[8].SetTitle(f"GE11-{region_str}-L{layer}-{chamber}")

                leg = ROOT.TLegend(0.15, 0.55, 0.4, 0.85)
                for ieta in range(1, 9):
                    leg.AddEntry(hs[ieta], r'i_{#eta} = '+f'{ieta} ({ieta_eta[ieta-1]} < '+r'|#eta|'+f' <{ieta_eta[ieta]})','lep')
                    hs[ieta].DrawCopy("E SAME")
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].SetLineColor(hs[ieta].GetLineColor())
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].Draw("same")
                leg.SetFillStyle(0)
                leg.SetBorderSize(0)
                leg.Draw()
                txt = ROOT.TLatex()
                # txt.DrawLatexNDC(0.52, 0.7, f"Hit rate at L = {r_inst_lumi}"+r" x 10^{34}cm^{-2}s^{-1}")
                txt.SetTextFont(61)
                txt.SetTextSize(0.055)
                txt.DrawLatexNDC(0.1, 0.91, "CMS")
                txt.SetTextFont(52)
                txt.SetTextSize(0.03)
                txt.DrawLatexNDC(0.19, 0.91, f"Preliminary")
                txt.SetTextSize(0.025)
                txt.DrawLatexNDC(0.62, 0.91, f"Fill {fill_number}"+\
                        r"#sqrt{s}"+\
                        f" = 13.6 TeV ({year[fill_number]}) {intg_lumi[fill_number]}"+\
                        r"fb^{-1}")
                # cvs.SaveAs(f"{file_path}/fit/fit_{region}_{layer}_{chamber}.png")
                xarr = xevenarr if chamber == 'even' else xoddarr
                if chamber == 'odd':
                    gs[chamber] = ROOT.TGraphErrors(8, xarr, yarr, xerrarr, yerrarr)
                    gs[f'{chamber}_band'] = ROOT.TGraph(16)
                else:
                    gs[chamber] = ROOT.TGraphErrors(8, xarr, yarr, xerrarr, yerrarr)
                    gs[f'{chamber}_band'] = ROOT.TGraph(12)
                if chamber == 'odd':
                    r_fit_odd = ROOT.TF1("rfunc", "expo(0)", 1, -1)
                    _ = gs['odd'].Fit(r_fit_odd, 'F')
                    odd_f_par = r_fit_odd.GetParameters()
                    odd_f_err = r_fit_odd.GetParErrors()
                else:
                    r_fit_even = ROOT.TF1("rfunc", "expo(0)", 1, -1)
                    _ = gs['even'].Fit(r_fit_even, 'F')
                    even_f_par = r_fit_even.GetParameters()
                    even_f_err = r_fit_even.GetParErrors()


                gs[chamber].SetMarkerSize(2)
                gs[chamber].SetMarkerStyle(22)
                gs[chamber].SetTitle(f"GE11-{region_str}-L{layer}")# -{chamber}")
                gs[chamber].GetXaxis().SetTitle("R [cm]")
                gs[chamber].GetYaxis().SetTitle(r"Hit Rate [Hz / cm^{2}]")
                gs[chamber].SetMinimum(0.)
                gs[chamber].SetMaximum(500.)
            txt = ROOT.TLatex()
            txt.SetTextFont(43)
            txt.SetTextSize(40)
            leg = ROOT.TLegend(0.52, 0.5, 0.8, 0.7)
            oddupperarr = array('f')
            oddlowerarr = array('f')
            evenupperarr = array('f')
            evenlowerarr = array('f')
            odd_lower_f = lambda x: math.exp((odd_f_par[0] - odd_f_err[0]) + (odd_f_par[1] - odd_f_err[1]) * x)
            odd_upper_f = lambda x: math.exp((odd_f_par[0] + odd_f_err[0]) + (odd_f_par[1] + odd_f_err[1]) * x)
            even_lower_f = lambda x: math.exp((even_f_par[0] - even_f_err[0]) + (even_f_par[1] - even_f_err[1]) * x)
            even_upper_f = lambda x: math.exp((even_f_par[0] + even_f_err[0]) + (even_f_par[1] + even_f_err[1]) * x)

            for i in range(251):
                oddlowerarr.append(odd_lower_f(xallarr[i]))
                oddupperarr.append(odd_upper_f(xallarr[i]))
                evenlowerarr.append(even_lower_f(xallarr[i]))
                evenupperarr.append(even_upper_f(xallarr[i]))

            g_odd_band = ROOT.TGraph(502)
            g_odd_upper = ROOT.TGraph(251, xallarr, oddupperarr)
            g_odd_lower = ROOT.TGraph(251, xallarr, oddlowerarr)
            g_even_band = ROOT.TGraph(502)
            g_even_upper = ROOT.TGraph(251, xallarr, evenupperarr)
            g_even_lower = ROOT.TGraph(251, xallarr, evenlowerarr)

            for i in range(251):
                g_odd_band.SetPoint(i, xallarr[i], oddupperarr[i])
                g_odd_band.SetPoint(251 + i, xallarr[251 - i - 1], oddlowerarr[251 - i - 1])
                g_even_band.SetPoint(i, xallarr[i], evenupperarr[i])
                g_even_band.SetPoint(251 + i, xallarr[251 - i - 1], evenlowerarr[251 - i - 1])

            g_odd_upper.SetLineColorAlpha(ROOT.kRed, 0.7)
            g_odd_lower.SetLineColorAlpha(ROOT.kRed, 0.7)
            g_even_upper.SetLineColorAlpha(ROOT.kBlue, 0.7)
            g_even_lower.SetLineColorAlpha(ROOT.kBlue, 0.7)
            g_odd_band.SetFillStyle(4010)
            # g_odd_band.SetFillColor(ROOT.kGreen)
            g_odd_band.SetFillColorAlpha(ROOT.kRed, 0.05)
            g_even_band.SetFillStyle(4003)
            # g_even_band.SetFillColor(ROOT.kBlue)
            g_even_band.SetFillColorAlpha(ROOT.kBlue, 0.05)
            gs['even'].GetFunction("rfunc").SetLineColor(ROOT.kBlue)
            gs['odd'].GetFunction("rfunc").SetLineColor(ROOT.kRed)
            gs['even'].GetFunction("rfunc").SetRange(0, 250)
            gs['odd'].GetFunction("rfunc").SetRange(0, 250)
            gs['odd'].GetXaxis().SetLimits(125, 250)
            gs['even'].SetMarkerColor(ROOT.kBlue)
            # gs['low_even'].SetMarkerColor(ROOT.kBlue)
            gs['odd'].SetMarkerColor(ROOT.kRed)
            gs['odd'].Draw("AP")
            gs['even'].Draw("P")
            # gs['low_even'].Draw("P")
            g_odd_band.Draw("f")
            g_even_band.Draw("f")
            g_odd_upper.Draw("l")
            g_odd_lower.Draw("l")
            g_even_upper.Draw("l")
            g_even_lower.Draw("l")


            cvs.Update()
            stats1 = gs['odd'].GetListOfFunctions().FindObject('stats')
            stats2 = gs['even'].GetListOfFunctions().FindObject('stats')
            stats1.Draw()
            stats2.Draw()
            stats1.SetTextColor(ROOT.kRed)
            stats2.SetTextColor(ROOT.kBlue)
            stats1.SetX1NDC(0.72)
            stats1.SetX2NDC(0.92)
            stats1.SetY1NDC(0.75)
            stats2.SetX1NDC(0.52)
            stats2.SetX2NDC(0.72)
            stats2.SetY1NDC(0.75)
            leg.AddEntry(gs['even'], 'even chambers', 'lep')
            leg.AddEntry(gs['odd'], 'odd chambers', 'lep')
            leg.SetFillStyle(0)
            leg.SetBorderSize(0)
            leg.Draw()
            txt.DrawLatexNDC(0.47, 0.7, f"Hit rate at L = {r_inst_lumi}"+r" x 10^{34}cm^{-2}s^{-1}")
            txt.SetTextFont(61)
            txt.SetTextSize(0.055)
            txt.DrawLatexNDC(0.1, 0.91, "CMS")
            txt.SetTextFont(52)
            txt.SetTextSize(0.03)
            txt.DrawLatexNDC(0.19, 0.91, f"Preliminary")
            txt.SetTextSize(0.025)
            # txt.DrawLatexNDC(0.62, 0.95, r"Fill 8456 #sqrt{s} = 13.6 TeV (2022) 0.67fb^{-1}")
            txt.DrawLatexNDC(0.62, 0.95, f"Fill {fill_number}"+\
                    r"#sqrt{s}"+\
                    f" = 13.6 TeV ({year[fill_number]}) {intg_lumi[fill_number]}"+\
                    r"fb^{-1}")
            # txt.DrawLatexNDC(0.85, 0.05, f"Avg Lumi. = 1.0"+r" x 10^{34}cm^{-2}s^{-1}")
            # txt.DrawLatexNDC(0.15, 0.5, f"Fill 8220")
            # txt.SetTextSize(0.6)
            # txt.DrawLatexNDC(0.45, 0.3, title)
            cvs.SaveAs(f"{file_path}/fit/GE11_{region_str}_L{layer}.png")# _{chamber}.png")


            for chamber in ['even', 'odd']:
                yarr = array('f')
                xerrarr = array('f')
                yerrarr = array('f')
                ylowarr = array('f')
                xlowerrarr = array('f')
                ylowerrarr = array('f')
                for ieta in range(1, 9):
                    # f.Get(f"h_{region}_{layer}_{ieta}_{chamber}") = f.Get(f"h_{region}_{layer}_{ieta}_{chamber}")
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"] = ROOT.TF1("myfunc", "[0] + [1]*x", 0, 1000)
                    _ = f.Get(f"h_{region}_{layer}_{ieta}_{chamber}").Fit(fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"], 'F')
                    br_15 = fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"](r_inst_lumi)
                    err = fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].GetParErrors()
                    # if chamber == 'even' and ieta < 3:
                    #     xlowerrarr.append(0)
                    #     ylowerrarr.append(err[0] + err[1] * r_inst_lumi)
                    #     ylowarr.append(br_15)
                    #     continue
                    xerrarr.append(0)
                    yerrarr.append(err[0] + err[1] * r_inst_lumi)
                    yarr.append(br_15)
                h_tmp = f.Get(f"h_{region}_{layer}_8_{chamber}")
                h_tmp.SetTitle(f"GE11-{region_str}-L{layer}-{chamber}")
                # h_tmp.GetYaxis().SetRange(0, 4000)
                # h_tmp.SetAxisRange(0, 1000, 'Y')
                h_tmp.Draw()
                # f.Get(f"h_{region}_{layer}_8_{chamber}").Draw()
                leg = ROOT.TLegend(0.15, 0.55, 0.5, 0.85)
                for ieta in range(1, 9):
                    # if chamber == 'even' and ieta < 3: continue
                    leg.AddEntry(f.Get(f"h_{region}_{layer}_{ieta}_{chamber}"), r'i_{#eta} = '+f'{ieta} ({ieta_eta[ieta-1]} < '+r'|#eta|'+f' <{ieta_eta[ieta]})','lep')
                    f.Get(f"h_{region}_{layer}_{ieta}_{chamber}").Draw("same")
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].Draw("same")
                    fit_f[f"h_{region}_{layer}_{ieta}_{chamber}"].SetLineColor(f.Get(f"h_{region}_{layer}_{ieta}_{chamber}").GetLineColor())
                leg.SetFillStyle(0)
                leg.SetBorderSize(0)
                leg.Draw()
                cvs.SaveAs(f"{file_path}/fit/fit_{region}_{layer}_{chamber}.png")
                xarr = xevenarr if chamber == 'even' else xoddarr
                # if chamber == 'even':
                if False:
                    gs[chamber] = ROOT.TGraphErrors(6, xarr, yarr, xerrarr, yerrarr)
                    gs['low_even'] = ROOT.TGraphErrors(2, xlowarr, ylowarr, xlowerrarr, ylowerrarr)
                else:
                    gs[chamber] = ROOT.TGraphErrors(8, xarr, yarr, xerrarr, yerrarr)
                r_fit = ROOT.TF1("rfunc", "expo(0)", -1, -1)
                _ = gs[chamber].Fit(r_fit, 'F')
                f_par = r_fit.GetParameters()
                f_err = r_fit.GetParErrors()
                gs[chamber].SetMarkerSize(2)
                gs[chamber].SetMarkerStyle(22)
                # gs['low_even'].SetMarkerSize(2)
                # gs['low_even'].SetMarkerStyle(22)
                gs[chamber].GetFunction("rfunc").SetLineColor(ROOT.kBlack)
                gs[chamber].SetTitle(f"GE11-{region_str}-L{layer}-{chamber}")
                gs[chamber].GetXaxis().SetTitle("R [cm]")
                gs[chamber].GetYaxis().SetTitle(r"Hit Rate [Hz / cm^{2}]")
                gs[chamber].SetMinimum(0.)
                gs[chamber].SetMaximum(500.)

                upperarr = array('f')
                lowerarr = array('f')

                lower_f = lambda x: math.exp((f_par[0] - f_err[0]) + (f_par[1] - f_err[1]) * x)
                upper_f = lambda x: math.exp((f_par[0] + f_err[0]) + (f_par[1] + f_err[1]) * x)

                for i in range(251):
                    lowerarr.append(lower_f(xallarr[i]))
                    upperarr.append(upper_f(xallarr[i]))

                g_band = ROOT.TGraph(482)
                g_upper = ROOT.TGraph(251, xallarr, upperarr)
                g_lower = ROOT.TGraph(251, xallarr, lowerarr)

                for i in range(251):
                    g_band.SetPoint(i, xallarr[i], upperarr[i])
                    g_band.SetPoint(251 + i, xallarr[251 - i - 1], lowerarr[251 - i - 1])

                g_band.SetFillStyle(4010)
                g_lower.SetLineColorAlpha(ROOT.kBlue, 0.7)
                g_upper.SetLineColorAlpha(ROOT.kBlue, 0.7)
                g_band.SetFillColorAlpha(ROOT.kBlue, 0.1)
                gs[chamber].GetFunction("rfunc").SetRange(0, 250)
                gs[chamber].GetXaxis().SetLimits(125, 250)
                gs[chamber].Draw("AP")
                # if chamber == 'even':
                #     gs['low_even'].Draw('P')
                g_band.Draw("f")
                g_upper.Draw("l")
                g_lower.Draw("l")
                cvs.Update()
                stats1 = gs[chamber].GetListOfFunctions().FindObject('stats')
                stats1.Draw()
                txt = ROOT.TLatex()
                txt.SetTextFont(43)
                txt.SetTextSize(38)
                txt.DrawLatexNDC(0.47, 0.7, f"Hit rate at L = {r_inst_lumi}"+r" x 10^{34}cm^{-2}s^{-1}")
                txt.SetTextFont(61)
                txt.SetTextSize(0.055)
                txt.DrawLatexNDC(0.1, 0.91, "CMS")
                txt.SetTextFont(52)
                txt.SetTextSize(0.03)
                txt.DrawLatexNDC(0.19, 0.91, f"Preliminary")
                txt.SetTextSize(0.025)
                # txt.DrawLatexNDC(0.62, 0.95, r"Fill 8456 #sqrt{s} = 13.6 TeV (2022) 0.67fb^{-1}")
                txt.DrawLatexNDC(0.62, 0.95, f"Fill {fill_number}"+\
                    r"#sqrt{s}"+\
                    f" = 13.6 TeV ({year[fill_number]}) {intg_lumi[fill_number]}"+\
                    r"fb^{-1}")
                cvs.SaveAs(f"{file_path}/fit/GE11_{region_str}_L{layer}_{chamber}.png")

if __name__=='__main__':
    main()
    main2()
