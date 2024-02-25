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

from lattice2Common import *


__title__="FuseCompound module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

# -------------------------- document object --------------------------------------------------

def makeFuseCompound(name):
    '''makeFuseCompound(name): makes a FuseCompound object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _FuseCompound(obj)
    obj.Refine = getParamRefine()
    if FreeCAD.GuiUp:
        _ViewProviderFuseCompound(obj.ViewObject)
    return obj

class _FuseCompound:
    "The FuseCompound object"
    def __init__(self,obj):
        self.Type = "FuseCompound"
        obj.addProperty("App::PropertyLink","Base","FuseCompound","Compound with self-intersections to be fused")
        obj.addProperty("App::PropertyBool","Refine","FuseCompound","True = refine resulting shape. False = output as is.")
        obj.addProperty("App::PropertyInteger","recomputeQuota","FuseCompound","recompute limiter. Will decrease by one each time it recomputes. Setting to zero disables recomputes. Setting negative makes recomputes unlimited.")
        obj.recomputeQuota = -1
        obj.Proxy = self
        

    def execute(self,obj):
        rst = None
        shps = screen(obj.Base).Shape.childShapes()
        if len(shps) > 1:
            rst = shps[0].multiFuse(shps[1:])
            if obj.Refine:
                rst = rst.removeSplitter()
            obj.Shape = rst
        else:
            obj.Shape = shps[0]
        return
        
        
class _ViewProviderFuseCompound:
    "A View Provider for the FuseCompound object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return getIconPath("Lattice2_FuseCompound.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def dumps(self):
        return None

    def loads(self,state):
        return None

    def claimChildren(self):
        return [screen(self.Object.Base)]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            screen(self.Object.Base).ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + str(err))
        return True

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateFuseCompound(name):
    FreeCAD.ActiveDocument.openTransaction("Create FuseCompound")
    FreeCADGui.addModule("FuseCompound2")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = FuseCompound2.makeFuseCompound(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = FreeCADGui.Selection.getSelection()[0]")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f.Base.ViewObject.hide()")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()

class _CommandFuseCompound:
    "Command to create FuseCompound feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_FuseCompound.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_FuseCompound","Fuse compound"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_FuseCompound","Fuse objects contained in a compound")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            CreateFuseCompound(name = "FuseCompound")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_FuseCompound", "Select a shape that is a compound whose children intersect, first!", None))
            mb.setWindowTitle(translate("Lattice2_FuseCompound","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return activeBody() is None
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_FuseCompound', _CommandFuseCompound())

exportedCommands = ['Lattice2_FuseCompound']

# -------------------------- /Gui command --------------------------------------------------
