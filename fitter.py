#!/usr/local/bin/python3

# Input on stdin
# Output to stdout
# Other options for configpath and packagefile

# Copyright John Andrea, 2019

import sys
import os
import json

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util   import get_header_key,get_command_options,read_framer_results,field_is_a_string,get_float_format
from framer_config import get_configurations

def perform_fit( out_format, given, details ):
    y = None

    n = details['n']

    if details['type'] == 'polyu':
       x = 1.0  # x^0
       y = 0.0

       for i in range( n ):
           y += ( details['coeffs'][i] * x )
           x *= given  # x^i

    elif details['type'] == 'polyf':
       y = details['coeffs'][0]
       for i in range( 1, n ):
           y *= ( given - details['coeffs'][i] )

    elif details['type'] == 'optic2':
       y = details['coeffs'][2] * details['coeffs'][1] * ( given - details['coeffs'][0] )

    elif details['type'] == 'optic3':
       y = details['coeffs'][2] * details['coeffs'][1] * ( given - details['coeffs'][0] ) * details['coeffs'][3] / details['coeffs'][4]

    elif details['type'] == 'pow10':
       exponent = ( given - details['coeffs'][0] ) / details['coeffs'][1]
       y = details['coeffs'][2] * pow( 10.0, exponent )

    return out_format % ( y )

def collect_coeffs( fit_config ):
    details = dict()

    n = len( fit_config['coeffs'] )
    details['type']   = fit_config['type']
    details['coeffs'] = []
    details['n']      = n
    for i in range( n ):
        details['coeffs'].append( None )

    if details['type'] == 'optic3':
       # exact set
       # don't know which order they are listed in, loop to get names
       for i in range(3):
           name = fit_config['coeffs'][i]['name']
           value= float( fit_config['coeffs'][i]['value'] )
           if   name == 'a0':   details['coeffs'][0] = value
           elif name == 'a1':   details['coeffs'][1] = value
           elif name == 'im':   details['coeffs'][2] = value
           elif name == 'cint': details['coeffs'][3] = value
           elif name == 'aint': details['coeffs'][4] = value

    elif details['type'] == 'optic2':
       # exact set
       # don't know which order they are listed in, loop to get names
       for i in range(3):
           name = fit_config['coeffs'][i]['name']
           value= float( fit_config['coeffs'][i]['value'] )
           if   name == 'a0': details['coeffs'][0] = value
           elif name == 'a1': details['coeffs'][1] = value
           else:              details['coeffs'][2] = value #Im

    elif details['type'] == 'pow10':
       # exact set
       # don't know which order they are listed in, loop to get names
       for i in range(3):
           name = fit_config['coeffs'][i]['name']
           value= float( fit_config['coeffs'][i]['value'] )
           if   name == 'a0': details['coeffs'][0] = value
           elif name == 'a1': details['coeffs'][1] = value
           else:              details['coeffs'][2] = value #Im

    else:
       # polyf and polyu
       # also loop over the names making a0, a1, a2, ...
       # and where the name matches the index then put the value into the index
       for i in range( n ):
           want = 'a' + str(i)
           for i in range( n ):
               name = fit_config['coeffs'][i]['name']
               if name == want:
                  details['coeffs'][i] = float( fit_config['coeffs'][i]['value'] )

    return details

options = get_command_options( 'filter',
                               'Convert values using coeffecients. Input on stdin. Output to stdout.' )

packagefile= options['packagefile']
configpath = options['configpath']
verbose    = int( options['verbose'] )

if not os.path.isfile( packagefile ):
   print( 'package file does not exist', file=sys.stderr )
   sys.exit( 1 )
if not os.path.isdir( configpath ):
   print( 'data file does not exist', file=sys.stderr )
   sys.exit( 1 )

error, configs = get_configurations( True, packagefile, configpath )

if error:
   print( error, file=sys.stderr )
   sys.exit( 1 )

error,data = read_framer_results()
if error:
  print( error, file=sys.stderr )
  sys.exit( 1 )

# either no fitting defined, or some of the instruments in the
# data don't have loaded configurations (which is ok)

n_fit = 0
for instrument in data:
    if instrument in configs:
       if configs[instrument]['enabled_fit']:
          n_fit += 1
       if configs[instrument]['enabled_duplicates_fit']:
          n_fit += 1

if n_fit < 1:
   # no work to do, input directly to output
   json.dump( data, sys.stdout, indent=1 )
   sys.exit( 0 )

# work directly on the existing data rather than a copy

header_key = get_header_key()
out_format = get_float_format()

for instrument in data:
    if instrument == header_key:
       # add metadata
       data[instrument]['fitter'] = True
       if 'operations' in data[instrument]:
          op = data[instrument]['operations']
          data[instrument]['operations'] = op + '/fitter'
       else:
          data[instrument]['operations'] = 'fitter'
       continue

    if instrument not in configs:
       # if no config for a found instrument, then no fitting
       continue

    if not ( configs[instrument]['enabled_fit'] or configs[instrument]['enabled_duplicates_fit'] ):
       # maybe none turned on
       continue

    # make sure there are some fields worthy of fitting
    # and along the way collect all the coeffs for faster processing

    coeffs = dict()

    fields_with_fits = dict()

    tag = 'fields'
    for i in range( configs[instrument]['n_' + tag] ):
        if configs[instrument][tag][i]['enabled_fit']:
           # a field can only have one fit, so if the field says enabled...
           name = configs[instrument][tag][i]['name']
           if not field_is_a_string( instrument, name, data[header_key] ):
              fields_with_fits[name] = i

              coeffs[name] = collect_coeffs( configs[instrument][tag][i]['fit'] )

    tag = 'duplicates'
    for i in range( configs[instrument]['n_' + tag] ):
        if configs[instrument][tag][i]['enabled_fit']:
           name = configs[instrument][tag][i]['name']
           fields_with_fits[name] = i

           coeffs[name] = collect_coeffs( configs[instrument][tag][i]['fit'] )

    if not fields_with_fits:
       continue

    for time in data[instrument]:
        for name in fields_with_fits:

            # does this field exist at this time
            if name in data[instrument][time]:
               value = float( data[instrument][time][name] )

               data[instrument][time][name] = perform_fit( out_format, value, coeffs[name] )

json.dump( data, sys.stdout, indent=1 )
