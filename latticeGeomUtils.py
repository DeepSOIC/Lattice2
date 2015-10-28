#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - Victor Titov (DeepSOIC)                          *
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


import FreeCAD as App

from latticeCommon import *

__title__="Geometric utility routines for Lattice workbench for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""


def makeOrientationFromLocalAxes(ZAx, XAx = None):
    '''
    makeOrientationFromLocalAxes(ZAx, XAx): constructs App.Rotation to get into 
    alignment with given local Z and X axes. Z axis is followed strictly; X axis
    is a guide and can be not strictly perpendicular to Z axis; it will be 
    corrected and modified

    '''
    if XAx is None:
        XAx = App.Vector(0,0,1) #Why Z? Because I prefer local X axis to be aligned so that local XZ plane is parallel to global Z axis.
    #First, compute all three axes.
    ZAx.normalize() #just to be sure; it's important to have the matrix normalized
    YAx = ZAx.cross(XAx) # construct Y axis
    if YAx.Length < ParaConfusion*10.0:
        #failed, try some other X axis direction hint
        XAx = App.Vector(0,0,1)
        YAx = ZAx.cross(XAx)
        if YAx.Length < ParaConfusion*10.0:
            #failed again. Now, we can tell, that local Z axis is along global
            # Z axis
            XAx = App.Vector(1,0,0)
            YAx = ZAx.cross(XAx)
        
    YAx.normalize()
    XAx = YAx.cross(ZAx) # force X perpendicular
    
    #hacky way of constucting rotation to a local coordinate system: 
    # make matrix,
    m = App.Matrix()
    m.A = list(XAx)+[0.0]+list(YAx)+[0.0]+list(ZAx)+[0.0]+[0.0]*3+[1.0]
    m.transpose() # local axes vectors are columns of matrix, but we put them in as rwos, because it is convenient, and then transpose it.
    # make placement out of matrix,
    tmpplm = App.Placement(m)
    # and extract rotation from placement. 
    ori = tmpplm.Rotation
    return ori
