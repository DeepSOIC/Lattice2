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
        
        obj.addProperty("App::PropertyString","ParameterRef","Lattice ParaSeries","Reference to the parameter to vary. Use expression. Example: Box.Height")
                
        obj.addProperty("App::PropertyEnumeration","ValuesSource","Lattice ParaSeries","Select where to take the values for parameter from.")
        obj.ValuesSource = ["Values Property","Spreadsheet", "Generator"]
        
        obj.addProperty("App::PropertyStringList","Values","Lattice ParaSeries","List of values for series")
        
        obj.addProperty("App::PropertyEnumeration","Recomputing","Lattice ParaSeries","Sets recomputing policy.")
        obj.Recomputing = ["Disabled", "Recompute Once", "Enabled"]
        obj.Recomputing = "Disabled" # recomputing ParaSeries can be very long, so disable it by default
        

    def derivedExecute(self,selfobj):
        if selfobj.Recomputing == "Disabled":
            raise ValueError("Recomputing of this object is currently disabled. Modify 'Recomputing' property to enable it.")
        try:
            #collect values
            values = []
            if selfobj.ValuesSource == "Values Property":
                pass
            else:
                raise ValueError(selfobj.Name + ": ValuesSource = "+selfobj.ValuesSource+" is not yet implemented")
            
            #convert values to type
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
                        scale = selfobj.Object.Shape.BoundBox.DiagonalLength/math.sqrt(3)/math.sqrt(len(shps))
                except Exception:
                    pass
                if scale < DistConfusion * 100:
                    scale = 1.0
                selfobj.Shape = markers.getNullShapeShape(scale)
                raise ValueError(selfobj.Name + ": list of values is empty.") 
            
            doc1 = selfobj.Document
            doc2 = App.newDocument()
            object_in_doc2 = None # define the variable, to prevent del() in finally block from raising another error
            try:
                object_in_doc2 = doc2.copyObject(selfobj.Object, True)
                refstr = selfobj.ParameterRef #dict(selfobj.ExpressionEngine)["ParameterRef"]
                pieces = refstr.split(".")
                objname = pieces[0]
                obj_to_modify = doc2.getObject(objname)
                output_shapes = []
                for val in values:
                    if obj_to_modify.isDerivedFrom("Spreadsheet::Sheet"):
                        if len(pieces) != 2:
                            raise ValueError(selfobj.Name + ": failed to parse parameter reference: "+refstr )
                        obj_to_modify.set(pieces[1], str(val))
                    elif obj_to_modify.isDerivedFrom("Sketcher::SketchObject") and pieces[1] == "Constraints":
                        if len(pieces) != 3:
                            raise ValueError(selfobj.Name + ": failed to parse parameter reference: "+refstr )
                        obj_to_modify.setDatum(pieces[2],val)
                    else:
                        if len(pieces) != 2:
                            raise ValueError(selfobj.Name + ": failed to parse parameter reference: "+refstr )
                        setattr(obj_to_modify, pieces[1], val)
                    
                    doc2.recompute()
                    
                    shape = None
                    for obj in doc2.Objects:
                        if 'Invalid' in obj.State:
                            latticeExecuter.error(obj,"Recomputing shape for parameter value of "+val+" failed.")
                            
                            scale = 1.0
                            try:
                                if not selfobj.Object.Shape.isNull():
                                    scale = selfobj.Object.Shape.BoundBox.DiagonalLength/math.sqrt(3)/math.sqrt(len(shps))
                            except Exception:
                                pass
                            if scale < DistConfusion * 100:
                                scale = 1.0
                            shape = markers.getNullShapeShape(scale)
                    if shape is None:
                        shape = object_in_doc2.Shape.copy()
                    output_shapes.append(shape)
                    
                    
            finally:
                #delete all references, before destroying the document. Probably not required, but to be sure...
                del(object_in_doc2)
                doc2_name = doc2.Name
                del(doc2)
                App.closeDocument(doc2_name)
                
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
                    "Setting up the series involves: specifying the parameter to modify (ParameterRef property - set up an expression), and setting up the value list.")
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