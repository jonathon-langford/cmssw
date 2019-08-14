# Script for making efficiency plot
#  > Input: l1t ntuples produced in ./ntuples directory
#  > Output: eff plot vs pT/eta
#  > Note, not currently configured to plot efficiency for newly trained egid. For this, please update
#    L1T TPG software with the new models and remake the ntuples

import ROOT
import sys
import os
import math
from array import array
from optparse import OptionParser

# Define eta regions for different trainings
eta_regions = {"low":[1.5,2.7],"high":[2.7,3.0]}

print "~~~~~~~~~~~~~~~~~~~~~~~~ EFFICIENCY PLOTTER ~~~~~~~~~~~~~~~~~~~~~~~~"
def leave():
  print "~~~~~~~~~~~~~~~~~~~~~ EFFICIENCY PLOTTER (END) ~~~~~~~~~~~~~~~~~~~~~"
  sys.exit(1)

def get_options():
  parser = OptionParser()
  parser = OptionParser( usage="usage: python make_eff_plot.py <options>")
  parser.add_option("--signalType", dest="signalType", default='electron_200PU', help="Signal sample to plot") 
  parser.add_option("--clusteringAlgo", dest="clusteringAlgo", default="Histomaxvardr", help="Clustering algorithm used in ntuple production")
  parser.add_option("--minimumEff", dest="minimumEff", default=0.75, type='float', help="Minimum efficiency to plot")
  return parser.parse_args()

(opt,args) = get_options()

# Mapping to extract TDirectory for different clustering algo
clusteringAlgoDirDict = {"gen":"Floatingpoint8ThresholdDummyHistomaxvardrGenclustersntuple","Histomaxvardr":"Floatingpoint8ThresholdDummyHistomaxvardrGenclustersntuple","Histomaxvardr_stc":"Floatingpoint8SupertriggercellDummyHistomaxvardrClustersntuple"}

# Mapping: sample type to pdgid used for gen matching
pdgIdDict = {
  "electron":[11],
  "photon":[22]
}
pdgid = pdgIdDict[ opt.signalType.split("_")[0] ]

#Check: clustering exists in dir
clusteringAlgo = opt.clusteringAlgo
if clusteringAlgo not in clusteringAlgoDirDict:
  print " --> [ERROR] not configured for %s clustering. Leaving..."%clusteringAlgo
  leave()

# Check ntuples exist. If so then make combined ntuple using hadd
if os.path.isdir("%s/ntuples/%s"%(os.environ['HGCAL_L1T_BASE'],opt.signalType)):
  if not os.path.exists("%s/ntuples/%s/all.root"%(os.environ['HGCAL_L1T_BASE'],opt.signalType)):
    print " --> Making combined ntuple: ntuples/%s/all.root"%opt.signalType
    os.system("hadd %s/ntuples/%s/all.root %s/ntuples/%s/ntuple*"%(os.environ['HGCAL_L1T_BASE'],opt.signalType,os.environ['HGCAL_L1T_BASE'],opt.signalType))
else:
  print " --> [ERROR] No input ntuples for %s detected. Please make. Leaving..."%opt.signalType
  leave()

# Extract trees from input ntuple
f_in = ROOT.TFile("%s/ntuples/%s/all.root"%(os.environ['HGCAL_L1T_BASE'],opt.signalType))
genTree = f_in.Get("%s/HGCalTriggerNtuple"%clusteringAlgoDirDict["gen"])
cl3dTree = f_in.Get("%s/HGCalTriggerNtuple"%clusteringAlgoDirDict[ opt.clusteringAlgo ])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Define histograms for total, gen matched, passin quality flag for pt and eta
hist_tot_genpt = ROOT.TH1F("h_tot_genpt","",20,0,100)
hist_tot_geneta = ROOT.TH1F("h_tot_geneta","",64,-3.2,3.2)
hist_matched_genpt = ROOT.TH1F("h_matched_genpt","",20,0,100)
hist_matched_geneta = ROOT.TH1F("h_matched_geneta","",64,-3.2,3.2)
hist_egid_genpt = ROOT.TH1F("h_egid_genpt","",20,0,100)
hist_egid_geneta = ROOT.TH1F("h_egid_geneta","",64,-3.2,3.2)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Loop over events
print " --> Matching gen particles to cl3d"
for ev_idx in range( genTree.GetEntries() ):
  if ev_idx % 10000 == 0: print " --> Processing event: %g/%g"%(ev_idx,genTree.GetEntries())
  genTree.GetEntry(ev_idx)
  cl3dTree.GetEntry(ev_idx)

  #Extract number of gen particles + cl3d in event
  N_gen = genTree.gen_n
  N_cl3d = cl3dTree.cl3d_n

  # Loop over gen particles
  for gen_idx in range( N_gen ):

    # Apply selection and add to total histogram
    # If electron ...
    if abs( genTree.gen_pdgid[gen_idx] ) in pdgid:
      if genTree.gen_pt[gen_idx] > 30.:
        
        #Apply eta selection: slighlty tighter
        if( abs( genTree.gen_eta[gen_idx] ) > (eta_regions['low'][0]+0.05))&( abs( genTree.gen_eta[gen_idx] ) <= (eta_regions['high'][1]-0.05) ):

          hist_tot_genpt.Fill( genTree.gen_pt[gen_idx] )
          hist_tot_geneta.Fill( genTree.gen_eta[gen_idx] )

          # Define 4 vector for gen particle
          gen_p4 = ROOT.TLorentzVector()
          gen_p4.SetPtEtaPhiE( genTree.gen_pt[gen_idx], genTree.gen_eta[gen_idx], genTree.gen_phi[gen_idx], genTree.gen_energy[gen_idx] )
  
          # Loop over clusters in events: pT > 20 GeV (choose highest pT cluster) and dR < 0.2
          cl3d_genmatched_maxpt_idx = -1
          cl3d_genmatched_maxpt = -999.
          for cl3d_idx in range(N_cl3d):
            # Apply selection
            if cl3dTree.cl3d_pt < 20.: continue
            # Define 4 cevtor for cl3d
            cl3d_p4 = ROOT.TLorentzVector()
            cl3d_p4.SetPtEtaPhiE( cl3dTree.cl3d_pt[cl3d_idx], cl3dTree.cl3d_eta[cl3d_idx], cl3dTree.cl3d_phi[cl3d_idx], cl3dTree.cl3d_energy[cl3d_idx] )

            # Require clister to be in dR < 0.2
            if gen_p4.DeltaR(cl3d_p4) < 0.2:
            
              # If cluster pT > present max then set
              if cl3d_p4.Pt() > cl3d_genmatched_maxpt:
                cl3d_genmatched_maxpt = cl3d_p4.Pt()
                cl3d_genmatched_maxpt_idx = cl3d_idx

          #If gen matched idx set, then fill gen matched histo
          hist_matched_genpt.Fill( genTree.gen_pt[gen_idx] )
          hist_matched_geneta.Fill( genTree.gen_eta[gen_idx] )

          # egid: use quality flag
          if cl3dTree.cl3d_quality[cl3d_genmatched_maxpt_idx] > 0:
            hist_egid_genpt.Fill( genTree.gen_pt[gen_idx] )
            hist_egid_geneta.Fill( genTree.gen_eta[gen_idx] )
         
# END OF EVENTS LOOP
print " --> Finished processing events..."
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MAKE EFFICIENCY PLOTS
print " --> Making efficiency plots: function of gen pt and gen eta..." 
hist_eff_genpt = hist_egid_genpt.Clone()
hist_eff_genpt.Draw()
raw_input("Press any key to continue...")
hist_eff_geneta = hist_egid_geneta.Clone()
# Deal with uncertainties correctly
hist_eff_genpt.Sumw2()
hist_eff_geneta.Sumw2()
# Divide by total histogram
hist_eff_genpt.Divide( hist_tot_genpt )
hist_eff_geneta.Divide( hist_tot_geneta )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Make canvases
ROOT.gStyle.SetOptStat(0)
#genpt
canv_genpt = ROOT.TCanvas("c_genpt","c_genpt")
hist_eff_genpt.GetYaxis().SetRangeUser(opt.minimumEff,1.1)
hist_eff_genpt.GetYaxis().SetTitle("(L1>thr. & matched to GEN)/GEN")
hist_eff_genpt.GetYaxis().SetLabelSize(0.03)
hist_eff_genpt.GetYaxis().SetTitleSize(0.04)
hist_eff_genpt.GetYaxis().SetTitleOffset(1.0)
hist_eff_genpt.GetXaxis().SetRangeUser(25,100)
hist_eff_genpt.GetXaxis().SetTitle("p_{T}^{GEN}  [GeV]")
hist_eff_genpt.GetXaxis().SetLabelSize(0.03)
hist_eff_genpt.GetXaxis().SetTitleSize(0.04)
hist_eff_genpt.GetXaxis().SetTitleOffset(0.95)

hist_eff_genpt.SetMarkerColor(2)
hist_eff_genpt.SetMarkerSize(1.3)
hist_eff_genpt.SetMarkerStyle(34)
hist_eff_genpt.SetLineColor(2)
hist_eff_genpt.SetLineWidth(2)

hist_eff_genpt.Draw("P Hist")

#Draw a line at 100% efficiency
line_genpt = ROOT.TLine(25,1,100,1)
line_genpt.SetLineWidth(2)
line_genpt.SetLineStyle(2)
line_genpt.Draw("Same")

#Latex
lat_genpt = ROOT.TLatex()
lat_genpt.SetTextFont(42)
lat_genpt.SetLineWidth(2)
lat_genpt.SetTextAlign(11)
lat_genpt.SetNDC()
lat_genpt.SetTextSize(0.04)
lat_genpt.DrawLatex(0.12,0.85,"%s, %s, p_{T}^{L1} > 20GeV, p_{T}^{GEN} > 30GeV"%(opt.signalType.split("_")[1],opt.clusteringAlgo))

#Legend
leg_genpt = ROOT.TLegend(0.6,0.2,0.89,0.35)
leg_genpt.SetFillColor(0)
leg_genpt.SetLineColor(0)
leg_genpt.AddEntry(hist_eff_genpt,"TPG (quality flag)","P")
leg_genpt.Draw("Same")

# Check if directory exists to make plots
if not os.path.isdir("./plots"): os.system("mkdir plots")
canv_genpt.SaveAs("./plots/efficiency_vs_genpt.png")
canv_genpt.SaveAs("./plots/efficiency_vs_genpt.pdf")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# gen eta
canv_geneta = ROOT.TCanvas("c_geneta","c_geneta")
hist_eff_geneta.GetYaxis().SetRangeUser(opt.minimumEff,1.1)
hist_eff_geneta.GetYaxis().SetTitle("(L1>thr. & matched to GEN)/GEN")
hist_eff_geneta.GetYaxis().SetLabelSize(0.03)
hist_eff_geneta.GetYaxis().SetTitleSize(0.04)
hist_eff_geneta.GetYaxis().SetTitleOffset(1.0)
hist_eff_geneta.GetXaxis().SetRangeUser(-3.2,3.2)
hist_eff_geneta.GetXaxis().SetTitle("#eta^{GEN}")
hist_eff_geneta.GetXaxis().SetLabelSize(0.03)
hist_eff_geneta.GetXaxis().SetTitleSize(0.04)
hist_eff_geneta.GetXaxis().SetTitleOffset(0.95)

hist_eff_geneta.SetMarkerColor(2)
hist_eff_geneta.SetMarkerSize(1.3)
hist_eff_geneta.SetMarkerStyle(34)
hist_eff_geneta.SetLineColor(2)
hist_eff_geneta.SetLineWidth(2)

hist_eff_geneta.Draw("P Hist")

#Draw a line at 100% efficiency
line_geneta = ROOT.TLine(25,1,100,1)
line_geneta.SetLineWidth(2)
line_geneta.SetLineStyle(2)
line_geneta.Draw("Same")

# Also lines for difference eta regions
eta_lines = {}
eta_values = []
for reg in eta_regions:
  for bound in [0,1]:
    if eta_regions[reg][bound] in eta_values: continue #avoid double lines
    else: 
      eta_values.append( eta_regions[reg][bound] )
      eta_lines["%s_%g_neg"%(reg,bound)] = ROOT.TLine( -1*eta_regions[reg][bound], opt.minimumEff, -1*eta_regions[reg][bound], 1.03 )
      eta_lines["%s_%g_neg"%(reg,bound)].SetLineWidth(2)
      eta_lines["%s_%g_neg"%(reg,bound)].SetLineStyle(2)
      eta_lines["%s_%g_neg"%(reg,bound)].Draw("Same")
      eta_lines["%s_%g_pos"%(reg,bound)] = ROOT.TLine( eta_regions[reg][bound], opt.minimumEff, eta_regions[reg][bound], 1.03 )
      eta_lines["%s_%g_pos"%(reg,bound)].SetLineWidth(2)
      eta_lines["%s_%g_pos"%(reg,bound)].SetLineStyle(2)
      eta_lines["%s_%g_pos"%(reg,bound)].Draw("Same")

#Latex
lat_geneta = ROOT.TLatex()
lat_geneta.SetTextFont(42)
lat_geneta.SetLineWidth(2)
lat_geneta.SetTextAlign(11)
lat_geneta.SetNDC()
lat_geneta.SetTextSize(0.04)
lat_geneta.DrawLatex(0.12,0.85,"%s, %s, p_{T}^{L1} > 20GeV, p_{T}^{GEN} > 30GeV"%(opt.signalType.split("_")[1],opt.clusteringAlgo))

#Legend
leg_geneta = ROOT.TLegend(0.6,0.2,0.89,0.35)
leg_geneta.SetFillColor(0)
leg_geneta.SetLineColor(0)
leg_geneta.AddEntry(hist_eff_geneta,"TPG (quality flag)","P")
leg_geneta.Draw("Same")

# Check if directory exists to make plots
canv_geneta.SaveAs("./plots/efficiency_vs_geneta.png")
canv_geneta.SaveAs("./plots/efficiency_vs_geneta.pdf")

print " --> All plots saved!"

leave()
