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

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2CompoundExplorer as LCE
import lattice2Executer
import lattice2GeomUtils as Utils

__title__="Lattice ProjectArray module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""


# -------------------------- common stuff --------------------------------------------------

def makeProjectArray(name):
    '''makeProjectArray(name): makes a Lattice ProjectArray object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticeProjectArray, ViewProviderProjectArray)

class LatticeProjectArray(lattice2BaseFeature.LatticeFeature):
    "The Lattice ProjectArray object"
        
    def derivedInit(self,obj):
        self.Type = "LatticeProjectArray"

        obj.addProperty("App::PropertyLink","Base","Lattice ProjectArray","Array to be altered")
        obj.addProperty("App::PropertyLink","Tool","Lattice ProjectArray","Shape to project onto")
        
        obj.addProperty("App::PropertyEnumeration","TranslateMode","Lattice ProjectArray","")
        obj.TranslateMode = ['keep','projected','mixed']
        obj.TranslateMode = 'projected'
        
        obj.addProperty("App::PropertyFloat","PosMixFraction","Lattice ProjectArray","Value controls mixing of positioning between the shape and the placement. 0 is on shape, 1 is at placement.")
        
        obj.addProperty("App::PropertyDistance","PosElevation","Lattice ProjectArray","Extra displacement along normal to face or along gap, away from the shape.")

        obj.addProperty("App::PropertyEnumeration","OrientMode","Lattice ProjectArray","")
        obj.OrientMode = ['keep','along gap','tangent plane','along u', 'along v']
        obj.OrientMode = 'along u'
        
        obj.addProperty("App::PropertyEnumeration","Multisolution","Lattice ProjectArray","Specify the way of dealing with multiple solutions of projection")
        obj.Multisolution = ['use first','use all']
                

    def derivedExecute(self,obj):
        #validity check
        if not lattice2BaseFeature.isObjectLattice(obj.Base):
            lattice2Executer.warning(obj,"A lattice object is expected as Base, but a generic shape was provided. It will be treated as a lattice object; results may be unexpected.")
        
        toolShape = obj.Tool.Shape
        if lattice2BaseFeature.isObjectLattice(obj.Tool):
            lattice2Executer.warning(obj,"A lattice object was provided as Tool. It will be converted into points; orientations will be ignored.")
            leaves = LCE.AllLeaves(toolShape)
            points = [Part.Vertex(leaf.Placement.Base) for leaf in leaves]
            toolShape = Part.makeCompound(points)

        leaves = LCE.AllLeaves(obj.Base.Shape)
        input = [leaf.Placement for leaf in leaves]

        output = [] #variable to receive the final list of placements
        
        #cache settings
        elev = float(obj.PosElevation)
        posIsKeep = obj.TranslateMode == 'keep'
        posIsProjected = obj.TranslateMode == 'projected'
        posIsMixed = obj.TranslateMode == 'mixed'
        mixF = float(obj.PosMixFraction)
        oriIsKeep = obj.OrientMode == 'keep'
        oriIsAlongGap = obj.OrientMode == 'along gap'
        oriIsTangentPlane = obj.OrientMode == 'tangent plane'
        oriIsAlongU = obj.OrientMode == 'along u'
        oriIsAlongV = obj.OrientMode == 'along v'
        
        isMultiSol = obj.Multisolution == 'use all'
        
        for plm in input:
            v = Part.Vertex(plm.Base)
            projection = v.distToShape(toolShape)
            (dist, gaps, infos) = projection
            for iSol in range(0,len(gaps)):
                (posKeep, posPrj) = gaps[iSol]
                (dummy, dummy, dummy, el_topo, el_index, el_params) = infos[iSol]

                # Fetch all possible parameters (some may not be required, depending on modes)
                normal = posKeep - posPrj
                if normal.Length < DistConfusion:
                    normal = None
                
                tangU = None
                tangV = None
                if el_topo == 'Face':
                    face = toolShape.Faces[el_index]
                    if normal is None:
                        normal = face.normalAt(*el_params)
                    (tangU, tangV) = face.tangentAt(*el_params)
                elif el_topo == "Edge":
                    edge = toolShape.Edges[el_index]
                    tangU = edge.tangentAt(el_params)
                
                if normal is not None:
                    normal.normalize()
                
                #mode logic - compute new placement
                if posIsKeep:
                    pos = plm.Base
                elif posIsProjected:
                    pos = posPrj
                elif posIsMixed:
                    pos = posKeep*mixF + posPrj*(1-mixF)
                else:
                    raise ValueError("Positioning mode not implemented: " + obj.TranslateMode )
                
                if abs(elev) > DistConfusion:
                    if normal is None:
                        raise ValueError("Normal vector not available for a placement resting on " + el_topo +". Normal vector is required for nonzero position elevation.")
                    pos += normal * elev
                    
                    
                if oriIsKeep:
                    ori = plm.Rotation
                elif oriIsAlongGap:
                    if normal is None:
                        raise ValueError("Normal vector not available for a placement resting on " + el_topo +". Normal vector is required for orientation mode '"+obj.OrientMode+"'")
                    ori = Utils.makeOrientationFromLocalAxesUni("X",XAx= normal*(-1.0))
                elif oriIsTangentPlane:
                    if normal is None:
                        raise ValueError("Normal vector not available for a placement resting on " + el_topo +". Normal vector is required for orientation mode '"+obj.OrientMode+"'")
                    ori = Utils.makeOrientationFromLocalAxesUni("Z",ZAx= normal)
                elif oriIsAlongU:
                    if normal is None:
                        raise ValueError("Normal vector not available for a placement resting on " + el_topo +". Normal vector is required for orientation mode '"+obj.OrientMode+"'")
                    if tangU is None:
                        raise ValueError("TangentU vector not available for point on " + el_topo +". TangentU vector is required for orientation mode '"+obj.OrientMode+"'")
                    ori = Utils.makeOrientationFromLocalAxesUni("ZX",ZAx= normal, XAx= tangU)
                elif oriIsAlongV:
                    if normal is None:
                        raise ValueError("Normal vector not available for a placement resting on " + el_topo +". Normal vector is required for orientation mode '"+obj.OrientMode+"'")
                    if tangV is None:
                        raise ValueError("TangentV vector not available for point on " + el_topo +". TangentV vector is required for orientation mode '"+obj.OrientMode+"'")
                    ori = Utils.makeOrientationFromLocalAxesUni("ZX",ZAx= normal, XAx= tangV)
                else:
                    raise ValueError("Orientation mode not implemented: " + obj.OrientMode )
                
                output.append(App.Placement(pos,ori))
                
                if not isMultiSol:
                    break
        
        return output
        
        
class ViewProviderProjectArray(lattice2BaseFeature.ViewProviderLatticeFeature):
    "A View Provider for the Lattice ProjectArray object"

    def getIcon(self):
        return getIconPath("Lattice2_ProjectArray.svg")

    def claimChildren(self):
        return [self.Object.Base]

def CreateLatticeProjectArray(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    
    # selection order independece logic (lattice object and generic shape stencil can be told apart)
    iLtc = 0 #index of lattice object in selection
    iStc = 1 #index of stencil object in selection
    for i in range(0,len(sel)):
        if lattice2BaseFeature.isObjectLattice(sel[i]):
            iLtc = i
            iStc = i-1 #this may give negative index, but python accepts negative indexes
            break
    FreeCAD.ActiveDocument.openTransaction("Create ProjectArray")
    FreeCADGui.addModule("lattice2ProjectArray")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("sel = Gui.Selection.getSelectionEx()")    
    FreeCADGui.doCommand("f = lattice2ProjectArray.makeProjectArray(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[iLtc].ObjectName)
    FreeCADGui.doCommand("f.Tool = App.ActiveDocument."+sel[iStc].ObjectName)

    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandProjectArray:
    "Command to create Lattice ProjectArray feature"
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ProjectArray.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_ProjectArray","Project Array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_ProjectArray","Project Array: alter placements based on their proximity to a shape.")}
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2:
            CreateLatticeProjectArray(name= "Project")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_ProjectArray", "Select one lattice object to be projected, and one shape to project onto, first!", None))
            mb.setWindowTitle(translate("Lattice2_ProjectArray","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_ProjectArray', _CommandProjectArray())

exportedCommands = ['Lattice2_ProjectArray']

# -------------------------- /Gui command --------------------------------------------------
