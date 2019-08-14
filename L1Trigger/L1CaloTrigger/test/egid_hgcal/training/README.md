# Training the e/gamma ID
This subfolder contains all the scripts to train the e/gamma ID BDT, convert to an xml file, evaluate the new BDT and then extract the working points and the ROC curves. 

The BDTs are trained with the `_train.root` output from the `cl3d_selection` subfolder. To train with electron as signal and pile-up as background:

```
python egid_training.py --signalType electron_200PU --backgroundType neutrino_200PU --bdtConfig baseline
```

The `--bdtConfig` option corresponds to the set of input features. There are currently two options: `baseline` and `full`. The list of input features are defined in [L36](https://github.com/jonathon-langford/hgcal_l1t_egid/blob/master/training/egid_training.py#L36). For new configurations, add to the `egid_vars` dictionary.

By default, the signal and background clusters are reweighted so the signal and background samples are in effect the same size. This can be turned off using `--reweighting 0`. Also, the hyperparameters of the BDT can be changed using the `--trainParams` option, and specifying the hyperparameters in a comma-separated list.

The `egid_training.py` trains a BDT separately in the high and low eta regions, and outputs both as `.model` files in the `models` directory.  

## Converting to xml
To convert the `.model` files to `.xml`:

```
python egid_to_xml.py --signalType electron_200PU --backgroundType neutrino_200PU --bdtConfig baseline
```

The output `.xml` files are stored in the `xml` directory. These can be added directly into the HGCal L1T TPG software in the [data](https://github.com/PFCal-dev/cmssw/tree/v3.13.4_1061p2/L1Trigger/L1THGCal/data) directory (keep the same naming convention e.g. egamma_id_histomax_370_higheta_v0.xml, where 370 corresponds to the version of the TPG software). You will then need to update [egammaIdentification.py](https://github.com/PFCal-dev/cmssw/blob/v3.13.4_1061p2/L1Trigger/L1THGCal/python/egammaIdentification.py) accordingly.

## Evaluating the newly-trained BDTs
To evaluate the trained BDTs on the test/all samples you can use the `egid_evaluate.py` script. This uses the output of `egid_to_xml.py` to describe the models. For example, if you have trained BDTs for both the `baseline` and `full` options, and want to evaluate both on the test sample:

```
python egid_evaluate.py --sampleType electron_200PU --dataset test --bdts electron_200PU_vs_neutrino_200PU:baseline,electron_200PU_vs_neutrino_200PU:full
```

The output is a flat ntuple of 3d clusters, with the new BDT scores. These are placed in the `results` directory.

## Summarising the performance
The `egid_summary.py` script outputs the performance of a BDT to the screen, in terms of the background rejections at various signal efficiency working points. The script can be used to compare amongst different BDTs. For example to look at the performance of the `baseline`, `full`, and original `tpg` BDTs you would run:

```
python egid_summary.py --inputMap electron_200PU,neutrino_200PU,Histomaxvardr,test --bdts electron_200PU_vs_neutrino_200PU:tpg:black,electron_200PU_vs_neutrino_200PU:baseline:blue,electron_200PU_vs_neutrino_200PU:full:red --outputROC 1
```

This takes as input the `_eval.root` files in the `results` directory, so make sure that you have evaluated all the BDTs that you want to summarise. The `--inputMap` option has the following format (signalType),(backgroundType),(cl3dAlgo),(sample), where sample can be train, test or all.

The script will output the BDT score working points for all bdts in the `wp` directory. These working points can then be added to the [egammaIdentification.py](https://github.com/PFCal-dev/cmssw/blob/v3.13.4_1061p2/L1Trigger/L1THGCal/python/egammaIdentification.py) script in the TPG software.

Finally, if the `--outputROC` option is used (on by default), the script will draw the ROC curves on the same canvas for all BDTs specified. The curves are plotted with the colours defined in the `--bdts` option. 
