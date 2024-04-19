#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Victor Titov (DeepSOIC)                          *
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

__title__="LatticeSlice module for FreeCAD"
__author__ = "DeepSOIC"

# -------------------------- document object --------------------------------------------------

def makeLatticeSlice(name):
    '''makeLatticeSlice(name): makes a LatticeSlice object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    LatticeSlice(obj)
    obj.Refine = getParamRefine()
    if FreeCAD.GuiUp:        
        ViewProviderLatticeSlice(obj.ViewObject)
    return obj

def float_fuzzy_equal(v1, v2, rel_tol):
    return abs(v1-v2) <= (abs(v1)+abs(v2))*0.5*rel_tol

class LatticeSlice:
    "The LatticeSlice object"
    def __init__(self,obj):
        self.Type = "LatticeSlice"
        obj.addProperty("App::PropertyLink","Base","LatticeSlice","Object to slice. Can be almost anything, including invalid compounds.")
        obj.addProperty("App::PropertyLink","Tool","LatticeSlice","Slicer object. Must be a solid, or a face/shell. If compound, children will be used for successive slices.")
        obj.addProperty("App::PropertyBool","Refine","LatticeSlice","True = refine resulting shape. False = output as is.")

        obj.Proxy = self
        

    def execute(self,obj):
        rst = []
        pieces = LCE.AllLeaves(screen(obj.Base).Shape)
        cutters = LCE.AllLeaves(screen(obj.Tool).Shape)
        # prepare cutter shapes by converting them to solids
        cutters_solids = []
        for cutter in cutters:
            if cutter.ShapeType == "Face":
                cutter = Part.makeShell([cutter])
            if cutter.ShapeType == "Shell":
                cutter = Part.makeSolid(cutter)
            if cutter.ShapeType == "Solid":
                # all right, nothing to do
                cutters_solids.append(cutter)
            else:
                raise TypeError("Cannot slice with shape of type '{typ}'".format(typ= cutter.ShapeType))
        # cut everything successively with one cutter at a time
        for cutter in cutters_solids:
            pieces_old = pieces
            pieces = []
            for piece in pieces_old:
                pieces_1 = LCE.AllLeaves(piece.cut(cutter))
                pieces_2 = LCE.AllLeaves(piece.common(cutter))
                # when cutting with shells, and object doesn't intersect cutter, duplicates are sometimes produced. This is probably as occ bug. 
                # But we can filter the duplicates out. The trick is to test, if the result of a cut is the same as the original, which can be done by simply comparing masses.
                pieces_12 = pieces_1+pieces_2
                all_same = True
                for piece_test in pieces_12:
                    if float_fuzzy_equal(piece_test.Mass, piece.Mass, 1e-9):
                        # piece doesn't intersect cutter (probably).
                        # this test may fail, if the piece cut off by the cutter is very small.... So we discard cut result only if all masses are equal (no smaller objects are found)
                        pass
                    else:
                        all_same = False
                        break
                if all_same:
                    #the object doesn't intersect with cutter. Special processing, to remove duplicates if we are cutting with shells.
                    pieces += [piece]
                else:
                    pieces += pieces_1 + pieces_2
        if obj.Refine:
            pieces_old = pieces
            pieces = []
            for piece in pieces_old:
                pieces.append(piece.removeSplitter())
        obj.Shape = Part.makeCompound(pieces)
        
class ViewProviderLatticeSlice:
    "A View Provider for the LatticeSlice object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return getIconPath("Lattice2_Slice.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def dumps(self):
        return None

    def loads(self,state):
        return None

    def claimChildren(self):
        return [screen(self.Object.Base), screen(self.Object.Tool)]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            screen(self.Object.Base).ViewObject.show()
            screen(self.Object.Tool).ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + str(err))
        return True

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticeSlice(name):
    FreeCAD.ActiveDocument.openTransaction("Create LatticeSlice")
    FreeCADGui.addModule("lattice2Slice")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("sel = FreeCADGui.Selection.getSelectionEx()")
    FreeCADGui.doCommand("f = lattice2Slice.makeLatticeSlice(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = sel[0].Object")
    FreeCADGui.doCommand("f.Tool = sel[1].Object")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f.Base.ViewObject.hide()")
    FreeCADGui.doCommand("f.Tool.ViewObject.hide()")
    FreeCAD.ActiveDocument.commitTransaction()

class CommandLatticeSlice:
    "Command to create LatticeSlice feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_Slice.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2Slice","Slice"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2Slice","Lattice Slice: Split object by cutting it with another object, and pack resulting pieces as compound.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelectionEx()) == 2 :
                CreateLatticeSlice(name = "Slice")
            else:
                infoMessage("Lattice Slice","Please select object to be sliced, first, then the cutter object. Then invoke this tool.\n\n"
                                            "Object to be sliced: any shape, or compound of shapes (self-intersecting compounds are allowed).\n\n"
                                            "Cutter object: face, shell, or solid. Or a compound of any of these (self-intersecting compound allowed). Shells must be manifold (no triple-connected edges are allowed; non-closed is OK).")
        except Exception as err:
            msgError(err)
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return activeBody() is None
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2Slice', CommandLatticeSlice())

exportedCommands = ['Lattice2Slice']

# -------------------------- /Gui command --------------------------------------------------
