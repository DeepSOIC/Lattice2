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

__title__="Base feature module for lattice object of lattice workbench for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

import Part
from pivy import coin

from latticeCommon import *
import latticeCompoundExplorer as LCE

def makeLatticeFeature(name, AppClass, icon, ViewClass = None):
    '''makeLatticeFeature(name, AppClass, ViewClass = None): makes a document object for a LatticeFeature-derived object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    AppClass(obj)
    if ViewClass:
        ViewClass(obj.ViewObject)
    else:
        vp = ViewProviderLatticeFeature(obj.ViewObject)
        vp.icon = icon
    return obj
    

class LatticeFeature():
    "Base object for lattice objects (arrays of placements)"
    
    def __init__(self,obj):
        self.Type = "latticeFeature"

        prop = "NumElements"
        obj.addProperty("App::PropertyInteger",prop,"Info","Number of placements in the array")
        obj.setEditorMode(prop, 1) # set read-only
        self.derivedInit(obj)
        
        obj.Proxy = self

        
    def derivedInit(self, obj):
        '''for overriding by derived classes'''
        pass
        
    def execute(self,obj):
        derivedExecute(self, obj)
        obj.NumElements = LCE.CalculateNumberOfLeaves(obj.Shape)
        
        return
    
    def derivedExecute():
        '''For overriding by derived class'''
        pass
    
    
class ViewProviderLatticeFeature:
    "A View Provider for base lattice object"

    def __init__(self,vobj):
        vobj.Proxy = self
#        vobj.DisplayMode = "Markers"
        vobj.PointSize = 4
        vobj.PointColor = (1.0, 0.7019608020782471, 0.0, 0.0) #orange
       
    def getIcon(self):
        if hasattr(self, "icon"):
            if self.icon:
                return getIconPath(self.icon)
        return getIconPath("Lattice.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None


    