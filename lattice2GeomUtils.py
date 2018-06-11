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

from lattice2Common import *

__title__="Geometric utility routines for Lattice workbench for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

def PlacementsFuzzyCompare(plm1, plm2):
    pos_eq = (plm1.Base - plm2.Base).Length < 1e-7   # 1e-7 is OCC's Precision::Confusion
    
    q1 = plm1.Rotation.Q
    q2 = plm2.Rotation.Q
    # rotations are equal if q1 == q2 or q1 == -q2. 
    # Invert one of Q's if their scalar product is negative, before comparison.
    if q1[0]*q2[0] + q1[1]*q2[1] + q1[2]*q2[2] + q1[3]*q2[3] < 0:
        q2 = [-v for v in q2]
    rot_eq = (  abs(q1[0]-q2[0]) + 
                abs(q1[1]-q2[1]) + 
                abs(q1[2]-q2[2]) + 
                abs(q1[3]-q2[3])  ) < 1e-12   # 1e-12 is OCC's Precision::Angular (in radians)
    return pos_eq and rot_eq


def makeOrientationFromLocalAxes(ZAx, XAx = None):
    '''
    makeOrientationFromLocalAxes(ZAx, XAx): constructs App.Rotation to get into 
    alignment with given local Z and X axes. Z axis is followed strictly; X axis
    is a guide and can be not strictly perpendicular to Z axis; it will be 
    corrected and modified

    '''
    return makeOrientationFromLocalAxesUni("ZX",XAx= XAx, ZAx= ZAx)
    
    #dead old code that worked
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

def makeOrientationFromLocalAxesUni(priorityString, XAx = None, YAx = None, ZAx = None):
    '''
    makeOrientationFromLocalAxesUni(priorityString, XAx = None, YAx = None, ZAx = None): 
    constructs App.Rotation to get into alignment with given local axes. 
    Priority string is a string like "ZXY", which defines how axes are made 
    perpendicular. For example, "ZXY" means that Z is followed strictly, X is 
    made to be perpendicular to Z, and Y is completely ignored (a new one will 
    be computed from X and Z). The strict axis must be specified, all other are 
    optional.
    '''
    
    if XAx is None:
        XAx = App.Vector()
    if YAx is None:
        YAx = App.Vector()
    if ZAx is None:
        ZAx = App.Vector()
    
    axDic = {"X": XAx, "Y": YAx, "Z": ZAx}
    
    #expand priority string to list all axes
    if len(priorityString) == 0:
        priorityString = "ZXY"
    if len(priorityString) == 1:
        if priorityString == "X":
            priorityString = priorityString + "Z"
        elif priorityString == "Y":
            priorityString = priorityString + "Z"
        elif priorityString == "Z":
            priorityString = priorityString + "X"
    if len(priorityString) == 2:
        for ch in "XYZ":
            if not (ch in priorityString):
                priorityString = priorityString + ch
                break
    
    mainAx = axDic[priorityString[0]] #Driving axis
    secAx = axDic[priorityString[1]]  #Hint axis
    thirdAx = axDic[priorityString[2]] #Ignored axis
    #Note: since we need to change the actual XAx,YAx,ZAx while assigning to 
    # mainAx, secAx, thirdAx, we can't use '=' operator, because '=' reassigns 
    # the reference, and the variables lose linkage. For that purpose, 
    # _assignVector routine was introuced. It assigns the coordinates of the 
    # vector, without replacing referenes
    
    #force the axes be perpendicular
    mainAx.normalize()
    tmpAx = mainAx.cross(secAx)
    if tmpAx.Length < ParaConfusion*10.0:
        #failed, try some other secondary axis
        #FIXME: consider thirdAx, maybe??
        _assignVector( secAx, { "X":App.Vector(0,0,1),
                                "Y":App.Vector(0,0,1), #FIXME: revise
                                "Z":App.Vector(0,0,1)
                                }[priorityString[1]])
        tmpAx = mainAx.cross(secAx)
        if tmpAx.Length < ParaConfusion*10.0:
            #failed again. (mainAx is Z). try some other secondary axis.
            # Z axis
            _assignVector(secAx, {"X":App.Vector(1,0,0),
                                  "Y":App.Vector(0,1,0), #FIXME: revise
                                  "Z":App.Vector(1,0,0)
                                  }[priorityString[1]])
            tmpAx = mainAx.cross(secAx)
            assert(tmpAx.Length > ParaConfusion*10.0)
    tmpAx.normalize()
    _assignVector(secAx, tmpAx.cross(mainAx))
    
    #secAx was made perpendicular and valid, so we can compute the last axis. 
    # Here we need to take care to produce right handedness.
    _assignVector(thirdAx, tmpAx)
    if XAx.cross(YAx).dot(ZAx) < 0.0:
        _assignVector(thirdAx, tmpAx * (-1.0))

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
    
def _assignVector(lhs, rhs):
    '''A helper function for assigning vectors without creating new ones. Used as a hack to make aliases in OrientationFromLocalAxesUni'''
    (lhs.x,lhs.y,lhs.z) = tuple(rhs)