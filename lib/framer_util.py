# Copyright John Andrea, 2019

import struct
import argparse
import re
import sys
import datetime
import json

def version_string():
    return '1.7'

def get_header_key():
    # use an item which won't ever occur as an instrument name
    return 'header info'

def get_final_float_format():
    # for the viewer program
    return '%.7g'

def get_float_format():
    # for all the intermediate data
    return '%.9g'

def is_hex_int(s):
    if s is not None:
       try:
         int( s, 16 )
         return True
       except:
         return False

    return False

def is_number(s):
    try:
      float(s)
    except ValueError:
      return False

    return True

def field_is_a_string( instrument, field, data ):
    # fields which are string values and should be ignored
    # by averaging, fitting, etc
    #
    # the input should be the header section

    result = False

    if 'strings' in data:
       if instrument in data['strings']:
          result = field in data['strings'][instrument]
    return result

def json_data_is_framer( must_have_data, data ):
    error = ''

    if data:
       # check this needed key
       item    = get_header_key()
       subitem = 'extracted by'

       if item not in data:
          error += 'Missing "info" identifier tag in input file'
       else:
          if not isinstance( data[item], dict ):
             error += 'Identifier tag is not a json dictionary'
          else:
             if subitem not in data[item]:
                error += 'Missing framer id in info section'
             else:
                if not isinstance(data[item][subitem], str ):
                   error += 'Framer info id is not a simple string'
                else:
                   if data[item][subitem].lower().strip() != 'framer':
                      error += 'Framer info id is not as expected'
    else:
       # is empty
       if must_have_data:
          error += 'Input data is empty'

    return error

def read_framer_results_from_file( file ):
    error = ''
    data = dict()

    try:
       with open( file ) as f:
            data = json.load( f )
       error += json_data_is_framer( True, data )
    except:
       error += 'Cannot load data json file:' + file + '\n'

    return error,data

def read_framer_results():
    error = ''
    data = dict()

    try:
      data = json.load( sys.stdin )

      error += json_data_is_framer( True, data )

    except:
      error += 'Error loading input file'

    return error, data

def read_framer_results_allow_empty_stdin():
    error = ''
    data = dict()

    try:
      if not sys.stdin.isatty():
         data = json.load( sys.stdin )
         error += json_data_is_framer( False, data )

    except:
      error += 'Error loading input file'

    return error, data

def string_looks_like_time( s ):
    # years 1000 to 2999
    # ignoring leap seconds
    # and note that leading zeros are required
    #                            ^    y y y y-   m  m-   d  d    h  h:   m  m:   s  s$
    is_timestamp = re.compile( r'^[1-2]\d\d\d-[0-1]\d-[0-3]\d [0-2]\d:[0-5]\d:[0-5]\d$' )
    # probably contains millisec, but might not, so remove those numbers at the end
    msec_portion = re.compile( r'\.\d+$' )

    return bool(is_timestamp.match( msec_portion.sub('',s) ))

def get_command_options( program, desc ):
    need_data    = False
    need_package = False
    need_path    = False
    need_interval= False
    need_single_config = False
    need_dates   = False
    need_style   = False
    need_multi_files  = False
    need_enable_tests = False

    program = program.lower().strip()

    if program == 'main':
       need_data    = True
       need_package = True
       need_path    = True
       need_enable_tests = True
    if program == 'filter':
       need_package = True
       need_path    = True
    if program == 'validator':
       need_package = True
       need_path    = True
       need_enable_tests = True
    if program == 'average':
       need_interval = True
    if program == 'date-select':
       need_dates = True
    if program == 'check package':
       need_path    = True
       need_package = True
    if program == 'check config':
       need_single_config = True
    if program == 'viewer':
       need_style = True
    if program == 'multi-files':
       need_multi_files = True

    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument( '--version', help='Show version then quit' )
    parser.add_argument( '--verbose', help='Set information level. Default 1',
                         type=int, default=1 )

    if need_path:
       parser.add_argument( '-configpath', '--configpath',
                            default='.',
                            help='Location of configuration files. Default is current directory' )

    if need_interval:
       parser.add_argument( '--interval', help='Averaging interval minutes. Default 15',
                            type=int, default=15 )

    if need_style:
       parser.add_argument( '--style', help='Show data output "combined" or "separate". Default is "separate"',
                            type=str, default='separate' )

    if need_enable_tests:
       parser.add_argument( '--enable-tests', help='Enable checksums, etc. Default is "yes"',
                            type=str, default='yes' )

    if need_dates:
       parser.add_argument( '--mindate', help='Minimum date of data to be output.',
                            type=str, default='1900-01-01' )
       parser.add_argument( '--maxdate', help='Maximum date of data to be output.',
                            type=str, default='2999-01-01' )

    if need_package:
       # minimal style doesn't need this or data file
       parser.add_argument('packagefile', nargs=1, help='Name of package listing config files')

    if need_multi_files:
       # but files are optional
       parser.add_argument('datafiles', type=argparse.FileType('r'), nargs='*' )

    if need_single_config:
       # single input file
       parser.add_argument('configfile', nargs=1, help='Name of a config file')

    if need_data:
       # other types don't need this file
       # otherwise, its the end argument
       parser.add_argument('datafile', nargs=1, help='Name of input data file')

    args = parser.parse_args()

    # handle the version right away
    if args.version:
       print( version_string(), file=sys.stderr )
       sys.exit( 0 )

    results = dict()
    results['verbose']    = args.verbose
    results['configpath'] = None
    results['packagefile']= None
    results['datafile']   = None
    results['interval']   = None
    results['configfile'] = None
    results['mindate']    = None
    results['maxdate']    = None
    results['style']      = None
    results['enable tests'] = True

    if need_single_config: results['configfile']  = args.configfile[0]
    if need_path:          results['configpath']  = args.configpath
    if need_package:       results['packagefile'] = args.packagefile[0]
    if need_data:          results['datafile']    = args.datafile[0]
    if need_interval:      results['interval']    = args.interval
    if need_style:         results['style']       = args.style
    if need_dates:
       results['mindate'] = args.mindate
       results['maxdate'] = args.maxdate
    if need_enable_tests:
       if args.enable_tests.lower() == 'no':
          results['enable tests'] = False
    if need_multi_files:
       results['files'] = []
       for datafile in args.datafiles:
           results['files'].append( datafile.name )

    return results

def hide_binary_bytes( byte_string ):
    result = ''
    for b in byte_string:
        i = int(b)
        if (i < 32) or (i > 126):
           result += 'x(%02x)' % (i)
        else:
           result += chr(i)
    return result

def contains_binary_bytes( byte_string ):
    # that is, does this binary string contain non-printable chars
    # do allow tabs
    in_size  = 0
    out_size = 0
    for b in byte_string:
        in_size += 1
        i = int(b)
        if ( 31 < i < 127 ) or (i == 9):
           out_size += 1
    # be sure of the return value; equal sizes means "does not contain..."
    return in_size != out_size

def lowercase_and_trim_dict_keys( obj ):
    # don't trim/strip the values because they might remove CR or NL chars
    if isinstance(obj, dict):
       return {k.lower().strip():lowercase_and_trim_dict_keys(v) for k, v in obj.items()}
    elif isinstance(obj, (list, set, tuple)):
       t = type(obj)
       return t(lowercase_and_trim_dict_keys(o) for o in obj)
    else:
       return obj

def get_storx_timestamp( data, offset ):
    # the 7 byte binary timestamp at the end of every frame

    timestamp = None

    try:
       result = struct.unpack_from( '>7B', data, offset )

       f1 = 256
       f2 = 65536
       f3 = 16777216

       date = result[0] * f2 + result[1] * f1 + result[2]
       time = result[3] * f3 + result[4] * f2 + result[5] * f1 + result[6]

       year = int( date / 1000 )
       doy  = date - year * 1000

       remain = time
       div    = 10000000

       hour = int( remain / div )

       remain = remain - hour * div
       div    = div / 100
       minute = int( remain / div )
       remain = remain - minute * div
       div    = div / 100
       second = int( remain / div )
       msec   = remain - second * div

       d = datetime.datetime(year, 1, 1) + datetime.timedelta(doy - 1)

       # as an additional check on the decoded binary bytes
       # make sure the year is within a reasonable range

       if 1990 < d.year < 2120:
          timestamp = '%d-%02d-%02d %02d:%02d:%02d.%02d' % (d.year, d.month, d.day, hour, minute, second, msec )

    except:
       pass

    return timestamp
