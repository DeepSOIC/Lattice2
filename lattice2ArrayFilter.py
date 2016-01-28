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

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2CompoundExplorer as LCE
import lattice2Executer


__title__="Lattice ArrayFilter module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""


# -------------------------- common stuff --------------------------------------------------

def makeArrayFilter(name):
    '''makeArrayFilter(name): makes a Lattice ArrayFilter object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticeArrayFilter, ViewProviderArrayFilter)

class LatticeArrayFilter(lattice2BaseFeature.LatticeFeature):
    "The Lattice ArrayFilter object"
    
    stencilModeList = ['collision-pass','window-distance', 'pointing-at']
    
    def derivedInit(self,obj):
        self.Type = "LatticeArrayFilter"

        obj.addProperty("App::PropertyLink","Base","Lattice ArrayFilter","Array to be filtered")
        
        obj.addProperty("App::PropertyEnumeration","FilterType","Lattice ArrayFilter","")
        obj.FilterType = ['bypass','specific items']+LatticeArrayFilter.stencilModeList
        obj.FilterType = 'bypass'
        
        # properties controlling "specific items" mode
        obj.addProperty("App::PropertyString","items","Lattice ArrayFilter","list of indexes of items to be returned (like this: 1,4,8:10).")

        obj.addProperty("App::PropertyLink","Stencil","Lattice ArrayFilter","Object that defines filtering")
        
        obj.addProperty("App::PropertyLength","WindowFrom","Lattice ArrayFilter","Elements closer to stencil than this vaule are rejected by the filter.")
        obj.WindowFrom = 0.0
        obj.addProperty("App::PropertyLength","WindowTo","Lattice ArrayFilter","Elements farther from stencil than this vaule are rejected by the filter.")
        obj.WindowTo = 1.0
        
        obj.addProperty("App::PropertyBool","Invert","Lattice ArrayFilter","Output elements that are rejected by filter, instead")
        obj.Invert = False
        
        obj.Proxy = self
        

    def derivedExecute(self,obj):
        #validity check
        if not lattice2BaseFeature.isObjectLattice(obj.Base):
            lattice2Executer.warning(obj,"A lattice object is expected as Base, but a generic shape was provided. It will be treated as a lattice object; results may be unexpected.")

        output = [] #variable to receive the final list of placements
        leaves = LCE.AllLeaves(obj.Base.Shape)
        input = [leaf.Placement for leaf in leaves]
        if obj.FilterType == 'bypass':
            output = input
        elif obj.FilterType == 'specific items':
            flags = [False] * len(input)
            ranges = obj.items.split(';')
            for r in ranges:
                r_v = r.split(':')
                if len(r_v) == 1:
                    i = int(r_v[0])
                    output.append(input[i])
                    flags[i] = True
                elif len(r_v) == 2 or len(r_v) == 3:
                    if len(r_v) == 2:
                        r_v.append("") # fix issue #1: instead of checking length here and there, simply add the missing field =)
                    ifrom = None   if len(r_v[0].strip()) == 0 else   int(r_v[0])                    
                    ito = None     if len(r_v[1].strip()) == 0 else   int(r_v[1])
                    istep = None   if len(r_v[2].strip()) == 0 else   int(r_v[2])
                    output=output+input[ifrom:ito:istep]
                    for b in flags[ifrom:ito:istep]:
                        b = True
                else:
                    raise ValueError('index range cannot be parsed:'+r)
            if obj.Invert :
                output = []
                for i in xrange(0,len(input)):
                    if not flags[i]:
                        output.append(input[i])
        elif obj.FilterType == 'collision-pass':
            stencil = obj.Stencil.Shape
            for plm in input:
                pnt = Part.Vertex(plm.Base)
                d = pnt.distToShape(stencil)
                if bool(d[0] < DistConfusion) ^ bool(obj.Invert):
                    output.append(plm)
        elif obj.FilterType == 'window-distance':
            vals = [0.0] * len(input)
            for i in xrange(0,len(input)):
                if obj.FilterType == 'window-distance':
                    pnt = Part.Vertex(input[i].Base)
                    vals[i] = pnt.distToShape(obj.Stencil.Shape)[0]
            
            valFrom = obj.WindowFrom
            valTo = obj.WindowTo
            
            for i in xrange(0,len(input)):
                if bool(vals[i] >= valFrom and vals[i] <= valTo) ^ obj.Invert:
                    output.append(input[i])
        else:
            raise ValueError('Filter mode not implemented:'+obj.FilterType)
                            
        return output
        
        
class ViewProviderArrayFilter(lattice2BaseFeature.ViewProviderLatticeFeature):
    "A View Provider for the Lattice ArrayFilter object"

    def getIcon(self):
        return getIconPath("Lattice2_ArrayFilter.svg")

    def claimChildren(self):
        children = [self.Object.Base]
        if self.Object.Stencil:
            children.append(self.Object.Stencil)
        return children

def makeItemListFromSelection(sel, bMakeString = True):
    '''makeItemListFromSelection(sel, bMakeString = True): make a string for 
    "items" property of ArrayFilter from selection object. sel should be a 
    SelectionObject (e.g. Gui.Selection.getSelectionEx() returns a list of 
    SelectionObjects)
    Returns a string like
    If bMakeString == False, the output will be a list of integers'''
    
    # figure out element counts of array marker
    for (child, msg, it) in LCE.CompoundExplorer(sel.Object.Shape):
        if msg == LCE.CompoundExplorer.MSG_LEAF:
            vertices_per_marker = len(child.Vertexes)
            edges_per_marker = len(child.Edges)
            faces_per_marker = len(child.Faces)
            break;
    # get indexes 
    indexes = []
    for sub in sel.SubElementNames:
        # figure out array element index of selected shape subelement
        if "Vertex" in sub:
            i_vert = int(  sub[len("Vertex"):]  )  -  1
            i = i_vert/vertices_per_marker
        elif "Edge" in sub:
            i_edge = int(  sub[len("Edge"):]  )  -  1
            i = i_edge/edges_per_marker
        elif "Face" in sub:
            i_face = int(  sub[len("Face"):]  )  -  1
            i = i_face/faces_per_marker
        
        # add the index to index list, avoiding duplicates
        if len(indexes) > 0 and i == indexes[-1]:
            pass
        else:
            indexes.append(i)
    if bMakeString:
        list_of_strings = [str(item) for item in indexes]
        return ';'.join(list_of_strings)
    else:
        return indexes
    

def CreateLatticeArrayFilter(name,mode):
    sel = FreeCADGui.Selection.getSelectionEx()
    
    # selection order independece logic (lattice object and generic shape stencil can be told apart)
    iLtc = 0 #index of lattice object in selection
    iStc = 1 #index of stencil object in selection
    for i in range(0,len(sel)):
        if lattice2BaseFeature.isObjectLattice(sel[i]):
            iLtc = i
            iStc = i-1 #this may give negative index, but python accepts negative indexes
            break
    FreeCAD.ActiveDocument.openTransaction("Create ArrayFilter")
    FreeCADGui.addModule("lattice2ArrayFilter")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("sel = Gui.Selection.getSelectionEx()")    
    FreeCADGui.doCommand("f = lattice2ArrayFilter.makeArrayFilter(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = App.ActiveDocument."+sel[iLtc].ObjectName)
    FreeCADGui.doCommand("f.FilterType = '"+mode+"'")
    if mode == 'specific items':
        FreeCADGui.doCommand("f.items = lattice2ArrayFilter.makeItemListFromSelection(sel["+str(iLtc)+"])")
        if len(sel[0].SubElementNames) == 1:
            FreeCADGui.doCommand("f.ExposePlacement = True")
    else:
        FreeCADGui.doCommand("f.Stencil = App.ActiveDocument."+sel[iStc].ObjectName)
    FreeCADGui.doCommand("for child in f.ViewObject.Proxy.claimChildren():\n"+
                         "    child.ViewObject.hide()")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

_listOfSubCommands = []

class _CommandArrayFilterItems:
    "Command to create Lattice ArrayFilter feature in 'specific items' mode based on current selection"
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ArrayFilter.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_ArrayFilter","Array Filter: selected items"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_ArrayFilter","Array Filter: keep only items that are currently selected.")}
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 1 and sel[0].HasSubObjects:
            CreateLatticeArrayFilter(name= "ArrayFilter", mode= 'specific items')
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_ArrayFilter", "Select elements of a lattice feature, first! Placements other than those that were selected are going to be rejected. The order of selection matters.", None))
            mb.setWindowTitle(translate("Lattice2_ArrayFilter","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_ArrayFilter_Items', _CommandArrayFilterItems())
_listOfSubCommands.append('Lattice2_ArrayFilter_Items')

class _CommandArrayFilterStencilBased:
    "Command to create Lattice ArrayFilter feature in 'specific items' mode based on current selection"
    
    def __init__(self, mode):
        self.mode = mode
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ArrayFilter.svg"),
                'MenuText': "Array Filter: " + {"collision-pass":"touching",
                                                "window-distance":"within distance window",
                                                "pointing-at":"pointing at shape"}[mode],
                'Accel': "",
                'ToolTip': {"collision-pass":"keep only placements that are on and/or in a stencil shape",
                            "window-distance":"keep only placements that are within distance window to stencil shape",
                            "pointing-at":"keep only placements whose X axis ray touches stencil object"}[mode]}
        
    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 2 :
            CreateLatticeArrayFilter(name= "ArrayFilter", mode= self.mode)
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_ArrayFilter", "Select a lattice array and a stencil shape, first!", None))
            mb.setWindowTitle(translate("Lattice2_ArrayFilter","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
for mode in LatticeArrayFilter.stencilModeList:
    cmdName = 'Lattice2_ArrayFilter'+mode.replace("-","_")
    FreeCADGui.addCommand(cmdName, _CommandArrayFilterStencilBased(mode))
    _listOfSubCommands.append(cmdName)
    
class GroupCommandLatticeArrayFilter:
    def GetCommands(self):
        global _listOfSubCommands
        return tuple(_listOfSubCommands) # a tuple of command names that you want to group

    def GetDefaultCommand(self): # return the index of the tuple of the default command. This method is optional and when not implemented '0' is used  
        return 0

    def GetResources(self):
        return { 'MenuText': 'Array filter:', 
                 'ToolTip': 'Array filter: tool to exctract specific elements from lattice2 arrays.'}
        
    def IsActive(self): # optional
        return bool(App.ActiveDocument)
        
FreeCADGui.addCommand('Lattice2_ArrayFilter_GroupCommand',GroupCommandLatticeArrayFilter())


def ExplodeArray(feature):
    plms = lattice2BaseFeature.getPlacementsList(feature)
    features_created = []
    for i in range(len(plms)):
        af = makeArrayFilter(name = 'Placment')
        af.Label = u'Placement' + unicode(i)
        af.Base = feature
        af.FilterType = 'specific items'
        af.items = str(i)
        af.ExposePlacement = True
        af.ViewObject.DontUnhideOnDelete = True
        features_created.append(af)
    return features_created

def cmdExplodeArray():
    App.ActiveDocument.openTransaction("Explode array")
    try:
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) != 1:
            raise SelectionError("Bad selection","One array to be exploded must be selected. You have selected {num} objects.".format(num= len(sel)))
        obj = sel[0].Object
        FreeCADGui.addModule("lattice2ArrayFilter")
        FreeCADGui.addModule("lattice2Executer")
        FreeCADGui.doCommand("input_obj = App.ActiveDocument."+obj.Name)
        old_state = lattice2Executer.globalIsCreatingLatticeFeature
        lattice2Executer.globalIsCreatingLatticeFeature = True #for warnings to pop up
        FreeCADGui.doCommand("output_objs = lattice2ArrayFilter.ExplodeArray(input_obj)")
        lattice2Executer.globalIsCreatingLatticeFeature = old_state
        FreeCADGui.doCommand("\n".join([
                             "if len(output_objs) > 1:",
                             "    group = App.ActiveDocument.addObject('App::DocumentObjectGroup','GrExplode_'+input_obj.Name)",
                             "    group.Group = output_objs",
                             "    group.Label = 'Placements of '+input_obj.Label",
                             "    App.ActiveDocument.recompute()",
                             "else:",
                             "    lattice2Executer.executeFeature(output_objs[0])",
                             "",
                             ])                             )
        FreeCADGui.doCommand("input_obj.ViewObject.hide()")
    except Exception:
        App.ActiveDocument.abortTransaction()
        lattice2Executer.globalIsCreatingLatticeFeature = False
        raise
        
    App.ActiveDocument.commitTransaction()


class _CommandExplodeArray:
    "Command to explode array with parametric links to its elements"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ExplodeArray.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_ArrayFilter","Explode array"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_ArrayFilter","Explode array: get each element of array as a separate object")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())  > 0  :
                cmdExplodeArray()
            else:
                infoMessage("Explode array", 
                            "'Explode Array' command. Makes placements of array available as separate document objects.\n\n"+
                            "Select an object that is a Lattice array of placements, then invoke this command.")
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_ExplodeArray', _CommandExplodeArray())

exportedCommands = ['Lattice2_ArrayFilter_GroupCommand', 'Lattice2_ExplodeArray']

# -------------------------- /Gui command --------------------------------------------------
