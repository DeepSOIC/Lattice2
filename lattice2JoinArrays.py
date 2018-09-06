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

__title__="Lattice JoinArrays object: combine elements of two lattices"
__author__ = "DeepSOIC"
__url__ = ""

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2CompoundExplorer as LCE
import lattice2Executer

# -------------------------- document object --------------------------------------------------

def makeJoinArrays(name):
    '''makeJoinArrays(name): makes a JoinArrays object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, JoinArrays, ViewProviderJoinArrays)

class JoinArrays(lattice2BaseFeature.LatticeFeature):
    "The Lattice JoinArrays object"
        
    def derivedInit(self,obj):
        self.Type = "LatticeJoinArrays"
        
        obj.addProperty("App::PropertyLinkList","Links","Lattice JoinArrays","Links to arrays to be joined")
        
        obj.addProperty("App::PropertyBool","Interleave","Lattice JoinArrays","If false, first go all elements of array 1, nect go all elements of array 2, so on. If true, first go all first elements from each array, then all second elements, and so on.")
        
    def assureProperties(self, selfobj):
        super(JoinArrays, self).assureProperties(selfobj)
        created = self.assureProperty(selfobj, 
            'App::PropertyEnumeration', 
            'ReferencePlacementOption', 
            ['external', 'origin', 'inherit 1st'],
            "Lattice JoinArrays", 
            "Reference placement, corresponds to the original occurrence of the object to be populated."
        )
        if created:
            selfobj.ReferencePlacementOption = 'inherit 1st'
        self.assureProperty(selfobj,
            'App::PropertyBool',
            'AlignReferences',
            False,
            "Lattice JoinArrays",
            "If true, input arrays will be moved to make their reference placements equal, before joining."
        )

    def recomputeReferencePlm(self, selfobj, selfplacements): #override
        pass #disables standard recompute-reference call. The recompute is handled by derivedExecute 


    def derivedExecute(self, selfobj):
        align = selfobj.AlignReferences
        #recompute reference placement
        ref = selfobj.ReferencePlacementOption
        if ref == 'external':
            super(JoinArrays, self).recomputeReferencePlm(selfobj, [])
        elif ref == 'origin':
            self.setReferencePlm(selfobj, None)
        elif ref == 'inherit 1st':
            if len(selfobj.Links)>0:
                self.setReferencePlm(selfobj, lattice2BaseFeature.getReferencePlm(selfobj.Links[0]))
            else:
                self.setReferencePlm(selfobj, None)
        else:
            raise NotImplementedError("Reference option not implemented: " + ref)
        refplm = self.getReferencePlm(selfobj)

        #extract placements
        listlistPlms = []
        lengths = []
        for link in selfobj.Links:
            plms = lattice2BaseFeature.getPlacementsList(link, context= selfobj, dereferenced= align, torefplm = refplm)
            listlistPlms.append(plms)
            lengths.append(len(plms))
        
        #processing
        output = [] #list of placements
        if selfobj.Interleave:
            for l in lengths[1:]:
                if l != lengths[0]:
                    lattice2Executer.warning(selfobj,"Array lengths are unequal: "+repr(lengths)+". Interleaving will be inconsistent.")
                    break
            
            for iItem in range(0,max(lengths)):
                for list in listlistPlms:
                    if iItem < len(list):
                        output.append(list[iItem])
        else:
            for list in listlistPlms:
                output.extend(list)
                
        return output

class ViewProviderJoinArrays(lattice2BaseFeature.ViewProviderLatticeFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_JoinArrays.svg')

    def claimChildren(self):
        return self.Object.Links

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreateJoinArrays(name):
    sel = FreeCADGui.Selection.getSelection()
    FreeCAD.ActiveDocument.openTransaction("Create JoinArrays")
    FreeCADGui.addModule("lattice2JoinArrays")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2JoinArrays.makeJoinArrays(name='"+name+"')")
    FreeCADGui.doCommand("f.Links = []")
    for s in sel:
        FreeCADGui.doCommand("f.Links = f.Links + [App.ActiveDocument."+s.Name+"]")
    
    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


class _CommandJoinArrays:
    "Command to create JoinArrays feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_JoinArrays.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_JoinArrays","Join arrays"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_JoinArrays","Lattice JoinArrays: concatenate or interleave two or more arrays.")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection()) > 1 :
                CreateJoinArrays(name = "Join")
            else:
                infoMessage("Please select at least two lattice objects. Selected lattice objects will be concatenated or interleaved into one array.")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_JoinArrays', _CommandJoinArrays())

exportedCommands = ['Lattice2_JoinArrays']

# -------------------------- /Gui command --------------------------------------------------

