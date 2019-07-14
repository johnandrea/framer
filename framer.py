#!/usr/local/bin/python3

# Arguments
# 1 = name of package file
# 2 = config directory
# 3 = name of data file
#
# Output to stdout

# Copyright John Andrea, 2019

import sys
import os
import struct
import json
from datetime import datetime
#from pprint import pprint

# setup a few library files
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append( dir_path + '/lib/')

from framer_util   import version_string,get_header_key,hide_binary_bytes,contains_binary_bytes,is_number,get_command_options,get_storx_timestamp,is_hex_int
from framer_config import get_configurations,is_integer,is_valid_timestamp_string

def perform_transform( field, values, config ):
    # multiple transforms are possible
    value = values[field]
    for section in config['transform']:
        if section['is_enabled']:
           key = section['name']
           if key in values:
              check = values[key]

              # transforms can only be applied to numeric fields
              # but the check value might be anything

              if section['type'] == 'north-south':
                 if str( check ).lower() == 'n':
                    value = abs( float( value ) )
                 elif str( check ).lower() == 's':
                    value = -1.0 * abs( float( value ) )

              elif section['type'] == 'east-west':
                 if str( check ).lower() == 'e':
                    value = abs( float( value ) )
                 elif str( check ).lower() == 'w':
                    value = -1.0 * abs( float( value ) )

    return value

def checksum_ok( verbose, values, offset, length, config, data ):
    if not config['enabled_checksum']:
       return True

    log_this = verbose > 2

    ok = True

    for section in config['checksum']:
        if not section['is_enabled']:
           continue

        # this is the name of the field which contains the checksum
        sum_name = section['name']

        sum_type = section['type']

        if sum_type == 'aquadopp':
           print( 'checksum not implemented', sum_type, file=sys.stderr )

           # ABOUT THIS CHECK
           # problem with Aquadopp frames is the the StorX disposes of
           # the instrument sync (0xa5) and header id (sometimes 0x12)
           # so doing the computation here would always be a check failure

           #if (sum_name in values) and (values[sum_name] is not None):
           #
              ## the sum can't be anything but an intger
              #given = int( values[sum_name] )
              #
              ## find the start and end locations
              ## assuming binary
              #
              #start_loc = -1
              #end_loc   = -1
              #
              #for i in range( config['n_fields'] ):
              #    field_name = config['fields'][i]['name']
              #    if field_name == section['start']:
              #       start_loc = config['fields'][i]['offset']
              #    if field_name == sum_name:
              #       end_loc = config['fields'][i]['offset']
              #
              ## protect against a mistake in the configuration
              #if (start_loc >=0) and (end_loc > start_loc):
              #
              #   # skip past the header and the current location
              #   start_loc += config['sync_len'] + offset
              #   end_loc   += config['sync_len'] + offset
              #
              #   n_shorts = int(( end_loc - start_loc ) / 2)
              #   vals = struct.unpack_from("<%dH" % n_shorts, data, start_loc)
              #   #computed = sum(vals[:-1], 0xb58c) % 0x10000
              #
              #   ok = ( given == computed )
              #
              #   if not ok and log_this:
              #      print( 'Checksum failed: ',name,given,'vs',computed, file=sys.stderr )
              #else:
              #   # locations are invalid
              #   ok = False
           #
           #else:
           #   # if the checksum value is not available, is frame good or not
           #   # I'm going with not good
           #   # ok = False

        elif sum_type == 'nmea':
             if (sum_name in values) and (values[sum_name] is not None):

                given      = values[sum_name]
                calculated = None

                # find the asterix
                asterix_loc = data.find( b'*', offset+config['sync_len'] )

                # assuming that the terminator does not contain an asterix
                if 0 < asterix_loc < offset + length:

                   # this frame in the data
                   start = offset + section['len_skip']
                   end   = offset + length - config['term_len'] + 1

                   nmea_data,nmea_sum = data[start:end].decode('utf-8').split( '*', 1 )

                   # should have given == nmea_sum
                   # but check this sum incase the configuration specified the wrong field
                   if is_hex_int( nmea_sum ):

                      calculated = 0
                      for c in nmea_data:
                          calculated ^= ord(c)

                      ok = int( nmea_sum, 16 ) == calculated

                      if not ok and log_this:
                         print( '  ', 'Checksum failed: ',given,'hex vs',calculated, file=sys.stderr )

                   else:
                      ok = False
                      if log_this:
                         print( '  ', 'Checksum is invalid: ', nmea_sum, 'frame skipped', file=sys.stderr )

             else:
               # if the checksum value is not available, is frame good or not
               # I'm going with not good
               ok = False
               if log_this:
                  print( '  ', 'Missing checksum', sum_type, 'frame skipped', file=sys.stderr )

        else:
            # don't change value of 'ok'
            if log_this:
               print( '  ', 'Ignoring unknown checksum', sum_type, file=sys.stderr )

        if not ok:
           break

    return ok

def frame_passes_validity( verbose, values, config ):
    if not config['enabled_frame_validity']:
       return True

    log_this = verbose > 2

    ok = True

    # the section of config in question will look like this (there maybe more than 1 checks in the array
    # 'frame_validity': [{'enable': 'yes', 'is_enabled': True, 'name': 'psvolt',
    #                      'numerals': 'float', 'op': '>', 'value': 50000.7}],
    # The comparison type can be string or a number
    # 'frame_validity': [{'enable': 'yes', 'is_enabled': True, 'name': 'status',
    #                      'numerals': 'string', 'op': '=', 'value': 'A"}],
    # make the conversions needed below

    item = 'frame_validity'

    for i in range( config['n_frame_validity'] ):
        if config[item][i]['is_enabled']:
           key     = config[item][i]['name']
           op      = config[item][i]['op']
           value   = None
           if key in values.keys():
              if config[item][i]['numerals'] == 'float':
                 value = float( values[key] )
                 check = float( config[item][i]['value'] )
              else:
                 # should be ok to do this str conversion if integer or string
                 value = str( values[key] )
                 check = str( config[item][i]['value'] )

              if op in ['=', '==']:
                 ok = value == check
              elif op in ['!=', '<>' ]:
                 ok = value != check
              elif op == '>':
                 ok = value > check
              elif op in ['>=', '=>']:
                 ok = value >= check
              elif op == '<':
                 ok = value < check
              elif op in ['<=', '=<']:
                 ok = value <= check

           if not ok:
              if log_this:
                 print( '  ', 'Frame validity failed: ',key,value, file=sys.stderr )
              break

    return ok

def handle_binary_frame( validity, offset, config, data ):
    # return values indexed by name
    #
    # this version unpacks the fields from the binary string one at a time
    # beacuse it seems that if the unpack format gets too large the unpacker fails

    ok        = True
    length    = config['data_length']
    timestamp = ''
    values    = dict()

    # is there enough space left in the data for this frame
    # plus the sync word
    # plus the 7 byte storx timestamp

    remaining = len( data ) - offset
    needed    = length + config['sync_len'] + 7
    if remaining >= needed:

       timestamp = None

       # skip past the header
       frame_offset = offset + config['sync_len']

       try:
          for i in range( config['n_fields'] ):
              # don't even bother to return skipped fields
              if config['fields'][i]['numerals'] != 'skip':

                 result = struct.unpack_from( config['fields'][i]['format'], data, frame_offset )

                 values[config['fields'][i]['name']] = result[0]

                 if validity > 7:
                    print( '  ', config['fields'][i]['name'], result[0], file=sys.stderr )

              frame_offset += config['fields'][i]['length']

          timestamp = get_storx_timestamp( data, frame_offset )

       except:
          ok = False

    else:
       ok = False
       if verbose > 3:
          print( '   not enough bytes remaining', file=sys.stderr )

    return ok, timestamp, values, length

def handle_ascii_frame( verbose, offset, config, data ):
    # return values indexed by name

    ok        = True
    length    = 1
    timestamp = ''
    values    = dict()

    # is there enough space left in the data for this frame
    # plus the sync word
    # plus all the delimiters
    # plus the terminator
    # plus the 7 byte storx timestamp

    n_fields = config['n_fields']

    needed = config['sync_len'] + config['term_len'] + 7
    for i in range( n_fields ):
        needed += config['fields'][i]['len_delim']

    remaining = len( data ) - offset

    if remaining >= needed:

       # find the end
       end_loc = data.find( config['term'], offset )

       if end_loc > 1:
          # terminator has been found
          length = end_loc - offset + 1

          # skip past the header
          offset += config['sync_len']

          # should be at the start of the first delimiter
          # skip past it
          offset += len( config['fields'][i]['delim'] )

          prev_offset = offset
          for i in range( n_fields ):
              name     = config['fields'][i]['name']
              numerals = config['fields'][i]['numerals']
              value    = None

              # the end of this field will be the next delimiter
              if i == n_fields - 1:
                 # this is the last field it ends at the terminator
                 next_offset = end_loc
                 len_delim   = 1
              else:
                 next_delim = config['fields'][i+1]['delim']
                 len_delim  = config['fields'][i+1]['len_delim']
                 next_offset = data.find( next_delim, prev_offset )

              if next_offset >= 1:
                 if next_offset > end_loc:
                    # run past the end of the frame
                    ok = False
                    if verbose > 5:
                       print( '   delimiter not found in frame', file=sys.stderr )
                 else:
                    # string or skip types might contain binary bytes
                    if numerals in ['string', 'skip']:
                       # just grab the value, no matter what
                       value = hide_binary_bytes( data[prev_offset:next_offset] )
                    else:
                      if contains_binary_bytes( data[prev_offset:next_offset] ):
                         # this is an ascii frame, how did bin chars get in this number
                         ok = False
                         if verbose > 6:
                            print( '   binary bytes found in ascii field', file=sys.stderr )
                      else:
                         value = data[prev_offset:next_offset].decode('utf-8').strip()
                         if (value == '') or (value.lower() == 'nan') or (value.lower() == 'inf'):
                            value = None
                         else:
                            if numerals == 'int':
                               ok = is_integer( value )
                            elif numerals == 'float':
                               ok = is_number( value )
                            if not ok:
                               if verbose > 6:
                                  print( '   non-numeric where number expected', file=sys.stderr )
                    prev_offset = next_offset + len_delim
              else:
                 ok = False
              if not ok:
                 break

              if value is not None:
                 # don't even return skipped values
                 if numerals != 'skip':
                    values[name] = value
                    if verbose > 7:
                       print( '  ', name, value, file=sys.stderr )
       if ok:
          offset = end_loc + len( config['term'] )
          # check again for enough bytes
          if ( offset + 7 ) <= len( data ):
             timestamp = get_storx_timestamp( data, offset )
          else:
             ok = False
             if verbose > 4:
                print( '   not enough bytes for timestamp', file=sys.stderr )

    else:
       # not enough bytes remaining
       ok = False
       if verbose > 3:
          print( '   not enough bytes remain', file=sys.stderr )

    return ok, timestamp, values, length

options = get_command_options( 'main',
                               'Extract data from raw files. Output to stdout.' )

packagefile= options['packagefile']
configpath = options['configpath']
datafile   = options['datafile']
verbose    = int( options['verbose'] )
enable_tests = options['enable tests']

if not os.path.isfile( packagefile ):
   print( 'package file does not exist', file=sys.stderr )
   sys.exit( 1 )
if not os.path.isdir( configpath ):
   print( 'config path does not exist', file=sys.stderr )
   sys.exit( 1 )
if not os.path.isfile( datafile ):
   print( 'data file does not exist', datafile, file=sys.stderr )
   sys.exit( 1 )

error, configs = get_configurations( enable_tests, packagefile, configpath )

if error:
   print( error, file=sys.stderr )
   sys.exit( 1 )

# until documented, don't do this
#if verbose >= 99:
#    with open( 'framer.log', "w" ) as v:
#         pprint( configs, v )

# find if any fields require a transform

any_transforms = False
transform_fields = dict()
transform_name_to_tag = dict()
for frame_id in configs:
    transform_fields[frame_id] = dict()
    transform_name_to_tag[frame_id] = dict()
    tag = 'fields'
    if configs[frame_id]['enabled_field_transform']:
       any_transforms = True
       for i in range( configs[frame_id]['n_fields'] ):
           if configs[frame_id][tag][i]['enabled_transform']:
              name = configs[frame_id][tag][i]['name']
              transform_fields[frame_id][name] = i
              transform_name_to_tag[frame_id][name] = tag
    tag = 'duplicates'
    if configs[frame_id]['enabled_duplicates_field_transform']:
       any_transforms = True
       for i in range( configs[frame_id]['n_duplicates'] ):
           if configs[frame_id][tag][i]['enabled_transform']:
              name = configs[frame_id][tag][i]['name']
              transform_fields[frame_id][name] = i
              transform_name_to_tag[frame_id][name] = tag

# no need for an exception here
# if the data read causes exception then let it go to the command line

data = open( datafile, "rb" ).read()
end_of_data = len( data ) + 1

extracted_data = dict()

# save some meta data
header_key = get_header_key()
extracted_data[header_key] = dict()

extracted_data[header_key]['extracted by'] = 'Framer'
extracted_data[header_key]['extractor version'] = version_string()
extracted_data[header_key]['extracted on'] = datetime.today().strftime('%Y-%m-%d %H:%M')
extracted_data[header_key]['data file']    = datafile
extracted_data[header_key]['operations']   = 'framer'

# put info into the output to show which are the string fields
# which need to be skipped by the later averaging and fitting

extracted_data[header_key]['strings'] = dict()
for frame_id in configs:
    if configs[frame_id]['has_string_fields']:
       extracted_data[header_key]['strings'][frame_id] = []
       for i in range( configs[frame_id]['n_fields'] ):
           if configs[frame_id]['fields'][i]['numerals'] == 'string':
              name = configs[frame_id]['fields'][i]['name']
              extracted_data[header_key]['strings'][frame_id].append( name )

# start scanning through the data

# find all the locations of each sync word
# saving them as location:frame_id
# should not be any chance of the sync words overlapping because the substring tests are already done

locations = dict()

for frame_id in configs:
    sync = configs[frame_id]['sync']
    offset = data.find( sync )
    while offset >= 0:
          locations[offset] = frame_id
          offset = data.find( sync, offset + 1 )

n_attempt = 0
n_valid   = 0

# Note about this scanning method.
# It is extremely unlikely, but possible, that the header for one instrument
# occurs within the data of another instrument: leading to an attempt to extract
# the second one in mistake.
# The correct action is for an header offset included in a valid frame to
# be skipped.

for offset in sorted( locations ):
   n_attempt = n_attempt + 1
   frame_id = locations[offset]

   if verbose > 1:
      print( frame_id, 'at', offset, file=sys.stderr )

   # the values will be returned with the name as the key

   if configs[frame_id]['is_binary']:
      ok, timestamp, values, frame_len = handle_binary_frame( verbose, offset, configs[frame_id], data )
   else:
      ok, timestamp, values, frame_len = handle_ascii_frame( verbose, offset, configs[frame_id], data )

   if ok:
      if verbose > 7:
         print( '   frame ended at', frame_len, file=sys.stderr )

      if is_valid_timestamp_string( timestamp ):

         if verbose > 1:
            print( '  ', timestamp, file=sys.stderr )

         if ( frame_passes_validity( verbose, values, configs[frame_id] )
              and checksum_ok( verbose, values, offset, frame_len, configs[frame_id], data ) ):

            n_valid = n_valid + 1

            if frame_id not in extracted_data:
               # first time this produced a value to be output
               extracted_data[frame_id] = dict()

            have_values = False

            for name in values:
                # allow for zero
                if values[name] is not None:

                   # take all the values, even strings because they might be
                   # needed for validity or transforms

                   have_values = True

                   if timestamp not in extracted_data[frame_id]:
                      # first of this time
                      extracted_data[frame_id][timestamp] = dict()

                   extracted_data[frame_id][timestamp][name] = values[name]

            # check for constants that need to be output with the values
            # and duplicates

            if have_values:
               if configs[frame_id]['has_reportable_constants']:
                  tag = 'constants'
                  for i in range( configs[frame_id]['n_constants'] ):
                      if configs[frame_id][tag][i]['is_reportable']:
                         # this timestamp should already have been initialized above
                         name  = configs[frame_id][tag][i]['name']
                         value = configs[frame_id][tag][i]['value']
                         extracted_data[frame_id][timestamp][name] = value

               if configs[frame_id]['has_reportable_duplicates']:
                  tag = 'duplicates'
                  for i in range( configs[frame_id]['n_duplicates'] ):
                      if configs[frame_id][tag][i]['is_reportable']:
                         name   = configs[frame_id][tag][i]['name']
                         dup_of = configs[frame_id][tag][i]['of']
                         if dup_of in values and values[dup_of] is not None:
                            extracted_data[frame_id][timestamp][name] = values[dup_of]

            else:
              if verbose > 2:
                 print( '   no usable values in frame', file=sys.stderr )

            # the transforms have to be applied afterwards because the
            # values depend on each other

            if any_transforms:
               if frame_id in transform_fields:
                  if verbose > 6:
                     print( '   applying transforms', file=sys.stderr )
                  for name in extracted_data[frame_id][timestamp]:
                      if name in transform_fields[frame_id]:
                         field_id = transform_fields[frame_id][name]
                         tag = transform_name_to_tag[frame_id][name]
                         extracted_data[frame_id][timestamp][name] = \
                             perform_transform( name, \
                                    extracted_data[frame_id][timestamp], \
                                    configs[frame_id][tag][field_id] )
         else:
           if verbose > 2:
              print( '   frame not valid', file=sys.stderr )
      else:
        if verbose > 2:
           print( '   invalid timestamp:', timestamp, file=sys.stderr )
   else:
     if verbose > 1:
        print( '   frame incomplete', file=sys.stderr )

if verbose > 2:
   if n_attempt < 1:
      print( 'no frame matches', file=sys.stderr )
   if n_valid > 0:
      print( n_valid, 'frames output', file=sys.stderr )
   else:
      print( 'no valid frames', file=sys.stderr )

json.dump( extracted_data, sys.stdout, indent=1 )
