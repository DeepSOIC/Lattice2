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

__title__="Lattice ParaSeries feature"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Lattice ParaSeries feature: generates series of shapes by modifying a parameter"

import math

import FreeCAD as App
import Part

from lattice2Common import *
import lattice2BaseFeature
import lattice2Executer
import lattice2Markers as markers
from lattice2ValueSeriesGenerator import ValueSeriesGenerator

# -------------------------- document object --------------------------------------------------

def makeLatticeParaSeries(name):
    '''makeLatticeParaSeries(name): makes a LatticeParaSeries object.'''
    return lattice2BaseFeature.makeLatticeFeature(name, LatticeParaSeries, ViewProviderLatticeParaSeries)

class LatticeParaSeries(lattice2BaseFeature.LatticeFeature):
    "The Lattice ParaSeries object"
    
    def derivedInit(self,obj):
        self.Type = "LatticeParaSeries"
                
        obj.addProperty("App::PropertyLink","Object","Lattice ParaSeries","Object to make series from. Can be any generic shape, as well as an array of placements.")
        
        obj.addProperty("App::PropertyEnumeration","ParameterType","Lattice ParaSeries","Data type of parameter to vary.")
        obj.ParameterType = ['float','int','string']
        
        obj.addProperty("App::PropertyString","ParameterRef","Lattice ParaSeries","Reference to the parameter to vary. Syntax: ObjectName.Property. Examples: 'Box.Height'; 'Sketch.Constaints.myLength'.")
                        
        obj.addProperty("App::PropertyEnumeration","Recomputing","Lattice ParaSeries","Sets recomputing policy.")
        obj.Recomputing = ["Disabled", "Recompute Once", "Enabled"]
        obj.Recomputing = "Disabled" # recomputing ParaSeries can be very long, so disable it by default
        
        self.assureGenerator(obj)
        
    def assureGenerator(self, obj):
        '''Adds an instance of value series generator, if one doesn't exist yet.'''
        if hasattr(self,"generator"):
            return
        self.generator = ValueSeriesGenerator(obj)
        self.generator.addProperties(groupname= "Lattice ParaSeries", 
                                     groupname_gen= "Lattice ParaSeries Generator", 
                                     valuesdoc= "List of parameter values to compute object for.")
        self.generator.updateReadonlyness()

    def derivedExecute(self,selfobj):
        # values generator should be functional even if recomputing is disabled, so do it first
        self.assureGenerator(selfobj)
        self.generator.updateReadonlyness()
        self.generator.execute()
        
        if selfobj.Recomputing == "Disabled":
            raise ValueError(selfobj.Name+": recomputing of this object is currently disabled. Modify 'Recomputing' property to enable it.")
        try:            
            #convert values to type
            values = []
            for strv in selfobj.Values:
                if len(strv) == 0: continue
                if selfobj.ParameterType == 'float' or selfobj.ParameterType == 'int':
                    if len(strv.strip()) == 0: continue
                    v = float(strv.replace(",","."))
                    if selfobj.ParameterType == 'int':
                        v = int(round(v))
                elif selfobj.ParameterType == 'string':
                    v = strv.strip()
                else:
                    raise ValueError(selfobj.Name + ": ParameterType option not implemented: "+selfobj.ParameterType)
                values.append(v)
            
            if len(values) == 0:
                scale = 1.0
                try:
                    if not selfobj.Object.Shape.isNull():
                        scale = selfobj.Object.Shape.BoundBox.DiagonalLength/math.sqrt(3)
                except Exception:
                    pass
                if scale < DistConfusion * 100:
                    scale = 1.0
                selfobj.Shape = markers.getNullShapeShape(scale)
                raise ValueError(selfobj.Name + ": list of values is empty.") 
            
            bGui = bool(App.GuiUp)
            if bGui:
                import PySide
                progress = PySide.QtGui.QProgressDialog(u"Recomputing "+selfobj.Label, u"Abort", 0, len(values)+1)
                progress.setModal(True)
            
            doc1 = selfobj.Document
            doc2 = App.newDocument()
            object_in_doc2 = None # define the variable, to prevent del() in finally block from raising another error
            try:
                object_in_doc2 = doc2.copyObject(selfobj.Object, True)
                if bGui:
                    progress.setValue(1)
                refstr = selfobj.ParameterRef #dict(selfobj.ExpressionEngine)["ParameterRef"]
                if len(refstr) == 0:
                    raise ValueError(selfobj.Name+": ParameterRef is not set. It is required.")
                pieces = refstr.split(".")
                objname = pieces[0]
                obj_to_modify = doc2.getObject(objname)
                if obj_to_modify is None:
                    raise ValueError(selfobj.Name+": failed to get the object named '"+objname+"'. Maybe you had put in its label instead?..")
                output_shapes = []
                for val in values:
                    #set parameter
                    if obj_to_modify.isDerivedFrom("Spreadsheet::Sheet"):
                        if len(pieces) != 2:
                            raise ValueError(selfobj.Name + ": failed to parse parameter reference: "+refstr )
                        obj_to_modify.set(pieces[1], str(val))
                    elif obj_to_modify.isDerivedFrom("Sketcher::SketchObject") and pieces[1] == "Constraints":
                        if len(pieces) != 3:
                            raise ValueError(selfobj.Name + ": failed to parse parameter reference: "+refstr )
                        obj_to_modify.setDatum(pieces[2],val)
                    else:
                        if len(pieces) < 2:
                            raise ValueError(selfobj.Name + ": failed to parse parameter reference: "+refstr )
                        stack = [obj_to_modify]
                        for piece in pieces[1:-1]:
                            stack.append(getattr(stack[-1],piece))
                        setattr(stack[-1], pieces[-1], val)
                        for piece in pieces[1:-1:-1]:
                            compval = stack.pop()
                            setattr(stack[-1], piece, compval)
                        
                    
                    #recompute
                    doc2.recompute()
                    
                    #get shape
                    shape = None
                    for obj in doc2.Objects:
                        if 'Invalid' in obj.State:
                            latticeExecuter.error(obj,"Recomputing shape for parameter value of "+val+" failed.")
                            
                            scale = 1.0
                            try:
                                if not selfobj.Object.Shape.isNull():
                                    scale = selfobj.Object.Shape.BoundBox.DiagonalLength/math.sqrt(3)
                            except Exception:
                                pass
                            if scale < DistConfusion * 100:
                                scale = 1.0
                            shape = markers.getNullShapeShape(scale)
                    if shape is None:
                        shape = object_in_doc2.Shape.copy()
                    output_shapes.append(shape)
                    
                    #update progress
                    if bGui:
                        progress.setValue(progress.value()+1)
                        if progress.wasCanceled():
                            raise lattice2Executer.CancelError()

                    
            finally:
                #delete all references, before destroying the document. Probably not required, but to be sure...
                del(object_in_doc2)
                doc2_name = doc2.Name
                del(doc2)
                App.closeDocument(doc2_name)
                if bGui:
                    progress.setValue(len(values)+1)

                
            selfobj.Shape = Part.makeCompound(output_shapes)

            output_is_lattice = lattice2BaseFeature.isObjectLattice(selfobj.Object)
            if 'Auto' in selfobj.isLattice:
                new_isLattice = 'Auto-On' if output_is_lattice else 'Auto-Off'
                if selfobj.isLattice != new_isLattice:#check, to not cause onChanged without necessity (onChange messes with colors, it's better to keep user color)
                    selfobj.isLattice = new_isLattice                    
        finally:
            if selfobj.Recomputing == "Recompute Once":
                selfobj.Recomputing = "Disabled"
        return "suppress" # "suppress" disables most convenience code of lattice2BaseFeature. We do it because we build a nested array, which are not yet supported by lattice WB.

class ViewProviderLatticeParaSeries(lattice2BaseFeature.ViewProviderLatticeFeature):

    def getIcon(self):
        return getIconPath("Lattice2_ParaSeries.svg")  
        
    def claimChildren(self):
        return [self.Object.Object]

# -------------------------- /document object --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------



def CreateLatticeParaSeries(name, shapeObj):
    '''utility function; sharing common code for all populate-copies commands'''
    FreeCADGui.addModule("lattice2ParaSeries")
    FreeCADGui.addModule("lattice2Executer")
    
    #fill in properties
    FreeCADGui.doCommand("f = lattice2ParaSeries.makeLatticeParaSeries(name='"+name+"')")
    FreeCADGui.doCommand("f.Object = App.ActiveDocument."+shapeObj.Name)
    
    #execute
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    
    #hide something
    FreeCADGui.doCommand("f.Object.ViewObject.hide()")
        
    #finalize
    FreeCADGui.doCommand("Gui.Selection.addSelection(f)")
    FreeCADGui.doCommand("f = None")

def cmdCreateSeries():
    sel = FreeCADGui.Selection.getSelectionEx()
    if len(sel) == 1 :
        FreeCAD.ActiveDocument.openTransaction("Populate with copies")
        CreateLatticeParaSeries("ParaSeries",sel[0].Object)
        deselect(sel)
        FreeCAD.ActiveDocument.commitTransaction()
    else:
        raise SelectionError("Bad selection","Please select an object to generate series, first.")

class _CommandLatticeParaSeries:
    "Command to create LatticeParaSeries feature"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_ParaSeries.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_ParaSeries","ParaSeries"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_ParaSeries","ParaSeries: generate an array of shapes by varying a design parameter")}
        
    def Activated(self):
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("ParaSeries",
                    "ParaSeries command. Generates an array of shapes by varying a design parameter.\n\n"+
                    "Please select an object to generate array from. Then invoke the command. After that, set up the series in properties of ParaSeries feature created, and change Recomputing property to get a result.\n\n"+
                    "Setting up the series involves: specifying the parameter to modify (ParameterRef property), and setting up the value list.\n"+
                    "The reference is specified like an expression: ObjectName.Property. ObjectNane is the name of the object that has the parameter (name, not label - use Lattice Inspect to get the name).\n"+
                    "Examples of references:\n"+
                    "Box.Length\n"+
                    "Sketch001.Constraints.myLength (where myLength is the name of the constraint)\n"+
                    "Box.Placement.Base.y\n\n"+
                    "To set up the series of values for the parameter, you can simply edit the Values property. Or, a standard sequence can be generated (set ValuesSource to Generator)."
                    )
                return
            cmdCreateSeries()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
FreeCADGui.addCommand('Lattice2_ParaSeries', _CommandLatticeParaSeries())

exportedCommands = ['Lattice2_ParaSeries']
