#!/usr/local/bin/python3

import sys
import os
import argparse

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/./')

from xml_converter_lib import convert_xml_to_tdf

parser = argparse.ArgumentParser('Convert an XML file to JSON style config')
parser.add_argument( 'xmlfile', nargs=1, help='Name of an XML file' )
args = parser.parse_args()

in_file = args.xmlfile[0]

if not os.path.isfile( in_file ):
   print( 'XML file does not exist', file=sys.stderr )
   sys.exit( 1 )

convert_xml_to_tdf( in_file, False, dict() )
