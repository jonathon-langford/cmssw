# Script to plot cl3d variable (normalised)
#  > Input: selected cl3d ntuple in cl3d_selection/ or cl3d ntuple in training/results/
#  > Output: plot of vl3d variable

import ROOT
import sys
import os
from array import array
from optparse import OptionParser

print "~~~~~~~~~~~~~~~~~~~~~~~~ CL3D VAR PLOTTER ~~~~~~~~~~~~~~~~~~~~~~~~"
def leave():
  print "~~~~~~~~~~~~~~~~~~~~~ CL3D VAR PLOTTER (END) ~~~~~~~~~~~~~~~~~~~~~"
  sys.exit(1)

# Get options from option parser
def get_options():
  parser = OptionParser()
  parser = OptionParser( usage="usage: python make_cl3dVar_plot.py <options>" )
  parser.add_option("--inputMap", dest="inputMap", default="electron_200PU,Histomaxvardr,selection,2,23,Hist", help="List of inputs to plot, of the form:  sample type,clustering algo.,ntuple stage [selection,evaluation],colour,marker style,plotting option:..." )
  parser.add_option("--variable", dest="variable", default="pt", help="Variable to plot")
  parser.add_option("--legendMap", dest="legendMap", default='', help="List of elements of legend. Separate each element with '+'. Format: <text>,<colour>,<marker>,<option>+<text2>,<colour2>,<marker2>,<option2>+..." )
  parser.add_option("--legendPosition", dest="legendPosition", default="std", help="Position to plot legend in plot [std,centre,bottom_right]")
  parser.add_option("--batch", dest="batch", default=0, type='int', help="Suppress output of plots to screen")
  return parser.parse_args()

(opt,args) = get_options()

# Define sample to tree mapping
treeMap = {
  "electron":"e_sig",
  "photon":"g_sig",
  "pion":"pi_bkg",
  "neutrino":"pu_bkg"
}

# HARDCODED Variable plotting options: [bins,minium,maximum,log scale]
variable_plotting_options = {
  'pt':[150,0,150,0], 
  'eta':[50,-3.14,3.14,0], 
  'phi':[50,-3.14,3.14,0], 
  'clusters_n':[60,0,60,0], 
  'showerlength':[60,0,60,0], 
  'coreshowerlength':[30,0,30,0], 
  'firstlayer':[20,0,20,0], 
  'maxlayer':[50,0,50,0], 
  'seetot':[100,0,0.20,0], 
  'seemax':[50,0,0.1,0], 
  'spptot':[100,0,0.2,1], 
  'sppmax':[100,0,0.2,1], 
  'szz':[100,0,100,1], 
  'srrtot':[150,0,0.03,1], 
  'srrmax':[150,0,0.03,1], 
  'srrmean':[50,0,0.01,1], 
  'emaxe':[60,0,1.2,0], 
  'bdteg':[50,-1,1.,1], 
  'quality':[6,-1,5,0]
}
if "bdt" in opt.variable: variable_plotting_options[opt.variable] = [50,-1,1.,1]
if opt.variable not in variable_plotting_options: 
  print " --> [ERROR] Variables (%s) not supported. Leaving..."%opt.variable
  leave()

# Dictionaries to store files, trees and histograms from inputs
fileDict = {}
treeDict = {}
histDict = {}

# Extract inputs from map and store in dictionary
input_list = []
for _input in opt.inputMap.split(":"):
  inputInfo = _input.split(",")
  if len( inputInfo )!=6:
    print " --> [ERROR] Invalid input. Use the form: <sample type>,<clustering algo.>,<ntuple stage [selection,evaluation]>,<colour>,<marker style>,<plotting option>. Leaving..."
    leave()
  input_list.append({})
  input_list[-1]['sampleType'] = inputInfo[0]
  input_list[-1]['cl3d_algo'] = inputInfo[1]
  input_list[-1]['ntuple'] = inputInfo[2]
  input_list[-1]['colour'] = inputInfo[3]
  input_list[-1]['marker'] = inputInfo[4]
  input_list[-1]['option'] = inputInfo[5]

# Store maximum value of all histograms for keeping on same plot
maximum_value = 0
#Output options
if opt.batch: ROOT.gROOT.SetBatch(ROOT.kTRUE)
# Plotting options
binning = variable_plotting_options[opt.variable][:-1]
setLogY = variable_plotting_options[opt.variable][-1]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CONFIGURE OUTPUT
ROOT.gStyle.SetOptStat(0)
canv = ROOT.TCanvas("c","c")
if setLogY: canv.SetLogy()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LOOP OVER INPUTS: create histogram from var in tree
for i in input_list:

  key = "%s_%s_%s"%(i['sampleType'],i['cl3d_algo'],i['ntuple'])
  if i['ntuple'] == 'selection': fileDict[key] = ROOT.TFile( "%s/cl3d_selection/%s/%s_%s_all.root"%(os.environ['HGCAL_L1T_BASE'],i['sampleType'],i['sampleType'],i['cl3d_algo']) )
  elif i['ntuple'] == 'evaluation': fileDict[key] = ROOT.TFile( "%s/training/results/%s/%s_%s_all_eval.root"%(os.environ['HGCAL_L1T_BASE'],i['sampleType'],i['sampleType'],i['cl3d_algo']) )
  else:
    print " --> [ERROR] Invalid ntuple location. Please use selection or evaluation"
    leave()

  treeDict[key] = fileDict[key].Get( treeMap[i['sampleType'].split("_")[0]] )
  histDict[key] = ROOT.TH1F("h_%s"%key, "", binning[0], binning[1], binning[2] )

  for ev in treeDict[key]: histDict[key].Fill( getattr(ev,"cl3d_%s"%opt.variable) )

  # normalise histograms
  histDict[key].Scale(1./histDict[key].GetEntries())

  # plotting options
  histDict[key].SetLineWidth(2)
  histDict[key].SetLineColor(int(i['colour']))
  histDict[key].SetMarkerColor(int(i['colour']))
  histDict[key].SetMarkerStyle(int(i['marker']))
  histDict[key].SetMarkerSize(1.2)
  histDict[key].GetYaxis().SetTitle("1/N dN/d(%s)"%opt.variable)
  histDict[key].GetXaxis().SetTitle("%s"%opt.variable)
  if( i['ntuple'] == "evaluation" )&( "bdt" in opt.variable ): 
    histDict[key].GetYaxis().SetTitleSize(0.03)
    histDict[key].GetYaxis().SetTitleOffset(1.3)
    histDict[key].GetXaxis().SetTitleSize(0.03)
    histDict[key].GetXaxis().SetTitleOffset(1.3)
  else: 
    histDict[key].GetYaxis().SetTitleSize(0.05)
    histDict[key].GetYaxis().SetTitleOffset(0.95)
    histDict[key].GetXaxis().SetTitleSize(0.05)
    histDict[key].GetXaxis().SetTitleOffset(0.95)

  # if maximum > current: save new maximum
  if histDict[key].GetMaximum() > maximum_value: maximum_value = histDict[key].GetMaximum()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LOOP OVER INPUTS AGAIN AND PLOT
for _idx in range( len( input_list ) ):
  i = input_list[_idx]
  key = "%s_%s_%s"%(i['sampleType'],i['cl3d_algo'],i['ntuple'])
  if _idx == 0:
    if( setLogY ):
      histDict[key].SetMaximum( 1.3*maximum_value )
      histDict[key].SetMinimum( 1e-4 )
    else:
      histDict[key].SetMaximum( 1.1*maximum_value )
    histDict[key].Draw("%s"%i['option'])
  else:
    histDict[key].Draw("SAME %s"%i['option'])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# FORMAT CANVAS
lat = ROOT.TLatex()
lat.SetTextFont(42)
lat.SetLineWidth(2)
lat.SetTextAlign(11)
lat.SetNDC()
lat.SetTextSize(0.05)
lat.DrawLatex(0.1,0.92,"#bf{HGCal L1T} #scale[0.75]{#it{Working Progress}}")
lat.DrawLatex(0.8,0.92,"14 TeV")

# Legend: get from option
entry_list = []
#Entry of type: text,colour,option
if opt.legendMap != "":
  for _entry in opt.legendMap.split("+"):
    entryInfo = _entry.split(",")
    if len(entryInfo) != 4:
      print "  --> [ERROR] Invalid legend entry. Exiting..."
      leave()
    entry_list.append({})
    entry_list[-1]['text'] = entryInfo[0]
    entry_list[-1]['colour'] = entryInfo[1]
    entry_list[-1]['marker'] = entryInfo[2]
    entry_list[-1]['option'] = entryInfo[3]

  graph_list = []
  #Create dummy graphs to place in legend
  for entry in entry_list:
    gr = ROOT.TGraph()
    gr.SetFillColor( int(entry['colour']) )
    gr.SetLineColor( int(entry['colour']) )
    gr.SetLineWidth( 2 )
    gr.SetMarkerColor( int(entry['colour']) )
    gr.SetMarkerStyle( int(entry['marker']) )
    gr.SetMarkerSize( 1.2 )
    graph_list.append( gr )

  # Create legend and add entries
  if opt.legendPosition == "centre": leg = ROOT.TLegend(0.38,0.65,0.62,0.88)
  elif opt.legendPosition == "bottom_right": leg = ROOT.TLegend(0.65,0.15,0.88,0.38)
  else: leg = ROOT.TLegend(0.65,0.65,0.88,0.88)
  #Create legend and add entries
  leg.SetFillColor(0)
  leg.SetLineColor(0)
  for _idx in range( len( entry_list ) ):
    entry = entry_list[_idx]
    leg.AddEntry( graph_list[_idx], "%s"%entry['text'], "%s"%entry['option'] )
  leg.Draw("Same")

canv.Update()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Save canvas
if not os.path.isdir("./plots"): os.system("mkdir plots")
canv.SaveAs( "%s/plotting/plots/cl3d_%s.png"%(os.environ['HGCAL_L1T_BASE'],opt.variable) )
canv.SaveAs( "%s/plotting/plots/cl3d_%s.pdf"%(os.environ['HGCAL_L1T_BASE'],opt.variable) )

if not opt.batch: raw_input("Press any key to continue...")
leave()
