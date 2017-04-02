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

__title__="Lattice Resample object: changes the number of placements in an array, maintaining overall path. Aka interpolation."
__author__ = "DeepSOIC"
__url__ = ""

import math

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2CompoundExplorer as LCE
import lattice2InterpolatorUtil as LIU
import lattice2Executer

# -------------------------- document object --------------------------------------------------

def dotProduct(list1,list2):
    sum = 0
    for i in range(0,len(list1)):
        sum += list1[i]*list2[i]
    return sum

def makeLatticeResample(name):
    '''makeLatticeResample(name): makes a LatticeResample object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticeResample, ViewProviderLatticeResample)

class LatticeResample(lattice2BaseFeature.LatticeFeature):
    "The Lattice Resample object"
    
    def derivedInit(self,obj):
        self.Type = "LatticeResample"
                
        obj.addProperty("App::PropertyLink","Base","Lattice Resample","Lattice, the array of placements to be interpolated.")
                
        obj.addProperty("App::PropertyEnumeration","TranslateMode","Lattice Resample","What to do with translation part of placements")
        obj.TranslateMode = ['interpolate', 'reset']
        obj.TranslateMode = 'interpolate'
        
        obj.addProperty("App::PropertyEnumeration","OrientMode","Lattice Resample","what to do with orientation part of placements")
        obj.OrientMode = ['interpolate', 'reset']
        obj.OrientMode = 'interpolate'
        
        obj.addProperty("App::PropertyFloat","NumberSamples","Lattice Resample","Number of placements to generate")
        obj.NumberSamples = 51

    def derivedExecute(self,obj):
        # cache stuff
        base = screen(obj.Base).Shape
        if not lattice2BaseFeature.isObjectLattice(screen(obj.Base)):
            lattice2Executer.warning(obj, "Base is not a lattice, but lattice is expected. Results may be unexpected.\n")
        input = [leaf.Placement for leaf in LCE.AllLeaves(base)]
        
        if len(input) < 2:
            raise ValueError("At least 2 placements ar needed to interpolate; there are just "+str(len(input))+" in base array.")
        if obj.NumberSamples < 2:
            raise ValueError("Can output no less than 2 samples; "+str(obj.NumberSamples)+" was requested.")
                        
        #cache mode comparisons, for speed
        posIsInterpolate = obj.TranslateMode == 'interpolate'
        posIsReset = obj.TranslateMode == 'reset'
        
        oriIsInterpolate = obj.OrientMode == 'interpolate'
        oriIsReset = obj.OrientMode == 'reset'        
        
        # construct interpolation functions
        #  prepare lists of input samples
        IArray = [float(i) for i in range(0,len(input))]
        XArray = [plm.Base.x for plm in input]
        YArray = [plm.Base.y for plm in input]
        ZArray = [plm.Base.z for plm in input]
        QArrays = [[],[],[],[]]
        prevQ = [0.0]*4
        for plm in input:
            Q = plm.Rotation.Q
            #test if quaernion has changed sign compared to previous one. 
            # Quaternions of opposite sign are equivalent in terms of rotation, 
            # but sign changes confuse interpolation, so we are detecting sign 
            # changes and discarding them
            if dotProduct(Q,prevQ) < -ParaConfusion: 
                Q = [-v for v in Q] 
            for iQ in [0,1,2,3]:
                QArrays[iQ].append( Q[iQ] ) 
            prevQ = Q
        
        #  constuct function objects
        if posIsInterpolate:
            FX = LIU.InterpolateF(IArray,XArray)
            FY = LIU.InterpolateF(IArray,YArray)
            FZ = LIU.InterpolateF(IArray,ZArray)
        if oriIsInterpolate:
            FQs = []
            for iQ in [0,1,2,3]:
                FQs.append(LIU.InterpolateF(IArray,QArrays[iQ]))
                
        # initialize output containers and loop variables
        outputPlms = [] #list of placements

        for i_output in range(0,math.trunc(obj.NumberSamples+ParaConfusion)):
            i_input = float(i_output) / (obj.NumberSamples-1) * (len(input)-1)
            pos = App.Vector()
            ori = App.Rotation()
            if posIsInterpolate:
                pos = App.Vector(FX.value(i_input), FY.value(i_input), FZ.value(i_input))
            
            if oriIsInterpolate:
                ori = App.Rotation(FQs[0].value(i_input),
                                   FQs[1].value(i_input),
                                   FQs[2].value(i_input),
                                   FQs[3].value(i_input))                
            plm = App.Placement(pos, ori)
            outputPlms.append(plm)
        return outputPlms


class ViewProviderLatticeResample(lattice2BaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_Resample.svg')
    
    def claimChildren(self):
        return [screen(self.Object.Base)]


# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticeResample(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create LatticeResample")
    FreeCADGui.addModule("lattice2Resample")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2Resample.makeLatticeResample(name='"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[0].ObjectName)
    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandLatticeResample:
    "Command to create LatticeResample feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_Resample.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_Resample","Resample Array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_Resample","Lattice Resample: interpolate placement-path using 3-rd degree b-spline interpolation.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            CreateLatticeResample(name = "Resample")
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_Resample", "Please select one object, first. The object must be a lattice object (array of placements).", None))
            mb.setWindowTitle(translate("Lattice2_Resample","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_Resample', _CommandLatticeResample())

exportedCommands = ['Lattice2_Resample']

# -------------------------- /Gui command --------------------------------------------------

