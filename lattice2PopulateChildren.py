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

__title__="Lattice PopulateWithChildren object: puts a copy of an object at every placement in a lattice object (makes the array real)."
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2CompoundExplorer as LCE
import lattice2Executer
from lattice2PopulateCopies import DereferenceArray
import lattice2ShapeCopy as ShapeCopy

# -------------------------- document object --------------------------------------------------

def makeLatticePopulateChildren(name):
    '''makeLatticePopulateChildren(name): makes a LatticePopulateChildren object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticePopulateChildren, ViewProviderLatticePopulateChildren)

class LatticePopulateChildren(lattice2BaseFeature.LatticeFeature):
    "The Lattice PopulateChildren object"
    
    def derivedInit(self,obj):
        self.Type = "LatticePopulateChildren"
                
        obj.addProperty("App::PropertyLink","Object","Lattice PopulateChildren","Compound containing objects to be copied.")
        
        obj.addProperty("App::PropertyEnumeration","ObjectTraversal","Lattice PopulateChildren","Sets whether first-level compound is traversed, or the whole compounding tree.")
        obj.ObjectTraversal = ["Direct children only","Recursive"]
        obj.ObjectTraversal = "Direct children only"
        
        obj.addProperty("App::PropertyBool","LoopObjectSequence","Lattice PopulateChildren","If true, children of Object will be traversed in a loop if there are more placements than children. Otherwise, extra placements will be dropped.")
                
        obj.addProperty("App::PropertyEnumeration","Referencing","Lattice PopulateChildren","Reference for array of placements.")
        obj.Referencing = ["Origin","First item", "Last item", "Use PlacementsFrom"]
        
        
        obj.addProperty("App::PropertyLink","PlacementsTo","Lattice PopulateChildren", "Placement or array of placements, containing target locations.")
        obj.addProperty("App::PropertyLink","PlacementsFrom", "Lattice PopulateChildren","Placement or array of placements to be treated as origins for PlacementsTo.")
        
        self.initNewProperties(obj)

    def initNewProperties(self, obj):
        # properties that can be missing on objects made with earlier version of Lattice2
        if self.assureProperty(obj, "App::PropertyEnumeration","Copying", ShapeCopy.copy_types, "Lattice PopulateChildren", "Sets, what method to use for copying shapes."):
            self.Copying = ShapeCopy.copy_types[0]

    def derivedExecute(self,obj):
        
        self.initNewProperties(obj)
        
        outputIsLattice = lattice2BaseFeature.isObjectLattice(obj.Object)
        
        if not lattice2BaseFeature.isObjectLattice(obj.Object):
            if obj.ObjectTraversal == "Direct children only":
                objectShapes = obj.Object.Shape.childShapes()
                if obj.Object.Shape.ShapeType != "Compound":
                    lattice2Executer.warning(obj,"shape supplied as object is not a compound. It is going to be downgraded one level down (e.g, if it is a wire, the edges are going to be enumerated as children).")
            elif obj.ObjectTraversal == "Recursive":
                objectShapes = LCE.AllLeaves(obj.Object.Shape)
            else:
                raise ValueError("Traversal mode not implemented: "+obj.ObjectTraversal)
        else:
            objectPlms = lattice2BaseFeature.getPlacementsList(obj.Object, obj)
        placements = lattice2BaseFeature.getPlacementsList(obj.PlacementsTo, obj)

        
        # Precompute referencing
        placements = DereferenceArray(obj, placements, obj.PlacementsFrom, obj.Referencing)
                
        # initialize output containers and loop variables
        outputShapes = [] #output list of shapes
        outputPlms = [] #list of placements
        iChild = 0
        numChildren = len(objectPlms) if outputIsLattice else len(objectShapes) 
        copy_method_index = ShapeCopy.getCopyTypeIndex(obj.Copying)
        
        # the essence
        for iPlm in range(len(placements)):
            if iChild == numChildren:
                if obj.LoopObjectSequence:
                    iChild = 0
                else:
                    break
            
            plm = placements[iPlm]
             
            if outputIsLattice:
                objectPlm = objectPlms[iChild]
                outputPlms.append(plm.multiply(objectPlm))
            else:
                outputShape = ShapeCopy.copyShape(objectShapes[iChild], copy_method_index, plm)
                # outputShape.Placement = plm.multiply(outputShape.Placement) #now done by shape copy routine
                outputShapes.append(outputShape)
            
            iChild += 1
            
        if len(placements) > numChildren and not obj.LoopObjectSequence:
            lattice2Executer.warning(obj,"There are fewer children to populate, than placements to be populated (%1, %2). Extra placements will be dropped.".replace("%1", str(numChildren)).replace("%2",str(len(placements))))
            
        if len(placements) < numChildren:
            lattice2Executer.warning(obj,"There are more children to populate, than placements to be populated (%1, %2). Extra children will be dropped.".replace("%1", str(numChildren)).replace("%2",str(len(placements))))
            
        if outputIsLattice:
            return outputPlms
        else:
            obj.Shape = Part.makeCompound(outputShapes)
            return None

class ViewProviderLatticePopulateChildren(lattice2BaseFeature.ViewProviderLatticeFeature):

    def getIcon(self):
        if lattice2BaseFeature.isObjectLattice(self.Object):
            return getIconPath(
                {"Origin":"Lattice2_PopulateChildren_Plms_Normal.svg",
                 "First item":"Lattice2_PopulateChildren_Plms_Array.svg",
                 "Last item":"Lattice2_PopulateChildren_Plms_Array.svg",
                 "Use PlacementsFrom":"Lattice2_PopulateChildren_Plms_Move.svg",
                }[self.Object.Referencing]
                )  
        else:
            return getIconPath(
                {"Origin":"Lattice2_PopulateChildren_Normal.svg",
                 "First item":"Lattice2_PopulateChildren_Array.svg",
                 "Last item":"Lattice2_PopulateChildren_Array.svg",
                 "Use PlacementsFrom":"Lattice2_PopulateChildren_Move.svg",
                }[self.Object.Referencing]
                )  
        
    def claimChildren(self):
        children = [self.Object.Object, self.Object.PlacementsTo]
        if self.Object.Referencing == "Use PlacementsFrom":
            children.append(self.Object.PlacementsFrom)
        return children

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------



def CreateLatticePopulateChildren(name, label, shapeObj, latticeObjFrom, latticeObjTo, refmode):
    '''utility function; sharing common code for all populate-Children commands'''
    FreeCADGui.addModule("lattice2PopulateChildren")
    FreeCADGui.addModule("lattice2Executer")
    
    #fill in properties
    FreeCADGui.doCommand("f = lattice2PopulateChildren.makeLatticePopulateChildren(name='"+name+"')")
    FreeCADGui.doCommand("f.Object = App.ActiveDocument."+shapeObj.Name)
    FreeCADGui.doCommand("f.PlacementsTo = App.ActiveDocument."+latticeObjTo.Name)
    if latticeObjFrom is not None:
        FreeCADGui.doCommand("f.PlacementsFrom = App.ActiveDocument."+latticeObjFrom.Name)        
    FreeCADGui.doCommand("f.Referencing = "+repr(refmode))
    FreeCADGui.doCommand("f.Label = " + repr(label))                         
    
    #execute
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    
    #hide something
    if (refmode != "Origin" and refmode != "Use PlacementsFrom") or lattice2BaseFeature.isObjectLattice(shapeObj):
        FreeCADGui.doCommand("f.Object.ViewObject.hide()")
    if lattice2BaseFeature.isObjectLattice(shapeObj):
        FreeCADGui.doCommand("f.PlacementsTo.ViewObject.hide()")
        if latticeObjFrom is not None:
            FreeCADGui.doCommand("f.PlacementsFrom.ViewObject.hide()")
        
    #finalize
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    FreeCADGui.doCommand("f = None")

def cmdPopulate_shapes_nonFromTo(refmode):
    sel = FreeCADGui.Selection.getSelectionEx()
    (lattices, shapes) = lattice2BaseFeature.splitSelection(sel)
    if len(shapes) > 0 and len(lattices) == 1:
        FreeCAD.ActiveDocument.openTransaction("Populate with Children")
        lattice = lattices[0]
        for shape in shapes:
            CreateLatticePopulateChildren("Populate",u"Populate "+lattice.Object.Label+u" with "+shape.Object.Label,shape.Object,None,lattice.Object,refmode)
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()
    elif len(shapes) == 1 and len(lattices) > 1:
        shape = shapes[0]
        FreeCAD.ActiveDocument.openTransaction("Populate with Children")
        for lattice in lattices:
            CreateLatticePopulateChildren("Populate",u"Populate "+lattice.Object.Label+u" with "+shape.Object.Label,shape.Object,None,lattice.Object,refmode)
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()
    elif len(shapes) == 0 and len(lattices) == 2:
        shape = lattices[0]
        lattice = lattices[1]
        FreeCAD.ActiveDocument.openTransaction("Populate with Children")
        CreateLatticePopulateChildren("Populate",u"Populate "+lattice.Object.Label+u" with "+shape.Object.Label,shape.Object,None,lattice.Object,refmode)
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()        
    else:
        raise SelectionError("Bad selection","Please select some shapes and some arrays, first. You can select multiple shapes and one array, or multiple arrays and one shape.")
    
def cmdPopulate_shapes_FromTo():
    sel = FreeCADGui.Selection.getSelectionEx()
    (lattices, shapes) = lattice2BaseFeature.splitSelection(sel)
    if len(shapes) == 0 and len(sel) >= 3:
        shapes = sel[:-2]
        lattices = sel[-2:]
    if len(shapes) > 0 and len(lattices) == 2:
        FreeCAD.ActiveDocument.openTransaction("Populate with Children")
        latticeFrom = lattices[0]
        latticeTo = lattices[1]
        for shape in shapes:
            CreateLatticePopulateChildren("Populate",u"Moved "+shape.Object.Label, shape.Object, latticeFrom.Object, latticeTo.Object,"Use PlacementsFrom")
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()
    else:
        raise SelectionError("Bad selection","Please select either:\n one or more shapes, and two placements/arrays \nor\nthree placements/arrays")


class _CommandLatticePopulateChildren_Normal:
    "Command to create LatticePopulateChildren feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PopulateChildren_Normal.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateChildren","Populate with Children"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateChildren","Populate with Children: distribute children of an object to placements in an array. Select a compound to take children from, and a placement/array.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Populate with Children",
                    "Populate with Children command. Places each child of a selected object at different placements of an array.\n\n"+
                    "Please select an object that is a compound, and an array of placements. Then invoke the command. It is also allowed to use another array of placements instead of compound.\n\n"+
                    "A new compound will be created, with child shapes placed by corresponding placements of the array.")
                return
            cmdPopulate_shapes_nonFromTo("Origin")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_PopulateChildren_Normal', _CommandLatticePopulateChildren_Normal())

class _CommandLatticePopulateChildren_Array:
    "Command to create LatticePopulateChildren feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PopulateChildren_Array.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateChildren","Populate with Children: Build Array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateChildren","Populate with Children: Build Array: poplate placements with children so that the first child is not moved. Select a compound, and a placement/array.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Populate with Children: Build Array",
                    "Populate with Children: Build Array command. Creates an array from children packed into a compound.\n\n"+
                    "Please select a compound, and an array of placements. Then invoke the command. It is also allowed to use another array of placements instead of compound.\n\n"+
                    "Compared to plain 'Populate With Children' command, the placements are treated as being relative to the first placement in the array. As a result, the first child always remains wher it was.")
                return
            cmdPopulate_shapes_nonFromTo("First item")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_PopulateChildren_Array', _CommandLatticePopulateChildren_Array())

class _CommandLatticePopulateChildren_Move:
    "Command to create LatticePopulateChildren feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PopulateChildren_Move.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateChildren","Move children"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateChildren","Move children: move children of compound from one placement to another placement. Select a compound, a placement/array to move from, and an array to move to.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Move children",
                    "Moved Children command. Creates a compound from another compound, by moving its children.\n\n"+
                    "Each child is moved from one placement to another placement. Please select a compound, then a placement/array to move from, and  an array of placements to move to (order matters).\n"+
                    "An array of placements can be used insead of a compound.")
                return
            cmdPopulate_shapes_FromTo()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_PopulateChildren_Move', _CommandLatticePopulateChildren_Move())

class _CommandLatticePopulateChildrenGroup:
    def GetCommands(self):
        return ("Lattice2_PopulateChildren_Normal","Lattice2_PopulateChildren_Array","Lattice2_PopulateChildren_Move") 

    def GetDefaultCommand(self): # return the index of the tuple of the default command. 
        return 0

    def GetResources(self):
        return { 'MenuText': 'Populate with Children:', 
                 'ToolTip': 'Populate with Children: put children of compound at corresponding placements in an array of placements.'}
        
    def IsActive(self): # optional
        return True
        
FreeCADGui.addCommand('Lattice2_PopulateChildrenGroupCommand',_CommandLatticePopulateChildrenGroup())

exportedCommands = ['Lattice2_PopulateChildrenGroupCommand']

# -------------------------- /Gui command --------------------------------------------------

