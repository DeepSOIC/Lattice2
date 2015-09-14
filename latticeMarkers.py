import Part, os

__title__="latticeMarkers module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Module for loading marker shapes for Lattice workbench"

_nullShapeShape = 0

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
