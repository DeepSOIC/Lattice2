#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Victor Titov (DeepSOIC)                          *
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

__title__="ShapeCopy module for Lattice2"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Utility methods to copy shapes"

import FreeCAD
import Part

def shallowCopy(shape, extra_placement = None):
    """shallowCopy(shape, extra_placement = None): creates a shallow copy of a shape. The 
    copy will match by isSame/isEqual/isPartner tests, but will have an independent placement."""
    
    copiers = {
      "Vertex": lambda sh: sh.Vertexes[0],
      "Edge": lambda sh: sh.Edges[0],
      "Wire": lambda sh: sh.Wires[0],
      "Face": lambda sh: sh.Faces[0],
      "Shell": lambda sh: sh.Shells[0],
      "Solid": lambda sh: sh.Solids[0],
      "CompSolid": lambda sh: sh.CompSolids[0],
      "Compound": lambda sh: sh.Compounds[0],
      }
    copier = copiers.get(shape.ShapeType)
    if copier is None:
        copier = lambda sh: sh.copy()
        FreeCAD.Console.PrintWarning("Lattice2: shallowCopy: unexpected shape type '{typ}'. Using deep copy instead.\n".format(typ= shape.ShapeType))
    ret = copier(shape)
    if extra_placement is not None:
        if hasattr(extra_placement, 'toMatrix'):
            ret.Placement = extra_placement.multiply(ret.Placement)
        elif extra_placement.determinant() - 1.0 < 1e-7:
            ret.transformShape(extra_placement)
        else:
            raise NonPlacementMatrixError("Matrix supplied to shallowCopy must be unitary.")
    return ret
    
def deepCopy(shape, extra_placement = None):
    """deepCopy(shape, extra_placement = None): Copies all subshapes. The copy will not match by isSame/isEqual/
    isPartner tests."""
    
    if extra_placement is not None:
        if hasattr(extra_placement, 'toMatrix'):
            ret = shape.copy()
            ret.Placement = extra_placement.multiply(ret.Placement)
        else:
            ret = shallowCopy(shape)
            ret.transformShape(extra_placement, True)
    return ret    
    
def transformCopy(shape, extra_placement = None):
    """transformCopy(shape, extra_placement = None): creates a deep copy shape with shape's placement applied to 
    the subelements (the placement of returned shape is zero)."""
    
    if extra_placement is None:
        extra_placement = FreeCAD.Placement()
    if hasattr(extra_placement, 'toMatrix'):
        extra_placement = extra_placement.toMatrix()
    ret = shape.copy()
    if ret.ShapeType == "Vertex":
        # oddly, on Vertex, transformShape behaves strangely. So we'll create a new vertex instead.
        ret = Part.Vertex(extra_placement.multiply(ret.Point))
    else:
        splm = ret.Matrix
        ret.Matrix = FreeCAD.Base.Matrix()
        ret.transformShape(extra_placement.multiply(splm), True)
    return ret

    
copy_types = ["Shallow copy", "Deep copy", "Transformed deep copy"]
copy_functions = [shallowCopy, deepCopy, transformCopy]

def getCopyTypeIndex(copy_type_string):
    return copy_types.index(str(copy_type_string))

def copyShape(shape, copy_type_index, extra_placement = None):
    """copyShape(shape, copy_type_index, extra_placement = None): copies a shape (or creates 
    a moved copy of shape, if extra_placement is given). copy_type_index should be obtained 
    from string by getCopyTypeIndex() function."""
    
    global copy_functions
    return copy_functions[copy_type_index](shape, extra_placement)    

def transformShape(shape, extra_placement):
    """transformShape(shape, extra_placement): returns shape with  extra_placement applied to it.
    extra_placement must be either a Placement, or a Matrix. Matrix can be mirroring.
    shallowCopy is done if Placement or a placement matrix. transformCopy is done if the matrix features mirroring."""

    if hasattr(extra_placement, 'toMatrix'):
        # extra_placement is a Placement
        return shallowCopy(shape, extra_placement)
    else:
        # extra_placement is a Matrix
        return transformCopy(shape, extra_placement)
    

class NonPlacementMatrixError(ValueError):
    pass
