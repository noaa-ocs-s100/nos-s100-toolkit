#!/usr/bin/env python
"""
Download and convert OFS output to S-111 format using an operational configuration.
The latest OFS output model run is downloaded from the FTP server, then is converted
to both default-grid and subset-grid S-111 files in parallel.  The resulting S-111
files are then moved to an operational storage volume for FTP dissemination.
"""

from multiprocessing import Pool
import shutil
import os
from glob import glob
import argparse

import ofs
from s100ofs import s111

# Max number of subprocess workers to spin up
MAXWORKERS = 2

SOURCE_PATH = "/opt/s100/"
DEST_PATH = "/win/ofsdata/%Y%m%d/HDF5/S111_1.0.0/"

MODEL_INDEX_FILE = {
    "cbofs": {
        "index_default_path": "{}indexes/CBOFS_Index_Default_500m.nc".format(SOURCE_PATH),
        "index_subset_path": "{}indexes/CBOFS_Index_Subgrid_Band4_500m.nc".format(SOURCE_PATH)
    },
    "dbofs": {
        "index_default_path": "{}indexes/DBOFS_Index_Default_500m.nc".format(SOURCE_PATH),
        "index_subset_path": "{}indexes/DBOFS_Index_Subgrid_Band4_500m.nc".format(SOURCE_PATH)
    }
}


def run_ofs(ofs_model):
    cycletime = ofs.get_latest_cycletime(ofs_model)
    if cycletime is None:
        print("Error: Latest model cycle time cannot be determined. Verify that system time is correct and review model cycle configuration.")
        return 1
    local_files = ofs.download(ofs_model, ofs.get_latest_cycletime(ofs_model), "{}netcdf/".format(SOURCE_PATH))

    workerPool = Pool(processes=max(1, MAXWORKERS))
    workers = []

    index_default_path = MODEL_INDEX_FILE[ofs_model]["index_default_path"]
    index_subset_path = MODEL_INDEX_FILE[ofs_model]["index_subset_path"]
    s111_dir = "{}hdf5/{}/".format(SOURCE_PATH, ofs_model)
    model_dir = "{}{}/".format(DEST_PATH, ofs_model.upper())

    # Call default grid processing
    workers.append(workerPool.apply_async(s111.roms_to_s111, (index_default_path, local_files, s111_dir, cycletime, ofs_model, ofs.MODELS[ofs_model]["ofs_metadata"], None)))

    # Call subgrid processing
    workers.append(workerPool.apply_async(s111.roms_to_s111, (index_subset_path, local_files, s111_dir, cycletime, ofs_model, ofs.MODELS[ofs_model]["ofs_metadata"], None)))

    s111_file_paths = []
    for w in workers:
        s111_file_paths.extend(w.get())

    # Copy s111 files to OCS FTP /win/ofsdata/{forecast_date}/HDF5/S111_1.0.0
    for s111_file_path in s111_file_paths:
        split_path = os.path.split(s111_file_path)
        dst = os.path.join(cycletime.strftime(model_dir), split_path[1])
        shutil.copyfile(s111_file_path, dst)

        # Remove s111 files from hdf5 directory
    delete_files = glob("{}/*.h5".format(s111_dir))
    for delete_files in delete_files:
        os.remove(delete_files)


def main():
    parser = argparse.ArgumentParser(description="Convert surface currents model output to S-111 HDF5 format operationally")
    parser.add_argument("-o", "--ofs_model", help="Identifier of target Operational Forecast System (OFS) to be processed (e.g. cbofs, dbofs)", required=True)
    args = parser.parse_args()

    ofs_model = args.ofs_model
    if not ofs_model or ofs_model.lower() not in MODEL_INDEX_FILE:
        parser.error(
            "A valid -o/--ofs_model must be specified. Possible values: {}".format(", ".join(list(MODEL_INDEX_FILE.keys()))))
        return 1
    ofs_model = ofs_model.lower()

    run_ofs(ofs_model)


if __name__ == "__main__":
    main()
