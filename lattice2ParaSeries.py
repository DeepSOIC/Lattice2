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

# --------------------------- general routines ------------------------------------------------

def getParameter(doc, strParameter):
    return setParameter(doc, strParameter, value= None, get_not_set= True)

def setParameter(doc, strParameter, value, get_not_set = False):
    '''Sets parameter in the model. strParameter should be like "Box.Height"'''
    pieces = strParameter.split(".")
    objname = pieces[0]
    obj_to_modify = doc.getObject(objname)
    if obj_to_modify is None:
        raise ValueError(selfobj.Name+": failed to get the object named '"+objname+"'. Maybe you had put in its label instead?..")
    
    if obj_to_modify.isDerivedFrom("Spreadsheet::Sheet"):
        # SPECIAL CASE: spreadsheet cell
        if len(pieces) != 2:
            raise ValueError(selfobj.Name + ": failed to parse parameter reference: "+refstr )
        oldval = obj_to_modify.get(pieces[1])
        if get_not_set:
            return oldval
        if value != oldval:
            obj_to_modify.set(pieces[1], str(value))
    elif obj_to_modify.isDerivedFrom("Sketcher::SketchObject") and pieces[1] == "Constraints":
        # SPECIAL CASE: sketcher constraint
        if len(pieces) != 3:
            raise ValueError(selfobj.Name + ": failed to parse parameter reference: "+refstr )
        oldval = obj_to_modify.getDatum(pieces[2])
        if get_not_set:
            return oldval
        if value != oldval:
            try:
                obj_to_modify.setDatum(pieces[2],value)
            except ValueError as err:
                # strangely. n setDatum, sketch attempts to solve itself, and if fails, throws. However, the constraint datum is actually modified... funny, isn't it?
                App.Console.PrintWarning("Setting sketch constraint {constr} failed with a ValueError. This could have been caused by sketch failing to be solved.\n"
                                         .format(constr= pieces[2]))
    else:
        # All other non-special cases: properties or subproperties of objects
        if len(pieces) < 2:
            raise ValueError(selfobj.Name + ": failed to parse parameter reference: "+refstr )
        # Extract property, subproperty, subsub... FreeCAD doesn't track mutating returned objects, so we need to mutate them and write back explicitly.
        stack = [obj_to_modify]
        for piece in pieces[1:-1]:
            stack.append(getattr(stack[-1],piece))
        oldval = getattr(stack[-1], pieces[-1])
        if get_not_set:
            return oldval
        if value != oldval:
            setattr(stack[-1], pieces[-1], value)
            for piece in pieces[1:-1:-1]:
                compval = stack.pop()
                setattr(stack[-1], piece, compval)

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
        
        obj.addProperty("App::PropertyString","ParameterRef","Lattice ParaSeries","Reference to the parameter to vary. Syntax: ObjectName.Property. Examples: 'Box.Height'; 'Sketch.Constraints.myLength'.")
                        
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
            #test parameter references and read out their current values
            refstr = selfobj.ParameterRef #dict(selfobj.ExpressionEngine)["ParameterRef"]
            refstrs = refstr.replace(";","\t").split("\t")
            defvalues = []
            for refstr in refstrs:
                refstr = refstr.strip();
                val = None;
                try:
                    val = getParameter(selfobj.Document,refstr)
                except Exception as err:
                    App.Console.PrintError("{obj}: failed to read out parameter '{param}': {err}\n"
                                            .format(obj= selfobj.Name,
                                                    param= refstr,
                                                    err= str(err)))
                defvalues.append(val)
            N_params = len(defvalues)
            if N_params == 0:
                raise ValueError(selfobj.Name+": ParameterRef is not set. It is required.")
            
            #parse values
            values = []
            for strrow in selfobj.Values:
                if len(strrow) == 0:
                    break;
                row = strrow.split(";")
                row = [(strv.strip() if len(strv.strip())>0 else None) for strv in row] # clean out spaces and replace empty strings with None
                if len(row) < N_params:
                    row += [None]*(N_params - len(row))
                values.append(row)
            
            # convert values to type, filling in defaults where values are missing
            for row in values:
                for icol in range(N_params):
                    strv = row[icol]
                    val = None
                    if strv is None:
                        val = defvalues[icol]
                    elif selfobj.ParameterType == 'float' or selfobj.ParameterType == 'int':
                        val = float(strv.replace(",","."))
                        if selfobj.ParameterType == 'int':
                            val = int(round(val))
                    elif selfobj.ParameterType == 'string':
                        val = strv.strip()
                    else:
                        raise ValueError(selfobj.Name + ": ParameterType option not implemented: "+selfobj.ParameterType)
                    row[icol] = val
            
            if len(values) == 0:
                scale = 1.0
                try:
                    if not screen(selfobj.Object).Shape.isNull():
                        scale = screen(selfobj.Object).Shape.BoundBox.DiagonalLength/math.sqrt(3)
                except Exception:
                    pass
                if scale < DistConfusion * 100:
                    scale = 1.0
                selfobj.Shape = markers.getNullShapeShape(scale)
                raise ValueError(selfobj.Name + ": list of values is empty.") 
            
            bGui = False #bool(App.GuiUp) #disabled temporarily, because it causes a crash if property edits are approved by hitting Enter
            if bGui:
                import PySide
                progress = PySide.QtGui.QProgressDialog(u"Recomputing "+selfobj.Label, u"Abort", 0, len(values)+1)
                progress.setModal(True)
                progress.show()
            
            doc1 = selfobj.Document
            doc2 = App.newDocument() #create temporary doc to do the computations
            
            # assign doc's filename before copying objects, otherwise we get errors with xlinks
            try:
                doc2.FileName = doc1.FileName
            except Exception as err:
                pass #in old FreeCADs, FileName property is read-only, we can safely ignore that
            
            object_in_doc2 = None # define the variable, to prevent del() in finally block from raising another error
            try:
                doc2.copyObject(screen(selfobj.Object), True)
                
                #if there are nested paraseries in the dependencies, make sure to enable them
                for objd2 in doc2.Objects:
                    if hasattr(objd2,"Recomputing"):
                        try:
                            objd2.Recomputing = "Enabled"
                            objd2.purgeTouched()
                        except exception:
                            lattice2Executer.warning(selfobj,"Failed to enable recomputing of "+objd2.Name)
                
                object_in_doc2 = doc2.getObject(screen(selfobj.Object).Name)
                if bGui:
                    progress.setValue(1)
                output_shapes = []
                for row in values:
                    for icol in range(len(row)):
                        setParameter(doc2, refstrs[icol].strip(), row[icol])
                    
                    #recompute
                    doc2.recompute()
                    
                    #get shape
                    shape = None
                    for obj in doc2.Objects:
                        if 'Invalid' in obj.State:
                            lattice2Executer.error(obj,"Recomputing shape for parameter value of "+repr(row)+" failed.")
                            
                            scale = 1.0
                            try:
                                if not screen(selfobj.Object).Shape.isNull():
                                    scale = screen(selfobj.Object).Shape.BoundBox.DiagonalLength/math.sqrt(3)
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

            output_is_lattice = lattice2BaseFeature.isObjectLattice(screen(selfobj.Object))
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
        return [screen(self.Object.Object)]

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
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_ParaSeries', _CommandLatticeParaSeries())

exportedCommands = ['Lattice2_ParaSeries']
