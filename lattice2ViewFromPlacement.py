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

__title__="Lattice Recompute Locker: hack to manual recompute of documents."
__author__ = "DeepSOIC"
__url__ = ""

import FreeCAD as App

from lattice2Common import *
import lattice2BaseFeature as LBF
import lattice2CompoundExplorer as LCE

import Show

def getSelectedPlacement(obj, sub):
    leaves = LCE.AllLeaves(obj.Shape)
    if sub == '':
        return 0 if len(leaves) == 1 else None
    subshape = obj.Shape.getElement(sub)
    getter = {
        'Vertex': (lambda sh: sh.Vertexes),
        'Edge': (lambda sh: sh.Edges),
        'Face': (lambda sh: sh.Faces)
    } [subshape.ShapeType]
    matches = []
    for index, leaf in enumerate(leaves):
        for it_sh in getter(leaf):
            if it_sh.isSame(subshape):
                matches.append(index)
    assert(len(matches) < 2)
    return matches[0]

# --------------------------------Gui commands----------------------------------

_library = {} #instances of TempoVis, per document

class CommandViewFromPlacement:
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ViewFromPlacement.svg"),
                'MenuText': "View from placement",
                'Accel': "",
                'ToolTip': "View from placement. Places camera to where selected placement is. Click again to restore view.",
                'CmdType':"ForEdit"}
        
    def Activated(self):
        import FreeCADGui as Gui

        oldTV =  _library.pop(App.ActiveDocument.Name, None)
        if oldTV is None:            
            V = App.Vector
            sel = Gui.Selection.getSelectionEx()
            if len(sel) == 1 and len(sel[0].SubElementNames) < 2:
                #get placement
                index = getSelectedPlacement(sel[0].Object, sel[0].SubElementNames[0] if len(sel[0].SubElementNames) == 1 else '')
                plm = LBF.getPlacementsList(sel[0].Object)[index]
                OZ = plm.Rotation.multVec(V(0,0,1))
                OY = plm.Rotation.multVec(V(0,1,0))
                OX = plm.Rotation.multVec(V(1,0,0))
                print(OX)
                print(OZ)
            
                #prepare
                tv = Show.TempoVis(App.ActiveDocument)
                tv.saveCamera()
                
                #set up camera
                Gui.ActiveDocument.ActiveView.setCameraType('Perspective')
                from pivy import coin
                cam = Gui.ActiveDocument.ActiveView.getCameraNode()
                cam.position = tuple(plm.Base)
                rot = App.Rotation(V(), -OZ, -OX,'ZYX')
                cam.orientation = tuple(rot.Q)
                cam.heightAngle = -cam.heightAngle.getValue() #reversing hight angle inverts the image. Using it in conjunction with upside-down camera to effectively reverse how view reacts to mouse.
                cam.focalDistance = 1e-5 #small focal distance makes camera spin about itself
                
                #all done, remember.
                _library[App.ActiveDocument.Name] = tv
            else:
                infoMessage("Lattice2 View From Placement", 
                "Lattice2 View From Placement command."
                "\n\nPlease select a placement, and invoke this tool. The camera will be placed there,"
                " and you'll be able to rotate around."
                "\n\nClick again to leave the mode.")
        else:
            oldTV.restore()
            if Gui.ActiveDocument.ActiveView.getCameraType() == 'Perspective':
                cam = Gui.ActiveDocument.ActiveView.getCameraNode()
                cam.heightAngle = abs(cam.heightAngle.getValue()) #workaround
            
    def IsActive(self):
        if not App.ActiveDocument: return False
        return True
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_ViewFromPlacement', CommandViewFromPlacement())

exportedCommands = [
    "Lattice2_ViewFromPlacement",
]
