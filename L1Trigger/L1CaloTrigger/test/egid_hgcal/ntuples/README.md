# Making the ntuples

This subfolder contains the CMSSW config script to create the signal and background ntuples for training the e/gamma ID. For standard ntuples you do not need to make changes to `hgcal_l1t_ntupliser_v9_cfg.py`. However if you wish to use additional clustering algorithms, please add to the trigger chains in [L94-96](https://github.com/jonathon-langford/hgcal_l1t_egid/blob/master/ntuples/hgcal_l1t_ntupliser_v9_cfg.py#L94-L96).

All operations are automated with the `crab_interface.py` script. The script is currently configured for the standard signal (electron 200PU) and background (neutrino 200PU). To run over different samples you will need to add the LFN to `sampleDict`, the total number of files to `totalFilesDict` and a identifier tag to `datasetTagDict`.

## Submission
CRAB is used to submit jobs to the grid. To run ntupliser over all samples for signal (background just replace electron_200PU with neutrino_200PU):

```
python crab_interface.py --mode sub --numberOfSamples -1 --sampleType electron_200PU
```

You need to use a storage site that you have write access for, using the option `--storageSite <Name of site e.g. T2_UK_London_IC'>`.

## Checking the status of submission
```
python crab_interface.py --mode status --sampleType electron_200PU
```

If any jobs have failed then you can resubmit with...
```
python crab_interface.py --mode resub --sampleType electron_200PU
```

## Extracting the ntuples
This mode should only be used when all jobs have finished. If so, then the following command will get the output ntuples and move to a directory. The default is in a directory with the name of the sampleType (e.g. electron_200PU) in the `ntuples` subfolder. To store in a user defined location then use the option `--outputPath <path to directory>`.

```
python crab_interface.py --mode extract --numberOfSamples -1 --sampleType electron_200PU
```

## Killing a crab submission
```
python crab_interface.py --mode kill --sampleType electron_200PU
```
