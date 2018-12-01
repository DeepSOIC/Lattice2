#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2018 - Victor Titov (DeepSOIC)                          *
#*                                               <vv.titov@gmail.com>      *  
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__= "Lattice2 rounder module"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "helper module for Lattice add-on workbench for FreeCAD. Provides special rounding routines."

import math
from math import log

nice_numbers = [1.0, 2.0, 5.0]
nice_magnitudes = []
for degree in range(-3,6):
    order = 10.0 ** degree
    nice_magnitudes.extend([order * val for val in nice_numbers])
    
def roundToNiceValue(value, nice_value_list = nice_magnitudes):
    if value == 0.0:
        return 0.0
        
    bestmatch_logdist = log(1e10)
    bestmatch = None
    
    for nice_val in nice_value_list:
        logdist = abs(log(abs(value)) - log(nice_val))
        if logdist < bestmatch_logdist:
            bestmatch_logdist = logdist
            bestmatch = nice_val
            
    return math.copysign(bestmatch, value)

def roundToPrecision(value, precision):
    if precision < 1e-12:
        return value
    return round(value/precision)*precision