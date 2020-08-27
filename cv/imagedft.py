#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''

@File   : imagedft.py   
@Author : alexander.here@gmail.com
@Date   : 2020-04-03 16:26 CST(+0800)   
@Brief  : generate DFT spectrum with opencv

'''

from __future__ import print_function, division
import os, sys
import glob
import math
import numpy as np
import cv2

def prompt( msg, default) :
    if sys.version_info.major <= 2:
        result = raw_input( msg + " [Y/n]" if default else " [y/N]")
    else:
        result = input( msg + " [Y/n]" if default else " [y/N]")
    if len( result) <= 0 :
        return default
    elif result.lower().startswith( "y") :
        return True
    elif result.lower().startswith( "n") :
        return False
    else :
        return prompt( msg, default)

def dft_spectrum( mat, target_range = 255):
    height, width = mat.shape[:2]
    padded_height = cv2.getOptimalDFTSize( height)
    padded_width = cv2.getOptimalDFTSize( width)
    padded = cv2.copyMakeBorder( mat, 0, padded_height - height, 0, padded_width - width, cv2.BORDER_CONSTANT, value = [ 0])

    result_channels = []
    for channel in cv2.split( padded):
        dft = cv2.dft( channel.astype( np.float64), flags = cv2.DFT_COMPLEX_OUTPUT)
        dft = cv2.magnitude( dft[ :, :, 0], dft[ :, :, 1])
        dft = np.fft.fftshift( dft)
        dft = cv2.log( dft + 1)
        result_channels.append( dft)
    
    result = cv2.merge( result_channels)
    cv2.normalize( result, result, 0, target_range, cv2.NORM_MINMAX)
    return result

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument( '-o', '--output', type = str, default = '', help = 'path to save spectrum image.')
    parser.add_argument( '--format', type = str,
                            choices = [ 'auto', 'png', 'jpg', 'bmp', 'tiff'],
                            default = 'auto',
                            help = 'format extension to save spectrum image with.')
    parser.add_argument( '-f', '--force', action = 'store_true', help = 'force to rewrite existing file(s)')
    parser.add_argument( '-s', '--suffix', type = str,
                            default = '_spec.png',
                            help = 'suffix to generate output filename, no effect if -o option set.')
    parser.add_argument( '-d', '--destination', type = str,
                            default = '',
                            help = 'destination directory to output into, no effect if -o option set.')
    args, files = parser.parse_known_args( sys.argv[ 1:])
    try :
        files.remove( '--')
    except:
        pass

    if os.name != 'posix':
        expanded_files = []
        for raw_path in files:
            if '*' in raw_path:
                expanded_files += glob.glob( raw_path)
            else:
                expanded_files.append( raw_path)
        files = expanded_files

    for idx, path in enumerate( files):
        print( '[%2d%%] %s ...' % ( idx * 100 / len( files), path))
        if len( args.output) > 0:
            output_path = args.output
        else:
            output_path = os.path.join( args.destination, os.path.basename( path) + args.suffix)
        if os.path.isfile( output_path) \
                and not args.force \
                and not prompt( "File '" + output_path + "' already exists, overwrite?", True):
            continue
        if args.format == 'auto':
            ext = os.path.splitext( output_path)[ 1]
            if len( ext) <= 0:
                ext = '.png'
        else:
            ext = '.' + args.format
        with open( path, 'rb') as inf: # use open() so we can read from pipes
            data = np.frombuffer( inf.read(), dtype = np.uint8)
            raw = cv2.imdecode( data, cv2.IMREAD_UNCHANGED)
            if raw is None:
                print( "WARNING: failed decoding image '%s', skipped!" % ( path), file = sys.stderr)
                continue
            # drop alpha channel:
            if len( raw.shape) == 3 and raw.shape[ 2] in ( 2, 4):
                raw = raw[ :, :, :-1]
        if ext.lower() in ( '.png', '.tiff'):
            spec = dft_spectrum( raw, 65535).round().astype( np.uint16)
        else:
            spec = dft_spectrum( raw).round().astype( np.uint8)
        folder = os.path.dirname( output_path)
        if len( folder) > 0 and not os.path.isdir( folder):
            try:
                os.makedirs( folder)
            except Exception as e:
                print( "failed to create output folder '%s': %s" % ( folder, str( e)), file = sys.stderr)
                # do NOT exit here, try writing the result anyway.
        ret, output_data = cv2.imencode( ext, spec)
        if ret:
            output_data.tofile( output_path)
        else:
            print( 'WARNING: failed encoding output image, skipped!', file = sys.stderr)
            continue


# End of 'imagedft.py' 

