FROM python:3.7-alpine

ENV USER_PY=pyuser
ENV PATH_S100=/opt/s100
ENV PATH_S100_OFS=$PATH_S100/ofs
ENV PATH_S100_S100PY=$PATH_S100/s100py
ENV PATH_S100_THYME=$PATH_S100/thyme
ENV PATH_S100_RUN=$PATH_S100/run
ENV PATH_S100_RUN_SHP=$PATH_S100_RUN/shapefiles
ENV PATH_S100_RUN_NETCDF=$PATH_S100_RUN/netcdf
ENV PATH_S100_RUN_HDF5=$PATH_S100_RUN/hdf5
ENV HDF5_VERSION="1.10.4"
ENV HDF5_DIR="/usr/local"
ENV NETCDF_VERSION="4.6.2"

WORKDIR /tmp/setup

RUN set -ex; \
    echo "Updating Alpine packages" \
      && apk --no-cache upgrade; \
    \
    echo "Adding edge main/testing repositories (required for installing hdf5)" \
      && echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories \
      && echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories;\
    \
    echo "Installing required system packages" \
      && apk --no-cache add --virtual=hdf5_deps zlib; \
    \
    echo "Installing build dependency packages" \
      && apk --no-cache add --virtual=build_deps gcc g++ make m4 musl-dev zlib-dev; \
    \
    echo "Downloading HDF5 source code" \
      && hdf5_archive=hdf5-${HDF5_VERSION}.tar.bz2 \
      && hdf5_src_dir=hdf5-${HDF5_VERSION} \
      && wget -q -O ${hdf5_archive} https://www.hdfgroup.org/package/source-bzip-2/?wpdmdl=13047 \
      && tar xf ${hdf5_archive} \
      && echo "Compiling/installing HDF5 native library" \
      && cd ${hdf5_src_dir} \
      # --enable-unsupported required when building high-level libs with thread safety config
      && ./configure --prefix=$HDF5_DIR --with-zlib=/usr/include,/lib --enable-threadsafe --enable-unsupported --with-pthread=/usr/include,/usr/lib \
      && make \
      && make install \
      && cd .. \
      && rm ${hdf5_archive} \
      && rm -r ${hdf5_src_dir}; \
    \
    echo "Downloading NetCDF source code" \
      && netcdf_archive=netcdf-v${NETCDF_VERSION}.tar.gz \
      && netcdf_src_dir=netcdf-c-${NETCDF_VERSION} \
      && wget -q -O ${netcdf_archive} https://github.com/Unidata/netcdf-c/archive/v${NETCDF_VERSION}.tar.gz \
      && tar xf ${netcdf_archive} \
      && echo "Compiling/installing NetCDF native library" \
      && cd ${netcdf_src_dir} \
      && CPPFLAGS='-I/usr/local/include -I/usr/include' LDFLAGS='-L/usr/local/lib -L/lib' ./configure --prefix=/usr/local --disable-dap \
      && make \
      && make install \
      && cd .. \
      && rm ${netcdf_archive} \
      && rm -r ${netcdf_src_dir}; \
    \
    echo "Removing build dependency packages" \
      && apk --no-cache del --purge -r build_deps hdf5_deps;

# Assuming 's100py.tar.gz' is an archive of the s100py repository contents
COPY s100py.tar.gz /tmp/setup
#$PATH_S100_S100PY

# Assuming 'thyme.tar.gz' is an archive of the thyme repository contents
COPY thyme.tar.gz /tmp/setup
#$PATH_S100_THYME

# Assuming 'ofs_s100_hdf5.tar.gz' is an archive of the ofs_s100_hdf5 repository contents
COPY ofs.tar.gz /tmp/setup
#$PATH_S100_OFS

# Assuming 'nos80k.zip' is a zip of the nos80k shapefile
COPY nos80k.zip /tmp/setup
#$PATH_S100_RUN_SHP


RUN set -ex; \
    echo "Installing required system packages" \
      && apk --no-cache add --virtual=py_deps gdal lapack; \
    \
    echo "Installing build dependency packages" \
      && apk --no-cache add --virtual=build_deps gcc g++ make m4 musl-dev gfortran lapack-dev gdal-dev; \
    \
    echo "Setting up run directories" \
      && mkdir -p $PATH_S100_RUN_SHP $PATH_S100_RUN_NETCDF $PATH_S100_RUN_HDF5 $PATH_S100_S100PY $PATH_S100_THYME $PATH_S100_OFS; \
    echo "Extracting packages/data" \
      && cd $PATH_S100_S100PY && tar xzvf /tmp/setup/s100py.tar.gz \
      && cd $PATH_S100_THYME && tar xzvf /tmp/setup/thyme.tar.gz \
      && cd $PATH_S100_OFS && tar xzvf /tmp/setup/ofs.tar.gz \
      && cd $PATH_S100_RUN_SHP && unzip /tmp/setup/nos80k.zip; \
    echo "Upgrading pip" \
      && pip install --no-cache-dir -U pip; \
    echo "Installing python dependencies" \
      # numpy must be installed first (separately) or scipy install won't work
      && pip install --no-cache-dir numpy \
      && pip install --no-cache-dir shapely scipy netCDF4 gdal; \
    echo "Installing python packages" \
      && pip install --no-cache-dir -e $PATH_S100_THYME \
      && pip install --no-cache-dir -e $PATH_S100_S100PY; \
    echo "Adding group/user [$USER_PY] & updating path ownership" \
      && addgroup -S $USER_PY && adduser -S $USER_PY -G $USER_PY \
      && chown -R $USER_PY.$USER_PY $PATH_S100; \
    echo "Cleaning up packages" \
      && rm -f /tmp/setup/*.tar.gz; \
    echo "Removing build packages" \
      && apk --no-cache del --purge -r build_deps;


WORKDIR $PATH_S100_RUN
USER $USER_PY
CMD ["/bin/sh"]


