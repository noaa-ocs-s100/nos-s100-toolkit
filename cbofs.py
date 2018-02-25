#!/usr/bin/env python
"""Download and convert CBOFS NetCDF output to S-111 compliant HDF5."""
import argparse

from s100ofs.model import roms
from s100ofs.s111 import S111File

def main():
    """Parse command line arguments and execute target functions."""
    parser = argparse.ArgumentParser(description='Create or modify S-111 File')
    parser.add_argument("model_output_file", help="Path to a NetCDF file containing raw model output to be converted to S111 format or used to build an index file.")
    parser.add_argument('index_file', help='Path to index and coefficient netcdf file used when adding model output to the S111 HDF5 file, or to be created when -b is specified.')
    parser.add_argument('-s', '--s111_file', help='Name of target S111 HDF5 file (should end in .h5). If the file does not already exist, it will be created. Ignored if -b is specified.')
    parser.add_argument('-b', '--build_index', action='store_true', help='Build the regular grid index/coefficients NetCDF file (WARNING: Takes up to ~12 hours).')
    args = parser.parse_args()

    if not args.s111_file and not args.build_index:
        parser.error("Either --s111_file or --build_index must be specified.")
        print(args)
        return 1

    if args.build_index:
        with roms.ROMSIndexFile(args.index_file) as index_file:
            with roms.ROMSOutputFile(args.model_output_file) as model_output_file:
                index_file.init_nc(model_output_file, 445, 761)
                index_file.compute_indexes_coefficients(model_output_file)
    elif args.s111_file:
        with S111File(args.s111_file) as s111_file:
            s111_file.add_output(args.model_output_file, args.index_file)

    return 0

if __name__ == "__main__":
    main()

