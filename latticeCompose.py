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

__title__="Lattice Compose object: combine elements of two lattices"
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from latticeCommon import *
import latticeBaseFeature
import latticeCompoundExplorer as LCE

# -------------------------- document object --------------------------------------------------

def makeCompose(name):
    '''makeCompose(name): makes a Compose object.'''
    return latticeBaseFeature.makeLatticeFeature(name, Compose,'Lattice_Compose.svg', ViewProviderCompose)

class Compose(latticeBaseFeature.LatticeFeature):
    "The Lattice Compose object"
    
    operList = ['MultiplyPlacements','AveragePlacements', 'IgnoreBasePlacements','OverrideBasePlacements']
    
    def derivedInit(self,obj):
        self.Type = "LatticeCompose"
        
        obj.addProperty("App::PropertyEnumeration","Operation","Lattice Compose","Operation to perform between pairs of shapes")
        
        obj.Operation = Compose.operList
        
        
        obj.addProperty("App::PropertyLink","Base","LatticeCompose Base","Base object. Usually a compound of generic shapes, but can be a lattice too.")
        
        obj.addProperty("App::PropertyBool","LoopSequence","LatticeCompose Base","If index goes out of range, apply modulo math.")
        
        obj.addProperty("App::PropertyBool","FlattenBaseHierarchy","LatticeCompose Base","Unpack subcompounds, to use all shapes, not just direct children.")
        
        obj.addProperty("App::PropertyBool","KeepBaseFirstItemPos","LatticeCompose Base","Apply extra transform, so that first item doesn't move.")
        obj.KeepBaseFirstItemPos = True
        
        obj.addProperty("App::PropertyLink","Tool","LatticeCompose Tool","Tool object. Must be a lattice object. Contains placements to be applied.")

        obj.addProperty("App::PropertyBool","FlattenToolHierarchy","LatticeCompose Tool","Unpack subcompounds, to use all shapes, not just direct children.")
        obj.FlattenToolHierarchy = True


    def derivedExecute(self,obj):
        # cache stuff
        base = obj.Base.Shape
        if base.ShapeType != 'Compound':
            base = Part.makeCompound([base])
        if obj.FlattenBaseHierarchy:
            baseChildren = LCE.AllLeaves(base)
        else:
            baseChildren = base.childShapes()
        
        tool = obj.Tool.Shape
        if tool.ShapeType != 'Compound':
            tool = Part.makeCompound([tool])
        if obj.FlattenToolHierarchy:
            toolChildren = LCE.AllLeaves(tool)
        else:
            toolChildren = tool.childShapes()
        
        iBase = 0
        isMult = obj.Operation == 'MultiplyPlacements' # cache mode comparisons to speed them up
        isAvg = obj.Operation == 'AveragePlacements'
        isIgnore = obj.Operation == 'IgnoreBasePlacements'
        isOverride = obj.Operation == 'OverrideBasePlacements'

        #mode validity logic
        if not latticeBaseFeature.isObjectLattice(obj.Tool):
            FreeCAD.Console.PrintWarning(obj.Name+': Tool is not a lattice object. Results may be unexpected.\n')
        outputIsLattice = latticeBaseFeature.isObjectLattice(obj.Base)
        if isOverride and outputIsLattice:
            FreeCAD.Console.PrintWarning(obj.Name+': Base is a lattice object. OverrideBasePlacements operation requires a generic compound as Base. So, the lattice is being treated as a generic compound.\n')
            outputIsLattice = False
        
        # initialize output containers and loop variables
        outputShapes = [] #output list of shapes
        outputPlms = [] #list of placements
        bFirst = True
        plmMatcher = App.Placement() #extra placement, that aligns first tool member and first base member
        
        
        # the essence
        for toolChild in toolChildren:
            
            # early test for termination
            if iBase > len(baseChildren)-1:
                if obj.LoopSequence:
                    iBase = 0
                else:
                    FreeCAD.Console.PrintWarning(obj.Name+': There are '+str(len(toolChildren)-len(baseChildren))+
                                                 ' more placements in Tool than children in Base. Those placements'+
                                                 ' were dropped.\n')
                    break

            #cache some stuff
            basePlm = baseChildren[iBase].Placement
            toolPlm = toolChild.Placement

            if not outputIsLattice:
                outputShape = baseChildren[iBase].copy()
            
            #prepare alignment placement
            if bFirst:
                bFirst = False
                if obj.KeepBaseFirstItemPos:
                    plmMatcher = toolPlm.inverse()

            #mode logic
            if isMult:
                outPlm = toolPlm.multiply(plmMatcher.multiply(basePlm))
            elif isAvg:
                plm1 = toolPlm
                plm2 = pltMatcher.multiply(basePlm)
                transl = plm1.Base*0.5 + plm2.Base*0.5
                a1,b1,c1,d1 = plm1.Rotation.Q
                a2,b2,c2,d2 = plm2.Rotation.Q
                rot = App.Rotation((a1+a2,b1+b2,c1+c2,d1+d2)) #no divide-by-two, because FreeCAD will normalize the quaternion automatically
                outPlm = App.Placement(transl,rot)
            elif isIgnore:
                outPlm = toolPlm
            elif isOverride:
                assert(not outputIsLattice)
                outputShape.transformShape(toolPlm.inverse.multiply(plmMatcher.multiply(basePlm)))
                outPlm = toolPlm
            
            if outputIsLattice:
               outputPlms.append(outPlm)
            else:
                outputShape.Placement = outPlm
                outputShapes.append(outputShape)
            
            iBase += 1
            
        if outputIsLattice:
            return outputPlms
        else:
            obj.Shape = Part.makeCompound(outputShapes)

class ViewProviderCompose(latticeBaseFeature.ViewProviderLatticeFeature):

    def claimChildren(self):
        return [self.Object.Base, self.Object.Tool]

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateCompose(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create Compose")
    FreeCADGui.addModule("latticeCompose")
    FreeCADGui.doCommand("f = latticeCompose.makeCompose(name='"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[0].ObjectName)
    FreeCADGui.doCommand("f.Tool = App.ActiveDocument."+sel[1].ObjectName)
    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("f.Proxy.execute(f)")
    FreeCADGui.doCommand("f.purgeTouched()")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandCompose:
    "Command to create Compose feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_Compose.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_Compose","Compose arrays"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_Compose","Lattice Compose: element-wise operations between compounds")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 2 :
            CreateCompose(name = "Compose")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice_Compose", "Please select two objects, first. The fist object is Base, second is Tool. Base can contain real shapes, as well as be a lattice object. Tool is typically a lattice object.", None))
            mb.setWindowTitle(translate("Lattice_Compose","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_Compose', _CommandCompose())

exportedCommands = ['Lattice_Compose']

# -------------------------- /Gui command --------------------------------------------------

