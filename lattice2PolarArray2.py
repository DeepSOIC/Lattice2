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

__title__="Polar array feature module for lattice workbench for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

import math
turn = 2 * math.pi

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
from lattice2BaseFeature import assureProperty
import lattice2Executer
import lattice2GeomUtils
from lattice2ValueSeriesGenerator import ValueSeriesGenerator
import lattice2Utils as Utils
from lattice2Utils import linkSubList_convertToOldStyle
import lattice2AttachablePlacement as APlm

V = App.Vector

def make():
    '''make(): makes a PolarArray object.'''
    obj = lattice2BaseFeature.makeLatticeFeature('PolarArray', PolarArray, ViewProviderPolarArray, no_disable_attacher= True)
    return obj
    
def fetchArc(obj, sub):
    """returns None, or tuple (arc_span, arc_radius)"""
    if len(sub) > 0:
        linkedShape = obj.Shape.getElement(sub)
    else:
        linkedShape = obj.Shape

    if linkedShape.ShapeType == 'Edge':
        crv = linkedShape.Curve
        if isinstance(crv, Part.Circle):
            return linkedShape.LastParameter - linkedShape.FirstParameter, crv.Radius

    
class PolarArray(APlm.AttachableFeature):
    """The Lattice Polar Array of placements"""
    def derivedInit(self,selfobj):
        super(PolarArray, self).derivedInit(selfobj)
        selfobj.addProperty('App::PropertyLength','Radius',"Polar Array","Radius of the array (set to zero for just rotation).")  
        selfobj.Radius = 3 
        selfobj.addProperty('App::PropertyEnumeration', 'UseArcRange', "Polar Array", "If attachment mode is concentric, supporting arc's range can be used as array's Span or Step.")
        selfobj.UseArcRange = ['ignore', 'as Span', 'as Step']
        selfobj.addProperty('App::PropertyBool', 'UseArcRadius', "Polar Array", "If True, and attachment mode is concentric, supporting arc's radius is used as array radius.")
        selfobj.addProperty('App::PropertyEnumeration','OrientMode',"Polar Array","Orientation of placements. Zero - aligns with origin. Static - aligns with self placement.")
        selfobj.OrientMode = ['Zero', 'Static', 'Radial', 'Vortex', 'Centrifuge', 'Launchpad', 'Dominoes']
        selfobj.OrientMode = 'Radial'
        selfobj.addProperty('App::PropertyBool', 'Reverse', "Polar Array", "Reverses array direction.")
        selfobj.addProperty('App::PropertyBool', 'FlipX', "Polar Array", "Reverses x axis of every placement.")
        selfobj.addProperty('App::PropertyBool', 'FlipZ', "Polar Array", "Reverses z axis of every placement.")
        
        self.assureGenerator(selfobj)

        selfobj.ValuesSource = 'Generator'
        selfobj.SpanStart = 0
        selfobj.SpanEnd = 360
        selfobj.EndInclusive = False
        selfobj.Step = 55
        selfobj.Count = 7
        
    def assureGenerator(self, selfobj):
        '''Adds an instance of value series generator, if one doesn't exist yet.'''
        if hasattr(self,'generator'):
            return
        self.generator = ValueSeriesGenerator(selfobj)
        self.generator.addProperties(groupname= "Polar Array", 
                                     groupname_gen= "Lattice Series Generator", 
                                     valuesdoc= "List of angles, in degrees.",
                                     valuestype= 'App::PropertyFloat')
        self.updateReadonlyness(selfobj)
        
    def updateReadonlyness(self, selfobj):
        self.generator.updateReadonlyness()
        
        arc = self.fetchArc(selfobj) if self.isOnArc(selfobj) else None 
        selfobj.setEditorMode('Radius', 1 if arc and selfobj.UseArcRadius else 0)
        self.generator.setPropertyWritable('SpanEnd', False if arc and selfobj.UseArcRange == 'as Span' else True)
        self.generator.setPropertyWritable('SpanStart', False if arc and selfobj.UseArcRange == 'as Span' else True)
        self.generator.setPropertyWritable('Step', False if arc and selfobj.UseArcRange == 'as Step' else True)
    
    def fetchArc(self, selfobj):
        """returns None, or tuple (arc_span, arc_radius)"""
        if selfobj.Support:
            lnkobj, sub = selfobj.Support[0]
            sub = sub[0]
            #resolve the link        
            return fetchArc(lnkobj, sub)
        
    def derivedExecute(self,selfobj):
        self.assureGenerator(selfobj)
        self.updateReadonlyness(selfobj)
        
        selfobj.positionBySupport()
        
        # Apply links
        if (selfobj.UseArcRange != 'ignore' or selfobj.UseArcRadius) and self.isOnArc(selfobj):
            range, radius = self.fetchArc(selfobj)
            if selfobj.UseArcRange == 'as Span':
                selfobj.SpanStart = 0.0
                selfobj.SpanEnd = range/turn*360
            elif selfobj.UseArcRange == 'as Step':
                selfobj.Step = range/turn*360
            if selfobj.UseArcRadius:
                selfobj.Radius = radius
        self.generator.execute()
        
        # cache properties into variables
        radius = float(selfobj.Radius)
        values = [float(strv) for strv in selfobj.Values]
        
        irot = selfobj.Placement.inverse().Rotation
        
        # compute internam placement, one behind OrientMode property
        baseplm = App.Placement()
        is_zero = selfobj.OrientMode == 'Zero'
        is_static = selfobj.OrientMode == 'Static'
        if is_zero or is_static:
            pass
        elif selfobj.OrientMode == 'Radial':
            baseplm = App.Placement()
        elif selfobj.OrientMode == 'Vortex':
            baseplm = App.Placement(V(), App.Rotation(
                V( 0, 1, 0), 
                V(        ),
                V( 0, 0, 1)
            ))
        elif selfobj.OrientMode == 'Centrifuge':
            baseplm = App.Placement(V(), App.Rotation(
                V( 0, 1, 0), 
                V(        ),
                V(-1, 0, 0)
            ))
        elif selfobj.OrientMode == 'Launchpad':
            baseplm = App.Placement(V(), App.Rotation(
                V( 0, 0, 1), 
                V(        ),
                V( 1, 0, 0)
            ))
        elif selfobj.OrientMode == 'Dominoes':
            baseplm = App.Placement(V(), App.Rotation(
                V( 0, 0, 1), 
                V(        ),
                V( 0,-1, 0)
            ))
        else:
            raise NotImplementedError()
            
        flipX = selfobj.FlipX    
        flipZ = selfobj.FlipZ
        flipY = flipX ^ flipZ
        flipplm = App.Placement(V(), App.Rotation(
            V( -1 if flipX else 1, 0, 0), 
            V( 0, -1 if flipY else 1, 0),
            V( 0, 0, -1 if flipZ else 1)
        ))
        
        baseplm = baseplm.multiply(flipplm)
            
        # Make the array
        on_arc = self.isOnArc(selfobj)
        angleplus = -90.0 if on_arc else 0.0
        mm = -1.0 if selfobj.Reverse else +1.0
        output = [] # list of placements
        for ang in values:
            localrot = App.Rotation(App.Vector(0,0,1), ang * mm + angleplus)
            localtransl = localrot.multVec(App.Vector(radius,0,0))
            localplm = App.Placement(localtransl, localrot)
            resultplm = localplm.multiply(baseplm)
            if is_zero:
                resultplm.Rotation = irot
                resultplm = resultplm.multiply(flipplm)
            elif is_static:
                resultplm.Rotation = App.Rotation()
                resultplm = resultplm.multiply(flipplm)
            output.append(resultplm)

        return output
    
    def isOnArc(self, selfobj):
        return selfobj.MapMode == 'Concentric' and len(linkSubList_convertToOldStyle(selfobj.Support)) == 1
        
    def onChanged(self, selfobj, propname):
        super(PolarArray, self).onChanged(selfobj, propname)
        if 'Restore' in selfobj.State: return
        if propname == 'Reverse' and self.isOnArc(selfobj):
            if selfobj.Reverse == True and abs(selfobj.MapPathParameter - 0.0) < ParaConfusion:
                selfobj.MapPathParameter = 1.0
            elif selfobj.Reverse == False and abs(selfobj.MapPathParameter - 1.0) < ParaConfusion:
                selfobj.MapPathParameter = 0.0

class ViewProviderPolarArray(APlm.ViewProviderAttachableFeature):
        
    def getIcon(self):
        return getIconPath('Lattice2_PolarArray.svg')
        
# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

def CreatePolarArray(genmode = 'SpanN'):
    sublinks = Utils.getSelectionAsPropertyLinkSubList()
    FreeCAD.ActiveDocument.openTransaction("Create PolarArray")
    FreeCADGui.addModule('lattice2PolarArray2')
    FreeCADGui.addModule('lattice2Executer')
    FreeCADGui.addModule("lattice2Base.Autosize")
    FreeCADGui.doCommand('f = lattice2PolarArray2.make()')
    FreeCADGui.doCommand("f.GeneratorMode = {mode}".format(mode= repr(genmode)))
    attached = False
    if len(sublinks) == 1:
        lnk, sub = sublinks[0]
        arc = fetchArc(lnk, sub)
        if arc:
            arcspan, radius = arc
            fullcircle = abs(arcspan - turn) < ParaConfusion
            endinclusive = not fullcircle
            usearcrange = 'as Step' if genmode == 'StepN' and not fullcircle else 'as Span'
            FreeCADGui.doCommand(
                'f.Support = [(App.ActiveDocument.{lnk}, {sub})]\n'
                'f.MapMode = \'Concentric\'\n'
                'f.UseArcRange = {usearcrange}\n'
                'f.EndInclusive = {endinclusive}\n'
                'f.UseArcRadius = True'
                .format(lnk= lnk.Name, sub= repr(sub), usearcrange= repr(usearcrange), endinclusive= repr(endinclusive))
            )
            attached = True
    if not attached:
        FreeCADGui.doCommand("f.Placement.Base = lattice2Base.Autosize.convenientPosition()")    
        FreeCADGui.doCommand("f.Radius = lattice2Base.Autosize.convenientModelSize()/2")
    FreeCADGui.doCommand('lattice2Executer.executeFeature(f)')
    if len(sublinks) > 0 and not attached:
        FreeCADGui.addModule('lattice2AttachablePlacement')
        FreeCADGui.doCommand('lattice2AttachablePlacement.editNewAttachment(f)')
        #commitTransaction will be called by attachment editor
    else:
        FreeCADGui.doCommand(
            'Gui.Selection.clearSelection()\n'
            'Gui.Selection.addSelection(f)'
        )
        FreeCAD.ActiveDocument.commitTransaction()


class CommandPolarArray(object):
    """Command to create PolarArray feature"""
    def __init__(self, mode):
        self.mode = mode

    def GetResources(self):
        mode_tooltips = {
            'SpanN': "fit N placements into angle Span",
            'StepN': "make N placements spaced by Step",
            'SpanStep': "fill Span with placements spaced by Step",
            'Random': "put N placements into Span randomly",
        }
        return {'Pixmap'  : getIconPath('Lattice2_PolarArray_New.svg'),
                'MenuText': "Polar array: {mode}".format(mode= ValueSeriesGenerator.mode_userfriendly_names[self.mode]),
                'Accel': "",
                'ToolTip': "New polar array. Make a polar array of placements - {mode_tooltip}.".format(mode_tooltip= mode_tooltips[self.mode])}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection()) < 2 :
                CreatePolarArray(self.mode)
            else:
                infoMessage("Lattice Polar Array", 
                    "Polar array command. Creates a polar array of placements.\n\n"
                    "Preselection: you can select nothing -> an array on XY plane is created."
                    " You can select a circle or arc of circle -> an array on that arc/circle is"
                    " created, with array span controlled by arc range.\n\n"
                    "You can later attach the array to anything. Right-click the array in model tree, click 'Attachment...'"
                )
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
_listOfSubCommands = []
for m in ValueSeriesGenerator.gen_modes:
    cmd_name = 'Lattice2_PolarArray2_'+m
    _listOfSubCommands.append(cmd_name)
    if FreeCAD.GuiUp:
        FreeCADGui.addCommand(cmd_name, CommandPolarArray(m))


class GroupCommandPolarArray:
    def GetCommands(self):
        global _listOfSubCommands
        return tuple(_listOfSubCommands) # a tuple of command names that you want to group

    def GetDefaultCommand(self): # return the index of the tuple of the default command. This method is optional and when not implemented '0' is used  
        return 0

    def GetResources(self):
        return { 'MenuText': 'Polar Array', 'ToolTip': 'Polar Array: circular array of placements.'}
        
    def IsActive(self): # optional
        return FreeCAD.ActiveDocument is not None

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_PolarArray2_GroupCommand',GroupCommandPolarArray())



import lattice2Compatibility as Compat
if Compat.attach_extension_era:
    exportedCommands = ['Lattice2_PolarArray2_GroupCommand']
else:
    import lattice2PolarArray
    exportedCommands = lattice2PolarArray.exportedCommands

# -------------------------- /Gui command --------------------------------------------------

