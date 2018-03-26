#!/usr/bin/env python
"""Download and convert CBOFS NetCDF output to S-111 compliant HDF5."""
import argparse
import datetime
import shutil
import urllib.request

from s100ofs.model import roms
from s100ofs import s111

# Target resolution of regular grid cells, in meters. Actual x/y resolution of
# grid cells will vary slightly, since the regular grid uses lat/lon
# coordinates (thus a cell's width/height in meters will vary by latitude), and
# since it will be adjusted in order to fit a whole number of grid cells in the
# x and y directions within the calculated grid extent.
TARGET_GRID_RESOLUTION_METERS = 500

# Path to shoreline shapefile used to mask out land areas during index file
# creation.
SHORELINE_SHP_PATH = "shp/nos80k.shp"

# Path to grid subset shapefile used to identify subgrid areas during index
# file creation.
GRID_SUBSET_SHP_PATH = "shp/grids_160k.shp"

# Path format/prefix for output S111 files. Forecast initialization (reference)
# time will be injected using datetime.strftime()
S111_PATH_FORMAT = "h5/cbofs_s111_%Y%m%d_%H"

# Base URL of CO-OPS HTTP server for NetCDF files
HTTP_SERVER_COOPS = "https://opendap.co-ops.nos.noaa.gov"

# Path format of NetCDF files. Forecast initialization (reference) time will be
# injected using datetime.strftime() and zero-padded forecast designation (e.g.
# 'f012') will be injected by using str.format().
# Example:
#    reftime.strftime(HTTP_NETCDF_PATH_FORMAT).format(forecast_str='f012')
HTTP_NETCDF_PATH_FORMAT = "/thredds/fileServer/NOAA/CBOFS/MODELS/%Y%m/nos.cbofs.fields.{forecast_str}.%Y%m%d.t%Hz.nc"

# Folder path of downloaded NetCDF files.
LOCAL_NETCDF_PATH_FORMAT = "netcdf/nos.cbofs.fields.{forecast_str}.%Y%m%d.t%Hz.nc"

# List of forecast projection hours to be processed
FORECAST_HOURS = list(range(1,6))#49))

def download(cycletime, forecasts):
    """Download specified forecasts for specified model cycle time.

    Args:
        cycletime: `datetime.datetime` representing model intiialization
            (reference/cycle) time.
        forecasts: List of forecast projection hours to be downloaded.

    Returns:
        List of paths to NetCDF files downloaded successfully, corresponding
        with the order specified in `forecasts`.
    """
    local_files = []
    for forecast in forecasts:
        forecast_str = "f{0:03d}".format(forecast)
        url = cycletime.strftime("{}{}".format(HTTP_SERVER_COOPS,HTTP_NETCDF_PATH_FORMAT)).format(forecast_str=forecast_str)
        local_file = cycletime.strftime(LOCAL_NETCDF_PATH_FORMAT).format(forecast_str=forecast_str)
        print("Downloading {} to {}...".format(url, local_file))
        with urllib.request.urlopen(url) as response, open(local_file, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        print("Download successful.")
        local_files.append(local_file)
    return local_files

def download_and_process(index_file_path, s111_path):
    """Download latest model run and convert to S-111 format.

    Args:
        index_file_path: Path to NetCDF index file required for interpolation.
        s111_path: Path prefix of output S111 HDF5 file(s).
    """
    now = datetime.datetime.utcnow()
    print(now)
    if now.hour < 1 and now.minute < 50:
        yesterday = now - datetime.timedelta(days=1)
        cycletime = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 18, 0)
        print(cycletime)
    elif now.hour < 7 or (now.hour == 7 and now.minute < 50):
        cycletime = datetime.datetime(now.year, now.month, now.day, 0, 0)
        print(cycletime)
    elif now.hour < 13 or (now.hour == 13 and now.minute < 50):
        cycletime = datetime.datetime(now.year, now.month, now.day, 6, 0)
        print(cycletime)
    elif now.hour < 19 or (now.hour == 7 and now.minute < 50):
        cycletime = datetime.datetime(now.year, now.month, now.day, 12, 0)
        print(cycletime)
    else:
        cycletime = datetime.datetime(now.year, now.month, now.day, 18, 0)
        print(cycletime)
    
    model_output_files = download(cycletime, FORECAST_HOURS)
    print("Converting files to S111 format...")
    s111.romsToS111(index_file_path, model_output_files, s111_path)
    print("Conversion complete.")

def main():
    """Parse command line arguments and execute target functions."""
    parser = argparse.ArgumentParser(description='Create or modify S-111 File')
    parser.add_argument('index_file_path', help='Path to regular grid index netcdf file used to add model output to the S111 HDF5 file, or to be created when --build_index is specified.')
    parser.add_argument('-s', '--s111_path', help='Path prefix of output S111 HDF5 file(s) (without file extension). Any required identifying information (e.g. model reference/cycle time, subgrid id) as well as the .h5 extension will be appended to create the final output path(s). Ignored if -b is specified.')
    parser.add_argument('-b', '--build_index', action='store_true', help='Build the regular grid index NetCDF file (WARNING: Takes up to ~12 hours). This file must be generated before processing any model output. Once created, it can be used indefinitely unless changes to the regular grid extent/resolution are required.')
    parser.add_argument('-g', '--grid_subset', action='store_true', help='Use grid subsetting to build index file when --build_index is specified. If not specified, the model extent will be used to generate the index file and no subsetting will occur.')
    parser.add_argument("-m", "--model_output_files", metavar="roms_file_path", nargs="+", help="Path to one or more NetCDF files containing raw model output to be converted to S111 format or used to build an index file. If not specified, the latest model run will be downloaded and processed. Required when --build_index is specified.", required=False)
    args = parser.parse_args()

    if not args.s111_path and not args.build_index:
        parser.error("Either --s111_path or --build_index must be specified.")
        print(args)
        return 1
    
    if args.build_index:
        if args.model_output_files is None:
            parser.error("At least one model output file must be specified with --model_output_files when --build_index is specified.")
            print(args)
            return 1
        grid_subset = None
        if args.grid_subset:
            grid_subset = GRID_SUBSET_SHP_PATH
        with roms.ROMSIndexFile(args.index_file_path) as index_file, \
             roms.ROMSOutputFile(args.model_output_files[0]) as model_output_file:
            index_file.init_nc(model_output_file, TARGET_GRID_RESOLUTION_METERS, shoreline_shp=SHORELINE_SHP_PATH, subset_grid_shp=grid_subset)
    elif args.s111_path:
        if args.model_output_files is not None:
            s111.romsToS111(args.index_file_path, args.model_output_files, args.s111_path)
        else:
            download_and_process(args.index_file_path, args.s111_path)

    return 0

if __name__ == "__main__":
    main()

