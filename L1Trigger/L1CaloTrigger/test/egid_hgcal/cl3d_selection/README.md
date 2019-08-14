# 3D Cluster selection
The next step is to run the cluster selection on the ntuples. To run on a single file, over all events...

```
python hgcal_l1t_cl3d_selection.py --sampleType electron_200PU --fileNumber <number of file to process>
```

If the ntuples are not stored in the default location, then specify the path to the files using the `--inputPath` option. Also, if using a different clustering algorithm then add the long TDirectory name to the `clusteringAlgoDirDict`. 

The script matches 3D clusters to gen particles e.g. for electrons requires a gen particle with pdgID=11, with the requirement dR between the cluster and the gen particle is less than 0.2. There is no gen matching for background (neutrino). Additionally clusters are required to have a pT > 20 (10) GeV for signal (background).

The output of this script is a flat ntuple with clusters corresponding to the input sampleType i.e. for signal you obtain an ntuple of gen-matched electron clusters, and for background you obtain an ntuple of pile-up initiated clusters. 

## Running in parallel
There is an additional script, `submit_cl3d_selection.py`, which allows you to run the cluster selection over each file in parallel. The number of files to run over can be set as an option, but the default is to run over all (specified in `totalFilesDict`). The jobs are submitted using the HTCondor batch.

```
python submit_cl3d_selection.py --sampleType electron_200PU
```

These jobs should not take long. You can specify the queue using the `--queue` option.

## Adding the cluster ntuples: test, train and all
The final step is to combine the output flat ntuples, into test (10%), train (90%) and all (100%) samples. This has been automated by the `add_files.py` script. The script calculates the number of files in the relevant directory and combines accordingly.

```
python add_files.py --sampleType electron_200PU --deleteIndividualFiles 1
```
The `--deleteIndividualFiles` option deletes all the individual flat ntuples that have been used to create the test, train and all samples. This should be used to avoid taking up to much space.
