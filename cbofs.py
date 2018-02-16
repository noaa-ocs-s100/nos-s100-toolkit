#!/usr/bin/env python
"""Download and convert CBOFS NetCDF output to S-111 compliant HDF5."""
import argparse

from s100ofs.model import roms
from s100ofs.s111 import S111File

def main():
    """Parse command line arguments and execute target functions."""
    parser = argparse.ArgumentParser(description='Create or modify S-111 File')
    parser.add_argument("s111File", help="Name of target S111 HDF5 file (should end in .h5). If the file does not already exist, it will be created.")
    # No need to specify --create - class will automatically create file/add
    # metadata if it doesn't already exist
    #parser.add_argument("--create", action="store_true", help="Create/initialize a new HDF5 file")
    parser.add_argument('-a', '--add_output', help='Path to an ocean model netcdf file to be added to the S111 HDF5.')
    parser.add_argument('-i', '--index_file', help='Path to index and coefficient netcdf file. Required when adding model output to the S111 HDF5 file.')
    args = parser.parse_args()

    if args.add_output and not args.index_file:
        parser.error("--index_file (-i) required when --add_output (-a) specified.")
        print(args)
        return 1

    with S111File(args.s111File) as s111_file:
        if args.add_output:
            s111_file.add_output(args.add_output, args.index_file)

    return 0

if __name__ == "__main__":
    main()

