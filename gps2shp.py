#!/usr/bin/env python

"""
Program to convert longitude/latitude geo coordinates from a GPS input file
into KML (Google Maps/Google Earth etc...) and/or ESRI Shapefile formats.

Program detects if all input files are valid and for problems writing to
destination files *before* any conversion actually happens, so you do not
end up with half-converted datasets.

Compatability: Linux, OSX, Windows (use --exe-path). Python 2.7, Python 3.x
Author       : James Martin
Version      : 0.2 (2018-02-09)
License      : Public Domain

Thanks to Joshua Anderson for financing the creation of this program.
"""

from __future__ import print_function
__version_num__ = (0, 2)

import argparse
import os
import subprocess
import tempfile

try:
    from shutil import which
except ImportError:
    def which(cmd):
        """Python 2.7 and <3.3 does not have which() so we implement it"""
        def is_exe(path):
            """Check if file exists and can access it"""
            return os.path.isfile(path) and os.access(path, os.X_OK)

        path, _ = os.path.split(cmd)
        if path:
            if is_exe(cmd):
                return cmd
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, cmd)
                if is_exe(exe_file):
                    return exe_file

        return None

# Can tweak these variables to change how maps are displayed
LINE_COLOR = 'ff0000ff'     # R G B Opacity
LINE_WIDTH = '1.5'
POLY_COLOR = '7d0000ff'
POLY_FILL = '1'
POLY_OUTLINE = '1'

VALID_CHARS = list('0123456789.+-')

__version__ = '.'.join(str(_) for _ in __version_num__)

# A bit messy but gets the job done without needing KML libs
KML_TEMPLATE="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>%s</name>
    <description/>
    <Style id="poly-%s-1000-125-normal">
      <LineStyle>
        <color>%s</color>
        <width>%s</width>
      </LineStyle>
      <PolyStyle>
        <color>%s</color>
        <fill>%s</fill>
        <outline>%s</outline>
      </PolyStyle>
    </Style>
    <Style id="poly-%s-1000-125-highlight">
      <LineStyle>
        <color>%s</color>
        <width>%s</width>
      </LineStyle>
      <PolyStyle>
        <color>%s</color>
        <fill>%s</fill>
        <outline>%s</outline>
      </PolyStyle>
    </Style>
    <StyleMap id="poly-%s-1000-125">
      <Pair>
        <key>normal</key>
        <styleUrl>#poly-%s-1000-125-normal</styleUrl>
      </Pair>
      <Pair>
        <key>highlight</key>
        <styleUrl>#poly-%s-1000-125-highlight</styleUrl>
      </Pair>
    </StyleMap>
    <Folder>
      <name>%s</name>
      <Placemark>
        <name>%s</name>
        <styleUrl>#poly-%s-1000-125</styleUrl>
        <Polygon>
          <outerBoundaryIs>
            <LinearRing>
              <tessellate>1</tessellate>
              <coordinates>
%s              </coordinates>
            </LinearRing>
          </outerBoundaryIs>
        </Polygon>
      </Placemark>
    </Folder>
  </Document>
</kml>"""


def check_line(file_, line, line_num):
    """Function to check that a line is valid "lng,lat" format"""

    try:
        lng, lat = line.split(' ')
    except ValueError:
        raise Exception('Line must be specified as longitude<space>latitude. '
                        'Line: %d [%s] in file "%s"' % (line_num, line, file_))

    for _ in lng:
        if _ not in VALID_CHARS:
            raise Exception('Invalid character for longitude %s. Line: %d '
                            '[%s] in file "%s"' %
                            (lng, line_num, line, file_))

    for _ in lat:
        if _ not in VALID_CHARS:
            raise Exception('Invalid character for latitude %s. Line: %d [%s] '
                            'in file "%s"' %
                            (lat, line_num, line, file_))

    f_lng = float(lng)
    if f_lng < -180.0 or f_lng > 180.0:
        raise Exception('Longitude %s is outside valid range of -180.0 to '
                        '180.0. Line: %d [%s] in file "%s"' %
                        (lng, line_num, line, file_))

    f_lat = float(lat)
    if f_lat < -90.0 or f_lat > 90.0:
        raise Exception('Latitude %s is outside valid range of -90.0 to '
                        '90.0. Line: %d [%s] in file "%s"' %
                        (lat, line_num, line, file_))


def create_kml(filepath):
    """Create KML as a string by reading the lng/lat file"""
    vectors = []

    with open(filepath, 'rt') as file_:
        for line in file_:
            line = line.strip()
            if len(line) > 0:               # pylint: disable=len-as-condition
                lng, lat = line.split(' ')
                vectors.append((lng, lat))

    name = os.path.splitext(os.path.basename(filepath))[0]
    style_color = LINE_COLOR[:6].upper()

    vector_spacing = ' ' * 12
    vector_data = ''

    for _ in vectors:
        vector_data += '%s%s,%s,0\n' % (vector_spacing, _[0], _[1])

    kml = KML_TEMPLATE % (name,
                          style_color,
                          LINE_COLOR,
                          LINE_WIDTH,
                          POLY_COLOR,
                          POLY_FILL,
                          POLY_OUTLINE,
                          style_color,
                          LINE_COLOR,
                          LINE_WIDTH,
                          POLY_COLOR,
                          POLY_FILL,
                          POLY_OUTLINE,
                          style_color,
                          style_color,
                          style_color,
                          name,
                          name,
                          style_color,
                          vector_data)

    return kml


def get_ogr2ogr_exe(path):
    """Check if we have have GDAL ogr2ogr tool instaled and return exe path"""
    if path is None:
        exe = which('ogr2ogr')
    else:
        exe = path

    # Ensure program can run
    proc = subprocess.Popen([exe, '--version'], shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    out, err = proc.communicate()

    if out.decode()[:5] != 'GDAL ':
        print('STDOUT>', out.decode())
        print('STDERR>', err.decode())
        raise Exception('executable %s does not appear to be valid' % (exe, ))

    return exe


def parse_command_line():
    """Parse the command line options"""
    parser = \
        argparse.ArgumentParser(description='Convert lng/lat vector list to '
                                'KML & ESRI shapefile formats')

    output_group = parser.add_mutually_exclusive_group()

    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='file(s) to convert')

    parser.add_argument('--overwrite', '-w', action='store_true',
                        help='overwrite destination files')

    output_group.add_argument('--no-kml', '-k', action='store_true',
                              help="don't create KML files")

    output_group.add_argument('--no-shp', '-s', action='store_true',
                              help="don't create SHP, DBF, PRJ & SHX files")

    parser.add_argument('--exe-path', '-p', metavar='file', type=str,
                        help=('specify alternate path for ogr2ogr binary '
                              '(e.g. /home/me/bin/ogr2ogr). Default is to '
                              'automatically search your path for the binary'))

    return parser.parse_args()


def check_input_files(args):
    """Check input file(s) exist and are formatted correctly"""

    # Create a list of files+extensions to check for if we are not overwriting
    if not args.overwrite:
        if not args.no_kml:
            extensions_to_check = ['kml']
        else:
            extensions_to_check = []
        if not args.no_shp:
            extensions_to_check += ['dbf', 'prj', 'shp', 'shx']

    print('Checking input files')
    for _ in args.files:
        _ = os.path.abspath(_)
        with open(_, 'rt') as file_:
            print('\t%s' % (_, ), end='\t')
            line_count = 0
            data_lines = 0
            for line in file_:
                line_count += 1
                line = line.strip()
                if len(line) > 0:           # pylint: disable=len-as-condition
                    check_line(_, line, line_count)
                    data_lines += 1

            if data_lines < 3:  # Minimum polygon is a triangle (3 vectors)
                raise Exception('File "%s" contains no polygon data' % (_, ))

        if not args.overwrite:
            # Check if destination file(s) exist
            no_extension = os.path.splitext(_)[0]
            for ext in extensions_to_check:
                dest_file = '%s.%s' % (no_extension, ext)
                if os.path.isfile(dest_file):
                    raise Exception('Destination file "%s" already exists!' %
                                    (dest_file, ))

        print('OK!')


def call_ogr2ogr(exe, shp_file, kml_file):
    """Calls the ogr2ogr exe to conver kml to shp"""
    proc_args = [exe, '-f', 'ESRI Shapefile', '-overwrite',
                 shp_file, kml_file]
    proc = subprocess.Popen(proc_args,
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    out, err = proc.communicate()

    err_list = err.decode().strip().split('\n')
    errors = 0
    for _ in err_list:
        if _[:8] == 'Warning ':     # Ignore warnings
            continue
        else:
            errors += 1

    if len(out) > 0 or errors > 0:          # pylint: disable=len-as-condition
        cmd_args = ' '.join(proc_args).replace('ESRI Shapefile',
                                               "'ESRI Shapefile'")

        print('\nARGS>  ', cmd_args)
        print('STDOUT>', out.decode())
        print('STDERR>', err.decode())
        raise Exception('Conversion error. Command information above.')


def main():
    """Main function"""

    print('gps2shp v%s\n' % (__version__, ))

    args = parse_command_line()

    if not args.no_shp:
        exe = get_ogr2ogr_exe(args.exe_path)

    # Check our input files exist and are valid form
    check_input_files(args)

    if not args.no_kml and not args.no_shp:
        convert_desc = 'KML files and ESRI Shapefiles'
    elif not args.no_kml:
        convert_desc = 'KML files'
    else:
        convert_desc = 'ESRI Shapefiles'

    print('\nConverting to %s' % (convert_desc, ))

    for file_ in args.files:
        file_ = os.path.abspath(file_)
        no_extension = os.path.splitext(file_)[0]
        kml = create_kml(file_)

        if not args.no_kml:
            kml_file = no_extension + '.kml'
            print('\t%s\t->\t%s\t' % (file_, kml_file), end='\t')
        else:
            # Use a tempfile for KML which we'll delete later
            _, kml_file = tempfile.mkstemp()

        with open(kml_file, 'wt') as outfile:
            outfile.write(kml)

        if not args.no_kml:
            print('OK!')

        if not args.no_shp:
            # Convert to ESRI Shapefiles
            shp_file = no_extension + '.shp'
            print('\t%s\t->\t%s,dbf,prj,shx' % (file_, shp_file), end='\t')

            call_ogr2ogr(exe, shp_file, kml_file)
            print('OK!')

        if args.no_kml:
            # Delete our temp kml file
            os.remove(kml_file)


if __name__ == '__main__':
    main()
