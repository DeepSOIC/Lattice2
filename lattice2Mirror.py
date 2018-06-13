#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2018 - Victor Titov (DeepSOIC)                          *
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

from lattice2Common import *
import lattice2CompoundExplorer as LCE
import lattice2ShapeCopy as ShapeCopy
import lattice2BaseFeature as LBF
from lattice2GeomUtils import makeOrientationFromLocalAxes
from lattice2Utils import getSelectionAsListOfLinkSub
import lattice2Executer

import FreeCAD as App

__title__="Lattice Mirror module for FreeCAD"
__author__ = "DeepSOIC"

def mirrorShape(shape, pivotPlacement, flipX, flipY, flipZ):
    plmM = pivotPlacement.toMatrix()
    mirrM = App.Base.Matrix()
    if flipX: mirrM.A11 = -1
    if flipY: mirrM.A22 = -1
    if flipZ: mirrM.A33 = -1
    m = plmM.multiply(mirrM.multiply(plmM.inverse()))
    return ShapeCopy.transformShape(shape, m)

def mirrorPlacement(placement, pivotPlacement, flipX, flipY, flipZ):
    """mirrorPlacement(placement, pivotPlacement, flipX, flipY, flipZ): mirrors a placement. Y axis of placement is adjusted to keep the placement's CS right-handed."""
    plmM = pivotPlacement.toMatrix()
    mirrM = App.Base.Matrix()
    if flipX: mirrM.A11 = -1
    if flipY: mirrM.A22 = -1
    if flipZ: mirrM.A33 = -1
    m = plmM.multiply(mirrM.multiply(plmM.inverse()))
    
    OX = App.Vector(1,0,0)
    OZ = App.Vector(0,0,1)
    
    base = m.multiply(placement.Base)
    xdir = m.submatrix(3).multiply(placement.Rotation.multVec(OX))
    zdir = m.submatrix(3).multiply(placement.Rotation.multVec(OZ))
    rot = makeOrientationFromLocalAxes(zdir, xdir)
    return App.Placement(base, rot)

def resolveSingleSublink(lnk):
    if lnk is None:
        raise ValueError("resolveSingleSublink: link is empty")
    obj, sub = lnk
    if len(sub)>1:
        raise ValueError("Too many subelements linked: num. Maximum: 1".format(num= len(sub)))
    sh = obj.Shape if len(sub) == 0 or sub[0] == '' else obj.Shape.getElement(sub[0])
    shs = LCE.AllLeaves(sh) #if whole object is linked, it may be a compound containing the shape of interest. Explode it.
    if len(shs) != 1:
        raise ValueError("Linked is {num} shapes, but should be exactly one.".format(num= len(shs)))
    return shs[0]


# -------------------------- document object --------------------------------------------------


def makeLatticeMirror(name):
    '''makeLatticeMirror(name): makes a LatticeMirror object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    LatticeMirror(obj)
    if FreeCAD.GuiUp:        
        ViewProviderLatticeMirror(obj.ViewObject)
    return obj


class LatticeMirror(LBF.LatticeFeature):
    "The LatticeMirror object"
    def derivedInit(self,obj):
        self.Type = "LatticeMirror"
        obj.addProperty("App::PropertyLink","Object","Lattice Mirror","Object to mirror.")
        obj.addProperty("App::PropertyLinkSub","Pivot","Lattice Mirror","Object to mirror against. Can be a placement, a planar face, an edge (line), or a vertex.")
        obj.addProperty("App::PropertyBool","FlipX","Lattice Mirror","Sets if the object is to be flipped along X axis.")
        obj.addProperty("App::PropertyBool","FlipY","Lattice Mirror","Sets if the object is to be flipped along Y axis.")
        obj.addProperty("App::PropertyBool","FlipZ","Lattice Mirror","Sets if the object is to be flipped along Z axis.")
        obj.addProperty("App::PropertyPlacement","PivotPlacement","Lattice Mirror","Mirror pivot")
        obj.addProperty("App::PropertyEnumeration","ObjectTraversal","Lattice Mirror","Sets if base object should be treated as an array or not.")
        obj.ObjectTraversal = ['Use whole', 'Direct children only', 'Recursive']
        
        obj.Proxy = self
        

    def derivedExecute(self,obj):
        base_is_lattice = LBF.isObjectLattice(obj.Object)
        pivot_is_lattice = LBF.isObjectLattice(obj.Pivot[0]) if obj.Pivot else True
        flipX = obj.FlipX
        flipY = obj.FlipY
        flipZ = obj.FlipZ
        
        # collect mirror pivot placements
        pivots = None
        em = 0 #editormode of PivotPlacement property. 0 = editable, 1 = read-only, 2 = hidden
        if obj.Pivot:
            em = 1 #read-only
            if pivot_is_lattice:
                pivots = LBF.getPlacementsList(obj.Pivot[0])
            else:
                pivot_shape = resolveSingleSublink(obj.Pivot)
                if pivot_shape.ShapeType == 'Edge' and type(pivot_shape.Curve) is Part.Line:
                    dir = pivot_shape.Curve.Direction
                    base = pivot_shape.CenterOfMass
                    if flipX != flipY:
                        raise ValueError("Unsupported combination of flips for mirroring against line. FlipX and FlipY must either be both on or both off.")
                    rot = makeOrientationFromLocalAxes(dir)
                    pivots = [App.Placement(base, rot)]
                elif  pivot_shape.ShapeType == 'Face' and type(pivot_shape.Surface) is Part.Plane:
                    dir = pivot_shape.Surface.Axis
                    base = pivot_shape.CenterOfMass
                    if flipX != flipY:
                        raise ValueError("Unsupported combination of flips for mirroring against line. FlipX and FlipY must either be both on or both off.")
                    rot = makeOrientationFromLocalAxes(dir)
                    pivots = [App.Placement(base, rot)]
                elif  pivot_shape.ShapeType == 'Vertex':
                    base = pivot_shape.Point
                    pivots = [App.Placement(base, obj.PivotPlacement.Rotation)]
                    em = 0 #editable
                else:
                    raise TypeError("Unsupported geometry for use as mirror")
            if len(pivots) == 1:
                obj.PivotPlacement = pivots[0]
            else:
                em = 2 #hidden
        else:
            pivots = [obj.PivotPlacement]
            em = 0
        obj.setEditorMode('PivotPlacement', em)
        
        # collect objects to be mirrored
        loop = False
        whole = obj.ObjectTraversal == 'Use whole'
        children = []
        if base_is_lattice:
            children = LBF.getPlacementsList(obj.Object)
        else:
            if obj.ObjectTraversal == 'Use whole':
                children = [obj.Object.Shape]
                loop = True
            elif obj.ObjectTraversal == 'Direct children only':
                children = obj.Object.Shape.childShapes()
            elif obj.ObjectTraversal == 'Use whole':
                children = LCE.AllLeaves(obj.Object.Shape)
            else:
                raise ValueError("Traversal mode not implemented: {mode}".format(mode= obj.ObjectTraversal))
        
        if len(pivots) != len(children) and not loop and not whole:
            lattice2Executer.warning(obj,"{label}: Number of children ({nch}) doesn't match the number of pivot placements ({npiv})"
                .format(
                    label= obj.Label,
                    nch= len(children),
                    npiv= len(pivots)
                )
            )
            n = min(len(pivots), len(children))
        else:
            n = len(pivots)
        
        # actual mirroring!
        result = []
        for i in range(n):
            piv = pivots[i]
            ichild = i % len(children)
            if base_is_lattice:
                if whole:
                    for plm in children:
                        result.append(mirrorPlacement(plm, piv, flipX, flipY, flipZ))
                else:
                    result.append(mirrorPlacement(children[ichild], piv, flipX, flipY, flipZ))
            else:
                result.append(mirrorShape(children[ichild], piv, flipX, flipY, flipZ))
        
        # write out the result
        if base_is_lattice:
            return result
        else:
            if n == 1:
                result = ShapeCopy.transformCopy(result[0])
            else:
                result = Part.Compound(result)
            obj.Shape = result
            return None
                
class ViewProviderLatticeMirror(LBF.ViewProviderLatticeFeature):
    "A View Provider for the LatticeMirror object"
       
    def getIcon(self):
        obj = self.Object
        base_is_lattice = LBF.isObjectLattice(obj.Object)
        pivot_is_lattice = LBF.isObjectLattice(obj.Pivot[0]) if obj.Pivot else True
        whole = obj.ObjectTraversal == 'Use whole'
        key = 'Plm' if base_is_lattice else 'Sh'
        key += 's' if not whole and pivot_is_lattice else ''
        key += 'Plms' if pivot_is_lattice else 'Sh'
        return getIconPath("Lattice2_Mirror_{key}.svg".format(key= key))

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def claimChildren(self):
        if self.Object.Pivot:
            return [screen(self.Object.Object), screen(self.Object.Pivot)]
        else:
            return [screen(self.Object.Object)]
# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticeMirror(name, extra_code = ''):
    sel = FreeCADGui.Selection.getSelectionEx()
    if not LBF.isObjectLattice(sel[0].Object) and activeBody():
        raise SelectionError("PartDesign Mode", "You can only mirror placements while in body. Please deactivate the body to mirror shapes. PartDesign Feature mirroring is not supported yet.")
    FreeCAD.ActiveDocument.openTransaction("Create LatticeMirror")
    FreeCADGui.addModule("lattice2Mirror")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.addModule("lattice2Utils")
    FreeCADGui.doCommand("sel = lattice2Utils.getSelectionAsListOfLinkSub()")
    FreeCADGui.doCommand("f = lattice2Mirror.makeLatticeMirror(name = '"+name+"')")
    FreeCADGui.doCommand("f.Object = sel[0][0]")
    FreeCADGui.doCommand("if len(sel) == 2:\n"
                         "    f.Pivot = sel[1]")
    FreeCADGui.doCommand("f.Label = '{name} of {olabel}'.format(name= f.Name, olabel= f.Object.Label)")
    if extra_code:
        FreeCADGui.doCommand(extra_code)
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCAD.ActiveDocument.commitTransaction()

class CommandLatticeMirror:
    "Command to create LatticeMirror feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Part_Mirror.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2Mirror","Mirror"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2Mirror","Lattice Mirror: mirror, inversion or 180-turn of placements and shapes")}
        
    def Activated(self):
        try:
            sel = getSelectionAsListOfLinkSub()
            if len(sel) == 1 :
                #TODO: pop-up with options
                CreateLatticeMirror(name= "Mirror", extra_code=
                    "f.FlipX = True"
                )
            elif len(sel) == 2 :
                #TODO: pop-up with options instead of guessing
                lnk = sel[1]
                if LBF.isObjectLattice(lnk[0]):
                    extra_code = (
                        "f.FlipY = True"
                    )                    
                else:
                    sh = resolveSingleSublink(lnk)
                    if sh.ShapeType == 'Face':
                        extra_code = (
                            "f.FlipZ = True"
                        )
                    elif sh.ShapeType == 'Edge':
                        extra_code = (
                            "f.FlipX = True\n"
                            "f.FlipY = True"
                        )
                    elif sh.ShapeType == 'Vertex':
                        extra_code = (
                            "f.FlipX = True\n"
                            "f.FlipY = True\n"
                            "f.FlipZ = True"
                        )
                CreateLatticeMirror(name = "Mirror", extra_code= extra_code)
            else:
                infoMessage("Lattice Mirror","Lattice Mirror feature. Mirrors shapes and placements. Please select object to be mirrored, first,"
                                             " and then the mirror object (optional). Then invoke this tool.\n\n"
                                             "Object to be mirrored: any shape, or compound of shapes, or a placement, or an array of placements."
                                             " Note that when a placement is mirrored, its Y axis is switched, for the coordinate system to remain right-handed.\n\n"
                                             "Mirror object: either a placement, an array of placements, a vertex, a line, or a plane face. If an array of"
                                             " placements is used, the object is reflected using each placement as mirror, and the result is packed into a compound.\n\n"
                                             "You can adjust the mirroring direction in property editor by editing FlipX, FlipY, FlipZ properties."
                                             " The mirror object is used to establish the coordinate system to work in. If the mirror object is not"
                                             " specified, global coordinate system is used (and a custom one can be set up by editing PivotPlacement).")
        except Exception as err:
            msgError(err)
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2Mirror', CommandLatticeMirror())

exportedCommands = ['Lattice2Mirror']

# -------------------------- /Gui command --------------------------------------------------
