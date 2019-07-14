#!/usr/local/bin/python3

import sys
import os
import re
import argparse

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/./')

from xml_converter_lib import delim_translate, output_to_json, is_number

parser = argparse.ArgumentParser('Convert a TDF file to JSON style config')
parser.add_argument( 'tdffile', nargs=1, help='Name of a TDF file' )
args = parser.parse_args()

in_file = args.tdffile[0]

if not os.path.isfile( in_file ):
   print( 'TDF file does not exist', file=sys.stderr )
   sys.exit( 1 )

data = dict()
data['instrument'] = 'unknown'
data['serial']     = '999'
data['frame_type'] = ''
data['frame_header'] = ''
data['fields']     = []

instrument_defined = False
sn_defined = False
terminator_defined = False
field_delim = ''
names = []
expecting_coeffs = False
n_fields = -1

prev_line = ''

error = ''

ignore_names = ['rate','datarate','sensor','sensorsn','caltemp','thermal_resp']
ignore_names.append( 'frame' )

fit_types = [ 'polyf', 'polyu', 'optic2', 'optic3' ]

with open( in_file ) as f:
     for line in f:
         line = re.sub( r'#.*', '', line ).lower().strip()
         if line == '': continue

         items = line.split()

         if (items[0] == 'instrument') or (items[0] == 'vlf_instrument'):
            if instrument_defined:
               error += 'Instrument defined twice\n'
            else:
               instrument_defined = True

               # the instrument name might not be exactly correct
               # since this item is more of the start of the sync word
               # both might need masaging

               data['instrument'] = items[1]
               data['frame_header'] = items[1]

               if items[0] == 'instrument':
                  data['frame_type'] = 'binary'
               else:
                  data['frame_type'] = 'ascii'

         elif items[0] == 'sn':
            if sn_defined:
               error += 'S/N defined twice\n'
            else:
               if 'instrument' in prev_line:
                  data['serial'] = items[1]
               else:
                  error += 'S/N should come immediately after instrument\n'

         elif items[0] == 'terminator':
            if terminator_defined:
               error += 'Terminator defined twice\n'
            else:
               terminator_defined = True
               data['frame_terminator'] = delim_translate( items[2] )

         elif items[0] in ignore_names:
            pass

         elif is_number( items[0] ):
            # must be coeffs
            if expecting_coeffs:

               c = 0
               for value in items:
                   data['fields'][n_fields]['fit']['coeffs'].append( dict() )

                   name = 'a' + str(c)

                   if data['fields'][n_fields]['fit']['type'] == 'optic2':
                      if c == 2: name = 'im'
                   elif data['fields'][n_fields]['fit']['type'] == 'optic3':
                      if c == 2: name = 'im'
                      if c == 3: name = 'cint'

                   data['fields'][n_fields]['fit']['coeffs'][c]['name'] = name
                   data['fields'][n_fields]['fit']['coeffs'][c]['value'] = value

                   c += 1

               expecting_coeffs = False
            else:
               error += 'Set of numbers out of order with fields\n'

         elif items[0] == 'field':
            # for the next field
            field_delim = items[2]

         else:
            # this muse be a field
            # Satlantic document says
            # TYPE ID UNITS FIELD-LENGTH DATA-TYPE CAL-LINES FIT-TYPE
            #   0   1   2      3          4         5         6

            n_fields += 1

            if items[1] == 'none': items[1] = ''
            name = items[0] + items[1]

            data['fields'].append( dict() )
            data['fields'][n_fields]['name'] = name
            data['fields'][n_fields]['type'] = items[4]
            if data['frame_type'] == 'binary':
               data['fields'][n_fields]['length'] = items[3]
            else:
               data['fields'][n_fields]['delimiter'] = delim_translate(field_delim)

            if name in names:
               error += 'Field defined twice: ' + name + '\n'
            names.append( name )

            if items[6] != 'count':
               expecting_coeffs = True
               if int(items[5]) > 1:
                  error += 'Cannot handle more than 1 set of coeffs\n'
               elif int(items[5]) == 1:
                  if items[6] in fit_types:
                     data['fields'][n_fields]['fit'] = dict()
                     data['fields'][n_fields]['fit']['type'] = items[6]
                     data['fields'][n_fields]['fit']['coeffs'] = []
                  else:
                     error += 'Undefined fit type: ' + items[5] + '\n'

         prev_line = items[0]

if error:
   print( error, file=sys.stderr )
   # output to an error so that an existing file won't be overwritten
   data['instrument'] = 'error'
   data['serial']     = '999'

output_to_json( False, [], '', data )
