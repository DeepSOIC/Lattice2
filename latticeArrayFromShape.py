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

from latticeCommon import *
import latticeBaseFeature
import latticeCompoundExplorer as LCE
import latticeGeomUtils as Utils

# -------------------------- document object --------------------------------------------------

def makeLatticeArrayFromShape(name):
    '''makeLatticeArrayFromShape(name): makes a LatticeArrayFromShape object.'''
    return latticeBaseFeature.makeLatticeFeature(name, LatticeArrayFromShape,'Lattice_ArrayFromShape.svg')

class LatticeArrayFromShape(latticeBaseFeature.LatticeFeature):
    "The Lattice ArrayFromShape object"
    
    def derivedInit(self,obj):
        self.Type = "LatticeArrayFromShape"
                
        obj.addProperty("App::PropertyLink","Base","Lattice ArrayFromShape","Object to generate array of placements from. Should be a compound. If not, single placement will be created.")
                
        obj.addProperty("App::PropertyBool","FlattenBaseHierarchy","Lattice ArrayFromShape","Unpack subcompounds, to use all shapes, not just direct children.")
        obj.FlattenBaseHierarchy = True
        
        obj.addProperty("App::PropertyEnumeration","TranslateMode","Lattice ArrayFromShape","Method of deriving translation part of output placements")
        obj.TranslateMode = ['(none)', 'base', 'child', 'child.CenterOfMass','child.CenterOfBoundBox','child.Vertex']
        obj.TranslateMode = 'child'
        
        obj.addProperty("App::PropertyInteger","TranslateElementIndex","Lattice ArrayFromShape","Index of vertex used for translation calculation.")
        
        obj.addProperty("App::PropertyEnumeration","OrientMode","Lattice ArrayFromShape","Method of deriving orientation part of output placements")
        obj.OrientMode = ['(none)', 'base', 'child', 'child.InertiaAxes','child.Edge', 'child.FaceAxis']
        obj.OrientMode = 'child'

        obj.addProperty("App::PropertyInteger","OrientElementIndex","Lattice ArrayFromShape","Index of subelement used for orientation calculation.")

    def derivedExecute(self,obj):
        # cache stuff
        base = obj.Base.Shape
        if base.ShapeType != 'Compound':
            base = Part.makeCompound([base])
        if obj.FlattenBaseHierarchy:
            baseChildren = LCE.AllLeaves(base)
        else:
            baseChildren = base.childShapes()
                        
        #cache mode comparisons, for speed
        posIsNone = obj.TranslateMode == '(none)'
        posIsBase = obj.TranslateMode == 'base'
        posIsChild = obj.TranslateMode == 'child'
        posIsCenterM = obj.TranslateMode == 'child.CenterOfMass'
        posIsCenterBB = obj.TranslateMode == 'child.CenterOfBoundBox'
        posIsVertex = obj.TranslateMode == 'child.Vertex'
        
        oriIsNone = obj.OrientMode == '(none)'
        oriIsBase = obj.OrientMode == 'base'
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
            elif posIsBase:
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
                             "CompSolid":""}
                #Center of mass of a compound is a weghted average of centers
                # of mass of individual objects.
                for leaf in leaves:
                    w = 1.0 if not weightAttrib else (getattr(leaf, weightAttrib))
                    if child.ShapeType == 'Vertex':
                        childCM = child.Point
                    #elif child.ShapeType == 'CompSolid':
                        #todo
                    else: 
                        childCM = child.CenterOfMass
                    pos += childCM * w
                    totalW += w
                pos = pos * (1.0/totalW)
            elif posIsCenterBB:
                import latticeBoundBox
                bb = latticeBoundBox.getPrecisionBoundBox(child)
                pos = bb.Center
            elif posIsVertex:
                v = child.Vertexes[obj.TranslateElementIndex - 1]
            else:
                raise ValueError("latticePolarArrayFromShape: translation mode not implemented: "+obj.TranslateMode)
            
            if oriIsNone:
                pass
            elif oriIsBase:
                ori = base.Placement.Rotation
            elif oriIsChild:
                ori = child.Placement.Rotation
            elif oriIsInertial:
                leaves = LCE.AllLeaves(child)
                if len(leaves)>1:
                    raise ValueError("latticePolarArrayFromShape: calculation of principal axes of compounds is not supported yet")
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
                raise ValueError("latticePolarArrayFromShape: rientation mode not implemented: "+obj.OrientMode)

            plm = App.Placement(pos, ori)
            outputPlms.append(plm)
            if (posIsNone or posIsBase) and (oriIsNone or oriIsBase):
                break #output just one placement if modes are set so that placement does not depend on current child
        return outputPlms

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticeArrayFromShape(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create LatticeArrayFromShape")
    FreeCADGui.addModule("latticeArrayFromShape")
    FreeCADGui.doCommand("f = latticeArrayFromShape.makeLatticeArrayFromShape(name='"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[0].ObjectName)
    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("f.Proxy.execute(f)")
    FreeCADGui.doCommand("f.purgeTouched()")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandLatticeArrayFromShape:
    "Command to create LatticeArrayFromShape feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice_ArrayFromShape.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice_ArrayFromShape","Make lattice from compound"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice_ArrayFromShape","Lattice ArrayFromShape: make placements array from shapes in a compound.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            CreateLatticeArrayFromShape(name = "ArrayFromShape")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice_ArrayFromShape", "Please select one object, first.", None))
            mb.setWindowTitle(translate("Lattice_ArrayFromShape","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice_ArrayFromShape', _CommandLatticeArrayFromShape())

exportedCommands = ['Lattice_ArrayFromShape']

# -------------------------- /Gui command --------------------------------------------------

