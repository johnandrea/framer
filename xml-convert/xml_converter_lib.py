import re
import json

def is_number(s):
    try:
      float(s)
    except ValueError:
      return False

    return True

def delete_fit( field_data ):
    result = False

    if 'fit' in field_data:
       if field_data['fit']['type'] == 'veritybyte':
          result = True

    return result

def fixup_instrument_and_serial( data ):
    instrument = data['instrument'].strip()

    if 'serial' in data:
       serial = data['serial'].strip()
    else:
       serial = ''

    # sometimes the serial isn't given
    # sometimes the instrument has the serial number attached

    if serial == '':

       # try to get it from the instrument
       if re.search( r'\d$', instrument ):

          # remove digits at end
          # why can't i solve this with python regex
          new = re.sub( r'\d*\d$', '', instrument )
          serial     = instrument[len(new):]
          instrument = instrument[0:len(new)]

    else:

       # try to remove it from the instrument
       pos = data['instrument'].find( serial )
       if pos > 0:
          instrument = instrument[0:pos]

    # there might still be zeros in the name, get rid of it
    instrument = re.sub( r'0+', '', instrument )

    # the chance of empty is very low, just in case
    if instrument == '':
       instrument = 'unknown'

    return instrument, serial

def filechars( s ):
    name = ''

    s = re.sub( r'^00*', '', s.strip() )
    if s:
       for c in s.lower():
           if c in 'abcdefghijklmnopqrstuvwxyz0123456789-_':
              name += c
    else:
       name = '0'

    return name

def delim_untranslate( s ):
    if   s == '\\u0009':        s = 'x09'
    elif s == '\\u000d':        s = 'x0D'
    elif s == '\\u000a':        s = 'x0A'
    elif s == '\\u000d\\u000a': s = 'x0Dx0A'
    elif s == '\\u000a\\u000d': s = 'x0Ax0D'

    return s

def delim_translate( s ):
    if   s == '&#x09':        s = '\u0009'
    elif s == '&#x09;':       s = '\u0009'
    elif s == '\x09':         s = '\u0009'

    elif s == '&#x0d&#x0a':   s = '\u000d\u000a'
    elif s == '&#x0d;&#x0a;': s = '\u000d\u000a'
    elif s == '\x0d\x0a':     s = '\u000d\u000a'

    elif s == '&#x0a&#x0d':   s = '\u000a\u000d'
    elif s == '&#x0a;&#x0d;': s = '\u000a\u000d'
    elif s == '\x0a\x0d':     s = '\u000a\u000d'

    elif s == '&#x0d;':       s = '\u000d'
    elif s == '\x0d':         s = '\u000d'

    elif s == '&#x0a;':       s = '\u000a'
    elif s == '\x0a':         s = '\u000a'

    return s

def end_quotes( s ):
    # remove everything after quotes
    return re.sub( r'".*', '', re.sub( r"'.*", '', s )).strip()

def is_reportable_type( name ):
    name = name.lower().strip()
    result = True

    unwanted = [ 'cr', 'tab', 'pval', 'datafield', 'timefield', 'checksum' ]
    unwanted.extend( [ 'checksum', 'check_sum', 'csum', 'csumlsb', 'csummsb'] )
    unwanted.extend( [ 'id', 'check', 'crlf', 'comma', 'fill' ] )
    unwanted.extend( [ 'year', 'month', 'day', 'hour', 'minute', 'second' ] )

    if name in unwanted:
       return False

    others = [ 'comma', 'checksum', 'unused', 'uv', 'aux', 'terminator' ]
    for other in others:
        if name.startswith( other ):
           return False

    return result

def output_to_json( check_sensors, sensors_list, frame_name, data ):
    filename = filechars(data['instrument']) + '.' + filechars(data['serial']) + '.conf'

    print( filename )  #show the file being produced

    for i in range( len( data['fields'] ) ):
        name = data['fields'][i]['name']
        if is_reportable_type( name ):
           if data['fields'][i]['type'] != 'as':
              if check_sensors:
                 if (frame_name in sensors_list) and (name in sensors_list[frame_name]):
                    data['fields'][i]['report'] = 'yes'
              else:
                 data['fields'][i]['report'] = 'yes'

    with open( filename, 'w' ) as out:
         json.dump( data, out, indent=2 )

def output_to_tdf( check_sensors, sensors_list, frame_name, data ):
    filename = filechars(data['instrument']) + '.' + filechars(data['serial']) + '.tdf'

    print( filename )  #show the file being produced

    with open( filename, 'w' ) as f:
         print( '###############################################', file=f )
         print( '# Telemetry Definition File:', file=f )
         print( '# Produced programatically from xml', file=f )
         print( '# Instrument', data['instrument'], data['serial'], file=f )
         print( '###############################################', file=f )

         sync  = data['frame_header']
         nsync = len( sync )

         print( '', file=f )
         out = ''
         if data['frame_type'] == 'ascii':
            out = 'VLF_INSTRUMENT'
         else:
            out = 'INSTRUMENT'

         out += ' ' + sync + " '' " + str(nsync) + ' AS 0 NONE'
         print( out, file=f )

         # units are set to empty

         for i, section in enumerate( data['fields'] ):
             print( '', file=f )
             out = section['name'].upper()
             if data['frame_type'] == 'binary':
                out += ' NONE \'\' ' + section['length']
             else:
                 print( 'FIELD NONE', "'"+ delim_untranslate(section['delimiter'])+"'", '1 AS 0 DELIMITER', file=f )
                 out += ' NONE \'\' V'

             out += ' ' + section['type'].upper()

             if 'fit' in section:
                # only allowing one set of coeffs
                out += ' 1 ' + section['fit']['type'].upper() + '\n'
                # keep the values ordered by the expected name
                for c in range( len( section['fit']['coeffs'] ) ):
                    expect = 'a' + str(c)
                    if section['fit']['coeffs'][c]['name'].lower() == expect:
                       out += section['fit']['coeffs'][c]['value'] + ' '
                    for c in range( len( section['fit']['coeffs'] ) ):
                        if section['fit']['coeffs'][c]['name'].lower() == 'cint':
                           out += section['fit']['coeffs'][c]['value'] + ' '
                if  section['fit']['type'] == 'optic2':
                    # these other two in this order
                    for c in range( len( section['fit']['coeffs'] ) ):
                        if section['fit']['coeffs'][c]['name'].lower() == 'im':
                           out += section['fit']['coeffs'][c]['value'] + ' '
                if  section['fit']['type'] == 'optic3':
                    # these other two in this order
                    for c in range( len( section['fit']['coeffs'] ) ):
                        if section['fit']['coeffs'][c]['name'].lower() == 'im':
                           out += section['fit']['coeffs'][c]['value'] + ' '
                    for c in range( len( section['fit']['coeffs'] ) ):
                        if section['fit']['coeffs'][c]['name'].lower() == 'cint':
                           out += section['fit']['coeffs'][c]['value'] + ' '

             else:
                out += ' 0 COUNT'

             print( out, file=f )

         if data['frame_type'] == 'ascii':
            print( '', file=f )
            print( 'TERMINATOR NONE', "'"+ delim_untranslate(data['frame_terminator']) +"'", 'V AS 0 DELIMITER', file=f )


def convert_xml_format( out_function, filename, check_sensors, sensors_list ):
    data = dict()
    data['fields'] = []

    in_sensorfieldgroup = False
    in_sensorfield = False
    in_fit = False

    default_field_delim = ''
    base = ''
    base2 = ''
    data_field = ''
    frame_type = ''
    frame_name = ''

    n_field = -1
    n_coeff = -1

    with open( filename ) as f:
         for line in f:
             uncased = line
             line = line.lower()
             if line == '': continue

             if re.search( r'</instrument>', line ):

                data['instrument'],data['serial'] = fixup_instrument_and_serial( data )
                data['frame_header'] = base + base2

                for i in range( n_field +1 ):
                    if delete_fit( data['fields'][i] ):
                       del data['fields'][i]['fit']

                out_function( check_sensors, sensors_list, frame_name, data )

                data   = dict()
                data['fields'] = []

                in_sensorfieldgroup = False
                in_sensorfield = False
                in_fit = False

                default_field_delim = ''

                frame_type = ''
                frame_name = ''
                base = ''
                base2 = ''
                data_field = ''

                n_field = -1

             if re.search( r'<instrument', line ):
                data['instrument'] = end_quotes( re.sub( r'^.*identifier=.', '', line ) )

                # still in the instrument line
                if re.search( r'serialnumber=', line ):
                   data['serial'] = end_quotes( re.sub( r'^.*serialnumber=.', '', line ) )
                #if re.search( r'model=', line ):
                #   data['model'] = end_quotes( re.sub( r'^.*model=.', '', line ) )

             elif re.search( r'model=', line ):
                  #data['model'] = end_quotes( re.sub( r'^.*model=.', '', line ) )
                  # still on the model line
                  if re.search( r'serialnumber=', line ):
                     data['serial'] = end_quotes( re.sub( r'^.*serialnumber=.', '', line ) )

             elif re.search( r'serialnumber=', line ):
                  data['serial'] = end_quotes( re.sub( r'^.*serialnumber=', '', line ) )

             elif re.search( r'<fixedframe ', line ):
                  data['frame_type'] = 'binary'
                  frame_type         = 'binary'
                  frame_name  = end_quotes( re.sub( r'^.*identifier=.', '', line ) )

             elif re.search( r'<varasciiframe ', line ):
                  data['frame_type'] = 'ascii'
                  frame_type         = 'ascii'
                  frame_name  = end_quotes( re.sub( r'^.*identifier=.', '', line ) )

             elif re.search( r'<fit>', line ):
                  in_fit = True
                  data['fields'][n_field]['fit'] = dict()
                  data['fields'][n_field]['fit']['enable'] = 'yes'
                  data['fields'][n_field]['fit']['coeffs'] = []
                  n_coeff = -1

             elif re.search( r'</fit>', line ):
                  in_fit = False

             elif re.search( r'<base>', line ):
                  base = re.sub( r'^.*<Base>', '', re.sub( r'</.*', '', uncased ) ).strip()

             elif re.search( r'binaryfloatingpointdata', line ):
                  name = re.sub( r'^.*<binaryfloatingpointdata>', '', re.sub( r'</.*', '', line ) ).strip()
                  data['fields'][n_field]['type'] = name
                  if name == 'bf':
                     data['fields'][n_field]['length'] = 4
                  else:
                     data['fields'][n_field]['length'] = 8

             elif re.search( r'<sensorfieldgroup>', line ):
                  in_sensorfieldgroup = True
                  n_field += 1
                  data_field = ''
                  data['fields'].append( dict() )
                  if frame_type == 'ascii':
                     data['fields'][n_field]['delimiter'] = default_field_delim

             elif re.search( r'</sensorfieldfroup>', line ):
                  in_sensorfieldgroup = False

             elif re.search( r'<sensorfield>', line ):
                  in_sensorfield = True

             elif re.search( r'</sensorfield>', line ):
                  in_sensorfield = False

             elif re.search( r'<serialnumber>', line ):
                  base2 = re.sub( r'^.*<SerialNumber>', '', re.sub( r'</.*', '', uncased ) ).strip()

             elif re.search( r'<identifier', line ):
                  if in_sensorfield:
                     name = re.sub( r'^.*<identifier>', '', re.sub( r'</.*', '', line )).strip()
                     data['fields'][n_field]['name'] = name

             elif re.search( r'<data>', line ):
                  if in_sensorfieldgroup:
                     if not in_fit:
                        data_field = re.sub( r'^.*<data>', '', re.sub( r'</.*', '', line )).strip()

             elif re.search( r'<length>', line ):
                  if in_sensorfieldgroup:
                     length = re.sub( r'^.*<length>', '', re.sub( r'</.*', '', line )).strip()
                     data['fields'][n_field]['length'] = length

             elif re.search( r'<type>', line ):
                  name = re.sub( r'^.*<type>', '', re.sub( r'</.*', '', line )).strip()
                  if in_fit:
                      data['fields'][n_field]['fit']['type'] = name
                  else:
                     # special case for mistakes in xml
                     if data_field == '':
                        # don't overwrite if it already exists
                        if 'type' in data['fields'][n_field].keys():
                           name = data['fields'][n_field]['type']
                     else:
                        name = data_field
                     data['fields'][n_field]['type'] = name

             elif re.search( r'<name>', line ):
                  if in_fit:
                     name = re.sub( r'^.*<name>', '', re.sub( r'</.*', '', line )).strip()
                     n_coeff += 1
                     data['fields'][n_field]['fit']['coeffs'].append( dict() )
                     data['fields'][n_field]['fit']['coeffs'][n_coeff]['name'] = name

             elif re.search( r'<value>', line ):
                  if in_fit:
                     name = re.sub( r'^.*<value>', '', re.sub( r'</.*', '', line )).strip()
                     data['fields'][n_field]['fit']['coeffs'][n_coeff]['value'] = name

             elif re.search( r'<terminator>', line ):
                  name = re.sub( r'^.*<terminator>', '', re.sub( r'</.*', '', line )).strip()
                  data['frame_terminator'] = delim_translate( name )

             elif re.search( r'<fielddelimiter>', line ):
                  name = re.sub( r'^.*<fielddelimiter>', '', re.sub( r'</.*', '', line )).strip()
                  default_field_delim = delim_translate( name )

             elif re.search( r'<delimiter>', line ):
                  name = re.sub( r'^.*<delimiter>', '', re.sub( r'</.*', '', line )).strip()
                  data['fields'][n_field]['delimiter'] = delim_translate( name )

def convert_xml( filename, check_sensors, sensors_list ):
    convert_xml_format( output_to_json, filename, check_sensors, sensors_list )

def convert_xml_to_tdf( filename, check_sensors, sensors_list ):
    convert_xml_format( output_to_tdf, filename, check_sensors, sensors_list )
