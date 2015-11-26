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

from lattice2Common import *
import lattice2BaseFeature
import lattice2CompoundExplorer as LCE
import lattice2Executer

# -------------------------- document object --------------------------------------------------

def makeLatticeApply(name):
    '''makeLatticeApply(name): makes a LatticeApply object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticeApply, ViewProviderLatticeApply)

class LatticeApply(lattice2BaseFeature.LatticeFeature):
    "The Lattice Apply object"
    
    def derivedInit(self,obj):
        self.Type = "LatticeApply"
                
        obj.addProperty("App::PropertyLink","Base","Lattice Apply","Base object. Can be any generic shape, as well as another lattice object.")
                
        obj.addProperty("App::PropertyBool","KeepBaseFirstItemPos","Lattice Apply","Apply extra transform, so that first item doesn't move.")
        obj.KeepBaseFirstItemPos = False
        
        obj.addProperty("App::PropertyLink","Tool","Lattice Apply","Tool object. Must be a lattice object. Contains placements to be applied.")

        obj.addProperty("App::PropertyBool","FlattenToolHierarchy","Lattice Apply","Unpack subcompounds, to use all shapes, not just direct children.")
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
        if not lattice2BaseFeature.isObjectLattice(obj.Tool):
            lattice2Executer.warning(obj, 'Tool is not a lattice object. Results may be unexpected.\n')
        outputIsLattice = lattice2BaseFeature.isObjectLattice(obj.Base)
        
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

class ViewProviderLatticeApply(lattice2BaseFeature.ViewProviderLatticeFeature):

    def getIcon(self):
        return getIconPath("Lattice2_Apply.svg")
        
    def claimChildren(self):
        return [self.Object.Base, self.Object.Tool]

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticeApply(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create LatticeApply")
    FreeCADGui.addModule("lattice2Apply")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2Apply.makeLatticeApply(name='"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[0].ObjectName)
    FreeCADGui.doCommand("f.Tool = App.ActiveDocument."+sel[1].ObjectName)
    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandLatticeApply:
    "Command to create LatticeApply feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_Apply.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_Apply","Apply array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_Apply","Lattice Apply: put copies of an object at every placement in an array.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 2 :
            CreateLatticeApply(name = "Apply")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_Apply", "Please select two objects, first. The fist object is Base, second is Tool. Base can be a lattice or any shape, that is to be arrayed. Tool must be a lattice object.", None))
            mb.setWindowTitle(translate("Lattice2_Apply","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_Apply', _CommandLatticeApply())

exportedCommands = ['Lattice2_Apply']

# -------------------------- /Gui command --------------------------------------------------

