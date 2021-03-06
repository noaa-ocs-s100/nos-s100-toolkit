NOS S-100 Toolkit
=================

A Python toolkit for downloading National Oceanic and Atmospheric
Administration (NOAA)/National Ocean Service (NOS) datasets and encoding
in International Hydrographic Organization (IHO)
[S-100](http://s100.iho.int/S100/) data formats.

Overview
--------

These scripts download NOS Ocean Model NetCDF Forecast files hosted on
the NOAA Operational Model Archive and Distribution System
[NOMADS](ftp://ftp.ncep.noaa.gov/pub/data/nccf/com/nos/prod/) and on
the NOAA CO-OPS
[THREDDS](https://opendap.co-ops.nos.noaa.gov/thredds/catalog.html) Data
Server and use the [thyme](https://github.com/noaa-ocs-modeling/thyme)
and [s100py](https://github.com/noaa-ocs-s100/s100py) libraries to
interpolate its surface current forecasts to a regular grid and encode
the result in S-100/S-111 compliant HDF5 files.

S-111 is an IHO standard outlining formats for storing and sending
surface water current data and metadata and is designed for
interoperability with Electronic Navigation Charts.

Features
--------

-   Download NOAA/NOS Operational Forecast System (OFS) NetCDF files
-   Given a target resolution and optionally a subgrid shapefile,
    generate a regular grid definition and save to a thyme Model Index
    NetCDF file
-   Process a full OFS forecast run (0 to 48+ hours) and encode the
    result into IHO S-111 format (a single HDF-5 file containing all
    forecast projections) on a regular grid
-   Chop S-111 output into smaller sub-grids to reduce file sizes
-   Calculate water currents at any depth-below-surface

Index File Data/Functionality
-----------------------------

For information about the model index files used by these scripts, see
the [thyme](https://github.com/noaa-ocs-modeling/thyme) documentation.

Supported Models
----------------

These scripts presently support the following hydrodynamic modeling
systems:

-   NCEP Real-Time Ocean Forecast System (RTOFS)
-   NOS Chesapeake Bay Operational Forecast System (CBOFS)
-   NOS Delaware Bay Operational Forecast System (DBOFS)
-   NOS Gulf of Maine Operational Forecast System (GoMOFS)
-   NOS Lake Erie Operational Forecast System (LEOFS)
-   NOS Lake Huron Operational Forecast System (LHOFS)
-   NOS Lake Michigan & Huron Operational Forecast System (LMHOFS)
-   NOS Lake Michigan Operational Forecast System (LMOFS)
-   NOS Lake Ontario Operational Forecast System (LOOFS)
-   NOS Lake Superior Operational Forecast System (LSOFS)
-   NOS New York/New Jersey Harbor Operational Forecast System (NYOFS)
-   NOS Northeast Gulf of Mexico Operational Forecast System (NEGOFS)
-   NOS Northern Gulf of Mexico Operational Forecast System (NGOFS)
-   NOS Northwest Gulf of Mexico Operational Forecast System (NWGOFS)
-   NOS San Francisco Bay Operational Forecast System (SFBOFS)
-   NOS Tampa Bay Operational Forecast System (TBOFS)
-   NOS West Coast Operational Forecast System (WCOFS)

Visit [NOS Operational Forecast
Systems](https://tidesandcurrents.noaa.gov/models.html) for more
information.

Requirements
------------

This codebase relies on the following Python packages:

-   [s100py](https://github.com/noaa-ocs-s100/s100py)
-   [thyme](https://github.com/noaa-ocs-modeling/thyme)

However, the above packages rely on the GDAL Python bindings to be
present, so it usually can\'t just be installed using `pip install gdal`.
We recommend installing GDAL either through a package manager (e.g.
`conda`, `apt`, `yum`, `pacman`) or by using the preconfigured conda
environment file provided in this repository that can be used to install
all dependencies quickly. To go this route, you must first install Miniconda.

For instructions downloading/installing Miniconda, please reference the
[official documentation](https://docs.conda.io/en/latest/miniconda.html).

Instructions for configuring your conda environment can be found in the
following sections.

Configuration
-------------

-   Create a parent directory that will contain the code and all other
    files that will be used or generated by this package. Ensure that
    the directory has appropriate user/group ownership and
    read/write/execute permissions settings that will allow the code to
    be checked out and run. For simplicity, this example assumes that
    directory is under the user\'s home directory.

```bash
    mkdir ~/nos-s100-toolkit
    cd ~/nos-s100-toolkit
```

-   Create a subdirectory that will store the NetCDF index files

```bash
    mkdir ~/nos-s100-toolkit/indexes
```

-   Copy existing index files, if any, to this directory

-   Create a subdirectory that will store downloaded model NetCDF files

```bash
    mkdir ~/nos-s100-toolkit/netcdf
```

-   Create a subdirectory that will store generated S-111 HDF5 output
    files

```bash
    mkdir ~/nos-s100-toolkit/hdf5
```

-   Create a subdirectory that will store shoreline and/or subgrid
    shapefiles. This is only required when generating new NetCDF index
    files. Make sure that any shapefiles being used have coverage for
    the model domain(s) you will be working with.

```bash
   mkdir ~/nos-s100-toolkit/shp
```

-   Copy the shapefiles, if any, to this directory.

-   Clone the repository to a new `src` subdirectory:

```bash
    git clone https://github.com/noaa-ocs-s100/nos-s100-toolkit ~/nos-s100-toolkit/src
```

-   Ensure that `ofs.py` is executable. If not, run

```bash
    chmod gou+x ~/nos-s100-toolkit/src/ofs.py
```

-   Ensure the new `src` directory is in your `$PATH` environment
    variable:

```bash
    export PATH=$PATH:~/nos-s100-toolkit/src
```

-   Create and configure a new conda environment from the conda
    environment file supplied with the code (this will download and
    install all required packages):

```bash
   conda create --name nos-s100 --file nos-s100_conda_env.txt
```

Execution
---------

-   Activate your new conda environment (once activated, conda prepends
    the environment name nos-s100 onto your system command prompt)
```bash
    conda activate nos-s100
    pip install s100py
```
-   To print detailed usage information:
```bash
    cd ~/nos-s100-toolkit/src
    python ofs.py -h
```
-   The following examples describe the steps to create different S-111
    data coding formats. For more information about S-111 data coding
    formats, see the [s100py](https://github.com/noaa-ocs-s100/s100py)
    documentation.

**To create regular-grid S-111 files (Coding Format 2)**

-   Generate an index (grid definition) file for a particular model at a
    particular resolution:

    > **WARNING:** Keep in mind that larger model domains and higher resolutions will take longer to generate.

    - Download a model output NetCDF file and place in the `netcdf`subdirectory, modifying the model abbreviation, timestamp, and forecast hour as necessary

    ```bash
            cd ~/nos-s100-toolkit/netcdf
            wget https://opendap.co-ops.nos.noaa.gov/thredds/fileServer/NOAA/CBOFS/MODELS/201907/nos.cbofs.fields.f001.20190701.t00z.nc
    ```

    - Download any land shapefile and/or subgrid shapefile, unzip and place in the `shp` subdirectory

    ```bash
            cd ~/nos-s100-toolkit/shp
            wget https://www.weather.gov/source/gis/Shapefiles/County/s_11au16.zip # U.S. States and Territories
    ```

    - Using the downloaded NetCDF file and subgrid/shoreline shapefiles, generate a "default grid" index file.
    The extent (envelope) of the resulting grid definition will match the model's native domain.
    Specifying `-t 500` implies a target cellsize of ~500 meters.

    ```bash
        python ofs.py -i ~/nos-s100-toolkit/indexes/cbofs_index_default_500m.nc -b -l ~/nos-s100-toolkit/shp/s_11au16.shp -m ~/nos-s100-toolkit/netcdf/nos.cbofs.fields.f001.20190701.t00z.nc -o cbofs -t 500 -code 2
    ```

    -   Alternatively, create a "subgrid" index file instead. This requires a
    shapefile containing orthogonal grid polygons describing areas for which
    distinct S-111 files will be generated (for all grid polygons that
    intersect the native model domain). Specifying `-f GridCellName`
    indicates the values from the supplied shapefile's "GridCellname"
    attribute to be used for the filename of any generated S-111 files. If
    not specified, the primary key identifier (e.g. `fid`) will be used
    instead to distinguish the S-111 files from each other.

    ```bash
        python ofs.py -i ~/nos-s100-toolkit/indexes/cbofs_index_subset_500m.nc -b -l ~/nos-s100-toolkit/shp/land.shp -g ~/nos-s100-toolkit/shp/grid.shp -f GridCellName -m ~/nos-s100-toolkit/netcdf/nos.cbofs.fields.f001.20190701.t00z.nc -o cbofs -t 500 -code 2
    ```

-   Download the latest full OFS forecast run and convert to S-111
    format (requires specifying a NetCDF index \[grid definition\]
    file):

```bash
    python ofs.py -i ~/nos-s100-toolkit/indexes/cbofs_index_default_500m.nc -s ~/nos-s100-toolkit/hdf5 -d ~/nos-s100-toolkit/netcdf -o cbofs -code 2
```

-   Skip the download step and convert an existing OFS forecast file to
    S-111 format

```bash
    python ofs.py -i ~/nos-s100-toolkit/indexes/cbofs_index_default_500m.nc -s ~/nos-s100-toolkit/hdf5 -m ~/nos-s100-toolkit/netcdf/nos.cbofs.fields.f001.20190701.t00z.nc -o cbofs -c 2019070100 -code 2
```

**To create \"ungeorectified gridded array\" S-111 files (Coding Format 3)**

-   Download the latest full OFS forecast run and convert to S-111
    format:

```bash
    python ofs.py -s ~/nos-s100-toolkit/hdf5 -d ~/nos-s100-toolkit/netcdf -o cbofs -code 3
```

-   Skip the download step and convert an existing OFS forecast file to
    S-111 format

```bash
    python ofs.py -s ~/nos-s100-toolkit/hdf5 -m ~/nos-s100-toolkit/netcdf/nos.cbofs.fields.f001.20190701.t00z.nc -o cbofs -c 2019070100 -code 3
```

Authors
-------

-   Erin Nagel (UCAR), <erin.nagel@noaa.gov>
-   Jason Greenlaw (ERT), <jason.greenlaw@noaa.gov>

License
-------

This project is licensed under the [Creative Commons Zero
1.0](https://creativecommons.org/publicdomain/zero/1.0/) public domain
dedication. See [LICENSE](LICENSE) for more information.

Disclaimer
----------

This repository is a scientific product and is not official
communication of the National Oceanic and Atmospheric Administration, or
the United States Department of Commerce. All NOAA GitHub project code
is provided on an 'as is' basis and the user assumes responsibility for
its use. Any claims against the Department of Commerce or Department of
Commerce bureaus stemming from the use of this GitHub project will be
governed by all applicable Federal law. Any reference to specific
commercial products, processes, or services by service mark, trademark,
manufacturer, or otherwise, does not constitute or imply their
endorsement, recommendation or favoring by the Department of Commerce.
The Department of Commerce seal and logo, or the seal and logo of a DOC
bureau, shall not be used in any manner to imply endorsement of any
commercial product or activity by DOC or the United States Government.

Acknowledgments
---------------

This software has been developed by the National Oceanic and Atmospheric
Administration (NOAA)/National Ocean Service (NOS)/Office of Coast
Survey (OCS)/Coast Survey Development Lab (CSDL) for use by the
scientific and oceanographic communities.

CSDL wishes to thank the following entities for their assistance:

-   NOAA/NOS/Center for Operational Oceanographic Products and Services
    (CO-OPS)
