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
import lattice2ShapeCopy as ShapeCopy

# ---------------------------shared code--------------------------------------

REF_MODES = ['Origin', 'First item', 'Last item', 'Use PlacementsFrom', 'Array\'s reference']

def DereferenceArray(obj, lnkTo, lnkFrom, refmode):
    '''common implementation of treatment Referencing property. Returns a list of placements to use directly.
    obj - feature being executed
    lnkTo - the array of target placements (documentobject).
    lnkFrom - object linked as a lattice of 'from' placements. Can be None, if mode is not 'Use PlacemenetsFrom'
    refmode - a string - enum property item'''
    placements = lattice2BaseFeature.getPlacementsList(lnkTo, obj)    
    plmDeref = App.Placement() #inverse placement of reference (reference is a substitute of origin)
    if lnkFrom is not None  and  refmode != "Use PlacementsFrom":
        lattice2Executer.warning(obj,"Referencing mode is '"+refmode+"', doesn't need PlacementsFrom link to be set. The link is set, but it will be ignored.")
    if refmode == "Origin":
        return placements
    elif refmode == "First item":
        plmDeref = placements[0].inverse()
    elif refmode == "Last item":
        plmDeref = placements[-1].inverse()
    elif refmode == "Use PlacementsFrom":
        if lnkFrom is None:
            raise ValueError("Referencing mode is 'Move from to', but PlacementsFrom link is not set.")
        placementsFrom = lattice2BaseFeature.getPlacementsList(lnkFrom, obj)
        if len(placementsFrom) == 1:
            plmDeref = placementsFrom[0].inverse()
        elif len(placementsFrom) == len(placements):
            return [lattice2BaseFeature.makeMoveFromTo(placementsFrom[i], placements[i]) for i in range(0, len(placements))]
        else:
            lattice2Executer.warning(obj,"Lengths of arrays linked as PlacementsTo and PlacementsFrom must equal, or PlacementsFrom can be one placement. Violation: lengths are "+str(len(placements))+ " and "+str(len(placementsFrom)))
    elif refmode == 'Array\'s reference':
        plmRef = lattice2BaseFeature.getReferencePlm(lnkTo)
        if plmRef is None:
            raise AttributeError('Object {obj} does not expose a reference placement.')
        plmDeref = plmRef.inverse()
    else:
        raise ValueError("Referencing mode not implemented: " + refmode)
    
    return [plm.multiply(plmDeref) for plm in placements]

    

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
        obj.Referencing = REF_MODES
        
        
        obj.addProperty("App::PropertyLink","PlacementsTo","Lattice PopulateCopies", "Placement or array of placements, containing target locations.")
        obj.addProperty("App::PropertyLink","PlacementsFrom", "Lattice PopulateCopies","Placement or array of placements to be treated as origins for PlacementsTo.")
        
        self.assureProperties(obj)
        obj.OutputCompounding = "(autosettle)" # this is default value for new features.

    def assureProperties(self, obj):
        '''Adds properties that might be missing, because of loaded project made with older version. Handles version compatibility.'''
        propname = 'OutputCompounding'
        if not hasattr(obj,propname):
            obj.addProperty("App::PropertyEnumeration", propname, "Lattice PopulateCopies","In case single object copy is made, this property controls, if it's packed into compoud or not.")
            setattr(obj,propname,["(autosettle)","always", "only if many"])
            setattr(obj,propname,"always") # this is to match the old behavior. This is not the default setting for new features.
        if self.assureProperty(obj, "App::PropertyEnumeration","Copying", ShapeCopy.copy_types, "Lattice PopulateChildren", "Sets, what method to use for copying shapes."):
            self.Copying = ShapeCopy.copy_types[0]


    def derivedExecute(self,obj):
        self.assureProperties(obj)
        
        # cache stuff
        objectShape = screen(obj.Object).Shape

        outputIsLattice = lattice2BaseFeature.isObjectLattice(screen(obj.Object))
        

        # Pre-collect base placement list, if base is a lattice. For speed.
        if outputIsLattice:
            objectPlms = lattice2BaseFeature.getPlacementsList(screen(obj.Object),obj)
        
        placements = DereferenceArray(obj, obj.PlacementsTo, screen(obj.PlacementsFrom), obj.Referencing)

        #inherit reference placement from the array being copied
        if outputIsLattice:
            refplm = None
            if obj.Referencing == 'Array\'s reference' or obj.Referencing == 'First item' or obj.Referencing == 'Last item':
                #simple cases - we just copy the reference plm from the object
                refplm = lattice2BaseFeature.getReferencePlm(obj.Object)
            else:
                #other cases - apply first transform to reference placement
                refplm = lattice2BaseFeature.getReferencePlm(obj.Object)
                if refplm is not None and len(placements) > 0:
                    refplm = placements[0].multiply(refplm)
            self.setReferencePlm(obj, refplm)
        
        # initialize output containers and loop variables
        outputShapes = [] #output list of shapes
        outputPlms = [] #list of placements
        copy_method_index = ShapeCopy.getCopyTypeIndex(obj.Copying)

        
        # the essence
        for plm in placements:

            if outputIsLattice:
                for objectPlm in objectPlms:
                    outputPlms.append(plm.multiply(objectPlm))
            else:
                outputShape = ShapeCopy.copyShape(objectShape, copy_method_index, plm)
                #outputShape.Placement = plm.multiply(outputShape.Placement) # now handled by copyShape
                outputShapes.append(outputShape)
            
        if outputIsLattice:
            return outputPlms
        else:
            # Output shape or compound (complex logic involving OutputCompounding property)
            #first, autosettle the OutputCompounding.
            if obj.OutputCompounding == "(autosettle)":
                if hasattr(screen(obj.PlacementsTo),"ExposePlacement") and screen(obj.PlacementsTo).ExposePlacement == False:
                    obj.OutputCompounding = "always"
                else:
                    obj.OutputCompounding = "only if many"
            #now, set the result shape
            if len(outputShapes) == 1 and obj.OutputCompounding == "only if many":
                sh = outputShapes[0]
                sh = ShapeCopy.transformCopy(sh)
                obj.Shape = sh
            else:
                obj.Shape = Part.makeCompound(outputShapes)
            return None

class ViewProviderLatticePopulateCopies(lattice2BaseFeature.ViewProviderLatticeFeature):

    def getIcon(self):
        if lattice2BaseFeature.isObjectLattice(self.Object):
            return getIconPath(
                {'Origin':'Lattice2_PopulateCopies_Plms_Normal.svg',
                 'First item':'Lattice2_PopulateCopies_Plms_Array.svg',
                 'Last item':'Lattice2_PopulateCopies_Plms_Array.svg',
                 'Use PlacementsFrom':'Lattice2_PopulateCopies_Plms_Move.svg',
                 'Array\'s reference':'Lattice2_PopulateCopies_Plms_Ref.svg',
                }[self.Object.Referencing]
                )  
        else:
            return getIconPath(
                {'Origin':'Lattice2_PopulateCopies_Normal.svg',
                 'First item':'Lattice2_PopulateCopies_Array.svg',
                 'Last item':'Lattice2_PopulateCopies_Array.svg',
                 'Use PlacementsFrom':'Lattice2_PopulateCopies_Move.svg',
                 'Array\'s reference':'Lattice2_PopulateCopies_Ref.svg',
                }[self.Object.Referencing]
                )  
        
    def claimChildren(self):
        children = [screen(self.Object.Object), screen(self.Object.PlacementsTo)]
        if self.Object.Referencing == "Use PlacementsFrom":
            children.append(screen(self.Object.PlacementsFrom))
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
    if refmode == 'Auto':
        if lattice2BaseFeature.getReferencePlm(latticeObjTo) is not None:
            refmode = 'Array\'s reference'
        else:
            refmode = 'First item'
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
    
def throwBody():
    raise SelectionError("PartDesign mode", "You can't use population tools on shapes in partdesign body. Use Lattice PartDesign Pattern instead. Or deactivate active body to use populate tools on shapes.")

def cmdPopulate_shapes_nonFromTo(refmode):
    sel = FreeCADGui.Selection.getSelectionEx()
    (lattices, shapes) = lattice2BaseFeature.splitSelection(sel)
    if activeBody() and len(shapes)>0:
        throwBody()
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
    if activeBody() and len(shapes)>0:
        throwBody()
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
            
if FreeCAD.GuiUp:
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
            cmdPopulate_shapes_nonFromTo("Auto")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_PopulateCopies_Array', _CommandLatticePopulateCopies_Array())

class _CommandLatticePopulateCopies_Move:
    "Command to create LatticePopulateCopies feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PopulateCopies_Move.svg"),
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
            
if FreeCAD.GuiUp:
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
        
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_PopulateCopiesGroupCommand',_CommandLatticePopulateCopiesGroup())

exportedCommands = ['Lattice2_PopulateCopiesGroupCommand']

# -------------------------- /Gui command --------------------------------------------------

