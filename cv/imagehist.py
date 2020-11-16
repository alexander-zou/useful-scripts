#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

'''

@File   : imagehist.py   
@Author : jiachen.zou@jiiov.com   
@Date   : 2020-11-09 18:07 CST(+0800)   
@Brief  : Show histgram of image(s)

'''

from __future__ import print_function, division
import os, sys
import glob
import math
import numpy as np
import cv2
import matplotlib.pyplot as plt

COLORS = [
    '#069af3', # azure
    '#029386', # teal
    '#ef4026', # tomato
    '#00ffff', # cyan
    '#bbf90f', # yellowgreen
    '#ff81c0', # pink
    '#380282', # indigo
    '#6E750E', # olive
    '#F97306', # orange
]

def choose_color( idx):
    if idx < len( COLORS):
        return COLORS[ idx]
    hex = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
    color = '#'
    color += hex[ ( 2 + idx * 13) % 16]
    color += hex[ ( 3 + idx * 1) % 16]
    color += hex[ ( 2 + idx * 7) % 16]
    color += hex[ ( 4 + idx * 3) % 16]
    color += hex[ ( 2 + idx * 3) % 16]
    color += hex[ ( 5 + idx * 5) % 16]
    return color

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

def count_channel( mat):
    if len( mat.shape) < 3:
        return 1
    else:
        return mat.shape[ 2]

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument( '-o', '--output', type = str, default = '', help = 'path to save image')
    parser.add_argument( '-f', '--force', action = 'store_true', help = 'force to rewrite existing file')
    parser.add_argument( '-n', '--no-gui', action = 'store_true', help = 'do not show GUI')
    parser.add_argument( '-l', '--log', action = 'store_true', help = 'logarithm scale')
    parser.add_argument( '-p', '--percentage', action = 'store_true', help = 'show percentage auxiliary line')
    parser.add_argument( '-c', '--channelwise', action = 'store_true', help = 'show histgram of individual channel')
    parser.add_argument( '-r', '--range', type = int, default = 0, help = 'range of pixel value')
    parser.add_argument( '-s', '--smooth', type = int, default = 0, help = 'radius of smooth window')
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
    
    if len( files) <= 0:
        print( "ERROR: no images found!", file = sys.stderr)
        exit( 1)

    plt.rcParams[ 'axes.unicode_minus'] = False
    plt.rcParams[ 'font.sans-serif'] = [ 'SimHei', 'Heiti TC', 'Adobe Heiti Std', 'Adobe Fan Heiti Std']
    fig, ax_left = plt.subplots()
    if args.percentage:
        ax_right = ax_left.twinx()
        ax_right.set_frame_on( True)
        ax_right.patch.set_visible( False)

    auto_x_range = 2
    auto_y_range = 2

    idx = 0
    for path in files:
        try :
            with open( path, 'rb') as inf: # use open() so we can read from pipes
                # load image:
                mat = cv2.imdecode( np.frombuffer( inf.read(), dtype = np.uint8), cv2.IMREAD_UNCHANGED)
                if mat is None:
                    raise Exception( "cv2.imdecode() failed with '%s'" % ( path))
                if count_channel( mat) == 1:
                    pass
                elif count_channel( mat) == 2:
                    mat = mat[ :, :, 0]
                elif 3 <= count_channel( mat) <= 4:
                    mat = mat[ :, :, 0:3]
                else:
                    raise Exception( "unrecognized image format!")
                if mat.dtype == np.uint8:
                    auto_x_range = max( auto_x_range, 256)
                elif mat.dtype == np.uint16:
                    auto_x_range = max( auto_x_range, 2 ** 16)
                elif mat.dtype == np.uint32:
                    auto_x_range = max( auto_x_range, 2 ** 32)
                else:
                    raise Exception( "unsupported image format!")
                name = os.path.basename( path)
                if args.range > 0:
                    limit = args.range
                else:
                    limit = auto_x_range
                def draw( mat, name, color):
                    global args, ax_left, limit, auto_y_range
                    hist = [ np.count_nonzero( mat == i) for i in range( mat.max() + 1)]
                    if args.percentage:
                        percent = [ sum( hist[:i+1]) * 100.0 / sum( hist) for i in range( len( hist))]
                        ax_right.plot( percent[ :limit], color = color + '60')
                    if args.smooth > 0:
                        n = args.smooth * 2 + 1
                        if n < len( hist):
                            hist = np.convolve( hist, [ 1.0 / n] * n, 'same')
                    ax_left.plot( hist[ :limit], label = name, color = color)
                    while auto_y_range < max( hist[ :limit]):
                        auto_y_range *= 2
                if args.channelwise and count_channel( mat) == 3:
                    while idx % 3 > 0:
                        idx += 1
                    draw( mat[ :, :, 0], name + "[B]", choose_color( idx))
                    idx += 1
                    draw( mat[ :, :, 1], name + "[G]", choose_color( idx))
                    idx += 1
                    draw( mat[ :, :, 2], name + "[R]", choose_color( idx))
                    idx += 1
                else:
                    draw( mat, name, choose_color( idx))
                    idx += 1
        except Exception as e:
            print( "ERROR: failed processing image '%s': %s" % ( path, str( e)), file = sys.stderr)
            exit( 2)
    ax_left.legend()
    ax_left.grid( True)
    if args.log:
        ax_left.set_yscale( 'symlog')
    if args.range > 0:
        ax_left.set_xlim( [ 0, args.range - 1])
    else:
        ax_left.set_xlim( [ 0, auto_x_range - 1])
    ax_left.set_ylim( [ 0, auto_y_range])
    if args.percentage:
        ax_right.set_ylim( [ 0, 100])
    plt.title( 'Histgram')
    if len( args.output) > 0:
        if not os.path.isfile( args.output) or args.force or prompt( "File '" + args.output + "' already exists, overwrite?", True):
            plt.savefig( args.output)
    if not args.no_gui:
        plt.show()

# End of 'imagehist.py' 

