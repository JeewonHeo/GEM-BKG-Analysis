import time
import ROOT
import numpy as np
ROOT.gROOT.SetBatch(True)


lumi = 0
# f = np.load('fill_8456/hit_time_ieta8.npy', allow_pickle='TRUE').item()
f = np.load('fill_8754/hit_time_ieta8.npy', allow_pickle='TRUE').item()

tlst = list(f['hit'].keys())
tlst.sort()

if lumi:
    f = f['lumi']
    tlst = list(f.keys())
    tlst.sort()

# bins = 2140
# min_time = 1669029677
# min_time = 1669075677
# max_time = 1669076788
min_time = min(tlst)
max_time = max(tlst)
bins = int((max_time - min_time) / 23.36)
# bins = int((max_time - min_time) / 1)
# ran = [bins, 1664620000, 1664670000]
ran = [bins, min_time, max_time]
h = ROOT.TH1F("", "", *ran)

for t in tlst:
    if lumi:
        h.Fill(t, f[t] / 10000)
    else:
        # print(len(set(f['event'][t])))
        # h.Fill(t, sum(f['hit'][t]) / 50)
        h.Fill(t, sum(f['hit'][t]) / len(set(f['event'][t])))

h.SetTitle("Average of All layers, ieta = 8")
h.GetXaxis().SetTitle("Time (hh:mm)")
if lumi:
    h.GetYaxis().SetTitle(r"Inst. Lumi. [10^{34}cm^{-2}s^{-1}]")
else:
    h.GetYaxis().SetTitle(r"Hit rate [Hz/cm^{2}]")
binsize = (ran[2] - ran[1]) / ran[0]
ticks = 21
print(f"{binsize = }")
print(ran[2] - ran[1])
t_h = f"{time.gmtime(h.GetBinCenter(1)).tm_hour}".zfill(2)
t_m = f"{time.gmtime(h.GetBinCenter(1)).tm_min}".zfill(2)
# h.GetXaxis().SetTickLength(0.10)
h.GetXaxis().SetBinLabel(1, f'{t_h}:{t_m}')
for i in range(1, ticks):
    t_h = f"{time.gmtime(h.GetBinCenter(i * bins // (ticks - 1))).tm_hour}".zfill(2)
    t_m = f"{time.gmtime(h.GetBinCenter(i * bins // (ticks - 1))).tm_min}".zfill(2)
    h.GetXaxis().SetBinLabel(i * bins // (ticks - 1), f'{t_h}:{t_m}')
h.GetXaxis().LabelsOption("h")
h.GetXaxis().SetLabelSize(0.05)
h.GetXaxis().SetTickLength(0)
# labels.SetNdivision(ticks)
# h.GetXaxis().SetNdivisions(ticks-1, 5, 0)
# h.GetXaxis().SetTimeDisplay(1)
# h.GetXaxis().SetNdivisions(-510)
# ti = ROOT.TDatime(1664620000)
# t = time.gmtime(1664620000)
# print(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
# a = ROOT.TDatime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec).Convert()
# ROOT.gStyle.SetTimeOffset(1664620000)
# h.GetXaxis().SetTimeFormat("%H:%M");
if lumi:
    h.Scale(1 / binsize)
else:
    # h.Scale(1 / (4 * binsize))
    # h.Scale(1 / (101 * binsize))
    # h.Scale(1 / (107 * binsize))
    # h.Scale(1 / (121 * binsize))  # 8456
    h.Scale(1 / (126 * binsize))  # 8754
cvs = ROOT.TCanvas('', '', 2400, 1000)
h.SetStats(0)
h.SetLineWidth(2)
# ROOT.gPad.SetGrid(1, 1)
# cvs.ReDrawAxis()
h.Draw('hist')
# h.DrawCopy()
cvs.Update()
cvs.SetGrid()
f1 = ROOT.TF1('f1', 'x', 0, ticks-1)
labels = ROOT.TGaxis(min_time, cvs.GetUymin(), max_time, cvs.GetUymin(), 'f1', (ticks-1))
labels.SetLabelSize(0)
labels.Draw()
txt = ROOT.TLatex()
txt.SetTextFont(61)
txt.SetTextSize(0.055)
txt.DrawLatexNDC(0.1, 0.91, "CMS")
txt.SetTextFont(52)
txt.SetTextSize(0.03)
txt.DrawLatexNDC(0.15, 0.91, f"Preliminary")
txt.SetTextSize(0.03)
# txt.DrawLatexNDC(0.76, 0.91, r"Fill 8456, #sqrt{s} = 13.6 TeV (2022) 0.67fb^{-1}")
txt.DrawLatexNDC(0.76, 0.91, r"Fill 8754, #sqrt{s} = 13.6 TeV (2023) 0.66fb^{-1}")
cvs.SetRightMargin(0.04)

# cvs.RedrawAxis()
# cvs.SaveAs('M_L1_21_time_vs_hit.png')
# cvs.SetLogy()
if lumi:
    cvs.SaveAs('time_lumi.png')
else:
    cvs.SaveAs('time_rate.png')
