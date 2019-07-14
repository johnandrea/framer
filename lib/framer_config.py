# Copyright John Andrea, 2019

import re
import json
import os
from datetime import datetime
#import sys

def get_min_sync_size():
    return 3

def get_max_sync_size():
    return 21

def get_max_field_length():
    return 20000

def get_max_frame_terminator():
    return 10

def get_max_delimiter():
    return 5

def is_yes_word(s):
    return str(s) in [ 'y', 'yes', 't', 'true', '1', 'on', 'ok' ]

def get_changable_config_keys():
    # these are the keys which have values that can be set to lowercase
    # and trimmed without any harm

    results = [ 'name' ]
    results.append( 'op' )
    results.append( 'type' )
    results.append( 'frame_type' )
    results.append( 'report' )
    results.append( 'enabled' )
    results.append( 'start' )
    results.append( 'length' )

    return results

def get_field_types():
    types = dict()
    types['binary'] = dict()
    types['ascii']  = dict()

    types['binary']['bb'] = 'binary bytes'
    types['binary']['bs'] = 'binary signed int'
    types['binary']['bf'] = 'binary float'
    types['binary']['bd'] = 'binary double'
    types['binary']['bu'] = 'binary unsigned int'
    types['binary']['bsle'] = 'binary signed int little endian'
    types['binary']['bule'] = 'binary unsigned int little endian'

    types['ascii']['as'] = 'ascii text'
    types['ascii']['ai'] = 'ascii int'
    types['ascii']['au'] = 'ascii int'
    types['ascii']['af'] = 'ascii float'
    types['ascii']['ad'] = 'ascii float'
    types['ascii']['ax'] = 'ascii skip'

    return types

def is_valid_fit( s ):
    return s in [ 'polyu', 'polyf', 'optic2', 'optic3', 'pow10' ]

def is_valid_operator( s ):
    return s in ['=', '==', '!=', '<>', '>', '>=', '=>', '<', '<=', '=<' ]

def quote( s ):
    # put quotes and spaces around the string
    return ' "' + s + '" '

def field_type_is_numeric( name ):
    if name:
       # exclude from the string types
       return (name not in ['as', 'ax', 'bb' ])
    else:
       return False

def is_atomic_type( name, data, prefix, suffix ):
    error = ''
    if not isinstance( data, (int,float,str) ):
       error += prefix + name + ' is not a simple value' + suffix
    return error

def is_nonempty_number( name, data, suffix='\n' ):
    error = ''

    if isinstance( data, str ):
       if data.strip() == '':
          error += name + ' cannot be empty' + suffix
       else:
          if not is_number( data ):
             error += name + ' is not numeric' + suffix

    elif isinstance( data, (int,float) ):
       pass

    else:
       error += name + ' is not simple numeric' + suffix

    return error

def is_nonempty_int( name, data, suffix='\n' ):
    error = ''

    if isinstance( data, str ):
       if data.strip() == '':
          error += name + ' cannot be empty' + suffix
       else:
          if not is_integer( data ):
             error += name + ' is not a number' + suffix

    elif isinstance( data, int ):
       pass

    else:
       error += name + ' is not simple number' + suffix

    return error

def is_nonempty_string( prefix, data, suffix='\n' ):
    error = ''

    if isinstance( data, str ):
       # don't strip, because anything which could be, already has been
       if data == '':
         error += prefix + ' cannot be empty' + suffix
    else:
       error += prefix + ' is not a simple string' + suffix

    return error

def has_string_values( name, good_values, data, suffix ):
    error = ''

    if isinstance( data, str ):
       if data == '':
          error += quote(name) + 'cannot be empty' + suffix
       else:
          if data not in good_values:
             error += name + ' must be one of'
             for value in good_values:
                 error += quote(value)
             error += suffix
    else:
      error += quote(name) + 'is not a simple string' + suffix

    return error

def is_valid_timestamp_string(s):
    ok = True
    if s:
       # remove msec digits at the end if they do exit
       msec_portion = re.compile( r'\.\d+$' )
       try:
         datetime.strptime( msec_portion.sub( '', s ), '%Y-%m-%d %H:%M:%S')
       except:
         ok = False
    else:
       ok = False

    return ok

def is_number(s):
    try:
      float(s)
    except ValueError:
      return False

    return True

def is_integer(s):
    try:
      int(s)
    except ValueError:
      return False

    return True

def specific_lower_and_trim( changable, parent, obj ):
    # lowercase and trim all keys in a dict,
    # but not all the value parts because they may have contents that should not be changed
    #
    # "changeable" is an array which contains the keys whose values can be changed

    if isinstance(obj, dict):
       return {k.lower().strip():specific_lower_and_trim(changable,k.lower().strip(),v) for k, v in obj.items()}
    elif isinstance(obj, (list, set, tuple)):
       t = type(obj)
       return t(specific_lower_and_trim(changable,parent,o) for o in obj)
    elif isinstance(obj, str):
       if parent in changable:
          obj = obj.lower().strip()
       return obj
    else:
       return obj

def reject_feature_in_array( item, data ):
    error = ''

    have_it = False

    if item in data.keys():
       for i in range( len( data[item] ) ):
           if 'enable' in data[item][i]:
              if is_yes_word( data[item][i]['enable'] ):
                 have_it = True

    if have_it:
       error = item + ' is not implemented, please un-enable'

    return error

def make_frame_extras( enable_tests, data ):
   # add extra information to the configuration
   # the configuration should already have been tested and passed
   # those validity tests

   data['sync']      = bytes( data['frame_header'], 'utf-8' )
   data['is_binary'] = data['frame_type'] == 'binary'

   frame_format  = ''
   length        = 0
   fields_length = 0

   n_fields = len( data['fields'] )

   if data['is_binary']:
      # a binary frame can be extracted via an unpack
      # so collect up the format items to use used in that unpack
      # for example, a storx is like this
      #format = ">10s 7H H H"

      data['term'] = ''

      length = len(data['sync'])

      # ignore the header
      # this unpack type will not return the item at all which is ok
      # because we don't need the header to be saved

      frame_format = '>' + str(length) + 'x'

      for i in range( n_fields ):
          field_len  = int( data['fields'][i]['length'] )
          data['fields'][i]['length']    = field_len
          data['fields'][i]['len_delim'] = 0
          field_type = data['fields'][i]['type']

          # add the length of the field to this point, useful for checksums
          data['fields'][i]['offset'] = fields_length

          fields_length += field_len
          numerals   = 'string'

          # https://docs.python.org/3/library/struct.html

          if field_type == 'bu':
             numerals = 'int'

             if   field_len == 1: field_format = '>B'
             elif field_len == 2: field_format = '>H'
             elif field_len == 4: field_format = '>L'
             elif field_len == 8: field_format = '>Q'

          elif field_type == 'bs':
             numerals = 'int'

             if   field_len == 1: field_format = '>b'
             elif field_len == 2: field_format = '>h'
             elif field_len == 4: field_format = '>l'
             elif field_len == 8: field_format = '>q'

          elif field_type == 'bf':
             numerals = 'float'
             field_format = '>f'

          elif field_type == 'bd':
             numerals = 'float'
             field_format = '>d'

          elif field_type == 'bb':
             numerals = 'skip'
             field_format = str( field_len ) + 's'

          elif field_type == 'bsle':
             numerals = 'int'
             if   field_len == 1: field_format = '<b'
             elif field_len == 2: field_format = '<h'
             elif field_len == 4: field_format = '<l'
             elif field_len == 8: field_format = '<q'

          elif field_type == 'bule':
             numerals = 'int'
             if   field_len == 1: field_format = '<b'
             elif field_len == 2: field_format = '<h'
             elif field_len == 4: field_format = '<l'
             elif field_len == 8: field_format = '<q'

          data['fields'][i]['numerals'] = numerals
          data['fields'][i]['format']   = field_format

          frame_format += field_format

   else:
      data['term'] = bytes( data['frame_terminator'], 'utf-8' )
      # and another conversion for faster processing later
      item = 'fields'
      for i in range( n_fields ):
          data[item][i]['delim'] = bytes( data[item][i]['delimiter'], 'utf-8' )
          data['fields'][i]['len_delim'] = len( data[item][i]['delim'] )
          field_type = data[item][i]['type']

          # this offset has no meaning in an ascii frame
          data['fields'][i]['offset'] = 0

          numerals = 'string'
          if   field_type in ['ai','au']: numerals = 'int'
          elif field_type in ['af','ad']: numerals = 'float'
          elif field_type == 'ax':        numerals = 'skip'

          data[item][i]['numerals'] = numerals

   # don't collect a format for the whole frame
   # when they get long, the unpack fails, so do one field at a time
   #data['format']       = frame_format

   data['frame_length'] = length + fields_length
   data['data_length']  = fields_length
   data['sync_len']     = len( data['sync'] )
   data['term_len']     = len( data['term'] )

   # begin by turning off all the boolean options
   # these will be used for easy checking by the calling programs

   data['n_fields']   = n_fields
   data['has_fields'] = ( n_fields > 0 )
   data['n_constants']= 0
   data['n_checksum'] = 0
   data['n_frame_validity'] = 0
   data['n_duplicates'] = 0

   field_names = dict()

   item = 'fields'
   for i in range( n_fields ):
       # there may be some redundancy in all these settings
       data[item][i]['is_reportable']    = False
       data[item][i]['has_fit']          = False
       data[item][i]['enabled_fit']      = False
       data[item][i]['n_validity']       = 0
       data[item][i]['enabled_validity'] = False
       data[item][i]['enabled_transform']= False
       data[item][i]['duplicates']       = []
       if 'name' in data[item][i]:
          field_names[data[item][i]['name']] = i

   item = 'constants'
   n_constants = 0
   if item in data.keys():
      n_constants = len( data[item] )
      data['n_constants'] = n_constants
      for i in range( n_constants ):
          data[item][i]['is_reportable']    = False
          data[item][i]['has_fit']          = False
          data[item][i]['enabled_fit']      = False
          data[item][i]['n_validity']       = 0
          data[item][i]['enabled_validity'] = False
          data[item][i]['numerals']         = 'float'

   item = 'duplicates'
   n_duplicates = 0
   if item in data.keys():
      n_duplicates = len( data[item] )
      data['n_duplicates'] = n_duplicates
      for i in range( n_duplicates ):
          # there may be some redundancy in all these settings
          data[item][i]['is_reportable']    = False
          data[item][i]['has_fit']          = False
          data[item][i]['enabled_fit']      = False
          data[item][i]['n_validity']       = 0
          data[item][i]['enabled_validity'] = False
          data[item][i]['enabled_transform']= False
          data[item][i]['numerals']         = 'float'
          data[item][i]['dup_of']           = -1

   # add duplicates to the fields and vise versa
   if n_duplicates > 0:
      item = 'duplicates'
      for i in range( n_duplicates ):
          if 'of' in data[item][i]:
             dup_of = data[item][i]['of']
             if dup_of in field_names:
                f = field_names[dup_of]
                data['fields'][f]['duplicates'].append( i )
                data[item][i]['dup_of'] = f

   # next, compute flags and counters

   # find which fields can be output and set a boolean for easy checking
   item = 'fields'
   for i in range( n_fields ):
       if 'report' in data[item][i]:
           data[item][i]['is_reportable'] = is_yes_word( data[item][i]['report'] )

   # never report 'skip fields' of 'bb' and 'ax'
   item = 'fields'
   for i in range( n_fields ):
       if data[item][i]['numerals'] == 'skip':
          data[item][i]['is_reportable'] = False

   # the reportability count
   item     = 'fields'
   n        = 0
   n_string = 0
   for i in range( n_fields ):
       if data[item][i]['numerals'] == 'string':
          n_string += 1
       if data[item][i]['is_reportable']:
          n += 1
   data['has_reportable_fields'] = ( n > 0 )
   data['has_string_fields']     = ( n_string > 0 )

   item = 'constants'
   n    = 0
   if n_constants > 0:
      for i in range( n_constants ):
          if 'report' in data[item][i]:
             data[item][i]['is_reportable'] = is_yes_word( data[item][i]['report'] )
          if data[item][i]['is_reportable']:
             n += 1
   data['has_reportable_constants'] = ( n > 0 )

   item = 'duplicates'
   n    = 0
   if n_duplicates > 0:
      for i in range( n_duplicates ):
          if 'report' in data[item][i]:
             data[item][i]['is_reportable'] = is_yes_word( data[item][i]['report'] )
          if data[item][i]['is_reportable']:
             # but only reportable if the source is too
             f = data[item][i]['dup_of']
             if data['fields'][f]['is_reportable']:
                n += 1
             else:
                data[item][i]['is_reportable'] = False
   data['has_reportable_duplicates'] = ( n > 0 )

   item = 'frame_validity'
   n    = 0
   if item in data.keys():
      data['n_frame_validity'] = len( data[item] )
      for i in range( data['n_frame_validity'] ):
          data[item][i]['is_enabled'] = False
          if enable_tests and ('enable' in data[item][i]):
             data[item][i]['is_enabled'] = is_yes_word( data[item][i]['enable'] )
          if data[item][i]['is_enabled']:
             n += 1
          # frame validity can be tested against a number or string value
          if is_number( data[item][i]['value'] ):
             # don't differentiate between float and int
             data[item][i]['numerals'] = 'float'
          else:
             data[item][i]['numerals'] = 'string'
   data['enabled_frame_validity'] = ( n > 0 )

   # fitting
   item    = 'fields'
   subitem = 'fit'
   n       = 0
   for i in range( n_fields ):
       if 'fit' in data[item][i]:
          # see how having, is different from being enabled
          data[item][i]['has_fit'] = True
          data[item][i][subitem]['is_enabled'] = False
          if 'enable' in data[item][i][subitem]:
             data[item][i][subitem]['is_enabled'] = is_yes_word( data[item][i][subitem]['enable'] )
          if data[item][i][subitem]['is_enabled']:
             data[item][i]['enabled_fit'] = True
             n += 1
   data['enabled_fit'] = ( n > 0 )

   item    = 'duplicates'
   subitem = 'fit'
   n       = 0
   for i in range( n_duplicates ):
       if 'fit' in data[item][i]:
          # see how having, is different from being enabled
          data[item][i]['has_fit'] = True
          data[item][i][subitem]['is_enabled'] = False
          if 'enable' in data[item][i][subitem]:
             data[item][i][subitem]['is_enabled'] = is_yes_word( data[item][i][subitem]['enable'] )
          if data[item][i][subitem]['is_enabled']:
             data[item][i]['enabled_fit'] = True
             n += 1
   data['enabled_duplicates_fit'] = ( n > 0 )

   item = 'checksum'
   n    = 0
   if item in data:
      data['n_checksum'] = len( data[item] )
      for i in range( data['n_checksum'] ):
          data[item][i]['is_enabled'] = False
          data[item][i]['len_skip'] = 0
          if 'skip' in data[item][i]:
             data[item][i]['len_skip'] = int( data[item][i]['skip'] )

          if enable_tests and ('enable' in data[item][i]):
             data[item][i]['is_enabled'] = is_yes_word( data[item][i]['enable'] )
          if data[item][i]['is_enabled']:
             n += 1
   data['enabled_checksum'] = ( n > 0 )

   # field validity
   # each field can have multiple validity checks
   item    = 'fields'
   subitem = 'validity'
   n       = 0
   for i in range( n_fields ):
       n_each = 0
       if subitem in data[item][i]:
          for v in range( len( data[item][i][subitem] ) ):
              data[item][i][subitem][v]['is_enabled'] = False
              if enable_tests and ('enable' in data[item][i][subitem][v]):
                 data[item][i][subitem][v]['is_enabled'] = is_yes_word( data[item][i][subitem][v]['enable'] )
              if data[item][i][subitem][v]['is_enabled']:
                 n += 1
                 n_each += 1
       data[item][i]['n_validity']       = n_each
       data[item][i]['enabled_validity'] = ( n_each > 0 )
   data['enabled_field_validity'] = ( n > 0 )

   item    = 'duplicates'
   subitem = 'validity'
   n       = 0
   for i in range( n_duplicates ):
       n_each = 0
       if subitem in data[item][i]:
          for v in range( len( data[item][i][subitem] ) ):
              data[item][i][subitem][v]['is_enabled'] = False
              if enable_tests and ('enable' in data[item][i][subitem][v]):
                 data[item][i][subitem][v]['is_enabled'] = is_yes_word( data[item][i][subitem][v]['enable'] )
              if data[item][i][subitem][v]['is_enabled']:
                 n += 1
                 n_each += 1
       data[item][i]['n_validity']       = n_each
       data[item][i]['enabled_validity'] = ( n_each > 0 )
   data['enabled_duplicates_field_validity'] = ( n > 0 )

   # field transforms
   # each field can have multiple validity checks
   item    = 'fields'
   subitem = 'transform'
   n       = 0
   for i in range( n_fields ):
       n_each = 0
       if subitem in data[item][i]:
          for v in range( len( data[item][i][subitem] ) ):
              data[item][i][subitem][v]['is_enabled'] = False
              if enable_tests and ('enable' in data[item][i][subitem][v]):
                 data[item][i][subitem][v]['is_enabled'] = is_yes_word( data[item][i][subitem][v]['enable'] )
              if data[item][i][subitem][v]['is_enabled']:
                 n += 1
                 n_each += 1
       data[item][i]['n_transform']       = n_each
       data[item][i]['enabled_transform'] = ( n_each > 0 )
   data['enabled_field_transform'] = ( n > 0 )

   item    = 'duplicates'
   subitem = 'transform'
   n       = 0
   for i in range( n_duplicates ):
       n_each = 0
       if subitem in data[item][i]:
          for v in range( len( data[item][i][subitem] ) ):
              data[item][i][subitem][v]['is_enabled'] = False
              if enable_tests and ('enable' in data[item][i][subitem][v]):
                 data[item][i][subitem][v]['is_enabled'] = is_yes_word( data[item][i][subitem][v]['enable'] )
              if data[item][i][subitem][v]['is_enabled']:
                 n += 1
                 n_each += 1
       data[item][i]['n_transform']       = n_each
       data[item][i]['enabled_transform'] = ( n_each > 0 )
   data['enabled_duplicates_field_transform'] = ( n > 0 )

   return data

def get_config_filenames( packagefile, configpath ):
    error = ''
    files = []

    if os.path.isfile( packagefile ):
       if os.path.isdir( configpath ):

          have_files = False

          with open( packagefile, "r" ) as p:
               for line in p:
                   line = re.sub( r'\s\s+', ' ', line ).lower().strip()
                   if line:
                      filename = configpath + os.sep + line.replace(' ','.') + '.conf'
                      # skip duplicates
                      if not filename in files:
                         if os.path.isfile( filename ):
                            have_files = True
                            files.append( filename )
                         else:
                            error += 'Config file does not exist: ' + filename + '\n'

          if not have_files:
             error += 'No config files found\n'
       else:
          error += 'config path does not exist\n'
    else:
       error += 'package file does not exist\n'

    return error, files

def get_configurations( enable_tests, packagefile, configpath ):
    error = ''

    configs = dict()

    error, config_files = get_config_filenames( packagefile, configpath )

    if error:
       return error, configs

    # handle each config file

    frame_names = dict()

    for file in config_files:

        json_contents = None
        # don't complain twice
        complained_about_json = False

        try:
           with open( file ) as f:
                json_contents = json.load( f )
        except:
           complained_about_json = True
           error += 'Cannot parse json file:' + file + '\n'

        if json_contents and (not error):
           config = specific_lower_and_trim( get_changable_config_keys(), '',
                                             json_contents )

           config_error = config_file_verify( config )

           if not config_error:
              # remove leading zeros from the serial number
              sn = re.sub( '^0*', '', config['serial'] ).lower().strip()
              if sn == '': sn = '0'

              frame_id = config['instrument'].lower().strip() + '/' + sn

              # not necessary, unless the definition of the frame id is changed
              lower_id = frame_id.lower().strip()

              if lower_id in frame_names:
                 error += 'Duplicate frame header in file ' + file
                 error += ' and ' + frame_names[lower_id] + '\n'
              else:
                 frame_names[lower_id] = file
                 configs[frame_id]     = make_frame_extras( enable_tests, config )

           else:
              error += 'Config file errors: ' + file + '\n' + config_error
        else:
           if not complained_about_json:
              error += 'Error parsing config file: ' + file + '\n'

        # don't exit on error yet, try to show as many errors as possible
        # ensure the headers don't collide
        # this test is made on the lowercase versions

        for frame_id in frame_names:
            for other_id in frame_names:
                # already checked for equal
                if frame_id != other_id:
                   if frame_id.startswith( other_id ):
                      error += 'One frame header is a subset of another:'
                      error += quote(frame_id) + 'and' + quote(other_id) + '\n'

    return error, configs

def check_found_tags( prefix, suffix, expected, required, found ):
    error = ''

    for item in found:
        if item not in expected:
           error += prefix + ' Unexpected item' + quote(item) + suffix
    for item in required:
        if item not in found:
           error += prefix + ' Missing' + quote(item) + suffix

    return error

def check_duplicates_are_numeric( data, numeric_fields ):
    error = ''
    already_checked = []
    for section in data:
        if 'of' in section:
           name = section['of']
           if name not in numeric_fields:
              if name not in already_checked:
                 already_checked.append( name )
                 error += 'Field: ' + name + ' cannot be duplicated because it it not numeric'
    return error

def check_for_terminator_conflict( data ):
    # note that all data has been passed in
    error = ''

    # if ascii, terminatior can't be a delimiter
    if data['frame_type'] == 'ascii':
       if 'frame_terminator' in data:
           for i, section in enumerate( data['fields'] ):
               if 'delimiter' in section:
                  if data['frame_terminator'] == section['delimiter']:
                     error += 'Frame terminator should not equal delimiter in field #' + str(i+1) + '\n'
    return error

def check_for_field_conflict( item, desc, data, field_names ):
    # note that all data has been passed in
    error = ''

    # note that this check is done even if the item is disabled

    if item in data:
       for i, section in enumerate( data[item] ):
           if 'name' in section:
              name = section['name']
              if name in field_names:
                 error += desc + ' conflicts with matching field'
                 error += ' "' + name + '" in #' + str(i+1) + '\n'
    return error

def check_for_matching_field_exists( item, tag, desc, data, field_names ):
    # note that all data has been passed in
    error = ''

    # these checks are expected to be done on list types
    # is not, that error will be reported elsewhere

    if item in data:
       if isinstance( data[item], list ):
          # note that this check is done even if the item is disabled

          if item in data:
             for i, section in enumerate( data[item] ):
                 if tag in section:
                    name = section[tag]
                    if name not in field_names:
                       error += desc + ' doesn\'t have a matching field'
                       error += ' "' + name + '" in #' + str(i+1) + '\n'
    return error

def check_config_frame_terminator( name, data ):
   error = ''

   # do not strip this item because the CR and LF must remain

   n = len( data )
   if n < 1:
      error += name + ' must not be empty\n'
   elif n > get_max_frame_terminator():
      error += name + ' is unreasonably large\n'

   return error

def check_config_frame_header( name, data ):
    error = is_nonempty_string( name, data, '\n' )

    if not error:
       n = len( data )
       if n < get_min_sync_size():
          error += name + ' is too short\n'
       elif n > get_max_sync_size():
          error += name + ' is unreasonably large\n'

    return error

def check_config_frame_validity( prefix, data ):
    error = ''

    if not isinstance( data, list ):
       return prefix + ' is not an array\n'

    required_tags = [ 'name', 'op', 'value' ]
    expected_tags = [ 'comment', 'enable' ]
    expected_tags.extend( required_tags )

    names = dict()

    for i, section in enumerate( data ):

        if not isinstance( section, dict ):
           error += prefix + ' #' + str(i+1) + ' is not a set\n'
           continue

        suffix = ' in ' + prefix + ' #' + str(i+1) + '\n'

        found_tags = []

        for item in section:
            if item in found_tags:
               error += 'Duplicate item ' + quote(item) + suffix
            else:
               found_tags.append( item )

            if item == 'enable':
               error += is_atomic_type( item, section[item], '', suffix )

            if item == 'name':
               this_error = is_nonempty_string( item, section[item], suffix )
               if this_error:
                  error += this_error
               else:
                  name = section[item]
                  if name in names:
                     error += 'Duplicate name tag' + suffix
                  else:
                     names[name] = i

            if item == 'op':
               this_error = is_nonempty_string( item, section[item], suffix )
               if this_error:
                  error += this_error
               else:
                  op = section[item]
                  if not is_valid_operator( op ):
                     error += 'Invalid op key' + quote(op) + suffix

            if item == 'value':
               error += is_nonempty_string( item, section[item], suffix )

        error += check_found_tags( prefix, suffix, expected_tags, required_tags, found_tags )

    return error

def check_config_constants( prefix, data ):
    error = ''

    required_tags = [ 'name', 'value' ]
    expected_tags = [ 'comment', 'report' ]
    expected_tags.extend( required_tags )

    names = dict()

    for i,section in enumerate( data ):

        if not isinstance( section, dict ):
           error += prefix + ' #' + str(i+1) + ' is not a set\n'
           continue

        suffix = ' in ' + prefix + ' #' + str(i+1) + '\n'

        found_tags = []

        for item in section:
            if item in found_tags:
               error += 'Duplicate item ' + quote(item) + suffix
            else:
               found_tags.append( item )

            if item == 'name':
               this_error = is_nonempty_string( item, section[item], suffix )
               if this_error:
                  error += this_error
               else:
                  name = section[item]
                  if name in names:
                     error += 'Duplicate name tag' + suffix
                  else:
                     names[name] = i

            if item == 'report':
               error += is_atomic_type( item, section[item], '', suffix )

            if item == 'value':
               error += is_nonempty_number( item, section[item], suffix )

        error += check_found_tags( prefix, suffix, expected_tags, required_tags, found_tags )

    return error

def check_config_fields_length( field_type, prefix, data, suffix ):

    error = is_nonempty_int( prefix, data, suffix )

    if not error:
       length = int( data )

       if length < 1:
          error += prefix + ' can\'t be less than 1' + suffix
       elif length > get_max_field_length():
          error += prefix + ' unreasonably large' + suffix
       else:

          this_error = ''

          if field_type in ['bu', 'bs', 'bule', 'bsle']:
             if (length > 4) or (length == 3):
                this_error = '1, 2, or 4'

          elif field_type == 'bf':
             if length != 4:
                this_error = '4'

          elif field_type == 'bd':
             if length != 8:
                this_error = '8'

          if this_error:
             error += prefix +' must be ' + this_error
             error += ' for type' + quote(field_type) + suffix

    return error

def check_config_fields_delimiter( prefix, data, suffix ):
    error = ''

    # another thing which can't be stripped: delimiters
    error += is_nonempty_string( prefix, data, suffix )

    if not error:
       if len( data ) > get_max_delimiter():
          # something this big can't be right
          error += 'Delimiter unreasonably large' + suffix

    return error

def check_config_fields_validity( prefix, data, suffix ):
    error = ''

    required_tags = ['op','value']
    expected_tags = ['comment','enable']
    expected_tags.extend( required_tags )

    for i, section in enumerate( data ):
        prefix = 'validity #' + str(i+1) + ' '

        if not isinstance( section, dict ):
           error += prefix + 'validity is not a set' + suffix
           continue

        found_tags = []

        for item in section:
            if item in found_tags:
               error += 'Duplicate item ' + quote(item) + suffix
            else:
               found_tags.append( item )

            if item == 'op':
               this_error = is_nonempty_string( '', section[item], suffix )
               if this_error:
                  error += prefix + this_error
               else:
                  op = section[item]
                  if not is_valid_operator( op ):
                     error += prefix + 'invalid op' + quote(op) + suffix

            if item == 'value':
               # note that field validity is not allowed for strings
               error += is_nonempty_number( prefix, section[item], suffix )

        error += check_found_tags( prefix, suffix, expected_tags, required_tags, found_tags )

    return error

def check_config_fields_fit_coeffs( prefix, data, suffix ):
    error = ''

    required_tags = [ 'name', 'value' ]
    expected_tags = [ 'comment' ]
    expected_tags.extend( required_tags )

    n = len( data )
    if n < 1:
       error += prefix + ' coeffs has no values' + suffix
    if n > 8:
       error += prefix + ' coeffs has an unreasonable large set' + suffix
    else:

       names = dict()

       for i,section in enumerate( data ):
           this_prefix = 'Coeff #' + str(i+1) + ' '
           if not isinstance( section, dict ):
              error += this_prefix + 'is not a set' + suffix
              continue

           found_tags = []

           for item in section:
               if item in found_tags:
                  error += 'Duplicate item ' + quote(item) + suffix
               else:
                  found_tags.append( item )

               if item == 'name':
                  this_error = is_nonempty_string( '', section[item], suffix )
                  if this_error:
                     error += this_prefix + this_error
                  else:
                     name = section[item]
                     if name in names:
                        error += this_prefix + 'duplicate name' + suffix
                     else:
                        names[name] = i
                        if (name in ['im','cint','aint']) or re.match( r'^a\d$', name ):
                           pass
                        else:
                           error += this_prefix + 'unexpected style of name'
                           error += quote(name) + suffix

               if item == 'value':
                  this_error = is_nonempty_number( '', section[item], suffix )
                  if this_error:
                     error += this_prefix + this_error

           error += check_found_tags( this_prefix, suffix, expected_tags, required_tags, found_tags )

    return error

def check_config_fields_fit( prefix, data, suffix ):
    error = ''

    required_tags = ['type','coeffs']
    expected_tags = ['comment','enable']
    expected_tags.extend( required_tags )

    found_tags = []

    for item in data:
        if item in found_tags:
           error += 'Duplicate item ' + quote(item) + suffix
        else:
           found_tags.append( item )

        if item == 'enable':
           error += is_atomic_type( item, data[item], '', suffix )

        if item == 'type':
           this_error = is_nonempty_string( item, data[item], suffix )
           if this_error:
              error += this_error
           else:
              fit_type = data[item]
              if not is_valid_fit( fit_type ):
                 error += 'Fit type invalid' + quote(fit_type) + suffix

        if item == 'coeffs':
           if isinstance( data[item], list ):
              error += check_config_fields_fit_coeffs( prefix, data[item], suffix )
           else:
              error += prefix + ' coeffs is not a list' + suffix

    error += check_found_tags( prefix, suffix, expected_tags, required_tags, found_tags )

    return error

def check_config_fields_transform( prefix, data, suffix ):
    error = ''

    required_tags = [ 'name', 'type' ]
    expected_tags = [ 'enable', 'comment' ]
    expected_tags.extend( required_tags )

    for section in data:
        if not isinstance( section, dict ):
           error += prefix + 'transform is not a set type' + suffix
           continue

        found_tags = []

        for item in section:
            if item in found_tags:
               error += 'Duplicate item ' + quote(item) + suffix
            else:
               found_tags.append( item )

            if item == 'name':
               # names can be duplicated
               this_error = is_nonempty_string( item, section[item], suffix )
               if this_error:
                  error += prefix + this_error

            if item == 'enable':
               error += is_atomic_type( item, section[item], '', suffix )

            elif item == 'type':
               this_error = is_nonempty_string( item, section[item], suffix )
               if this_error:
                  error += prefix + this_error
               else:
                  if section[item] not in ['north-south', 'east-west']:
                     error += prefix + ' invalid type' + quote(section[item]) + suffix

        error += check_found_tags( prefix, suffix, expected_tags, required_tags, found_tags )

    return error

def check_fields_transform_reference( fields_with_transform, field_names, data ):
    error = ''

    for i in fields_with_transform:
        # this field can have multiple transforms
        if isinstance( data[i]['transform'], list ):
           for t,transform in enumerate( data[i]['transform'] ):
               if 'name' in transform:
                  prefix = 'field transform #' + str(t+1) + ' in field #' + str(i+1) + ' '
                  name = transform['name']
                  if name in field_names:
                     # ensure not a self reference
                     if 'name' in data[i]:
                        if name == data[i]['name']:
                           error += prefix + 'references itself\n'
                  else:
                     error += prefix + 'has no matching field' + quote(name) + '\n'

    return error

def check_config_fields( prefix, data, field_types, frame_type ):
    error = ''

    required_tags = [ 'name', 'type' ]
    expected_tags = ['report','comment','length','fit','delimiter','validity','transform']
    expected_tags.extend( required_tags )

    n_fields = 0

    names = dict()

    has_transform = []

    for i,section in enumerate( data ):

        if not isinstance( section, dict ):
           error += prefix + ' #' + str(i+1) + ' is not a set\n'
           continue

        n_fields += 1

        suffix = ' in ' + prefix + ' #' + str(i+1) + '\n'

        # check the type right away, because other items depend upon it
        field_type    = None
        numeric_field = False

        item = 'type'
        if item in section:
           this_error = is_nonempty_string( item, section[item], suffix )
           if this_error:
              error += this_error
           else:
              field_type = section[item]
              if frame_type in field_types:
                 if field_type in field_types[frame_type]:
                    numeric_field = field_type_is_numeric( field_type )
                 else:
                    error += 'Invalid field type' + quote(field_type) + suffix

        found_tags   = []

        found_delim  = None
        found_length = None

        for item in section:
            if item in found_tags:
               error += 'Duplicate item ' + quote(item) + suffix
            else:
               found_tags.append( item )

            if item == 'report':
               error += is_atomic_type( item, section[item], '', suffix )

            if item == 'name':
               this_error = is_nonempty_string( prefix, section[item], suffix )
               if this_error:
                  error += this_error
               else:
                  name = section[item]
                  if name in names:
                     error += 'Duplicate name' + quote(name) + suffix
                  else:
                     names[name] = i

            if item == 'fit':
               if isinstance( section[item], dict ):
                  if numeric_field:
                     error += check_config_fields_fit( item, section[item], suffix )
                  else:
                     error += item + ' can only be applied to a numeric field' + suffix
               else:
                  error += item + ' is not a set' + suffix

            if item == 'validity':
               if isinstance( section[item], list ):
                  if numeric_field:
                     error += check_config_fields_validity( item, section[item], suffix )
                  else:
                     error += item + ' can only be applied to a numeric field' + suffix
               else:
                  error += item + ' is not a list' + suffix

            if item == 'transform':
               if isinstance( section[item], list ):
                  has_transform.append( i )
                  if numeric_field:
                     error += check_config_fields_transform( item, section[item], suffix )
                  else:
                     error += item + ' can only be applied to a numeric field' + suffix
               else:
                  error += item + ' is not a list' + suffix

            if item == 'length':
               found_length = section[item]

            if item == 'delimiter':
               found_delim = section[item]

        if frame_type == 'ascii':
           if found_delim:
               error += check_config_fields_delimiter( item, found_delim, suffix )
           else:
              error += 'Missing delimiter' + suffix
        elif frame_type == 'binary':
           if found_length:
              error += check_config_fields_length( field_type, 'length', found_length, suffix )
           else:
              error += 'Missing length' + suffix

        error += check_found_tags( '', suffix, expected_tags, required_tags, found_tags )

    if n_fields > 0:
       error += check_fields_transform_reference( has_transform, names, data )
    else:
       error += 'No fields defined\n'

    return error

def check_config_duplicates( prefix, data ):
    error = ''

    # duplicates don't need type, length, or delimiters
    #
    # the checks will be made later for 'of' pointing to numeric fields
    # because the duplicates can be defined before the true fields

    required_tags = [ 'name', 'of' ]
    expected_tags = ['report','comment','fit','validity','transform']
    expected_tags.extend( required_tags )

    names = dict()

    has_transform = []

    for i,section in enumerate( data ):

        if not isinstance( section, dict ):
           error += prefix + ' #' + str(i+1) + ' is not a set\n'
           continue

        suffix = ' in ' + prefix + ' #' + str(i+1) + '\n'

        found_tags   = []

        for item in section:
            if item in found_tags:
               error += 'Duplicate item ' + quote(item) + suffix
            else:
               found_tags.append( item )

            if item == 'report':
               error += is_atomic_type( item, section[item], '', suffix )

            if item == 'of':
               error += is_nonempty_string( prefix, section[item], suffix )

            if item == 'name':
               this_error = is_nonempty_string( prefix, section[item], suffix )
               if this_error:
                  error += this_error
               else:
                  name = section[item]
                  if name in names:
                     error += 'Duplicate name' + quote(name) + suffix
                  else:
                     names[name] = i

            if item == 'fit':
               if isinstance( section[item], dict ):
                  error += check_config_fields_fit( item, section[item], suffix )
               else:
                  error += item + ' is not a set' + suffix

            if item == 'validity':
               if isinstance( section[item], list ):
                  error += check_config_fields_validity( item, section[item], suffix )
               else:
                  error += item + ' is not a list' + suffix

            if item == 'transform':
               if isinstance( section[item], list ):
                  has_transform.append( i )
                  error += check_config_fields_transform( item, section[item], suffix )
               else:
                  error += item + ' is not a list' + suffix

        error += check_found_tags( '', suffix, expected_tags, required_tags, found_tags )

    return error

def check_config_checksum( prefix, data ):
    error = ''

    required_tags = [ 'name', 'type' ]
    expected_tags = [ 'comment', 'enable', 'skip' ]
    expected_tags.extend( required_tags )

    names = dict()

    for i, section in enumerate( data ):

        if not isinstance( section, dict ):
           error += prefix + ' #' + str(i+1) + ' is not a set\n'
           continue

        suffix = ' in ' + prefix + ' #' + str(i+1) + '\n'

        found_tags = []

        for item in section:
            if item in found_tags:
               error += 'Duplicate item ' + quote(item) + suffix
            else:
               found_tags.append( item )

            if item == 'name':
               this_error = is_nonempty_string( item, section[item], suffix )
               if this_error:
                  error += this_error
               else:
                  name = section[item]
                  if name in names.keys():
                     error += 'Duplicate name value' + suffix
                  else:
                     names[name] = i

            elif item == 'type':
               this_error = is_nonempty_string( item, section[item], suffix )
               if this_error:
                  error += this_error
               else:
                  check_type = section[item]
                  #if check_type not in ['nmea', 'aquadopp']:
                  if check_type not in ['nmea']:
                     error += 'Invalid type' + quote(check_type) + suffix

            elif item == 'skip':
               error += is_nonempty_number( item, section[item], suffix )

            else:
               # check any other keys
               if item not in expected_tags:
                  error += 'Invalid key' + quote(item) + suffix

        error += check_found_tags( '', suffix, expected_tags, required_tags, found_tags )

    return error

def config_file_verify( data ):
    error = ''

    # the passed in data should be a dict containing
    # the configuration for a single instrument

    if not isinstance( data, dict ):
       return 'Configuration is not a list\n'

    field_types = get_field_types()

    # track all the keys which are expected to exist
    # so that any unexpected ones can be detected at the end

    required_tags = ['instrument','serial','frame_header','frame_type','fields']
    expected_tags = [ 'comment','constants','checksum','frame_validity','frame_terminator','duplicates' ]
    expected_tags.extend( required_tags )

    # verify basic items right away because some other fields depend on these

    for item in required_tags:
        if item  not in data:
           error += 'Top level missing' + quote(item) + '\n'

    # exit right away if one of those are missing
    if error:
       return error

    # another special check right away, these must be strings
    for item in ['frame_type']:
        error += is_nonempty_string( item, data[item] )

    if error:
       return error

    found_tags = []

    for item in data:
        if item in found_tags:
           error += 'Duplicate item ' + quote(item) + '\n'
        else:
           found_tags.append( item )

        if item == 'frame_type':
            error += has_string_values( item, ['ascii','binary'], data[item], '\n' )

        if item == 'constants':
           if isinstance( data[item], list ):
              error += check_config_constants( item, data[item] )
           else:
              error += quote(item) + 'is not a list\n'

        if item == 'frame_validity':
           if isinstance( data[item], list ):
              error += check_config_frame_validity( item, data[item] )
           else:
              error += quote(item) + 'is not a list\n'

        if item == 'fields':
           if isinstance( data[item], list ):
              error += check_config_fields( item, data[item], field_types, data['frame_type'] )
           else:
              error += 'Fields is not a list\n'

        if item == 'duplicates':
           if isinstance( data[item], list ):
              error += check_config_duplicates( item, data[item] )
           else:
              error += 'Duplicates is not a list\n'

        if item == 'instrument':
            error += is_nonempty_string( item, data[item] )

        if item == 'serial':
           error += is_nonempty_string( item, data[item] )

        if item == 'frame_header':
           error += check_config_frame_header( item, data[item] )

        if item == 'frame_terminator':
           # don't use regular non-empty test, because this can't be stripped
           if isinstance( data[item], str ):
              if data['frame_type'] == 'ascii':
                 error += check_config_frame_terminator( item, data[item] )
           else:
              error += 'Frame terminator is not a simple string\n'

        if item == 'checksum':
           if isinstance( data[item], list ):
              error += check_config_checksum( item, data[item] )
           else:
              error += 'Checksum is not a list\n'

    error += check_found_tags( '', '\n', expected_tags, required_tags, found_tags )

    if data['frame_type'] == 'ascii':
       if 'frame_terminator' not in found_tags:
          error += 'Missing frame terminator\n'

    # double check

    # grab all field_names for further checks
    item = 'fields'
    field_names = []
    field_numeric = []
    if item in data:
       for section in data[item]:
           if 'name' in section:
              field_names.append( section['name'] )
              if 'type' in section:
                 if field_type_is_numeric( section['type'] ):
                    field_numeric.append( section['name'] )

    # for these items, the field they reference must exist

    error += check_for_matching_field_exists( 'frame_validity', 'name',
                                              'Frame validity',
                                              data, field_names )
    error += check_for_matching_field_exists( 'checksum', 'name',
                                              'Checksum',
                                              data, field_names )
    error += check_for_matching_field_exists( 'duplicates', 'of',
                                              'Duplicates',
                                              data, field_names )

    # for these there can't be a name conflict
    error += check_for_field_conflict( 'constants', 'Constants',
                                       data, field_names )
    error += check_for_field_conflict( 'duplicates', 'Duplicates',
                                       data, field_names )

    item = 'duplicates'
    if item in data:
       error += check_duplicates_are_numeric( data[item], field_numeric )

       # and there can't be any conflicts between constants and duplicates
       duplicate_names = []
       for section in data[item]:
           if 'name' in section:
              duplicate_names.append( section['name'] )
       error += check_for_field_conflict( 'constants', 'Constants', data, duplicate_names )

    error += check_for_terminator_conflict( data )

    return re.sub( r'^ ', '', re.sub( r' +', ' ', error ) )
