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
            try:
                setattr(stack[-1], pieces[-1], value)
            except TypeError as err:
                # setting int properties to float value inconveniently fails. 
                # we'll try to set int instead, and if it fails - then the error 
                # is raised
                try:
                    setattr(stack[-1], pieces[-1], int(value))
                except Exception:
                    raise err
            for piece in pieces[1:-1:-1]:
                compval = stack.pop()
                setattr(stack[-1], piece, compval)
                
def spshRCfromA1(A1_style_link):
    '''given a string like "A1", returns a tuple of two ints (row, col). Row and col are zero-based; address row index is one-based'''
    
    #assuming only two letter column
    if A1_style_link[1].isalpha():
        colstr = A1_style_link[0:2]
        rowstr = A1_style_link[2:]
    else:
        colstr = A1_style_link[0:1]
        rowstr = A1_style_link[1:]
    
    row = int(rowstr)-1
    
    colstr = colstr.upper()
    NUM_LETTERS = ord("Z")-ord("A")+1
    A = ord("A")
    mult = 1
    col = -1
    for ch in colstr[::-1]:
        col += mult * (ord(ch) - A + 1)
        mult *= NUM_LETTERS
        
    return (row,col)

def spshA1fromRC(row, col):
    '''outputs an address of A1-style, given row and column indexes (zero-based)'''
    NUM_LETTERS = ord("Z")-ord("A")+1
    A = ord("A")
    colstr = chr(A + col % NUM_LETTERS)
    col -= col % NUM_LETTERS
    col /= NUM_LETTERS
    if col > 0:
        colstr = chr(A + col % (NUM_LETTERS+1) - 1) + colstr
    
    rowstr = str(row+1)
    
    return colstr + rowstr

def read_refs_value_table(spreadsheet):
    '''returns tuple of two. First is list of parameter refs (strings). Second is a table of values (list of rows)'''
    
    # read out list of parameters
    r = 0
    c = 0
    params = []
    for c in range(spshRCfromA1("ZZ0")[1]):
        try:
            tmp = spreadsheet.get(spshA1fromRC(r,c))
            if not( type(tmp) is str or type(tmp) is unicode ):
                raise TypeError("Parameter reference must be a string; it is {type}".format(type= type(tmp).__name__))
            params.append(tmp)
        except ValueError: # ValueError is thrown in attempt to read empty cell
            break
    num_params = len(params)
    if num_params == 0:
        raise ValueError("Reading out parameter references from spreadsheet failed: no parameter reference found on A1 cell.")
    
    # read out values
    values = []
    num_nonempty_rows = 0
    num_empty_rows_in_a_row = 0
    while True:
        n_vals_got = 0
        r += 1
        val_row = [None]*num_params
        for c in range(num_params):
            try:
                val_row[c] = spreadsheet.get(spshA1fromRC(r,c))
                n_vals_got += 1
            except ValueError: # ValueError is thrown in attempt to read empty cell
                pass
        values.append(val_row)
        if n_vals_got == 0:
            num_empty_rows_in_a_row += 1
            if num_empty_rows_in_a_row > 1000:
                break
        else:
            num_empty_rows_in_a_row = 0
            num_nonempty_rows += 1
        
    # trim off the last train of empty rows
    if num_empty_rows_in_a_row > 0: #always true...
        values = values[0:-num_empty_rows_in_a_row]
    
    if num_nonempty_rows == 0:
        raise ValueError("Value table is empty. Please fill the spreadsheet with values, not just references to parameters.")
    return (params, values)

    
    

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
        b_auto_spreadsheet = selfobj.ValuesSource == "Spreadsheet" and selfobj.CellStart == ""
        if b_auto_spreadsheet:
            refstrs, values = read_refs_value_table(selfobj.SpreadsheetLink)
        else:
            self.generator.execute()
        
        if selfobj.Recomputing == "Disabled":
            raise ValueError(selfobj.Name+": recomputing of this object is currently disabled. Modify 'Recomputing' property to enable it.")
        try:            
            #test parameter references and read out their current values
            if not b_auto_spreadsheet:
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
                                                    err= err.message))
                defvalues.append(val)
            N_params = len(defvalues)
            if N_params == 0:
                raise ValueError(selfobj.Name+": ParameterRef is not set. It is required.")
            
            #parse values
            if not b_auto_spreadsheet:
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
            else: #b_auto_spreadsheet == True
                # only replace Nones with default values
                for row in values:
                    for icol in range(N_params):
                        if row[icol] is None:
                            row[icol] = defvalues[icol]
            
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
            
            # list of values and parameters have been read out, and prepared in variables 'refstrs' and 'values'.
            # prepare for computations
            
            bGui = False #bool(App.GuiUp) #disabled temporarily, because it causes a crash if property edits are approved by hitting Enter
            if bGui:
                import PySide
                progress = PySide.QtGui.QProgressDialog(u"Recomputing "+selfobj.Label, u"Abort", 0, len(values)+1)
                progress.setModal(True)
                progress.show()
            
            doc1 = selfobj.Document
            doc2 = App.newDocument()
            object_in_doc2 = None # define the variable, to prevent del() in finally block from raising another error
            try:
                doc2.copyObject(selfobj.Object, True)
                
                #if there are nested paraseries in the dependencies, make sure to enable them
                for objd2 in doc2.Objects:
                    if hasattr(objd2,"Recomputing"):
                        try:
                            objd2.Recomputing = "Enabled"
                            objd2.purgeTouched()
                        except exception:
                            lattice2Executer.warning(selfobj,"Failed to enable recomputing of "+objd2.Name)
                
                object_in_doc2 = doc2.getObject(selfobj.Object.Name)
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



def CreateLatticeParaSeries(name, shapeObj, SpreadsheetLink = None, bAskRecompute = True):
    '''utility function; sharing common code for all paraseries creation commands'''
    FreeCADGui.addModule("lattice2ParaSeries")
    FreeCADGui.addModule("lattice2Executer")
    
    #fill in properties
    FreeCADGui.doCommand("f = lattice2ParaSeries.makeLatticeParaSeries(name='"+name+"')")
    FreeCADGui.doCommand("f.Object = App.ActiveDocument."+shapeObj.Name)
    
    if SpreadsheetLink is not None:
        FreeCADGui.doCommand("f.SpreadsheetLink = App.ActiveDocument."+SpreadsheetLink.Name)
        FreeCADGui.doCommand("f.ValuesSource = 'Spreadsheet'")
        FreeCADGui.doCommand("f.CellStart = ''")
        try:
            read_refs_value_table(SpreadsheetLink)
            # if we got here, parameter-value table was read out successfully
            if 
        except:
            lattice2Executer.warning(App.ActiveDocument.ActiveObject, "Failed to read out parameters and values from spreadsheet {spsh}. {err}"
                                                                      .format(spsh= SpreadsheetLink.))
            pass
    
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
