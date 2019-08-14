# Plotting scripts

## Efficiency plots
Plot efficiency of the e/gamma ID as a function of generator-level pT and eta. The efficiency is defined as the number of generator level electrons with a matching 3D cluster passing the e/gamma ID working point, divided by the number of generator level electrons. The gen electrons are required to have pT > 30 GeV, and the 3D clusters with pT > 20 GeV. Note, this script only accommodates the e/gamma ID in the TPG software (not any newly-trained BDTs). 

The script takes as input the original ntuples generated in the `ntuples` subfolder:

```
python make_eff_plot.py --signalType electron_200PU
```

You can set the minimum efficiency to plot using the `--minimumEff` option (default is 0.75). The output plots will be saved in the `plots` directory.

## 3D cluster variable plots
Plot 3d cluster variable distributions from the flat ntuples either in the `cl3d_selection` subfolder, or to plot one of the new BDT scores, in the `training/results` directory. For example, to plot the cluster p_T distribution for both signal (electron 200PU) and background (neutrino 200PU):

```
python make_cl3dVar_plot.py --inputMap electron_200PU,Histomaxvardr,selection,2,23,Hist:neutrino_200PU,Histomaxvardr,selection,1,23,Hist --variable pt --legendMap "electron 200PU,2,23,L+pile-up,1,23,L"
```

The `--inputMap` has the following format: (sampleType),(cl3d algo.),(location of ntuples: selection/evaluation),(ROOT colour),(ROOT marker),(ROOT plotting style).

The `--legendMap` option details the entries in the legend. Separate each entry with a "+" symbol. The format is: (text),(ROOT colour),(ROOT marker),(Entry style e.g. L=line)

To suppress output to screen use the option: `--batch 1`.

### Examples
Example cluster p_T distribution and efficiency vs gen eta plots are stored in the `plots` directory.

