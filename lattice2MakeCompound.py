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

__title__="Mirror of Part MakeCompound command"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Mirror of Part MakeCompound command"

from lattice2Common import *
from latticeBaseFeature import isObjectLattice
import lattice2Executer

class _CommandLatticeMakeCompound:
    "Mirror of Part MakeCompound command"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_MakeCompound.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_MakeCompound","Make compound"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_MakeCompound","Make compound: combine several objects into one, without fusing them.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Make compound",
                    "Make compound command. Combines several shapes into one. The shapes are kept as-is. They are not fused together, and can be extracted unchanged.\n\n"+
                    "Compounds can contain combination of shapes of any topology: one can compound some edges with some solids. Compound is effectively another kind of group. But unlike normal FreeCAD group, compound only accepts OCC geometry. Compound cannot include meshes, dimensions, labels, or other objects that provide no Shape property.\n\n"+
                    "Note that compounds that have objects that touch or intersect are considered invalid by Part CheckGeometry. Such invalid compounds cannot be used for Part Cut/Common/Fuse.")
                return
            
            oldVal = lattice2Executer.globalIsCreatingLatticeFeature
            lattice2Executer.globalIsCreatingLatticeFeature = True
            
            sel = FreeCADGui.Selection.getSelectionEx()
            for s in sel:
                if isObjectLattice(s.Object):
                    lattice2Executer.warning(None,"For making a compound, generic shapes are expected, but some of the selected objects are placements/arrays of placements. These will be treated as generic shapes; results may be unexpected.")
                    break
            FreeCADGui.runCommand("Part_Compound")
        except Exception as err:
            msgError(err)
        finally:
            lattice2Executer.globalIsCreatingLatticeFeature = oldVal
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_Compound', _CommandLatticeMakeCompound())

exportedCommands = ["Lattice2_Compound"]