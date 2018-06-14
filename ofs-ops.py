#!/usr/bin/env python
""" Execute S100OFS Operationally"""

from multiprocessing import Pool
import shutil
import os
from glob import glob

import ofs
from s100ofs import s111

# Max number of subprocess workers to spin up
MAXWORKERS = 2

SOURCE_PATH = "/opt/s100/"
DEST_PATH = "/win/ofsdata/{forecast_date}/HDF5/S111_1.0.0/"
OFS_MODEL = "cbofs"


def run_cbofs():
    cycletime = ofs.get_latest_cycletime(OFS_MODEL)
    if cycletime is None:
        print("Error: Latest model cycle time cannot be determined. Verify that system time is correct and review model cycle configuration.")
        return 1
    local_files = ofs.download(OFS_MODEL, ofs.get_latest_cycletime(OFS_MODEL), "{}netcdf/".format(SOURCE_PATH))

    workerPool = Pool(processes=max(1, MAXWORKERS))
    workers = []

    index_default_path = "{}indexes/cbofs_index_default_500.nc".format(SOURCE_PATH)
    index_subset_path = "{}indexes/cbofs_index_subset_500.nc".format(SOURCE_PATH)
    s111_dir = "{}hdf5/{}/".format(SOURCE_PATH, OFS_MODEL)

    # Call default grid processing
    workers.append(workerPool.apply_async(s111.roms_to_s111, (index_default_path, local_files, s111_dir, cycletime, OFS_MODEL, ofs.MODELS[OFS_MODEL]["ofs_metadata"], None)))

    # Call subgrid processing
    workers.append(workerPool.apply_async(s111.roms_to_s111, (index_subset_path, local_files, s111_dir, cycletime, OFS_MODEL, ofs.MODELS[OFS_MODEL]["ofs_metadata"], None)))

    s111_file_paths = []
    for w in workers:
        s111_file_paths.extend(w.get())

    # Copy s111 files to OCS FTP /win/ofsdata/{forecast_date}/HDF5/S111_1.0.0
    for s111_file_path in s111_file_paths:
        split_path = os.path.split(s111_file_path)
        file_date = split_path[1][7:15]
        shutil.copy(s111_file_path, DEST_PATH.format(forecast_date=file_date))

    # Remove s111 files from hdf5 directory
    delete_files = glob("{}/*.h5".format(s111_dir))
    for delete_files in delete_files:
        os.remove(delete_files)


def main():
    run_cbofs()


if __name__ == "__main__":
    main()