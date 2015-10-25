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

import Part, os

__title__="latticeMarkers module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Module for loading marker shapes for Lattice workbench"

_nullShapeShape = 0
_ShapeDict = {}

def getShapePath(shapeName):
    """
     getShapePath(shapeName) converts marker file name without path 
     to a full path to a file. shapeName should be a file name with 
     extension, for example "empty-shape.brep"
     """
    return os.path.dirname(__file__) + os.path.sep + "shapes" + os.path.sep + shapeName
    
def getNullShapeShape(scale = 1.0):
    """obtains a shape intended ad a placeholder in case null shape was produced by an operation"""
    
    #read shape from file, if not done this before
    global _nullShapeShape
    if not _nullShapeShape:
        _nullShapeShape = Part.Shape()
        f = open(getShapePath("empty-shape.brep"))
        _nullShapeShape.importBrep(f)
        f.close()
    
    #scale the shape
    ret = _nullShapeShape
    if scale != 1.0:
        ret = _nullShapeShape.copy()
        ret.scale(scale)
        
    return ret

def loadShape(shapeID):
    global _ShapeDict
    sh = _ShapeDict.get(shapeID)
    if sh is None:
        try:
            sh = Part.Shape()
            f = open(getShapePath(shapeID + '.brep'))
            sh.importBrep(f)
            f.close()
        except Exception as err:
            FreeCAD.Console.PrintError('Failed to load standard shape "'+shapeID+'". \n' + err.message + '\n')
            sh = Part.Point() #Create at least something!
        _ShapeDict[shapeID] = sh
    return sh
        

def getPlacementMarker(scale = 1.0, markerID = None):
    '''getPlacementMarker(scale = 1.0, markerID = None): returns a placement marker shape. 
    The shape is scaled according to "scale" argument. 
    markerID sets the marker file name. If omitted, default placement marker is returned.'''
    if markerID is None:
        markerID = 'tetra-orimarker'
    sh = loadShape(markerID)
    if scale != 1.0:
        sh = sh.copy()
        sh.scale(scale)
    return sh
