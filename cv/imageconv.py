#!/usr/bin/env python

# Created by zoujiachen@megvii.com
# 2018-08-15

from __future__ import print_function
import sys
import os
import glob
import argparse
import cv2 as cv
import math
import numpy as np

DESC_STR = "Convert image(s) as designated format."
USAGE_STR = "imageconv.py [-h] [-p PATH] [-c COL] [-r ROW] [-s STRIDE] [-l SCANLINE] " + \
            "[-j BYTES] -i FORMAT -o FORMAT [-n NORMALIZE] " + \
            "[--] FILE [FILE ...]"
IMAGE_TYPES = [
    "u8", "u16", "u32", "f32",
    "bgr", "rgb", "rgba", "bgra",
    "yuv", "nv21", "nv12",
    "jpg", "png", "bmp",
    "csv",
]
YUV_COLOR_STDS = [ "bt601", "bt709", "bt2020"]
YUV_RANGES = [
    "fullrange", "fullswing",
    "videorange", "studioswing",
]

def verbose( info) :
    print( info[ "filename"] + ":")
    print( "\twidth:    " + str( info[ "width"]))
    print( "\theight:   " + str( info[ "height"]))
    if "stride" in info and info[ "stride"] > 0 :
        print( "\tstride:   " + str( info[ "stride"]))
    if "scanline" in info and info[ "scanline"] > 0 :
        print( "\tscanline: " + str( info[ "scanline"]))
    if "range" in info :
        print( "\trange:    " + info[ "range"])
    if "r_range" in info :
        print( "\tR-range:  " + info[ "r_range"])
    if "g_range" in info :
        print( "\tG-range:  " + info[ "g_range"])
    if "b_range" in info :
        print( "\tB-range:  " + info[ "b_range"])
    if "a_range" in info :
        print( "\tA-range:  " + info[ "a_range"])
    if "y_range" in info :
        print( "\tY-range:  " + info[ "y_range"])
    if "u_range" in info :
        print( "\tU-range:  " + info[ "u_range"])
    if "v_range" in info :
        print( "\tV-range:  " + info[ "v_range"])
    print( "\toutput:   " + info[ "output"])

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

def guess_width( original, pixel_bytes, args) :
    pixel_count = len( original) // pixel_bytes
    if args.input_type.startswith( "nv") :
        pixel_count = pixel_count * 2 // 3
    array = np.copy( original[ : pixel_count * pixel_bytes])
    if pixel_bytes == 1:
        pass
    elif pixel_bytes == 2 :
        array = np.frombuffer( array.data, dtype = np.uint16)
    elif pixel_bytes == 3 :
        mixed = np.empty( pixel_count * 4, dtype = np.uint8)
        mixed[ 0::4] = array[ 0::3]
        mixed[ 1::4] = array[ 1::3]
        mixed[ 2::4] = array[ 2::3]
        mixed[ 3::4] = 0
        array = np.frombuffer( mixed.data, dtype = np.uint32)
    elif pixel_bytes == 4 :
        array = np.frombuffer( array.data, dtype = np.uint32)
    else :
        print( "ERROR: internal error guess_width()", file = sys.stderr)
        exit( 1)
    min_width = int( math.floor( math.sqrt( pixel_count) / 2))
    max_width = pixel_count // min_width
    peak = 0
    best_ratio = 1
    result = int( round( math.sqrt( pixel_count)))
    for width in range( min_width, max_width) :
        height = pixel_count // width
        if args.input_type.startswith( "nv") :
            if width % 2 != 0 :
                continue
            if height % 2 != 0 :
                height -= 1
                if height <= 0 :
                    continue
        step = 23 if width > 160 else 1
        reshaped = array[ : width * height].reshape( height, width)
        part1 = reshaped[ 0 : height - 1 : step]
        part2 = reshaped[ 1 : height : step]
        probability = ( part1 == part2).mean()
        if probability > peak :
            peak = probability
            result = width
        elif probability == peak :
            ratio = abs( width / height - 1)
            if ratio < best_ratio :
                best_ratio = ratio
                result = width
    return result

def normalize( mat, info, args) :
    if args.normalize == None :
        norm_max = -1
    elif args.normalize > 0 :
        norm_max = args.normalize
    else:
        norm_max = 0
    if args.input_type in [ "u8", "u16", "u32", "f32"] :
        mat_max = mat.max()
        info[ "range"] = "[" + str( mat.min()) + "," + str( mat_max) + "]"
        if norm_max == 0 :
            norm_max = mat_max
        if norm_max <= 0 :
            if args.input_type == "u16" :
                return mat.astype( np.float32) / 256.0
            elif args.input_type == 'u32':
                return mat.astype( np.float32) / 16777216.0
            elif args.input_type == "f32" :
                return mat.astype( np.float32) * 255.0
            else :
                return mat.astype( np.float32)
        else :
            return np.clip( mat.astype( np.float32), 0, norm_max) * 255.0 / norm_max
    elif args.input_type in [ "bgr", "rgb", "rgba", "bgra"] :
        if norm_max >= 0:
            print( "Warning: option -n/--normalize only works with 1-channel input, ignored.", file = sys.stderr)
        b = mat[ :, :, 0]
        g = mat[ :, :, 1]
        r = mat[ :, :, 2]
        info[ "b_range"] = "[" + str( b.min()) + "," + str( b.max()) + "]"
        info[ "g_range"] = "[" + str( g.min()) + "," + str( g.max()) + "]"
        info[ "r_range"] = "[" + str( r.min()) + "," + str( r.max()) + "]"
        if info[ "channel"] >= 4 :
            a = mat[ :, :, 3]
            info[ "a_range"] = "[" + str( a.min()) + "," + str( a.max()) + "]"
        return mat
    else :
        return mat

def yuv2bgr( yuv_mat, standard, fullrange, info, args) :
    if args.normalize != None :
        print( "Warning: option -n, --normalize only work with 1-channel input, ignored.", file = sys.stderr)
    y = yuv_mat[ :, :, 0]
    y_min = y.min()
    y_max = y.max()
    u = yuv_mat[ :, :, 1]
    u_min = u.min()
    u_max = u.max()
    v = yuv_mat[ :, :, 2]
    v_min = v.min()
    v_max = v.max()
    info[ "y_range"] = "[" + str( y_min) + "," + str( y_max) + "]"
    info[ "u_range"] = "[" + str( u_min) + "," + str( u_max) + "]"
    info[ "v_range"] = "[" + str( v_min) + "," + str( v_max) + "]"
    if fullrange :
        yy = y.astype( np.float)
        uu = u.astype( np.float) - 127.5
        vv = v.astype( np.float) - 127.5
        if standard == "bt601" :
            r = np.clip( yy + 1.402 * vv, 0, 255).round().astype( np.uint8)
            g = np.clip( yy - 0.34413629 * uu - 0.71413629 * vv, 0, 255).round().astype( np.uint8)
            b = np.clip( yy + 1.772 * uu, 0, 255).round().astype( np.uint8)
        elif standard == "bt709" :
            r = np.clip( yy + 1.5748 * vv, 0, 255).round().astype( np.uint8)
            g = np.clip( yy - 0.18732427 * uu - 0.46812427 * vv, 0, 255).round().astype( np.uint8)
            b = np.clip( yy + 1.8556 * uu, 0, 255).round().astype( np.uint8)
        elif standard == "bt2020" :
            r = np.clip( yy + 1.4746 * vv, 0, 255).round().astype( np.uint8)
            g = np.clip( yy - 0.16455313 * uu - 0.57135313 * vv, 0, 255).round().astype( np.uint8)
            b = np.clip( yy + 1.8814 * uu, 0, 255).round().astype( np.uint8)
        else :
            print( "ERROR: internal error yuv2bgr()", file = sys.stderr)
            exit( 1)
    else : # if video-range
        if y_min < 16 or y_max > 235 :
            print( "Warning: Y-channel data exceed video-range!", file = sys.stderr)
        if u_min < 16 or u_max > 240 :
            print( "Warning: U-channel data exceed video-range!", file = sys.stderr)
        if v_min < 16 or v_max > 240 :
            print( "Warning: V-channel data exceed video-range!", file = sys.stderr)
        yy = np.clip( y, 16, 235).astype( np.float) - 16
        uu = np.clip( u, 16, 240).astype( np.float) - 128
        vv = np.clip( v, 16, 240).astype( np.float) - 128
        if standard == "bt601" :
            r = np.clip( 1.16438356 * yy + 1.59602679 * vv, 0, 255).round().astype( np.uint8)
            g = np.clip( 1.16438356 * yy - 0.39176229 * uu - 0.81296765 * vv, 0, 255).round().astype( np.uint8)
            b = np.clip( 1.16438356 * yy + 2.01723214 * uu, 0, 255).round().astype( np.uint8)
        elif standard == "bt709" :
            r = np.clip( 1.16438356 * yy + 1.79274107 * vv, 0, 255).round().astype( np.uint8)
            g = np.clip( 1.16438356 * yy - 0.21324861 * uu - 0.53290933 * vv, 0, 255).round().astype( np.uint8)
            b = np.clip( 1.16438356 * yy + 2.11240179 * uu, 0, 255).round().astype( np.uint8)
        elif standard == "bt2020" :
            r = np.clip( 1.16438356 * yy + 1.67867411 * vv, 0, 255).round().astype( np.uint8)
            g = np.clip( 1.16438356 * yy - 0.18732610 * uu - 0.65042432 * vv, 0, 255).round().astype( np.uint8)
            b = np.clip( 1.16438356 * yy + 2.14177232 * uu, 0, 255).round().astype( np.uint8)
        else :
            print( "ERROR: internal error yuv2bgr()", file = sys.stderr)
            exit( 1)
    bgr = np.empty( yuv_mat.shape, dtype = np.uint8)
    bgr[ :, :, 0] = b
    bgr[ :, :, 1] = g
    bgr[ :, :, 2] = r
    return bgr

def bgr2yuv( bgr_mat, standard, fullrange) :
    b = bgr_mat[ :, :, 0]
    g = bgr_mat[ :, :, 1]
    r = bgr_mat[ :, :, 2]
    if fullrange :
        if standard == "bt601" :
            y = ( 0.299 * r + 0.587 * g + 0.114 * b).round().astype( np.uint8)
            u = ( -0.168736 * r - 0.331264 * g + 0.5 * b + 127.5).round().astype( np.uint8)
            v = ( 0.5 * r - 0.418688 * g - 0.081312 * b + 127.5).round().astype( np.uint8)
        elif standard == "bt709" :
            y = ( 0.2126 * r + 0.7152 * g + 0.0722 * b).round().astype( np.uint8)
            u = ( -0.11457211 * r - 0.38542789 * g + 0.5 * b + 127.5).round().astype( np.uint8)
            v = ( 0.5 * r - 0.45415291 * g - 0.04584709 * b + 127.5).round().astype( np.uint8)
        elif standard == "bt2020" :
            y = ( 0.2627 * r + 0.6780 * g + 0.0593 * b).round().astype( np.uint8)
            u = ( -0.13963006 * r - 0.36036994 * g + 0.5 * b + 127.5).round().astype( np.uint8)
            v = ( 0.5 * r - 0.45978570 * g - 0.04021430 * b + 127.5).round().astype( np.uint8)
        else :
            print( "ERROR: internal error bgr2yuv()", file = sys.stderr)
            exit( 1)
    else : # if video-range
        if standard == "bt601" :
            y = ( 0.25678824 * r + 0.50412941 * g + 0.09790588 * b + 16).round().astype( np.uint8)
            u = ( -0.14822300 * r - 0.29099269 * g + 0.43921569 * b + 128).round().astype( np.uint8)
            v = ( 0.43921569 * r - 0.36778867 * g - 0.07142701 * b + 128).round().astype( np.uint8)
        elif standard == "bt709" :
            y = ( 0.18258588 * r + 0.61423059 * g + 0.06200706 * b + 16).round().astype( np.uint8)
            u = ( -0.10064373 * r - 0.33857195 * g + 0.43921569 * b + 128).round().astype( np.uint8)
            v = ( 0.43921569 * r - 0.39894216 * g - 0.04027352 * b + 128).round().astype( np.uint8)
        elif standard == "bt2020" :
            y = ( 0.22561294 * r + 0.58228235 * g + 0.05092824 * b + 16).round().astype( np.uint8)
            u = ( -0.12265543 * r - 0.31656026 * g + 0.43921569 * b + 128).round().astype( np.uint8)
            v = ( 0.43921569 * r - 0.40389019 * g - 0.03532550 * b + 128).round().astype( np.uint8)
        else :
            print( "ERROR: internal error bgr2yuv()", file = sys.stderr)
            exit( 1)
    return y, u, v

def save_bgr2yuv( bgr_mat, standard, fullrange, info) :
    height = int( info[ "height"])
    width = int( info[ "width"])
    y, u, v = bgr2yuv( bgr_mat, standard, fullrange)
    yuv = np.empty( ( height, width, 3), dtype = np.uint8)
    yuv[ :, :, 0] = y
    yuv[ :, :, 1] = u
    yuv[ :, :, 2] = v
    yuv.tofile( info[ "output"])

def save_bgr2nv21( bgr_mat, standard, fullrange, info) :
    height = int( info[ "height"])
    width = int( info[ "width"])
    y, u, v = bgr2yuv( bgr_mat, standard, fullrange)
    vu = np.empty( ( height // 2, width), dtype = np.uint8)
    for i in range( 0, height // 2) :
        for j in range( 0, width // 2) :
            ox = i * 2
            oy = j * 2
            sum_u = int( u[ ox, oy])
            sum_u += u[ ox + 1, oy]
            sum_u += u[ ox, oy + 1]
            sum_u += u[ ox + 1, oy + 1]
            sum_v = int( v[ ox, oy])
            sum_v += v[ ox + 1, oy]
            sum_v += v[ ox, oy + 1]
            sum_v += v[ ox + 1, oy + 1]
            vu[ i, j * 2] = sum_v / 4.0
            vu[ i, j * 2 + 1] = sum_u / 4.0
    vu = np.uint8( np.rint( vu))
    nv21 = np.concatenate( ( y, vu))
    nv21.tofile( info[ "output"])

def save_bgr2nv12( bgr_mat, standard, fullrange, info) :
    height = info[ "height"]
    width = info[ "width"]
    y, u, v = bgr2yuv( bgr_mat, standard, fullrange)
    uv = np.empty( ( height / 2, width), dtype = np.uint8)
    for i in range( 0, height / 2) :
        for j in range( 0, width / 2) :
            ox = i * 2
            oy = j * 2
            sum_u = int( u[ ox, oy])
            sum_u += u[ ox + 1, oy]
            sum_u += u[ ox, oy + 1]
            sum_u += u[ ox + 1, oy + 1]
            sum_v = int( v[ ox, oy])
            sum_v += v[ ox + 1, oy]
            sum_v += v[ ox, oy + 1]
            sum_v += v[ ox + 1, oy + 1]
            uv[ i, j * 2] = sum_u / 4.0
            uv[ i, j * 2 + 1] = sum_v / 4.0
    uv = np.uint8( np.rint( uv))
    nv12 = np.concatenate( ( y, uv))
    nv12.tofile( info[ "output"])

def prepare_save( info, args) :
    path = args.path if args.path else "."
    if os.path.isdir( path) :
        if args.suffix is not None:
            info[ "output"] = path + "/" + info[ "filename"] + args.suffix
        elif args.output_type == "jpg" :
            info[ "output"] = path + "/" + info[ "filename"] + ".jpg"
        elif args.output_type == "png" :
            info[ "output"] = path + "/" + info[ "filename"] + ".png"
        elif args.output_type == "bmp" :
            info[ "output"] = path + "/" + info[ "filename"] + ".bmp"
        elif args.output_type == "csv" :
            info[ "output"] = path + "/" + info[ "filename"] + ".csv"
        elif args.output_type == "nv21" :
            info[ "output"] = path + "/" + info[ "filename"] + ".nv21"
        elif args.output_type == "nv12" :
            info[ "output"] = path + "/" + info[ "filename"] + ".nv12"
        elif args.output_type.startswith( "yuv") or args.output_type.startswith( "uyv") or args.output_type.startswith( "vyu") :
            info[ "output"] = path + "/" + info[ "filename"] + ".yuv"
        else :
            info[ "output"] = path + "/" + info[ "filename"] + ".bin"
    else :
        info[ "output"] = path
        folder = os.path.dirname( path)
        if len( folder) > 0 and not os.path.isdir( folder):
            try: # to make folder
                os.makedirs( folder)
            except:
                pass

def encode_image( path, ext, mat) :
    # use imencode() instead of imwrite() to avoid failure of opencv with non-ascii path:
    ret, data = cv.imencode( ext, mat)
    if not ret :
        print( "Warning: fail to encode '" + path + "'.", file = sys.stderr)
        return
    data.tofile( path)

def save_csv( mat, info) :
    height = info[ "height"]
    width = info[ "width"]
    ch = info[ "channel"]
    if info[ "origin_dtype"] == np.uint8:
        mat = np.round( mat).astype( np.uint8)
    elif info[ "origin_dtype"] == np.uint16:
        mat = np.round( mat * 256).astype( np.uint16)
    elif info[ "origin_dtype"] == np.float32:
        mat /= 255.0
    with open( info[ "output"], "w") as out:
        for i in range( height):
            for j in range( width):
                if j > 0:
                    out.write( ",")
                if ch > 1:
                    out.write( '"' + str( tuple( mat[ i, j])) + '"')
                else:
                    out.write( str( mat[ i, j]))
            out.write( "\n")

def is_same_path( path1, path2):
    try:
        return os.path.samefile( path1, path2)
    except:
        return False

# mat is single-channel-float32(0~255) or BGR or BGRA:
def save_mat( mat, info, args) :
    if os.path.exists( info[ "output"]) and not args.force and not is_same_path( info[ "output"], '/dev/stdout') :
        if not prompt( "File '" + info[ "output"] + "' already exists, overwrite?", True) :
            return
    if args.verbose :
        verbose( info)
    yuv_cs = "bt601"
    if args.output_yuv_color :
        yuv_cs = args.output_yuv_color
    yuv_fullrange = True
    if args.output_yuv_range and not args.output_yuv_range.startswith( "full") :
        yuv_fullrange = False
    if args.output_type == "jpg" :
        encode_image( info[ "output"], ".jpg", mat)
    elif args.output_type == "png" :
        if np.issubdtype( mat.dtype, np.floating) and info[ "origin_dtype"] == np.uint16:
            encode_image( info[ "output"], ".png", np.round( ( mat * 256)).astype( np.uint16))
        else:
            encode_image( info[ "output"], ".png", mat)
    elif args.output_type == "bmp" :
        encode_image( info[ "output"], ".bmp", mat)
    elif args.output_type == 'csv' :
        save_csv( mat, info)
    elif args.output_type == "u8" :
        if info[ "channel"] == 3 :
            mat = cv.cvtColor( mat, cv.COLOR_BGR2GRAY)
        elif info[ "channel"] == 4 :
            mat = cv.cvtColor( mat, cv.COLOR_BGRA2GRAY)
        else :
            mat = np.uint8( np.rint( mat))
        mat.tofile( info[ "output"])
    elif args.output_type == "u16" :
        if info[ "channel"] == 3 :
            mat = cv.cvtColor( mat, cv.COLOR_BGR2GRAY)
        elif info[ "channel"] == 4 :
            mat = cv.cvtColor( mat, cv.COLOR_BGRA2GRAY)
        mat = np.uint16( np.rint( mat * 256))
        mat.tofile( info[ "output"])
    elif args.output_type == "u32":
        if info[ "channel"] == 3 :
            mat = cv.cvtColor( mat, cv.COLOR_BGR2GRAY)
        elif info[ "channel"] == 4 :
            mat = cv.cvtColor( mat, cv.COLOR_BGRA2GRAY)
        mat = np.uint32( np.rint( mat * 16843009))
        mat.tofile( info[ "output"])
    elif args.output_type == "f32" :
        if info[ "channel"] == 3 :
            mat = cv.cvtColor( mat, cv.COLOR_BGR2GRAY)
        elif info[ "channel"] == 4 :
            mat = cv.cvtColor( mat, cv.COLOR_BGRA2GRAY)
        mat = mat.astype( np.float32) / 255.0
        mat.tofile( info[ "output"])
    elif args.output_type == "bgr" :
        if info[ "channel"] == 1 :
            mat = np.uint8( np.rint( mat))
            mat = cv.cvtColor( mat, cv.COLOR_GRAY2BGR)
        elif info[ "channel"] == 4 :
            mat = mat[ :, :, :3]
        mat.tofile( info[ "output"])
    elif args.output_type == "rgb" :
        if info[ "channel"] == 1 :
            mat = np.uint8( np.rint( mat))
            mat = cv.cvtColor( mat, cv.COLOR_GRAY2BGR)
        elif info[ "channel"] == 4 :
            mat = mat[ :, :, :3]
        mat = cv.cvtColor( mat, cv.COLOR_BGR2RGB)
        mat.tofile( info[ "output"])
    elif args.output_type == "rgba" :
        if info[ "channel"] == 1 :
            mat = np.uint8( np.rint( mat))
            mat = cv.cvtColor( mat, cv.COLOR_GRAY2BGRA)
        elif info[ "channel"] == 3 :
            mat = cv.cvtColor( mat, cv.COLOR_BGR2BGRA)
        mat = cv.cvtColor( mat, cv.COLOR_BGRA2RGBA)
        mat.tofile( info[ "output"])
    elif args.output_type == "bgra" :
        if info[ "channel"] == 1 :
            mat = np.uint8( np.rint( mat))
            mat = cv.cvtColor( mat, cv.COLOR_GRAY2BGRA)
        elif info[ "channel"] == 3 :
            mat = cv.cvtColor( mat, cv.COLOR_BGR2BGRA)
        mat.tofile( info[ "output"])
    elif args.output_type == "yuv" :
        if info[ "channel"] == 1 :
            mat = np.uint8( np.rint( mat))
            mat = cv.cvtColor( mat, cv.COLOR_GRAY2BGR)
        save_bgr2yuv( mat, yuv_cs, yuv_fullrange, info)
    elif args.output_type == "nv21" :
        h = info[ "height"]
        w = info[ "width"]
        if h % 2 != 0 or w % 2 != 0 :
            print( "Error: cannot save nv21 image with height = " + str( h) + " and width = " + str( w), file = sys.stderr)
            return
        if info[ "channel"] == 1 :
            mat = np.uint8( np.rint( mat))
            mat = cv.cvtColor( mat, cv.COLOR_GRAY2BGR)
        save_bgr2nv21( mat, yuv_cs, yuv_fullrange, info)
    elif args.output_type == "nv12" :
        h = info[ "height"]
        w = info[ "width"]
        if h % 2 != 0 or w % 2 != 0 :
            print( "Error: cannot save nv12 image with height = " + str( h) + " and width = " + str( w), file = sys.stderr)
            return
        if info[ "channel"] == 1 :
            mat = np.uint8( np.rint( mat))
            mat = cv.cvtColor( mat, cv.COLOR_GRAY2BGR)
        save_bgr2nv12( mat, yuv_cs, yuv_fullrange, info)


def process_image( mat, filename, args) :
    info = {}
    info[ "origin_dtype"] = mat.dtype
    info[ "height"] = int( mat.shape[ 0])
    info[ "width"] = int( mat.shape[ 1])
    try:
        info[ "channel"] = int( mat.shape[ 2])
    except :
        info[ "channel"] = 1
    info[ "filename"] = os.path.basename( filename)
    info[ "stride"] = 0
    info[ "scanline"] = 0
    if info[ "channel"] == 1 :
        info[ "y_range"] = "[" + str( mat.min()) + "," + str( mat.max()) + "]"
        prepare_save( info, args)
        if args.normalize is not None:
            if args.normalize > 0:
                norm_max = args.normalize
            else:
                norm_max = mat.max()
            mat = mat.astype( np.float32) * 255 / norm_max
        elif mat.dtype == np.uint16:
            mat = mat.astype( np.float) / 256
        elif mat.dtype == np.float32:
            mat = mat * 255
        save_mat( mat.astype( np.float), info, args)
    elif info[ "channel"] == 2:
        if args.normalize is not None :
            print( "Warning: option -n/--normalize only works with 1-channel input, ignored.", file = sys.stderr)
        y = mat[ :, :, 0]
        a = mat[ :, :, 1]
        info[ "y_range"] = "[" + str( y.min()) + "," + str( y.max()) + "]"
        info[ "a_range"] = "[" + str( a.min()) + "," + str( a.max()) + "]"
        if mat.dtype == np.uint16:
            mat = mat / 256
            y = mat[ :, :, 0]
            a = mat[ :, :, 1]
        elif mat.dtype == np.float32:
            mat = mat * 255
            y = mat[ :, :, 0]
            a = mat[ :, :, 1]
        bgra = cv.merge( ( y, y, y, a))
        prepare_save( info, args)
        info[ "origin_dtype"] = np.uint8
        save_mat( bgra.astype( np.uint8), info, args)
    elif info[ "channel"] >= 3:
        if args.normalize is not None :
            print( "Warning: option -n/--normalize only works with 1-channel input, ignored.", file = sys.stderr)
        b = mat[ :, :, 0]
        g = mat[ :, :, 1]
        r = mat[ :, :, 2]
        info[ "b_range"] = "[" + str( b.min()) + "," + str( b.max()) + "]"
        info[ "g_range"] = "[" + str( g.min()) + "," + str( g.max()) + "]"
        info[ "r_range"] = "[" + str( r.min()) + "," + str( r.max()) + "]"
        if info[ "channel"] >= 4 :
            a = mat[ :, :, 3]
            info[ "a_range"] = "[" + str( a.min()) + "," + str( a.max()) + "]"
        if mat.dtype == np.uint16:
            mat = ( mat / 256).astype( np.uint8)
        elif mat.dtype == np.float32:
            mat = ( mat * 255).astype( np.uint8)
        prepare_save( info, args)
        info[ "origin_dtype"] = np.uint8
        save_mat( mat, info, args)
    else:
        print( "ERROR: internal error process_image()", file = sys.stderr)
        exit( 1)

def get_size( array, info, args) :
    # get stride and scanline:
    size = len( array)
    if args.input_type.startswith( "nv") :
        size = size * 2 // 3
    if args.stride != None and args.stride > 0 :
        info[ "stride"] = args.stride
        if not args.scanline or args.scanline <= 0 :
            info[ "scanline"] = size // info[ "stride"]
        else :
            info[ "scanline"] = args.scanline
    elif args.scanline != None and args.scanline > 0 :
        info[ "scanline"] = args.scanline
        info[ "stride"] = size // info[ "scanline"]
    else :
        info[ "scanline"] = 0
        info[ "stride"] = 0
    if args.input_type.startswith( "nv") :
        if args.scanline and args.scanline % 2 != 0 :
            return False
        elif args.row and args.row % 2 != 0 :
            return False
        elif args.col and args.col % 2 != 0 :
            return False
        if info[ "scanline"] % 2 != 0 :
            return False
    # get width and height:
    if args.row != None and args.row > 0 :
        info[ "height"] = int( args.row)
        if args.col != None and args.col > 0 :
            info[ "width"] = int( args.col)
        else :
            if info[ "stride"] > 0 :
                info[ "width"] = info[ "stride"] // info[ "pixel_bytes"]
            else :
                info[ "width"] = size // info[ "pixel_bytes"] // info[ "height"]
    elif args.col != None and args.col > 0 :
        info[ "width"] = int( args.col)
        if info[ "scanline"] > 0 :
            info[ "height"] = info[ "scanline"]
        else :
            info[ "height"] = size // info[ "pixel_bytes"] // info[ "width"]
    elif info[ "stride"] > 0 and info[ "scanline"] > 0 :
        info[ "height"] = info[ "scanline"]
        info[ "width"] = info[ "stride"] // info[ "pixel_bytes"]
    else :
        info[ "width"] = guess_width( array, info[ "pixel_bytes"], args)
        info[ "height"] = size // info[ "pixel_bytes"] // info[ "width"]
    if info[ "stride"] <= 0 :
        info[ "stride"] = info[ "width"] * info[ "pixel_bytes"]
    if info[ "scanline"] <= 0 :
        info[ "scanline"] = info[ "height"]
    # check if stride is large enough for width:
    if info[ "width"] * info[ "pixel_bytes"] > info[ "stride"] :
        return False
    # check if scanline is large enough for height:
    if info[ "scanline"] < info[ "height"] :
        return False
    # check if enough data for stride and scanline:
    if args.input_type.startswith( "nv") :
        expected_size = info[ "stride"] * info[ "scanline"] * 3 / 2
    else :
        expected_size = info[ "stride"] * info[ "scanline"]
    return len( array) >= expected_size


def process_raw( array, filename, args) :
    yuv_cs = "bt601"
    if args.input_yuv_color :
        yuv_cs = args.input_yuv_color
    yuv_fullrange = True
    if args.input_yuv_range and not args.input_yuv_range.startswith( "full") :
        yuv_fullrange = False
    info = {}
    info[ "filename"] = os.path.basename( filename)
    if args.input_type == "u8" :
        info[ "channel"] = 1
        info[ "pixel_bytes"] = 1
        info[ "origin_dtype"] = np.uint8
    elif args.input_type == "u16" :
        info[ "channel"] = 1
        info[ "pixel_bytes"] = 2
        info[ "origin_dtype"] = np.uint16
    elif args.input_type == "u32" :
        info[ "channel"] = 1
        info[ "pixel_bytes"] = 4
        info[ "origin_dtype"] = np.uint32
    elif args.input_type == "f32" :
        info[ "channel"] = 1
        info[ "pixel_bytes"] = 4
        info[ "origin_dtype"] = np.float32
    elif args.input_type in [ "bgr", "rgb", "yuv"] :
        info[ "channel"] = 3
        info[ "pixel_bytes"] = 3
        info[ "origin_dtype"] = np.uint8
    elif args.input_type in [ "bgra", "rgba"] :
        info[ "channel"] = 4
        info[ "pixel_bytes"] = 4
        info[ "origin_dtype"] = np.uint8
    elif args.input_type.startswith( "nv") :
        info[ "channel"] = 3
        info[ "pixel_bytes"] = 1
        info[ "origin_dtype"] = np.uint8
    else :
        print( "ERROR: internal error process_raw()", file = sys.stderr)
        exit( 1)
    if not get_size( array, info, args) :
        print( "Warning: invalid size configuration for input file '" + filename + "'", file = sys.stderr)
        return
    stride = int( info[ "stride"])
    scanline = int( info[ "scanline"])
    w = int( info[ "width"])
    h = int( info[ "height"])
    if args.input_type == "u8" :
        mat = array[ : stride * scanline].reshape( scanline, stride)
        mat = mat[ :h, :w]
        mat = normalize( mat, info, args)
    elif args.input_type == "u16" :
        mat = array[ : stride * scanline].reshape( scanline, stride)
        mat = mat[ : h, : w * 2]
        mat = np.frombuffer( mat.data, dtype = np.uint16)
        mat = mat.reshape( h, w)
        mat = normalize( mat, info, args)
    elif args.input_type == "u32" :
        mat = array[ : stride * scanline].reshape( scanline, stride)
        mat = mat[ : h, : w * 4]
        mat = np.frombuffer( mat.data, dtype = np.uint32)
        mat = mat.reshape( h, w)
        mat = normalize( mat, info, args)
    elif args.input_type == "f32" :
        mat = array[ : stride * scanline].reshape( scanline, stride)
        mat = mat[ : h, : w * 4]
        mat = np.frombuffer( mat.data, dtype = np.float32)
        mat = mat.reshape( h, w)
        mat = normalize( mat, info, args)
    elif args.input_type == "bgr" :
        mat = array[ : stride * scanline].reshape( scanline, stride)
        mat = mat[ : h, : w * 3].reshape( h, w, 3)
        mat = normalize( mat, info, args)
    elif args.input_type == "rgb" :
        mat = array[ : stride * scanline].reshape( scanline, stride)
        mat = mat[ : h, : w * 3].reshape( h, w, 3)
        mat = cv.cvtColor( mat, cv.COLOR_RGB2BGR)
        mat = normalize( mat, info, args)
    elif args.input_type == "rgba" :
        mat = array[ : stride * scanline].reshape( scanline, stride)
        mat = mat[ : h, : w * 4].reshape( h, w, 4)
        mat = cv.cvtColor( mat, cv.COLOR_RGBA2BGRA)
        mat = normalize( mat, info, args)
    elif args.input_type == "bgra" :
        mat = array[ : stride * scanline].reshape( scanline, stride)
        mat = mat[ : h, : w * 4].reshape( h, w, 4)
        mat = normalize( mat, info, args)
    elif args.input_type == "yuv" :
        mat = array[ : stride * scanline].reshape( scanline, stride)
        mat = mat[ : h, : w * 3].reshape( h, w, 3)
        mat = yuv2bgr( mat, yuv_cs, yuv_fullrange, info, args)
    elif args.input_type.startswith( "nv") :
        y = array[ : stride * scanline].reshape( scanline, stride)
        y = y[ : h, : w]
        uv = array[ stride * scanline: stride * scanline * 3 // 2].reshape( scanline // 2, stride)
        uv = uv[ : h // 2, : w]
        u = uv[ :, ::2]
        v = uv[ :, 1::2]
        if args.input_type == "nv21" :
            u, v = v, u
        yuv = np.empty( ( h, w, 3), dtype = np.uint8)
        yuv[ :, :, 0] = y
        yuv[ ::2, ::2, 1] = u
        yuv[ ::2, 1::2, 1] = u
        yuv[ 1::2, ::2, 1] = u
        yuv[ 1::2, 1::2, 1] = u
        yuv[ ::2, ::2, 2] = v
        yuv[ ::2, 1::2, 2] = v
        yuv[ 1::2, ::2, 2] = v
        yuv[ 1::2, 1::2, 2] = v
        mat = yuv2bgr( yuv, yuv_cs, yuv_fullrange, info, args)
    else :
        print( "ERROR: internal error process_raw()", file = sys.stderr)
        exit( 1)
    prepare_save( info, args)
    save_mat( mat, info, args)

def process( filename, args) :
    if not os.path.isfile( filename) :
        print( "Warning: input file '" + filename + "' does not exist, ignored.", file = sys.stderr)
        return
    try :
        if args.input_type == 'csv':
            import csv
            with open( filename, 'r') as csv_file:
                dialect = csv.Sniffer().sniff( csv_file.read())
                csv_file.seek( 0)
                reader = csv.reader( csv_file, dialect)
                jump_through = args.jump_through
                sheet = []
                for row in reader:
                    if jump_through > 0:
                        jump_through -= 1
                        continue
                    row_data = []
                    for data in row:
                        row_data.append( float( data))
                    if len( row_data) > 0:
                        sheet.append( row_data)
                        if len( row_data) != len( sheet[ 0]):
                            print( "ERROR: inconsistent number column within csv file!", file = sys.stderr)
                            exit( 1)
                array = np.array( sheet, dtype = np.float32)
        elif args.jump_through > 0:
            with open( filename, 'rb') as inp:
                inp.seek( args.jump_through)
                array = np.fromfile( inp, dtype = np.uint8)
        else:
            array = np.fromfile( filename, dtype = np.uint8)
    except :
        print( "Warning: cannot read from file '" + filename + "', ignored.", file = sys.stderr)
        return

    if args.input_type in [ "jpg", "png", "bmp"] :
        # use imdecode() instead of imread() to avoid failure of opencv with non-ascii path
        mat = cv.imdecode( array, cv.IMREAD_UNCHANGED)
        if mat is None :
            print( "Warning: fail to decode image '" + filename + "', ignored.", file = sys.stderr)
            return
        process_image( mat, filename, args)
    elif args.input_type == "csv":
        if args.normalize is None:
            args.normalize = 0
        process_image( array, filename, args)
    else :
        process_raw( array, filename, args)

def process_all( files, args):
    if args.path and not os.path.isdir( args.path) and ( len( files) > 1 or args.path.endswith('/') or args.path.endswith('\\')):
        try:
            os.makedirs( args.path)
        except Exception as e:
            print( "ERROR: failed creating output folder: " + str( e), file = sys.stderr)
            exit( 1)
    for file in files :
        process( file, args)

def main( args) :
    parser = argparse.ArgumentParser( description = DESC_STR, usage = USAGE_STR)
    parser.add_argument( "-p", "--path",
            help = "output file or directory path")
    parser.add_argument( "-c", "--col", "--width", type = int, default = 0,
            help = "image width, auto detect each image if not given")
    parser.add_argument( "-r", "--row", "--height", type = int, default = 0,
            help = "image height, auto detect each image if not given")
    parser.add_argument( "-s", "--stride", type = int,
            help = "image stride, bytes of each data line")
    parser.add_argument( "-l", "--scanline", type = int,
            help = "image scanline, lines of data")
    parser.add_argument( "-i", "--input-type", choices = IMAGE_TYPES, required = True,
            help = "data format of input image")
    parser.add_argument( "-o", "--output-type", choices = IMAGE_TYPES, required = True,
            help = "data format of output image")
    parser.add_argument( "-j", "--jump-through", type = int, default = 0,
            help = "number of bytes (or lines for csv) to jump through at the begining of input file")
    parser.add_argument( "--input-yuv-color", choices = YUV_COLOR_STDS,
            help = "color space of input yuv data, default is BT.601")
    parser.add_argument( "--input-yuv-range", choices = YUV_RANGES,
            help = "data range of input yuv data, default is full-range")
    parser.add_argument( "--output-yuv-color", choices = YUV_COLOR_STDS,
            help = "color space of output yuv data, default is BT.601")
    parser.add_argument( "--output-yuv-range", choices = YUV_RANGES,
            help = "data range of output yuv data, default is full-range")
    parser.add_argument( "-n", "--normalize", type = float,
            help = "scale value with NORMALIZE as max value, do softmax if set to zero")
    parser.add_argument( "-x", "--suffix", type = str,
            help = "specify suffix of output files.")
    parser.add_argument( "-f", "--force", action = "store_true",
            help = "force to rewrite existing file(s)")
    parser.add_argument( "-v", "--verbose", action = "store_true",
            help = "display detail info of each input file(s)")
    args, files = parser.parse_known_args( args)
    try :
        files.remove( "--")
    except :
        pass
    if os.name != "posix":
        expanded_files = []
        for f in files:
            expanded = glob.glob( f)
            if len( expanded) > 0:
                expanded_files += expanded
            else:
                expanded_files.append( f)
        files = expanded_files
    process_all( files, args)

if __name__ == "__main__" :
    main( sys.argv[ 1:])

# EOF
