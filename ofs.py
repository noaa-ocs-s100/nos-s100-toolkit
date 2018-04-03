#!/usr/bin/env python
"""Download and convert ROMS OFS NetCDF output to S-111 compliant HDF5."""
import argparse
import datetime
import shutil
import urllib.request
import os
from glob import glob
import sys

from s100ofs.model import roms
from s100ofs import s111

# Path to shoreline shapefile used to mask out land areas during index file
# creation.
SHORELINE_SHP_PATH = "shp/nos80k.shp"

# Path to grid subset shapefile used to identify subgrid areas during index
# file creation.
GRID_SUBSET_SHP_PATH = "shp/grids_160k.shp"

# Base URL of CO-OPS HTTP server for NetCDF files
HTTP_SERVER_COOPS = "https://opendap.co-ops.nos.noaa.gov"

# Path format of NetCDF files. Forecast initialization (reference) time will be
# injected using datetime.strftime() and zero-padded forecast designation (e.g.
# 'f012') will be injected by using str.format().
# Example:
#    reftime.strftime(HTTP_NETCDF_PATH_FORMAT).format(forecast_str='f012')
HTTP_NETCDF_PATH_FORMAT = "/thredds/fileServer/NOAA/{model_str_uc}/MODELS/%Y%m/nos.{model_str_lc}.fields.{forecast_str}.%Y%m%d.t%Hz.nc"

# Folder path of downloaded NetCDF files.
LOCAL_NETCDF_FILENAME_FORMAT ="nos.{model_str_lc}.fields.{forecast_str}.%Y%m%d.t%Hz.nc"

"""
Model configuration dictionary, where key is the lower-case model identifier
and value is another dictionary with the following properties:
    forecast_hours: List of forecast projections (hours from cycle time at
        which each forecast is valid).
    cycles: List of hour-of-day values corresponding with daily model cycles
        For example, for a model produced four times per day at 0000, 0600,
        1200, and 1800 UTC, specify (0,6,12,18).
    file_delay: `datetime.timedelta` representing delay (time since model cycle
        time) of file availability on HTTP server.
    target_cellsize_meters: Target size of regular grid cells, in meters.
        Actual size of x/y grid cells will vary slightly, since the regular
        grid uses lat/lon coordinates (thus a cell's width/height in meters
        will vary by latitude), and since it will be adjusted in order to fit a
        whole number of grid cells in the x and y directions within the
        calculated grid extent.
""" 
MODELS = {
    "cbofs": {
        # Hourly output from +1 to +48
        "forecast_hours": list(range(1,49)),
        "cycles": (0, 6, 12, 18),
        "file_delay": datetime.timedelta(minutes=170),
    },
    "gomofs": {
        # 3-hourly output from +3 to +72
        "forecast_hours": list(range(3,73,3)),
        "cycles": (0, 6, 12, 18),
        "file_delay": datetime.timedelta(minutes=170),
    },
    "dbofs": {
        # Hourly output from +1 to +48
        "forecast_hours": list(range(1,49)),
        "cycles": (0, 6, 12, 18),
        "file_delay": datetime.timedelta(minutes=170),
    },
    "tbofs": {
        # Hourly output from +1 to +48
        "forecast_hours": list(range(1,49)),
        "cycles": (0, 6, 12, 18),
        "file_delay": datetime.timedelta(minutes=170),
    }
}

def get_latest_cycletime(ofs_model):
    """Calculate and return the latest cycletime for specified model.

    Args:
        ofs_model: The target model identifier.
    
    Returns: A `datetime.datetime` instance representing the calculated
        cycletime, or None if one could not be determined using system time and
        configured thresholds.
    """
    ofs_model = ofs_model.lower()

    now = datetime.datetime.utcnow()
    print("Current system time (UTC): {}".format(now))

    cycletime = None

    # Calculate most recent cycle using configured thresholds
    cycles = MODELS[ofs_model]["cycles"]
    file_delay = MODELS[ofs_model]["file_delay"]

    # Start by listing all cycle times for today, chronologically
    today_cycletimes = sorted([datetime.datetime(now.year, now.month, now.day, cycle) for cycle in cycles])

    # Include yesterday's cycles as potential cycles to check
    potential_cycletimes = [today_cycletime - datetime.timedelta(days=1) for today_cycletime in today_cycletimes] + today_cycletimes

    # Now search through potential cycle times in reverse chronological
    # order until we find one that should be available
    for potential_cycletime in reversed(potential_cycletimes):
        if now >= potential_cycletime + file_delay:
            cycletime = potential_cycletime
            break

    return cycletime

def download_and_process(ofs_model, index_file_path, s111_dir, cycletime, download_dir):
    """Download latest model run and convert to S-111 format.

    Creates a list of paths to NetCDF files downloaded successfully, corresponding
    with the order specified in `forecasts`.

    Args:
        ofs_model: The target model identifier.
        index_file_path: Path to NetCDF index file required for interpolation.
        s111_dir: Path to a parent directory where output S111 HDF5 file(s)
            will be generated. Must exist.
        cycletime: `datetime.datetime` representing model intiialization
            (reference/cycle) time.
        download_dir: Path to a parent directory where model output files will
            be downloaded. Must exist. Files will be downloaded to a
            subdirectory named according to the model identifier (will be
            created if it does not yet exist; if it does exist, existing files
            will be removed before downloading new files).
    """
    if not download_dir.endswith("/"):
        download_dir += "/"
    download_dir += ofs_model.lower()
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir)
    else:
        # Clean the directory of all data files before downloading and
        # processing the new data:
        filesToDelete = glob("{}/*.nc".format(download_dir))
        for fileToDelete in filesToDelete:
            sys.stderr.write("Removing {0}\n".format(fileToDelete))
            os.remove(fileToDelete)

    local_files = []
    for forecast in MODELS[ofs_model]["forecast_hours"]:
        forecast_str = "f{0:03d}".format(forecast)
        url = cycletime.strftime("{}{}".format(HTTP_SERVER_COOPS, HTTP_NETCDF_PATH_FORMAT)).format(model_str_uc=ofs_model.upper(), model_str_lc=ofs_model.lower(), forecast_str=forecast_str)
        local_file = "{}/{}".format(download_dir, cycletime.strftime(LOCAL_NETCDF_FILENAME_FORMAT).format(model_str_lc=ofs_model.lower(), forecast_str=forecast_str))
        print("Downloading {} to {}...".format(url, local_file))
        with urllib.request.urlopen(url) as response, open(local_file, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        print("Download successful.")
        local_files.append(local_file)

    print("Converting files to S111 format...")
    s111.romsToS111(index_file_path, local_files, s111_dir, cycletime, ofs_model)
    print("Conversion complete.")

def main():
    """Parse command line arguments and execute target functions."""
    parser = argparse.ArgumentParser(description="Convert surface currents model output to S-111 HDF5 format")
    parser.add_argument("-i", "--index_file_path", help="Path to existing or to-be-created index netcdf file. This file contains regular grid definition and interpolation parameters, and is required to convert model output to S111 HDF5 format. If -b/--build_index is specified, any existing file at the specified path will be overwritten.", required=True)
    parser.add_argument("-s", "--s111_dir", help="Path to a directory where generated S-111 HDF5 file(s) will be generated. Generated files will be placed in a subdirectory named to match the model identifier (e.g. 'cbofs') and files will be auto-named using identifying information (e.g. model reference/cycle time, subgrid id) and with the .h5 file extension. Ignored if -b/--build_index is specified.")
    parser.add_argument("-b", "--build_index", action="store_true", help="Build a new index NetCDF file at the path specified by -i/--index_file_path. This file must be generated before processing any model output, as it will contain the regular grid definition and interpolation parameters. Once created, it can be used indefinitely for the target model unless changes to the regular grid extent/resolution are required or if the underlying model grid changes.")
    parser.add_argument("-g", "--grid_subset", action="store_true", help="Use grid subsetting to build index file when -b/--build_index is specified. If not specified, the model extent will be used to generate the index file and no subsetting will occur. Ignored if -b/--build_index is not specified.")
    parser.add_argument("-m", "--model_file_path", nargs="+", help="Path to one or more NetCDF files containing raw/native model output to be converted to S111 format (when -s/--s111_dir is specified) or used to build an index file (when -b/--build_index is specified). If not specified, the latest model run will be automatically downloaded and processed. Required when --build_index is specified.", required=False)
    parser.add_argument("-d", "--download_dir", help="Path to a directory where downloaded model output files can be placed. Files will be downloaded into a subdirectory named to match the model identifier (e.g. 'cbofs') (if it does not yet exist, it will be created). Prior to downloading, any existing NetCDF files in the model's subdirectory will be deleted to prevent file accumulation. Required when -m/--model_file_path is not specified.")
    parser.add_argument("-o", "--ofs_model", help="Identifier of target Operational Forecast System (OFS) to be processed (e.g. cbofs, dbofs, gomofs, or tbofs)", required=True)
    parser.add_argument("-c", "--cycletime", help="Model cycle time (i.e. initialization/reference time) to process, in the format YYYYMMDDHH. If not specified, the most recent cycle will be calculated using configured thresholds and present system time.")
    parser.add_argument("-t", "--target_cellsize_meters", help=" Target cellsize of regular grid cells in meters. Actual size of x/y grid cells will vary slightly, since the regular grid uses lat/lon coordinates (thus a cell's width/height in meters will vary by latitude), and since it will be adjusted in order to fit a whole number of grid cells in the x and y directions within the calculated grid extent.")
    args = parser.parse_args()

    ofs_model = args.ofs_model
    if not ofs_model or ofs_model.lower() not in MODELS:
        parser.error("A valid -o/--ofs_model must be specified. Possible values: {}".format(", ".join(list(MODELS.keys()))))
        return 1
    ofs_model = ofs_model.lower()

    if not args.s111_dir and not args.build_index:
        parser.error("Either --s111_dir or --build_index must be specified.")
        print(args)
        return 1

    cycletime = args.cycletime
    if cycletime is not None:
        try:
            cycletime = datetime.datetime.strptime(cycletime, "%Y%m%d%H")
        except ValueError as e:
            parser.error("Invalid -c/--cycletime specified [{}]. Format must be YYYYMMDD.".format(args.cycletime))
            return 1
    else:
        cycletime = get_latest_cycletime(ofs_model)
        if cycletime is None:
            print("Error: Latest model cycle time cannot be determined. Verify that system time is correct and review model cycle configuration.")
            return 1
        
    print("Processing forecast cycle with reference time (UTC): {}".format(cycletime))
    
    if args.build_index:
        if args.target_cellsize_meters is None:
            parser.error("Target cellsize in meters must be specfied when --build_index is specified.")
            print(args)
            return 1
        if args.model_file_path is None:
            parser.error("At least one model output file must be specified with --model_file_path when --build_index is specified.")
            print(args)
            return 1
        grid_subset = None
        if args.grid_subset:
            with roms.ROMSIndexFile(args.index_file_path) as index_file, \
                 roms.ROMSOutputFile(args.model_file_path[0]) as model_output_file:
                index_file.init_nc(model_output_file, int(args.target_cellsize_meters), args.ofs_model, shoreline_shp=SHORELINE_SHP_PATH, subset_grid_shp=GRID_SUBSET_SHP_PATH)
        else:
            with roms.ROMSIndexFile(args.index_file_path) as index_file, \
                 roms.ROMSOutputFile(args.model_file_path[0]) as model_output_file:
                index_file.init_nc(model_output_file, int(args.target_cellsize_meters), args.ofs_model, shoreline_shp=SHORELINE_SHP_PATH)

    elif not os.path.isdir(args.s111_dir):
        parser.error("Invalid/missing S-111 output directory (-s/-s111_dir) specified.")
        return 1
    else:
        if not os.path.exists(args.index_file_path):
            parser.error("Specified index file does not exist [{}]".format(args.index_file_path))
            return 1
        s111_dir = args.s111_dir
        if not s111_dir.endswith("/"):
            s111_dir += "/"
        s111_dir += ofs_model.lower()
        if not os.path.isdir(s111_dir):
            os.makedirs(s111_dir)
        if args.model_file_path is not None:
            s111.romsToS111(args.index_file_path, args.model_file_path, s111_dir, cycletime, ofs_model)
        else:
            if not args.download_dir or not os.path.isdir(args.download_dir):
                parser.error("Invalid/missing download directory (-d/--download_dir) specified.")
                return 1
            download_and_process(ofs_model, args.index_file_path, s111_dir, cycletime, args.download_dir)
    return 0

if __name__ == "__main__":
    main()

