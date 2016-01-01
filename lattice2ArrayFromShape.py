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

__title__="Lattice ArrayFromShape object: creates an array of placements from a compound."
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2CompoundExplorer as LCE
import lattice2GeomUtils as Utils
import lattice2Executer

# -------------------------- document object --------------------------------------------------

def makeLatticeArrayFromShape(name):
    '''makeLatticeArrayFromShape(name): makes a LatticeArrayFromShape object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticeArrayFromShape, ViewProviderArrayFromShape)

class LatticeArrayFromShape(lattice2BaseFeature.LatticeFeature):
    "The Lattice ArrayFromShape object"
    
    def derivedInit(self,obj):
        self.Type = "LatticeArrayFromShape"
                
        obj.addProperty("App::PropertyLink","ShapeLink","Lattice ArrayFromShape","Object to generate array of placements from. Should be a compound. If not, single placement will be created.")
                
        obj.addProperty("App::PropertyEnumeration","CompoundTraversal","Lattice ArrayFromShape","Sets whether first-level compound is traversed, or the whole compounding tree.")
        obj.CompoundTraversal = ["Use as a whole","Direct children only","Recursive"]
        obj.CompoundTraversal = "Direct children only"
        
        obj.addProperty("App::PropertyEnumeration","TranslateMode","Lattice ArrayFromShape","Method of deriving translation part of output placements")
        obj.TranslateMode = ['(none)', 'parent', 'child', 'child.CenterOfMass','child.CenterOfBoundBox','child.Vertex']
        obj.TranslateMode = 'child'
        
        obj.addProperty("App::PropertyInteger","TranslateElementIndex","Lattice ArrayFromShape","Index of vertex used for translation calculation.")
        
        obj.addProperty("App::PropertyEnumeration","OrientMode","Lattice ArrayFromShape","Method of deriving orientation part of output placements")
        obj.OrientMode = ['(none)', 'parent', 'child', 'child.InertiaAxes','child.Edge', 'child.FaceAxis']
        obj.OrientMode = 'child'

        obj.addProperty("App::PropertyInteger","OrientElementIndex","Lattice ArrayFromShape","Index of vertex or face used for orientation calculation. Vertex or face - depends on selected OrientMode")

    def derivedExecute(self,obj):
        # cache stuff
        if lattice2BaseFeature.isObjectLattice(obj.ShapeLink):
            lattice2Executer.warning(obj,"ShapeLink points to a placement/array of placements. The placement/array will be reinterpreted as a generic shape; the results may be unexpected.")

        base = obj.ShapeLink.Shape
        if obj.CompoundTraversal == "Use as a whole":
            baseChildren = [base]
        else:
            if base.ShapeType != 'Compound':
                base = Part.makeCompound([base])
            if obj.CompoundTraversal == "Recursive":
                baseChildren = LCE.AllLeaves(base)
            else:
                baseChildren = base.childShapes()
        
                        
        #cache mode comparisons, for speed
        posIsNone = obj.TranslateMode == '(none)'
        posIsParent = obj.TranslateMode == 'parent'
        posIsChild = obj.TranslateMode == 'child'
        posIsCenterM = obj.TranslateMode == 'child.CenterOfMass'
        posIsCenterBB = obj.TranslateMode == 'child.CenterOfBoundBox'
        posIsVertex = obj.TranslateMode == 'child.Vertex'
        
        oriIsNone = obj.OrientMode == '(none)'
        oriIsParent = obj.OrientMode == 'parent'
        oriIsChild = obj.OrientMode == 'child'
        oriIsInertial = obj.OrientMode == 'child.InertiaAxes'
        oriIsEdge = obj.OrientMode == 'child.Edge'
        oriIsFace = obj.OrientMode == 'child.FaceAxis'
        
        # initialize output containers and loop variables
        outputPlms = [] #list of placements
        
        # the essence
        for child in baseChildren:
            pos = App.Vector()
            ori = App.Rotation()
            if posIsNone:
                pass
            elif posIsParent:
                pos = base.Placement.Base
            elif posIsChild:
                pos = child.Placement.Base
            elif posIsCenterM:
                leaves = LCE.AllLeaves(child)
                totalW = 0
                weightAttrib = {"Vertex":"",
                             "Edge":"Length",
                             "Wire":"Length",
                             "Face":"Area",
                             "Shell":"Area",
                             "Solid":"Volume",
                             "CompSolid":""}[leaves[0].ShapeType]
                #Center of mass of a compound is a weghted average of centers
                # of mass of individual objects.
                for leaf in leaves:
                    w = 1.0 if not weightAttrib else (getattr(leaf, weightAttrib))
                    if leaf.ShapeType == 'Vertex':
                        leafCM = leaf.Point
                    #elif child.ShapeType == 'CompSolid':
                        #todo
                    else: 
                        leafCM = leaf.CenterOfMass
                    pos += leafCM * w
                    totalW += w
                pos = pos * (1.0/totalW)
            elif posIsCenterBB:
                import lattice2BoundBox
                bb = lattice2BoundBox.getPrecisionBoundBox(child)
                pos = bb.Center
            elif posIsVertex:
                v = child.Vertexes[obj.TranslateElementIndex - 1]
                pos = v.Point
            else:
                raise ValueError(obj.Name + ": translation mode not implemented: "+obj.TranslateMode)
            
            if oriIsNone:
                pass
            elif oriIsParent:
                ori = base.Placement.Rotation
            elif oriIsChild:
                ori = child.Placement.Rotation
            elif oriIsInertial:
                leaves = LCE.AllLeaves(child)
                if len(leaves)>1:
                    raise ValueError(obj.Name + ": calculation of principal axes of compounds is not supported yet")
                props = leaves[0].PrincipalProperties
                XAx = props['FirstAxisOfInertia']
                ZAx = props['ThirdAxisOfInertia']
                ori = Utils.makeOrientationFromLocalAxes(ZAx, XAx)
            elif oriIsEdge:
                edge = child.Edges[obj.OrientElementIndex - 1]
                XAx = edge.Curve.tangent(edge.Curve.FirstParameter)[0]
                ori1 = Utils.makeOrientationFromLocalAxes(ZAx= XAx)
                ori2 = Utils.makeOrientationFromLocalAxes(ZAx= App.Vector(1,0,0),XAx= App.Vector(0,0,1))
                ori = ori1.multiply(ori2)
            elif oriIsFace:
                face = child.Faces[obj.OrientElementIndex - 1]
                ZAx = face.Surface.Axis
            else:
                raise ValueError(obj.Name + ": orientation mode not implemented: "+obj.OrientMode)

            plm = App.Placement(pos, ori)
            outputPlms.append(plm)
        return outputPlms


class ViewProviderArrayFromShape(lattice2BaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_ArrayFromShape.svg') if self.Object.CompoundTraversal == "Use as a whole" == False else getIconPath('Lattice2_PlacementFromShape.svg')

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticeArrayFromShape(TranslateMode = 'child', OrientMode = 'child', WholeObject = False):
    sel = FreeCADGui.Selection.getSelectionEx()
    if len(sel) != 1:
        raise SelectionError(message= "Please select just one object, not "+str(len(sel)) +".", title= "Bad selection")
    FreeCAD.ActiveDocument.openTransaction("Create LatticeArrayFromShape")
    FreeCADGui.addModule("lattice2ArrayFromShape")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2ArrayFromShape.makeLatticeArrayFromShape(name='ArrayFromShape')")
    FreeCADGui.doCommand("f.ShapeLink = App.ActiveDocument."+sel[0].ObjectName)
    if WholeObject:
        FreeCADGui.doCommand("f.CompoundTraversal = 'Use as a whole'")
        FreeCADGui.doCommand("f.ExposePlacement = True")
        of_or_from = "of" if TranslateMode == 'child' and OrientMode == 'child' else "from"
        FreeCADGui.doCommand("f.Label = 'Placement "+of_or_from+" ' + f.ShapeLink.Label")
    else:
        FreeCADGui.doCommand("f.Label = 'Array from ' + f.ShapeLink.Label")
        
    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    FreeCADGui.doCommand("f = None")
    deselect(sel)
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandLatticeArrayFromShape:
    "Command to create LatticeArrayFromShape feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ArrayFromShape.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_ArrayFromShape","Array from compound"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_ArrayFromShape","Lattice ArrayFromShape: make placements array from shapes in a compound.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("ArrayFromShape command",
                    "Array From Shape command. Creates an array of placements from shapes in a compound.\n\n"
                    "Select the object that is a compound, first, then invoke this tool.")
                return
            CreateLatticeArrayFromShape(TranslateMode= 'child.CenterOfMass', OrientMode= 'child')
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_ArrayFromShape', _CommandLatticeArrayFromShape())

class _CommandLatticePlacementFromShape:
    "Command to create LatticeArrayFromShape feature linking to placement of one shape"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_PlacementFromShape.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_ArrayFromShape","Single Placement: linked to shape"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_ArrayFromShape","Lattice PlacementFromShape: make Placement linked to placement of selected object.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Single Placement: linked to shape",
                    "Single Placement: linked to shape command. Creates a placement linked to a placement of an object.\n\n"
                    "Select the object first, then invoke this tool.")
                return
            CreateLatticeArrayFromShape(TranslateMode= 'child', OrientMode= 'child', WholeObject= True)
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_PlacementFromShape', _CommandLatticePlacementFromShape())

exportedCommands = ['Lattice2_ArrayFromShape'] #Lattice2_PlacementFromShape will be included in lattice2Placement set of commands. I know, it's ugly....

# -------------------------- /Gui command --------------------------------------------------

