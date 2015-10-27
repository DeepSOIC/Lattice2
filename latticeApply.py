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

__title__="Lattice Apply object: puts a copy of an object at every placement in a lattice object (makes the array real)."
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from latticeCommon import *
import latticeBaseFeature
import latticeCompoundExplorer as LCE

# -------------------------- document object --------------------------------------------------

def makeLatticeApply(name):
    '''makeLatticeApply(name): makes a LatticeApply object.'''
    return latticeBaseFeature.makeLatticeFeature(name, LatticeApply,'Lattice_Apply.svg', ViewProviderLatticeApply)

class LatticeApply(latticeBaseFeature.LatticeFeature):
    "The Lattice Apply object"
    
    def derivedInit(self,obj):
        self.Type = "LatticeApply"
                
        obj.addProperty("App::PropertyLink","Base","LatticeApply Base","Base object. Can be any generic shape, as well as another lattice object.")
                
        obj.addProperty("App::PropertyBool","KeepBaseFirstItemPos","LatticeApply Base","Apply extra transform, so that first item doesn't move.")
        obj.KeepBaseFirstItemPos = True
        
        obj.addProperty("App::PropertyLink","Tool","LatticeApply Tool","Tool object. Must be a lattice object. Contains placements to be applied.")

        obj.addProperty("App::PropertyBool","FlattenToolHierarchy","LatticeApply Tool","Unpack subcompounds, to use all shapes, not just direct children.")
        obj.FlattenToolHierarchy = True


    def derivedExecute(self,obj):
        # cache stuff
        base = obj.Base.Shape
        
        tool = obj.Tool.Shape
        if tool.ShapeType != 'Compound':
            tool = Part.makeCompound([tool])
        if obj.FlattenToolHierarchy:
            toolChildren = LCE.AllLeaves(tool)
        else:
            toolChildren = tool.childShapes()
        
        # validity logic
        if not latticeBaseFeature.isObjectLattice(obj.Tool):
            FreeCAD.Console.PrintWarning(obj.Name+': Tool is not a lattice object. Results may be unexpected.\n')
        outputIsLattice = latticeBaseFeature.isObjectLattice(obj.Base)
        
        plmMatcher = App.Placement() #extra placement, that makes first item to preserve its original placement
        if obj.KeepBaseFirstItemPos:
            plmMatcher = toolChildren[0].Placement.inverse()
        
        # Pre-collect base placement list, if base is a lattice. For speed.
        if outputIsLattice:
            baseLeaves = LCE.AllLeaves(base)
            basePlms = []
            for leaf in baseLeaves:
                basePlms.append(plmMatcher.multiply(leaf.Placement))
            baseLeaves = None #free memory
        
        # initialize output containers and loop variables
        outputShapes = [] #output list of shapes
        outputPlms = [] #list of placements
        
        # the essence
        for toolChild in toolChildren:
            #cache some stuff
            toolPlm = toolChild.Placement

            if outputIsLattice:
                for basePlm in basePlms:
                    outputPlms.append(toolPlm.multiply(basePlm))
            else:
                outputShape = base.copy()
                outputShape.Placement = toolPlm.multiply(plmMatcher.multiply(outputShape.Placement))
                outputShapes.append(outputShape)
            
        if outputIsLattice:
            return outputPlms
        else:
            obj.Shape = Part.makeCompound(outputShapes)
            return None

class ViewProviderLatticeApply(latticeBaseFeature.ViewProviderLatticeFeature):

    def claimChildren(self):
        return [self.Object.Base, self.Object.Tool]

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticeApply(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create LatticeApply")
    FreeCADGui.addModule("latticeApply")
    FreeCADGui.doCommand("f = latticeApply.makeLatticeApply(name='"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[0].ObjectName)
    FreeCADGui.doCommand("f.Tool = App.ActiveDocument."+sel[1].ObjectName)
    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("f.Proxy.execute(f)")
    FreeCADGui.doCommand("f.purgeTouched()")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandLatticeApply:
    "Command to create LatticeApply feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_Apply.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_Apply","Apply array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_Apply","Lattice Apply: put copies of an object at every placement in an array.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 2 :
            CreateLatticeApply(name = "Apply")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice_Apply", "Please select two objects, first. The fist object is Base, second is Tool. Base can be a lattice or any shape, that is to be arrayed. Tool must be a lattice object.", None))
            mb.setWindowTitle(translate("Lattice_Apply","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_Apply', _CommandLatticeApply())

exportedCommands = ['Lattice_Apply']

# -------------------------- /Gui command --------------------------------------------------

