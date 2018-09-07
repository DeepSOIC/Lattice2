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

__title__="Lattice Resample object: changes the number of placements in an array, maintaining overall path. Aka interpolation."
__author__ = "DeepSOIC"
__url__ = ""

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2InterpolatorUtil as LIU
import lattice2Executer
from lattice2ValueSeriesGenerator import ValueSeriesGenerator

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
    
    def derivedInit(self,selfobj):
        selfobj.addProperty("App::PropertyLink","Base","Lattice Resample","Lattice, the array of placements to be interpolated.")
                
        selfobj.addProperty("App::PropertyEnumeration","TranslateMode","Lattice Resample","What to do with translation part of placements")
        selfobj.TranslateMode = ['interpolate', 'reset']
        selfobj.TranslateMode = 'interpolate'
        
        selfobj.addProperty("App::PropertyEnumeration","OrientMode","Lattice Resample","what to do with orientation part of placements")
        selfobj.OrientMode = ['interpolate', 'reset']
        selfobj.OrientMode = 'interpolate'
        
        self.assureGenerator(selfobj)
        selfobj.ValuesSource = "Generator"
        selfobj.GeneratorMode = "SpanN"
        selfobj.EndInclusive = True
        selfobj.SpanStart = 0.0
        selfobj.SpanEnd = 1.0
        selfobj.Step = 1.0/51.0
        selfobj.Count = 51
        
    def assureProperties(self, selfobj, creating_new = False):
        super(LatticeResample, self).assureProperties(selfobj, creating_new)

        created = self.assureProperty(selfobj, 
            'App::PropertyEnumeration', 
            'ReferencePlacementOption', 
            ['external', 'origin', 'inherit', 'SpanStart', 'SpanEnd', 'at custom value', 'first placement', 'last placement'],
            "Lattice Resample", 
            "Reference placement, corresponds to the original occurrence of the object to be populated."
        )
        if created:
            selfobj.ReferencePlacementOption = 'SpanStart'
        self.assureProperty(selfobj, 'App::PropertyFloat', 'ReferenceValue', 0.0, "Lattice Resample", "Sets the value to use for generating ReferencePlacement. This value sets, what coordinate the object to be populated corresponds to.")

    def assureGenerator(self, selfobj):
        '''Adds an instance of value series generator, if one doesn't exist yet.'''
        if hasattr(self,"generator"):
            return
        self.generator = ValueSeriesGenerator(selfobj)
        self.generator.addProperties(groupname= "Lattice Array", 
                                     groupname_gen= "Lattice Series Generator", 
                                     valuesdoc= "List of parameter values. Values should be in range 0..n-1 for interpolation, and can be outside for extrapolation.",
                                     valuestype= "App::PropertyFloat")
    
    def updateReadonlyness(self, selfobj):
        super(LatticeResample, self).updateReadonlyness(selfobj)
        
        self.assureGenerator(selfobj)
        self.generator.updateReadonlyness()
        
        selfobj.setEditorMode('ReferenceValue', 0 if selfobj.ReferencePlacementOption == 'at custom value' else 2)


    def recomputeReferencePlm(self, selfobj, selfplacements): #override
        if selfobj.ReferencePlacementOption == 'external':
            super(LatticeResample, self).recomputeReferencePlm(selfobj, selfplacements)
        #the remaining options are handled in derivedExecute

    def derivedExecute(self,selfobj):
        self.assureGenerator(selfobj)
        
        self.generator.execute()
        values = [float(strv) for strv in selfobj.Values]

        input = lattice2BaseFeature.getPlacementsList(selfobj.Base)
        
        if len(input) < 2:
            raise ValueError("At least 2 placements ar needed to interpolate; there are just "+str(len(input))+" in base array.")

        #cache mode comparisons, for speed
        posIsInterpolate = selfobj.TranslateMode == 'interpolate'
        posIsReset = selfobj.TranslateMode == 'reset'
        
        oriIsInterpolate = selfobj.OrientMode == 'interpolate'
        oriIsReset = selfobj.OrientMode == 'reset'        
        
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
                
        def plmByVal(val):
            pos = App.Vector()
            ori = App.Rotation()
            if posIsInterpolate:
                pos = App.Vector(FX.value(val), FY.value(val), FZ.value(val))
            
            if oriIsInterpolate:
                ori = App.Rotation(FQs[0].value(val),
                                   FQs[1].value(val),
                                   FQs[2].value(val),
                                   FQs[3].value(val))                
            return App.Placement(pos, ori)

        output = [plmByVal(val) for val in values]

        # update reference placement
        ref = selfobj.ReferencePlacementOption
        if ref == 'external':
            pass
        elif ref == 'origin':
            self.setReferencePlm(selfobj, None)
        elif ref == 'inherit':
            self.setReferencePlm(selfobj, lattice2BaseFeature.getReferencePlm(selfobj.Base))
        elif ref == 'SpanStart':
            self.setReferencePlm(selfobj, plmByVal(float(selfobj.SpanStart)))
        elif ref == 'SpanEnd':
            self.setReferencePlm(selfobj, plmByVal(float(selfobj.SpanEnd)))
        elif ref == 'at custom value':
            self.setReferencePlm(selfobj, plmByVal(float(selfobj.ReferenceValue)))
        elif ref == 'first placement':
            self.setReferencePlm(selfobj, output[0])
        elif ref == 'last placement':
            self.setReferencePlm(selfobj, output[-1])
        else:
            raise NotImplementedError("Reference option not implemented: " + ref)
            
        return output


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
    FreeCADGui.addModule("lattice2Resample2")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2Resample2.makeLatticeResample(name='"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[0].ObjectName)
    FreeCADGui.doCommand("f.setExpression('SpanEnd', '{base}.NumElements - 1')".format(base= lattice2BaseFeature.source(sel[0].Object)[1].Name))
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
        try:
            if len(FreeCADGui.Selection.getSelection()) == 1 :
                CreateLatticeResample(name = "Resample")
            else:
                infoMessage(
                    "Lattice Resample command. Interpolates an array of placements, using 3-rd dergee bsplines.\n\n"
                    "Please select one object, first. The object must be an array of placements."
                )
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_Resample2', _CommandLatticeResample())

exportedCommands = ['Lattice2_Resample2']

# -------------------------- /Gui command --------------------------------------------------

