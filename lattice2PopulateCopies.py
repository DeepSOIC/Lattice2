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

__title__="Lattice PopulateWithCopies object: puts a copy of an object at every placement in a lattice object (makes the array real)."
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2CompoundExplorer as LCE
import lattice2Executer

# -------------------------- document object --------------------------------------------------

def makeLatticePopulateCopies(name):
    '''makeLatticePopulateCopies(name): makes a LatticePopulateCopies object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticePopulateCopies, ViewProviderLatticePopulateCopies)

class LatticePopulateCopies(lattice2BaseFeature.LatticeFeature):
    "The Lattice PopulateCopies object"
    
    def derivedInit(self,obj):
        self.Type = "LatticePopulateCopies"
                
        obj.addProperty("App::PropertyLink","Object","Lattice PopulateCopies","Base object. Can be any generic shape, as well as another lattice object.")
                
        obj.addProperty("App::PropertyEnumeration","Referencing","Lattice PopulateCopies","Reference for array of placements.")
        obj.Referencing = ["Origin","First item", "Last item", "Use PlacementsFrom"]
        
        
        obj.addProperty("App::PropertyLink","PlacementsTo","Lattice PopulateCopies", "Placement or array of placements, containing target locations.")
        obj.addProperty("App::PropertyLink","PlacementsFrom", "Lattice PopulateCopies","Placement or array of placements to be treated as origins for PlacementsTo.")


    def derivedExecute(self,obj):
        # cache stuff
        objectShape = obj.Object.Shape
        placements = lattice2BaseFeature.getPlacementsList(obj.PlacementsTo, obj)

        outputIsLattice = lattice2BaseFeature.isObjectLattice(obj.Object)

        # Pre-collect base placement list, if base is a lattice. For speed.
        if outputIsLattice:
            objectPlms = lattice2BaseFeature.getPlacementsList(obj.Object,obj)
        
        # Precompute referencing
        plmDeref = App.Placement() #inverse placement of reference (reference is a substitute of origin)
        if obj.PlacementsFrom is not None  and  obj.Referencing != "Use PlacementsFrom":
            lattice2Executer.warning(obj,"Referencing mode is '"+obj.Referencing+"', doesn't need PlacementsFrom link to be set. The link is set, but it will be ignored.")
        if obj.Referencing == "Origin":
            pass
        elif obj.Referencing == "First item":
            plmDeref = placements[0].inverse()
        elif obj.Referencing == "Last item":
            plmDeref = placements[0].inverse()
        elif obj.Referencing == "Use PlacementsFrom":
            if obj.PlacementsFrom is None:
                raise ValueError("Referencing mode is 'Move from to', but PlacementsFrom link is not set.")
            placementsFrom = lattice2BaseFeature.getPlacementsList(obj.PlacementsFrom, obj)
            if len(placementsFrom) == 1:
                plmDeref = placementsFrom[0].inverse()
            elif len(placementsFrom) == len(placements):
                for i in range(0, len(placements)):
                    placements[i] = lattice2BaseFeature.makeMoveFromTo(placementsFrom[i],placements[i])
            else:
                latticeExecuter.warning(obj,"Lengths of arrays linked as PlacementsTo and PlacementsFrom must equal, or PlacementsFrom can be one placement. Violation: lengths are "+str(len(placements))+ " and "+str(len(placementsFrom)))
        else:
            raise ValueError("Referencing mode not implemented: "+obj.Referencing)
        
        
        # initialize output containers and loop variables
        outputShapes = [] #output list of shapes
        outputPlms = [] #list of placements
        
        # the essence
        for plm in placements:
            refdPlm = plm.multiply(plmDeref)

            if outputIsLattice:
                for objectPlm in objectPlms:
                    outputPlms.append(refdPlm.multiply(objectPlm))
            else:
                outputShape = objectShape.copy()
                outputShape.Placement = refdPlm.multiply(outputShape.Placement)
                outputShapes.append(outputShape)
            
        if outputIsLattice:
            return outputPlms
        else:
            obj.Shape = Part.makeCompound(outputShapes)
            return None

class ViewProviderLatticePopulateCopies(lattice2BaseFeature.ViewProviderLatticeFeature):

    def getIcon(self):
        if lattice2BaseFeature.isObjectLattice(self.Object):
            return getIconPath(
                {"Origin":"Lattice2_PopulateCopies_Plms_Normal.svg",
                 "First item":"Lattice2_PopulateCopies_Plms_Array.svg",
                 "Last item":"Lattice2_PopulateCopies_Plms_Array.svg",
                 "Use PlacementsFrom":"Lattice2_PopulateCopies_Plms_Move.svg",
                }[self.Object.Referencing]
                )  
        else:
            return getIconPath(
                {"Origin":"Lattice2_PopulateCopies_Normal.svg",
                 "First item":"Lattice2_PopulateCopies_Array.svg",
                 "Last item":"Lattice2_PopulateCopies_Array.svg",
                 "Use PlacementsFrom":"Lattice2_PopulateCopies_Move.svg",
                }[self.Object.Referencing]
                )  
        
    def claimChildren(self):
        children = [self.Object.Object, self.Object.PlacementsTo]
        if self.Object.Referencing == "Use PlacementsFrom":
            children.append(self.Object.PlacementsFrom)
        return children

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------



def CreateLatticePopulateCopies(name, label, shapeObj, latticeObjFrom, latticeObjTo, refmode):
    '''utility function; sharing common code for all populate-copies commands'''
    FreeCADGui.addModule("lattice2PopulateCopies")
    FreeCADGui.addModule("lattice2Executer")
    
    #fill in properties
    FreeCADGui.doCommand("f = lattice2PopulateCopies.makeLatticePopulateCopies(name='"+name+"')")
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
        FreeCAD.ActiveDocument.openTransaction("Populate with copies")
        lattice = lattices[0]
        for shape in shapes:
            CreateLatticePopulateCopies("Populate",u"Populate "+lattice.Object.Label+u" with "+shape.Object.Label,shape.Object,None,lattice.Object,refmode)
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()
    elif len(shapes) == 1 and len(lattices) > 1:
        shape = shapes[0]
        FreeCAD.ActiveDocument.openTransaction("Populate with copies")
        for lattice in lattices:
            CreateLatticePopulateCopies("Populate",u"Populate "+lattice.Object.Label+u" with "+shape.Object.Label,shape.Object,None,lattice.Object,refmode)
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()
    elif len(shapes) == 0 and len(lattices) == 2:
        shape = lattices[0]
        lattice = lattices[1]
        FreeCAD.ActiveDocument.openTransaction("Populate with copies")
        CreateLatticePopulateCopies("Populate",u"Populate "+lattice.Object.Label+u" with "+shape.Object.Label,shape.Object,None,lattice.Object,refmode)
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
        FreeCAD.ActiveDocument.openTransaction("Populate with copies")
        latticeFrom = lattices[0]
        latticeTo = lattices[1]
        for shape in shapes:
            CreateLatticePopulateCopies("Populate",u"Moved "+shape.Object.Label, shape.Object, latticeFrom.Object, latticeTo.Object,"Use PlacementsFrom")
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()
    else:
        raise SelectionError("Bad selection","Please select either:\n one or more shapes, and two placements/arrays \nor\nthree placements/arrays")


class _CommandLatticePopulateCopies_Normal:
    "Command to create LatticePopulateCopies feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PopulateCopies_Normal.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateCopies","Populate with copies"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateCopies","Populate with copies: put copies of an object at every placement in an array. Select the object(s) to be copied, and the placement/array.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Populate with copies",
                    "Populate with copies command. Places a copy of a selected object placed under selected placement.\n\n"+
                    "Please select some objects, and a placement/an array of placements. Then invoke the command.\n\n"+
                    "A copy of object will pe made and placed in local coordinate system of each placement in an array. Placement of the object is taken into account, and becomes a placement in local coordinates of a placement of the array item.")
                return
            cmdPopulate_shapes_nonFromTo("Origin")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_PopulateCopies_Normal', _CommandLatticePopulateCopies_Normal())

class _CommandLatticePopulateCopies_Array:
    "Command to create LatticePopulateCopies feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PopulateCopies_Array.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateCopies","Populate with copies: Build Array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateCopies","Populate with copies: Build Array: poplate placements with copies so that the array passes through original shape. Select the object(s) to be copied, and the placement/array.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Populate with copies: Build Array",
                    "Populate with copies: Build Array command. Creates an array of shapes.\n\n"+
                    "Please select some objects, and the array of placements. Then invoke the command. Object can also be a placement/array.\n\n"+
                    "Compared to plain 'Populate With copies' command, the placements are treated as being relative to the first placement in the array. As a result, the array built always includes the original object as-is.")
                return
            cmdPopulate_shapes_nonFromTo("First item")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_PopulateCopies_Array', _CommandLatticePopulateCopies_Array())

class _CommandLatticePopulateCopies_Move:
    "Command to create LatticePopulateCopies feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PopulateCopies.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateCopies","Moved object"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_PopulateCopies","Moved object: move object from one placement to another placement. Select the object, placement to move from, and placement to move to. Arrays of placements are accepted.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Moved Object",
                    "Moved Object command. Creates a moved copy of a shape.\n\n"+
                    "The shape is moved from one placement to another placement. Please select some shapes, then placement to move from, and placement to move to (order matters).\n"+
                    "Placement 'to' can be an array of placements; the array of objects will be created in this case. If 'to' is an array, 'from' can be either a single placement, or an array of matching length.\n\n"+
                    "Object can itself be an array of placements.")
                return
            cmdPopulate_shapes_FromTo()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_PopulateCopies_Move', _CommandLatticePopulateCopies_Move())

class _CommandLatticePopulateCopiesGroup:
    def GetCommands(self):
        return ("Lattice2_PopulateCopies_Normal","Lattice2_PopulateCopies_Array","Lattice2_PopulateCopies_Move") 

    def GetDefaultCommand(self): # return the index of the tuple of the default command. 
        return 0

    def GetResources(self):
        return { 'MenuText': 'Populate with copies:', 
                 'ToolTip': 'Populate with copies: put a copy of an object at every placement in an array of placements.'}
        
    def IsActive(self): # optional
        return True
        
FreeCADGui.addCommand('Lattice2_PopulateCopiesGroupCommand',_CommandLatticePopulateCopiesGroup())

exportedCommands = ['Lattice2_PopulateCopiesGroupCommand']

# -------------------------- /Gui command --------------------------------------------------

