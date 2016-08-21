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

__title__="Value Series generator module"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Value Series generator module: utility module to attach value generator to document object"

import math
import lattice2Executer
from lattice2Common import ParaConfusion

class ValueSeriesGenerator:
    def __init__(self, docObj):
        self.documentObject = docObj
        self.source_modes = ["Values Property","Spreadsheet", "Generator"]
        self.gen_modes = ['SpanN','StepN','SpanStep', 'Random']
        self.gen_laws = ['Linear','Exponential']
        self.alignment_modes = ['Low', 'Center', 'High', 'Justify', 'Mirrored']
        self.readonlynessDict = {} # key = property name (string). Value = boolean (True == writable, non-readonly). Stores property read-only status requested by external code.
        
    def addProperties(self, groupname, groupname_gen, valuesdoc, valuestype = 'App::PropertyFloat'):
        #    _addProperty(proptype                  , propname        , defvalue, group, tooltip)
        
        # first, try to guess interface version. If we are re-adding properties to old feature, 
        # it already has some other properties, but not Version. So we should default to 0 
        # in this case. Therwise the Version property already exists, so default desn't matter; 
        # or we are creating a new generator, so default to 1.
        self._addProperty("App::PropertyInteger"    ,"VSGVersion"     , 0 if hasattr(self.documentObject, "Values") else 1 , groupname_gen, "Interface version")
        self.documentObject.setEditorMode("VSGVersion", 2) #hide this property
        
        self._addProperty("App::PropertyStringList" ,"Values"         , None, groupname, valuesdoc)
        self._addProperty("App::PropertyEnumeration","ValuesSource"   , self.source_modes, groupname, "Select where to take the value series from.")
        self._addProperty("App::PropertyLink"       ,"SpreadsheetLink", None, groupname, "Link to spreadsheet to take values from.")
        self._addProperty("App::PropertyString"     ,"CellStart"      , 'A1', groupname, "Starting cell of first value (the rest are scanned downwards till an empty cell is encountered)")
                                                                                                           
        self._addProperty("App::PropertyEnumeration","GeneratorMode"  , self.gen_modes, groupname_gen,"")
        self._addProperty("App::PropertyEnumeration","DistributionLaw", self.gen_laws, groupname_gen,"")
                                                                                                           
        self._addProperty(valuestype                ,"SpanStart"      , 1.0, groupname_gen, "Starting value for value series generator")
        self._addProperty(valuestype                ,"SpanEnd"        , 7.0, groupname_gen, "Ending value for value series generator")
        self._addProperty("App::PropertyBool"       ,"EndInclusive"   , True, groupname_gen, "If True, the last value in series will equal SpanEnd. If False, the value equal to SpanEnd will be dropped.")
        self._addProperty("App::PropertyEnumeration","Alignment"      , self.alignment_modes,groupname_gen, "Sets how to align the values within span.")
        self._addProperty("App::PropertyFloat"      ,"Step"           , 1.0, groupname_gen, "Step for value generator. For exponential law, it is a natural logarithm of change ratio.") # using float for Step, because step's unit depends n selected distribution law
        self._addProperty("App::PropertyFloat"      ,"Count"          , 7.0, groupname_gen, "Number of values to generate")
        self._addProperty("App::PropertyFloat"      ,"Offset"         , 0.0, groupname_gen, "Extra offset for the series, expressed as fraction of step.")
            
    def _addProperty(self, proptype, propname, defvalue, group, tooltip):
        if hasattr(self.documentObject, propname):
            return
        self.documentObject.addProperty(proptype, propname, group, tooltip)
        if defvalue is not None:
            setattr(self.documentObject, propname, defvalue)

    def updateReadonlyness(self):
        obj = self.documentObject
        m = obj.GeneratorMode
        src = obj.ValuesSource
        
        self._setPropertyWritable("Values"          , src == "Values Property"                    )
        self._setPropertyWritable("ValuesSource"    , True                                        )
        self._setPropertyWritable("SpreadsheetLink" , src == "Spreadsheet"                        )
        self._setPropertyWritable("CellStart"       , src == "Spreadsheet"                        )
                                                                                                  
        self._setPropertyWritable("GeneratorMode"   , not self.isPropertyControlledByGenerator("GeneratorMode"  )  )
        self._setPropertyWritable("DistributionLaw" , not self.isPropertyControlledByGenerator("DistributionLaw")  )
                                                                                             
        self._setPropertyWritable("SpanStart"       , not self.isPropertyControlledByGenerator("SpanStart"      )  )
        self._setPropertyWritable("SpanEnd"         , not self.isPropertyControlledByGenerator("SpanEnd"        )  )
        self._setPropertyWritable("EndInclusive"    , not self.isPropertyControlledByGenerator("EndInclusive"   )  )
        self._setPropertyWritable("Alignment"       , not self.isPropertyControlledByGenerator("Alignment"      ) and m != "Random" )
        self._setPropertyWritable("Step"            , not self.isPropertyControlledByGenerator("Step"           )  )
        self._setPropertyWritable("Count"           , not self.isPropertyControlledByGenerator("Count"          )  )
        self._setPropertyWritable("Offset"          , not self.isPropertyControlledByGenerator("Offset"         )  )
    
    def isPropertyControlledByGenerator(self, propname):
        obj = self.documentObject
        if not hasattr(obj, propname):
            raise AttributeError(obj.Name+": has no property named "+propname)
        
        m = obj.GeneratorMode

        genOn = obj.ValuesSource == "Generator"
        if not genOn:
            return False        

        if propname == "SpanStart": 
            return False
        elif propname == "SpanEnd":
            return False
        elif propname == "Step":
            return m == "SpanN"
        elif propname == "Count":
            return m == "SpanStep"
        else:
            return False

    def setPropertyWritable(self, propname, bool_writable):
        '''setPropertyWritable(self, propname, bool_writable): Use to force a property read-only 
        (for example, when the property is driven by a link). If set to be writable, the read-onlyness 
        will be set according to series generator logic.'''
        self.readonlynessDict[propname] = bool_writable
        
    def _setPropertyWritable(self, propname, bool_writable, suppress_warning = False):
        if self.readonlynessDict.has_key(propname):
            bool_writable = bool_writable and self.readonlynessDict[propname] 
        self.documentObject.setEditorMode(propname, 0 if bool_writable else 1)
        
    def execute(self):
        obj = self.documentObject #shortcut
        
        values = [] #list to be filled with values, that are giong to be written to obj.Values
        
        if obj.ValuesSource == "Generator":
            #read out span and convert it to linear law
            if obj.DistributionLaw == 'Linear':
                vStart = float(obj.SpanStart)
                vEnd = float(obj.SpanEnd)
                vStep = float(obj.Step)
            elif obj.DistributionLaw == 'Exponential':
                vSign = 1 if obj.SpanStart > 0.0 else -1.0
                vStart = math.log(obj.SpanStart * vSign)
                if obj.SpanEnd * vSign < ParaConfusion: 
                    raise ValueError(obj.Name+": Wrong SpanEnd value. It is either zero, or of different sign compared to SpanStart. In exponential distribution, it is not allowed.")
                vEnd = math.log(obj.SpanEnd * vSign)
                vStep = float(obj.Step)
            else:
                raise ValueError(obj.Name+": distribution law not implemented: "+obj.DistributionLaw)
                
            if obj.GeneratorMode == 'SpanN':
                n = obj.Count
                if obj.EndInclusive:
                    n -= 1
                if n == 0:
                    n = 1
                vStep = (vEnd - vStart)/n
                obj.Step = vStep
            elif obj.GeneratorMode == 'StepN':
                if obj.VSGVersion < 1:
                    #old behavior: update span to match the end of array
                    n = obj.Count
                    if obj.EndInclusive:
                        n -= 1
                    vEnd = vStart + float(vStep)*n
                    if obj.DistributionLaw == 'Linear':
                        obj.SpanEnd = vEnd
                    elif obj.DistributionLaw == 'Exponential':
                        obj.SpanEnd = math.exp(vEnd)*vSign
                    else:
                        raise ValueError(obj.Name+": distribution law not implemented: "+obj.DistributionLaw)
                else:
                    # new behavior: keep span intact, as it can be used for alignment
                    pass
            elif obj.GeneratorMode == 'SpanStep':
                nfloat = float((vEnd - vStart) / vStep)
                n = math.trunc(nfloat - ParaConfusion) + 1
                if obj.EndInclusive and abs(nfloat-round(nfloat)) <= ParaConfusion:
                    n = n + 1
                obj.Count = n
            elif obj.GeneratorMode == 'Random':
                pass
            else:
                raise ValueError(obj.Name+": Generator mode "+obj.GeneratorMode+" is not implemented")
            
            # Generate the actual array. We can use Step and N directly to 
            # completely avoid mode logic, since we had updated them
            
            # cache properties into variables
            # vStart,vEnd are already in sync
            vStep = float(obj.Step)
            vOffset = float(obj.Offset)
            n = int(obj.Count)
            
            # Generate the values
            if obj.GeneratorMode == 'Random':
                import random
                list_evenDistrib = [vStart + vOffset*vStep + (vEnd-vStart)*random.random() for i in range(0, n)]
            else:
                # preprocess for alignment
                alignment_offset = 0.0
                vStep_justified = vStep
                if obj.Alignment != "Low" and n>0:
                    v_first = vStart
                    v_last = vStep*(n)   if obj.Alignment == "Justify" and obj.EndInclusive == False else    vStep*(n-1)
                    if obj.Alignment == "High":
                        alignment_offset = (vEnd-v_last)
                    elif obj.Alignment == "Center":
                        alignment_offset = (vEnd-v_last)*0.5
                    elif obj.Alignment == "Justify":
                        #replica of SpanN logic
                        n_tmp = n
                        if obj.EndInclusive:
                            n_tmp -= 1
                        if n_tmp == 0:
                            n_tmp = 1 #justify failed!
                        vStep_justified = (vEnd - vStart)/n_tmp
                        
                list_evenDistrib = [vStart + vOffset*vStep + alignment_offset + vStep_justified*i for i in range(0, n)]
                
                #post-process alignment
                if obj.Alignment == "Mirrored":
                    new_list = []
                    for v in list_evenDistrib:
                        new_list.append(v)
                        if v > 1e-12:
                            new_list.append(-v)
                    list_evenDistrib = new_list
                
            if obj.DistributionLaw == 'Linear':
                values = list_evenDistrib
            elif obj.DistributionLaw == 'Exponential':
                values = [math.exp(v)*vSign for v in list_evenDistrib]
            else:
                raise ValueError(obj.Name+": distribution law not implemented: "+obj.DistributionLaw)
        elif obj.ValuesSource == "Spreadsheet":
            #parse address
            addr = obj.CellStart
            #assuming only two letter column
            if addr[1].isalpha():
                col = addr[0:2]
                row = addr[2:]
            else:
                col = addr[0:1]
                row = addr[1:]
            row = int(row)
            
            #loop until the value can't be read out
            values = []
            while True:
                try:
                    values.append( obj.SpreadsheetLink.get(col+str(row)) )
                except ValueError:
                    break
                row += 1
        elif obj.ValuesSource == "Values Property":
            pass
        else:
            raise ValueError(obj.Name+": values source mode not implemented: "+obj.ValuesSource)
        
        # finally. Fill in the values.
        if obj.ValuesSource != "Values Property":
            obj.Values = [str(v) for v in values]
    