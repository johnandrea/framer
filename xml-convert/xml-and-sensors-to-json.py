#!/usr/local/bin/python3

import sys
import os
import argparse

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/./')

from xml_converter_lib import convert_xml

def get_sensors_fields( filename ):
    data = dict()

    with open( filename ) as f:
         for line in f:
             line = line.lower().strip()
             if line:
                items = line.split( ':' )
                frame = items[1].strip()
                if frame not in data:
                   data[frame] = []
                data[frame].append( items[2].strip() )
    return data

parser = argparse.ArgumentParser('Convert an XML file to JSON style config')
parser.add_argument( 'xmlfile', nargs=1, help='Name of an XML file' )
parser.add_argument( 'sensorsfile', nargs=1, help='Name the matching sensors file' )
args = parser.parse_args()

xml_file     = args.xmlfile[0]
sensors_file = args.sensorsfile[0]

if not os.path.isfile( xml_file ):
   print( 'XML file does not exist', file=sys.stderr )
   sys.exit( 1 )
if not os.path.isfile( sensors_file ):
   print( 'Sensors file does not exist', file=sys.stderr )
   sys.exit( 1 )

convert_xml( xml_file, True, get_sensors_fields( sensors_file) )
