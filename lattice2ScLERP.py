#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2019 - Victor Titov (DeepSOIC)                          *
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

__title__="Lattice ScLERP object: interpolation between two placements."
__author__ = "DeepSOIC"

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2Executer
from lattice2ValueSeriesGenerator import ValueSeriesGenerator

# -------------------------- document object --------------------------------------------------
def makeLatticeScLERP(name):
    '''makeLatticeScLERP(name): makes a LatticeScLERP object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticeScLERP, ViewProviderLatticeScLERP)

class LatticeScLERP(lattice2BaseFeature.LatticeFeature):
    "The Lattice ScLERP object"
    
    def derivedInit(self,host):
        host.addProperty("App::PropertyLink","Placement1Ref","Lattice ScLERP","First placement, or an array of two placements to interpolate between.")
        host.addProperty("App::PropertyLink","Placement2Ref","Lattice ScLERP","Second placement to interpolate between.")
        host.addProperty("App::PropertyBool","Shorten","Lattice ScLERP","Use shortest path. (if not, and angle difference of two placement exceeds 180 degrees, longer path will be taken)")
        host.Shorten = True
                        
        self.assureGenerator(host)
        host.ValuesSource = "Generator"
        host.GeneratorMode = "SpanN"
        host.EndInclusive = True
        host.SpanStart = 0.0
        host.SpanEnd = 1.0
        host.Step = 1.0/11
        host.Count = 11
        
    def assureGenerator(self, host):
        '''Adds an instance of value series generator, if one doesn't exist yet.'''
        if hasattr(self,"generator"):
            return
        self.generator = ValueSeriesGenerator(host)
        self.generator.addProperties(groupname= "Lattice Array", 
                                     groupname_gen= "Lattice Series Generator", 
                                     valuesdoc= "List of parameter values. Values should be in range 0..1 for interpolation, and can be outside for extrapolation.",
                                     valuestype= "App::PropertyFloat")
    
    def updateReadonlyness(self, host):
        super(LatticeScLERP, self).updateReadonlyness(host)
        
        self.assureGenerator(host)
        self.generator.updateReadonlyness()
        
        #host.setEditorMode('ReferenceValue', 0 if host.ReferencePlacementOption == 'at custom value' else 2)

    def derivedExecute(self,host):
        self.assureGenerator(host)
        
        self.generator.execute()
        values = [float(strv) for strv in host.Values]

        input = lattice2BaseFeature.getPlacementsList(host.Placement1Ref)
        if host.Placement2Ref is not None:
            input.extend(lattice2BaseFeature.getPlacementsList(host.Placement2Ref))
        
        if len(input) != 2:
            raise ValueError("Need exactly 2 placements. {n} provided.".format(n= len(input)))
            
        plm1, plm2 = input

        # construct interpolation functions
        #  prepare lists of input samples
                
        def plmByVal(val):
            return plm1.sclerp(plm2, val, host.Shorten)

        output = [plmByVal(val) for val in values]

        ## update reference placement
        #ref = host.ReferencePlacementOption
        #if ref == 'external':
        #    pass
        #elif ref == 'origin':
        #    self.setReferencePlm(host, None)
        #elif ref == 'inherit':
        #    self.setReferencePlm(host, lattice2BaseFeature.getReferencePlm(host.Base))
        #elif ref == 'SpanStart':
        #    self.setReferencePlm(host, plmByVal(float(host.SpanStart)))
        #elif ref == 'SpanEnd':
        #    self.setReferencePlm(host, plmByVal(float(host.SpanEnd)))
        #elif ref == 'at custom value':
        #    self.setReferencePlm(host, plmByVal(float(host.ReferenceValue)))
        #elif ref == 'first placement':
        #    self.setReferencePlm(host, output[0])
        #elif ref == 'last placement':
        #    self.setReferencePlm(host, output[-1])
        #else:
        #    raise NotImplementedError("Reference option not implemented: " + ref)
        #    
        return output


class ViewProviderLatticeScLERP(lattice2BaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_Resample.svg')
    
    def claimChildren(self):
        weakparenting = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Lattice2").GetBool("WeakParenting", True)
        if weakparenting:
            return []
        return [child for child in [self.Object.Placement1Ref,self.Object.Placement2Ref] if child is not None]


# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateLatticeScLERP(name):
    sel = FreeCADGui.Selection.getSelectionEx()
    FreeCAD.ActiveDocument.openTransaction("Create LatticeScLERP")
    FreeCADGui.addModule("lattice2ScLERP")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2ScLERP.makeLatticeScLERP(name='"+name+"')")
    FreeCADGui.doCommand("f.Placement1Ref = App.ActiveDocument."+sel[0].ObjectName)
    if len(sel) > 1:
        FreeCADGui.doCommand("f.Placement2Ref = App.ActiveDocument."+sel[1].ObjectName)
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCAD.ActiveDocument.commitTransaction()


class CommandLatticeScLERP:
    "Command to create LatticeScLERP feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ScLERP.svg"),
                'MenuText': "Helical interpolation (ScLERP)",
                'Accel': "",
                'ToolTip': "Helical interpolation (ScLERP): divides the move from one placement to another into a number of equal-transform steps."}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection()) in [1, 2] :
                CreateLatticeScLERP(name = "ScLERP")
            else:
                infoMessage(
                    "Helical interpolation (ScLERP)",
                    "Lattice Helical interpolation (ScLERP) command. Interpolates between two placements using ScLERP."
                    " It cretes a helical path between two placements, so that the placement moves and rotates by an"
                    " equal transform for each step. \n\n"
                    "Please select two placements, first. It can be two placements in one object, or two single placement objects."
                )
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_ScLERP', CommandLatticeScLERP())

exportedCommands = ['Lattice2_ScLERP'] if hasattr(App.Placement, 'sclerp') else []

# -------------------------- /Gui command --------------------------------------------------
