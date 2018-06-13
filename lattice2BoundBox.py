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


__title__="BoundingBox module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""


from lattice2Common import *
import lattice2BaseFeature as LBF
import lattice2Executer as Executer
import lattice2CompoundExplorer as LCE

import FreeCAD as App

# -------------------------- common stuff --------------------------------------------------

def boundBox2RealBox(bb):
    base = FreeCAD.Vector(bb.XMin, bb.YMin, bb.ZMin)
    OX = FreeCAD.Vector(1, 0, 0)
    OY = FreeCAD.Vector(0, 1, 0)
    OZ = FreeCAD.Vector(0, 0, 1)
    if bb.XLength > DistConfusion and bb.YLength > DistConfusion and bb.ZLength > DistConfusion :
        return Part.makeBox(bb.XLength,bb.YLength,bb.ZLength, base, OZ)
    elif bb.XLength > DistConfusion and bb.YLength > DistConfusion:
        return Part.makePlane(bb.XLength, bb.YLength, base, OZ, OX)
    elif bb.XLength > DistConfusion and bb.ZLength > DistConfusion :
        return Part.makePlane(bb.XLength, bb.ZLength, base, OY*-1, OX)
    elif bb.YLength > DistConfusion and bb.ZLength > DistConfusion :
        return Part.makePlane(bb.YLength, bb.ZLength, base, OX, OY)
    elif bb.XLength > DistConfusion:
        return Part.makeLine(base, base + OX*bb.XLength)
    elif bb.YLength > DistConfusion:
        return Part.makeLine(base, base + OY*bb.YLength)
    elif bb.ZLength > DistConfusion:
        return Part.makeLine(base, base + OZ*bb.ZLength)
    else:
        raise ValueError("Bounding box is zero")
        
def scaledBoundBox(bb, scale):
    bb2 = FreeCAD.BoundBox(bb)
    cnt = bb.Center
    bb2.XMin = (bb.XMin - cnt.x)*scale + cnt.x
    bb2.YMin = (bb.YMin - cnt.y)*scale + cnt.y
    bb2.ZMin = (bb.ZMin - cnt.z)*scale + cnt.z
    bb2.XMax = (bb.XMax - cnt.x)*scale + cnt.x
    bb2.YMax = (bb.YMax - cnt.y)*scale + cnt.y
    bb2.ZMax = (bb.ZMax - cnt.z)*scale + cnt.z
    return bb2
    
def getPrecisionBoundBox(shape):
    # First, we need a box that for sure contains the object.
    # We use imprecise bound box, scaled up twice. The scaling
    # is required, because the imprecise bound box is often a
    # bit smaller than the shape.
    bb = scaledBoundBox(shape.BoundBox, 2.0)
    # Make sure bound box is not collapsed in any direction, 
    # to make sure boundBox2RealBox returns a box, not plane
    # or line
    if bb.XLength < DistConfusion or bb.YLength < DistConfusion or bb.ZLength < DistConfusion:
        bb.enlarge(1.0)
    
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
    obj = App.ActiveDocument.addObject("Part::FeaturePython",name)
    _BoundBox(obj)
    if FreeCAD.GuiUp:        
        _ViewProviderBoundBox(obj.ViewObject)
    return obj

class _BoundBox:
    "The BoundBox object"
    def __init__(self,obj):
        self.Type = "BoundBox"
        obj.addProperty("App::PropertyLink","ShapeLink","BoundBox","Object to make a bounding box for")
        
        obj.addProperty("App::PropertyEnumeration","CompoundTraversal","BoundBox","Choose whether to make boundboxes for each child, or use compound overall/")
        obj.CompoundTraversal = ["Use as a whole","Direct children only","Recursive"]
        obj.CompoundTraversal = "Use as a whole"

        obj.addProperty("App::PropertyBool","Precision","BoundBox","Use precise alorithm (slower).")
        obj.Precision = True
        
        obj.addProperty("App::PropertyEnumeration","OrientMode","BoundBox","Choose the orientation of bounding boxes to be made.")
        obj.OrientMode = ["global","local of compound","local of child","use OrientLink"]
        
        obj.addProperty("App::PropertyLink","OrientLink","BoundBox","Link to placement/array to take orientations for bounding boxes")
        
        obj.addProperty("App::PropertyFloat","ScaleFactor","BoundBox","After constructing the bounding box, enlarge/shrink it with respect to center by the scale factor.")
        obj.ScaleFactor = 1.0
        
        obj.addProperty("App::PropertyDistance","Padding","BoundBox","After constructing the bounding box, enlarge/shrink it by specified amount (use negative for shrinking).")
        
        # read-only properties:
        prop = "Size"
        obj.addProperty("App::PropertyVector",prop,"Info","Diagonal vector of bounding box")
        obj.setEditorMode(prop, 1) # set read-only
        
        prop = "Center"
        obj.addProperty("App::PropertyVector",prop,"Info","Center of bounding box")
        obj.setEditorMode(prop, 1) # set read-only
        
        obj.Proxy = self
        

    def execute(self,obj):
        base = screen(obj.ShapeLink).Shape
        if obj.CompoundTraversal == "Use as a whole":
            baseChildren = [base]
        else:
            if base.ShapeType != 'Compound':
                base = Part.makeCompound([base])
            if obj.CompoundTraversal == "Recursive":
                baseChildren = LCE.AllLeaves(base)
            else:
                baseChildren = base.childShapes()
        
        N = len(baseChildren)
        
        orients = []
        if obj.OrientMode == "global":
            orients = [App.Placement()]*N
        elif obj.OrientMode == "local of compound":
            orients = [screen(obj.ShapeLink).Placement]*N
        elif obj.OrientMode == "local of child":
            orients = [child.Placement for child in baseChildren]
        elif obj.OrientMode == "use OrientLink":
            orients = LBF.getPlacementsList(screen(obj.OrientLink), context= obj)
            if len(orients) == N:
                pass
            elif len(orients)>N:
                Executer.warning(obj, "Array of placements linked in OrientLink has more placements ("+str(len(orients))+") than bounding boxes to be constructed ("+str(len(baseChildren))+"). Extra placements will be dropped.")
            elif len(orients)==1:
                orients = [orients[0]]*N
            else:
                raise ValueError(obj.Name+": Array of placements linked in OrientLink has not enough placements ("+str(len(orients))+") than bounding boxes to be constructed ("+str(len(baseChildren))+").")
        else:
            raise ValueError(obj.Name+": OrientMode "+obj.OrientMode+" not implemented =(")
        
        # mark placements with no rotation
        for i in range(N):
            Q = orients[i].Rotation.Q
            # Quaternions for zero rotation are either (0,0,0,1) or (0,0,0,-1). For non-zero
            # rotations, some of first three values will be nonzero, and fourth value will 
            # not be equal to 1. While it's enough to compare absolute value of fourth value
            # to 1, precision is seriously lost in such comparison, so we are checking if 
            # fisrt three values are zero instead.
            if abs(Q[0])+abs(Q[1])+abs(Q[2]) < ParaConfusion:
                orients[i] = None
        
        from lattice2ShapeCopy import shallowCopy
        boxes_shapes = []
        for i in range(N):
            child = baseChildren[i]
            if orients[i] is not None:
                child = shallowCopy(child)
                child.Placement = orients[i].inverse().multiply(child.Placement)

            if obj.Precision:
                bb = getPrecisionBoundBox(child)
            else:
                bb = child.BoundBox
                
            bb = scaledBoundBox(bb, obj.ScaleFactor)
            bb.enlarge(obj.Padding)

            bb_shape = boundBox2RealBox(bb)
            if orients[i] is not None:
                bb_shape.transformShape(orients[i].toMatrix(), True)
            boxes_shapes.append(bb_shape)
            
        #Fill in read-only properties
        if N == 1:
            obj.Size = App.Vector(bb.XLength,bb.YLength,bb.ZLength)
        
            cnt = bb.Center
            if orients[0] is not None:
                cnt = orients[0].multVec(cnt)
            obj.Center = cnt
        else:
            obj.Size = App.Vector()
            obj.Center = App.Vector()
        
        if obj.CompoundTraversal == "Use as a whole":
            assert(N==1)
            obj.Shape = boxes_shapes[0]
        else:
            obj.Shape = Part.makeCompound(boxes_shapes)

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
        
        
class _ViewProviderBoundBox:
    "A View Provider for the BoundBox object"

    def __init__(self,vobj):
        vobj.Proxy = self
        vobj.DisplayMode = "Wireframe"
       
    def getIcon(self):
        if self.Object.CompoundTraversal == "Use as a whole":
            return getIconPath("Lattice2_BoundBox.svg")
        else:
            return getIconPath("Lattice2_BoundBox_Compound.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

def CreateBoundBox(ShapeLink, 
                   CompoundTraversal = "Use as a whole", 
                   Precision = True, 
                   OrientMode = "global",
                   OrientLink = None):
    
    FreeCADGui.addModule("lattice2BoundBox")
    FreeCADGui.addModule("lattice2Executer")

    FreeCADGui.doCommand("f = lattice2BoundBox.makeBoundBox(name= 'BoundBox')")

    FreeCADGui.doCommand("f.ShapeLink = App.ActiveDocument."+ShapeLink.Name)
    if CompoundTraversal == "Use as a whole":
        Label = u"BoundBox of "+ShapeLink.Label
    else:
        Label = u"BoundBoxes of "+ShapeLink.Label
    FreeCADGui.doCommand("f.Label = "+repr(Label))    
    FreeCADGui.doCommand("f.CompoundTraversal = "+repr(CompoundTraversal))    
    FreeCADGui.doCommand("f.Precision = "+repr(Precision))    
    FreeCADGui.doCommand("f.OrientMode = "+repr(OrientMode))    
    if OrientLink is not None:
        FreeCADGui.doCommand("f.OrientLink = App.ActiveDocument."+OrientLink.Name)

    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    FreeCADGui.doCommand("f = None")

def cmdSingleBoundBox():
    sel = FreeCADGui.Selection.getSelectionEx()
    (lattices, shapes) = LBF.splitSelection(sel)
    if len(shapes) > 0 and len(lattices) == 0:
        FreeCAD.ActiveDocument.openTransaction("Make BoundBox")
        for shape in shapes:
            CreateBoundBox(shape.Object)
        FreeCAD.ActiveDocument.commitTransaction()
    elif len(shapes) == 1 and len(lattices) == 1:
        FreeCAD.ActiveDocument.openTransaction("Make BoundBox")
        CreateBoundBox(shapes[0].Object, OrientMode= "use OrientLink", OrientLink= lattices[0].Object)
        FreeCAD.ActiveDocument.commitTransaction()
    else:
        raise SelectionError("Bad selection", 
                             "Please select some shapes to make bounding boxes of, or a shape and a placement to make a rotated bounding box. You have selected {shapescount} objects and {latticescount} placements/arrays."
                                 .format(  shapescount= str(len(shapes)), 
                                           latticescount= str(len(lattices))  )
                            )
    deselect(sel)

def cmdMultiBoundBox():
    sel = FreeCADGui.Selection.getSelectionEx()
    (lattices, shapes) = LBF.splitSelection(sel)
    if len(shapes) > 0 and len(lattices) == 0:
        FreeCAD.ActiveDocument.openTransaction("Make BoundBox")
        for shape in shapes:
            CreateBoundBox(shape.Object, CompoundTraversal= "Direct children only")
        FreeCAD.ActiveDocument.commitTransaction()
    elif len(shapes) == 1 and len(lattices) == 1:
        FreeCAD.ActiveDocument.openTransaction("Make BoundBox")
        CreateBoundBox(shapes[0].Object, 
                       CompoundTraversal= "Direct children only",
                       OrientMode= "use OrientLink", 
                       OrientLink= lattices[0].Object)
        FreeCAD.ActiveDocument.commitTransaction()
    else:
        raise SelectionError("Bad selection", 
                             "Please select some shapes to make bounding boxes of, or a shape and a placement to make a rotated bounding box. You have selected {shapescount} objects and {latticescount} placements/arrays."
                                 .format(  shapescount= str(len(shapes)), 
                                           latticescount= str(len(lattices))  )
                            )
    deselect(sel)


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandBoundBoxSingle:
    "Command to create BoundBox feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_BoundBox.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_BoundBox","Bounding Box: whole"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_BoundBox","Bounding Box: whole: make a box that precisely fits the whole object")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Bounding Box",
                    "'Bounding Box: whole' command. Makes a box that precisely fits the whole object.\n\n"+
                    "Please select an object, then invoke the command. If you also preselect a placement, the bounding box will be computed in local space of that placement.")
                return
            cmdSingleBoundBox()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_BoundBox_Single', _CommandBoundBoxSingle())

class _CommandBoundBoxMulti:
    "Command to create BoundBox feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_BoundBox_Compound.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_BoundBox","Bounding Box: children"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_BoundBox","Bounding Box: children: make bounding boxes around each child of a compound.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Bounding boxes of children",
                    "'Bounding Box: children' command. Makes a box around each child of a compound.\n\n"+
                    "Please select a compound, then invoke the command. If you also preselect a placement/array of placements, bounding boxes will be constructed in local spaces of corresponding placements.")
                return
            cmdMultiBoundBox()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_BoundBox_Compound', _CommandBoundBoxMulti())

class _CommandBoundBoxGroup:
    def GetCommands(self):
        return ("Lattice2_BoundBox_Single","Lattice2_BoundBox_Compound") 

    def GetDefaultCommand(self): # return the index of the tuple of the default command. 
        return 0

    def GetResources(self):
        return { 'MenuText': 'Bounding Box:', 
                 'ToolTip': 'Bounding Box: make a box that precisely fits a shape.'}
        
    def IsActive(self): # optional
        return activeBody() is None

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_BoundBoxGroupCommand',_CommandBoundBoxGroup())


exportedCommands = ['Lattice2_BoundBoxGroupCommand']

# -------------------------- /Gui command --------------------------------------------------
