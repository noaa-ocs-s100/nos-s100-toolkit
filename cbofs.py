#!/usr/bin/env python
"""Download and convert CBOFS NetCDF output to S-111 compliant HDF5."""
import argparse

from s100ofs.model import roms
from s100ofs.s111 import S111File

# Target resolution of regular grid cells, in meters. Actual x/y resolution of
# grid cells will vary slightly, since the regular grid uses lat/lon
# coordinates (thus a cell's width/height in meters will vary by latitude), and
# since it will be adjusted in order to fit a whole number of grid cells in the
# x and y directions within the calculated grid extent.
TARGET_GRID_RESOLUTION_METERS = 500

def main():
    """Parse command line arguments and execute target functions."""
    parser = argparse.ArgumentParser(description='Create or modify S-111 File')
    parser.add_argument("model_output_file", help="Path to a NetCDF file containing raw model output to be converted to S111 format or used to build an index file.")
    parser.add_argument('index_file', help='Path to regular grid index netcdf file used to add model output to the S111 HDF5 file, or to be created when --build_index is specified.')
    parser.add_argument('-s', '--s111_file', help='Name of target S111 HDF5 file (should end in .h5). If the file does not already exist, it will be created. Ignored if -b is specified.')
    parser.add_argument('-b', '--build_index', action='store_true', help='Build the regular grid index NetCDF file (WARNING: Takes up to ~12 hours). This file must be generated before processing any model output. Once created, it can be used indefinitely unless changes to the regular grid extent/resolution are required.')
    args = parser.parse_args()

    if not args.s111_file and not args.build_index:
        parser.error("Either --s111_file or --build_index must be specified.")
        print(args)
        return 1

    if args.build_index:
        with roms.ROMSIndexFile(args.index_file) as index_file, \
             roms.ROMSOutputFile(args.model_output_file) as model_output_file:
             index_file.init_nc(model_output_file, TARGET_GRID_RESOLUTION_METERS, shoreline_shp = 'nos80k.shp', subset_grid_shp = 'grids_160k.shp')
    elif args.s111_file:
        with S111File(args.s111_file) as s111_file:
            s111_file.add_output(args.model_output_file, args.index_file)

    return 0

if __name__ == "__main__":
    main()

