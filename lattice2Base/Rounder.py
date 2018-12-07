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

# copied from FreeCAD /src/Base/UnitsSchema.h, enum UnitSystem
class UnitSystem(object): 
    SI1 = 0 #, /** internal (mm,kg,s) SI system (http://en.wikipedia.org/wiki/International_System_of_Units) */
    SI2 = 1 #, /** MKS (m,kg,s) SI system */
    Imperial1 = 2 #, /** the Imperial system (http://en.wikipedia.org/wiki/Imperial_units) */
    ImperialDecimal = 3 #, /** Imperial with length in inch only */
    Centimeters = 4 #, /** All lengths in centimeters, areas and volumes in square/cubic meters */
    ImperialBuilding = 5 #, /** All lengths in feet + inches + fractions */
    MmMin = 6 #, /** Lengths in mm, Speed in mm/min. Angle in degrees. Useful for small parts & CNC */
    
    @staticmethod
    def getActiveSchema():
        import FreeCAD as App
        return App.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("UserSchema", 0)

def getNiceLengths(unitschema = None):
    if unitschema is None:
        unitschema = UnitSystem.getActiveSchema()
    if unitschema == UnitSystem.SI1 or unitschema == UnitSystem.SI2 or unitschema == UnitSystem.Centimeters or unitschema == UnitSystem.MmMin:
        nice_numbers = [1.0, 2.0, 5.0]
        nice_magnitudes = []
        for degree in range(-3,6):
            order = 10.0 ** degree
            nice_magnitudes.extend([order * val for val in nice_numbers])
        return nice_magnitudes
    elif unitschema == UnitSystem.Imperial1 or unitschema == UnitSystem.ImperialBuilding or unitschema == UnitSystem.ImperialDecimal:
        inch = 25.4
        foot = 304.8
        yard = 914.4
        mile = 1609344.0
        #https://forum.freecadweb.org/viewtopic.php?f=8&t=32565#p271923
        #.005" .010", .025", .050", .100", .250", 1", 6", 1', 8', 50', 100', 500', 1000', 2500', 1 mile, 10 miles, 100 miles
        return [
            0.005*inch, 
            0.010*inch, 0.025*inch, 0.050*inch,
            0.10*inch, 0.25*inch, 0.50*inch,
            1*inch, 2*inch, 6*inch,
            
            1*foot, 2*foot, 4*foot, 8*foot, 
            16*foot, 32*foot, 50*foot, 
            100*foot, 250*foot, 500*foot, 
            1000*foot, 2500*foot,
            
            1*mile, 2*mile, 5*mile, 
            10*mile, 25*mile, 50*mile, 
            100*mile
        ]
    else:
        #unit unsupported? fall back to metric
        import FreeCAD as App
        App.PrintWarning("Lattice Autosize: Unit schema {n} is not yet supported.\n".format(n= unitschema))
        return getNiceLengths(UnitSystem.SI1)
    
def roundToNiceValue(value, nice_value_list = None):
    if value == 0.0:
        return 0.0
    
    if nice_value_list is None:
        nice_value_list = getNiceLengths()
    
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