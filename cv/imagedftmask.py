#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''

@File   : imagedftmask.py   
@Author : alexander.here@gmail.com
@Date   : 2020-04-08 12:07 CST(+0800)   
@Brief  : use masked dft spectrum to reconstruct image with opencv

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

def data_range( mat):
    if mat.dtype == np.uint8:
        return 255
    elif mat.dtype == np.uint16:
        return 65535
    elif np.issubdtype( mat.dtype, np.floating):
        return 1.0
    else:
        raise Exception( 'cannot process data type: ' + str( mat.dtype))

def channel_count( mat):
    if len( mat.shape) < 3:
        return 1
    else:
        return mat.shape[ 2]

def drop_alpha_channel( mat):
    if channel_count( mat) in ( 2, 4):
        return mat[ :, :, :-1]
    return mat

def dft_mask( mat, mask):
    height, width = mat.shape[:2]
    if height == mask.shape[ 0] and width == mask.shape[ 1]:
        padded = mat
    else:
        padded_height = cv2.getOptimalDFTSize( height)
        padded_width = cv2.getOptimalDFTSize( width)
        if padded_height != mask.shape[ 0] or padded_width != mask.shape[ 1]:
            raise Exception( "mismatched shape of image and mask!")
        padded = cv2.copyMakeBorder( mat, 0, padded_height - height, 0, padded_width - width, cv2.BORDER_CONSTANT, value = [ mat.mean()])

    masks = cv2.split( mask)
    channels = cv2.split( padded)

    result_channels = []
    for i in range( len( channels)):
        mask = np.fft.ifftshift( masks[ i % len( masks)])
        dft = cv2.dft( channels[ i].astype( np.float32), flags = cv2.DFT_COMPLEX_OUTPUT)
        dft *= np.stack( [ mask] * 2, axis = 2)
        rec = cv2.idft( dft, flags = cv2.DFT_SCALE | cv2.DFT_COMPLEX_OUTPUT)
        rec = cv2.magnitude( rec[:,:,0], rec[:,:,1])
        result_channels.append( rec)
    result = cv2.merge( result_channels)[ 0:height, 0:width]
    if not np.issubdtype( mat.dtype, np.floating):
            result = result.round()
    return result.clip( 0, data_range( mat)).astype( mat.dtype)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument( '-o', '--output', type = str, default = '', help = 'path to save reconstructed image.')
    parser.add_argument( '-m', '--mask', type = str, required = True, help = 'path of mask image.')
    parser.add_argument( '--format', type = str,
                            choices = [ 'auto', 'png', 'jpg', 'bmp', 'tiff'],
                            default = 'auto',
                            help = 'format extension to save reconstructed image with.')
    parser.add_argument( '-f', '--force', action = 'store_true', help = 'force to rewrite existing file(s)')
    parser.add_argument( '-s', '--suffix', type = str,
                            default = '_masked.png',
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

    with open( args.mask, 'rb') as inf: # use open() so we can read from pipes
        data = np.frombuffer( inf.read(), dtype = np.uint8)
        mask = cv2.imdecode( data, cv2.IMREAD_UNCHANGED)
        if mask is None:
            print( "ERROR: failed decoding mask image '%s'!" % ( args.mask))
            exit( 1)
        mask = drop_alpha_channel( mask)
        mask = mask.astype( np.float32) / data_range( mask)
            
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
            raw = drop_alpha_channel( raw)
        try:
            rec = dft_mask( raw, mask)
        except Exception as e:
            print( "WARNING: failed applying DFT mask to image '%s', skipped: %s" % ( path, str( e)), file = sys.stderr)
            continue
        folder = os.path.dirname( output_path)
        if len( folder) > 0 and not os.path.isdir( folder):
            try:
                os.makedirs( folder)
            except Exception as e:
                print( "WARNINS: failed to create output folder '%s': %s" % ( folder, str( e)), file = sys.stderr)
                # do NOT exit here, try writing the result anyway.
        try:
            ret, output_data = cv2.imencode( ext, rec)
            if ret:
                output_data.tofile( output_path)
            else:
                raise Exception( 'failed encoding with imencode()')
        except Exception as e:
            print( "WARNING: failed to output image '%s', skipped: %s" % ( output_path, str(e)), file = sys.stderr)
            continue

# End of 'imagedftmask.py' 

