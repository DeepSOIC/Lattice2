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

__title__="Lattice Invert object: creates an array of placements from a compound."
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

def makeLatticeInvert(name):
    '''makeLatticeInvert(name): makes a LatticeInvert object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticeInvert, ViewProviderInvert)

class LatticeInvert(lattice2BaseFeature.LatticeFeature):
    "The Lattice Invert object"
    
    def derivedInit(self,obj):
        self.Type = "LatticeInvert"
                
        obj.addProperty("App::PropertyLink","Base","Lattice Invert","Lattice, all the placements of which are to be inverted.")
                
        obj.addProperty("App::PropertyEnumeration","TranslateMode","Lattice Invert","What to do with translation part of placements")
        obj.TranslateMode = ['invert', 'keep', 'reset']
        obj.TranslateMode = 'invert'
        
        obj.addProperty("App::PropertyEnumeration","OrientMode","Lattice Invert","what to do with orientation part of placements")
        obj.OrientMode = ['invert', 'keep', 'reset']
        obj.OrientMode = 'invert'

    def derivedExecute(self,obj):
        # cache stuff
        base = screen(obj.Base).Shape
        if not lattice2BaseFeature.isObjectLattice(screen(obj.Base)):
            lattice2Executer.warning(obj, "Base is not a lattice, but lattice is expected. Results may be unexpected.\n")
        baseChildren = LCE.AllLeaves(base)
                        
        #cache mode comparisons, for speed
        posIsInvert = obj.TranslateMode == 'invert'
        posIsKeep = obj.TranslateMode == 'keep'
        posIsReset = obj.TranslateMode == 'reset'
        
        oriIsInvert = obj.OrientMode == 'invert'
        oriIsKeep = obj.OrientMode == 'keep'
        oriIsReset = obj.OrientMode == 'reset'
        
        # initialize output containers and loop variables
        outputPlms = [] #list of placements
        
        # the essence
        for child in baseChildren:
            pos = App.Vector()
            ori = App.Rotation()
            inverted = child.Placement.inverse()
            if posIsInvert:
                pos = inverted.Base
            elif posIsKeep:
                pos = child.Placement.Base
            elif posIsReset:
                pass
            
            if oriIsInvert:
                ori = inverted.Rotation
            elif oriIsKeep:
                ori = child.Placement.Rotation
            elif oriIsReset:
                pass
                
            plm = App.Placement(pos, ori)
            outputPlms.append(plm)
        return outputPlms


class ViewProviderInvert(lattice2BaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_Invert.svg')
    
    def claimChildren(self):
        weakparenting = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Lattice2").GetBool("WeakParenting", True)
        if weakparenting:
            return []
        return [screen(self.Object.Base)]


# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticeInvert(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create LatticeInvert")
    FreeCADGui.addModule("lattice2Invert")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2Invert.makeLatticeInvert(name='"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[0].ObjectName)
    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandLatticeInvert:
    "Command to create LatticeInvert feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_Invert.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_Invert","Invert lattice"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_Invert","Lattice Invert: invert all placements in a lattice object.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            CreateLatticeInvert(name = "Invert")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_Invert", "Please select one object, first. The object must be a lattice object (array of placements).", None))
            mb.setWindowTitle(translate("Lattice2_Invert","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_Invert', _CommandLatticeInvert())

exportedCommands = ['Lattice2_Invert']

# -------------------------- /Gui command --------------------------------------------------

