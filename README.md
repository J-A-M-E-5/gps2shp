# gps2shp
## Info
Program to convert longitude/latitude geo coordinates from a GPS input file
into KML (Google Maps/Google Earth etc...) and/or ESRI Shapefile formats.

Program detects if all input files are valid and for problems writing to
destination files *before* any conversion actually happens, so you do not
end up with half-converted datasets.

## Requirements
* Python 2.7 or Python 3.x
* Requires the ogr2ogr executable (GDAL) if you want to create ERSI Shapefiles

### Debian, Ubuntu
`sudo apt-get install gdal-bin`

### RedHat, CentOS
`sudo yum install gdal`

### OSX
`brew install gdal`

### Windows
See http://www.gisinternals.com/release.php and download latest GDAL 1.x
binary. You'll also need to use the `--exe-path` to specify location/name of
the ogr2ogr exe (untested).

## Installation
`git clone https://github.com/J-A-M-E-5/gps2shp`

### Optional - Linux & OSX (install as a command in your path)
`cd gps2shp && sudo ln -s "$(pwd)/gps2shp.py" /usr/local/bin/gps2shp`

## How to use
`gps2shp.py --help`

## Code Standards
* pep8 / pycodestyle / flake8 - 100%
* pylint - 10.00/10

## Thanks to
Joshua Anderson for financing the creation of this program.
