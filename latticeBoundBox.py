from latticeCommon import *


__title__="BoundingBox module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""



# -------------------------- common stuff --------------------------------------------------

def boundBox2RealBox(bb):
    return Part.makeBox(bb.XLength,bb.YLength,bb.ZLength,FreeCAD.Vector(bb.XMin, bb.YMin, bb.ZMin),FreeCAD.Vector(0,0,1))
    
def getPrecisionBoundBox(shape):
    # First, get imprecise bound box. Since the imprecise one 
    # is typically smaller than the shape, we should enlarge 
    # it to ensure it does not touch the shape.
    bb = shape.BoundBox 
    bb.enlarge(2) 
    
    # Make a boundingbox shape and compute distances from faces
    # of this enlarged bounding box to the actual shape. Shrink
    # the boundbox by the distances.
    bbshape = boundBox2RealBox(bb)
    #FIXME: it may be a good idea to not use hard-coded face indexes
    bb.XMin = bb.XMin + shape.distToShape(bbshape.Faces[0])[0]
    bb.YMin = bb.YMin + shape.distToShape(bbshape.Faces[2])[0]
    bb.ZMin = bb.ZMin + shape.distToShape(bbshape.Faces[4])[0]
    bb.XMax = bb.XMax - shape.distToShape(bbshape.Faces[1])[0]
    bb.YMax = bb.YMax - shape.distToShape(bbshape.Faces[3])[0]
    bb.ZMax = bb.ZMax - shape.distToShape(bbshape.Faces[5])[0]
    return bb


def makeBoundBox(name):
    '''makeBoundBox(name): makes a BoundBox object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _BoundBox(obj)
    _ViewProviderBoundBox(obj.ViewObject)
    return obj

class _BoundBox:
    "The BoundBox object"
    def __init__(self,obj):
        self.Type = "BoundBox"
        obj.addProperty("App::PropertyLink","Base","BoundBox","Object to make boundingbox")
        obj.addProperty("App::PropertyBool","Precision","BoundBox","Use precise alorithm (slower).")
        obj.Precision = True
        obj.Proxy = self
        

    def execute(self,obj):
        rst = None
        obj.Shape = boundBox2RealBox(getPrecisionBoundBox(obj.Base.Shape))
        return
        
        
class _ViewProviderBoundBox:
    "A View Provider for the BoundBox object"

    def __init__(self,vobj):
        vobj.Proxy = self
        vobj.DisplayMode = "Wireframe"
       
    def getIcon(self):
        return getIconPath("Lattice_BoundBox.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

def CreateBoundBox(name):
    FreeCAD.ActiveDocument.openTransaction("Create BoundBox")
    FreeCADGui.addModule("latticeBoundBox")
    FreeCADGui.doCommand("f = latticeBoundBox.makeBoundBox(name='"+name+"')")
    FreeCADGui.doCommand("f.Base = FreeCADGui.Selection.getSelection()[0]")
    FreeCADGui.doCommand("f.Proxy.execute(f)")
    FreeCADGui.doCommand("f.purgeTouched()")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandBoundBox:
    "Command to create BoundBox feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_BoundBox.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_BoundBox","Parametric bounding box"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_BoundBox","Make a box that precisely fits the object")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            CreateBoundBox(name = "BoundBox")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(_translate("Lattice_BoundBox", "Select a shape to make a bounding box for, first!", None))
            mb.setWindowTitle(_translate("Lattice_BoundBox","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_BoundBox', _CommandBoundBox())

exportedCommands = ['Lattice_BoundBox']

# -------------------------- /Gui command --------------------------------------------------
