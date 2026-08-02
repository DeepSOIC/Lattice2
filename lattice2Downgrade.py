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

from lattice2Common import *
from lattice2Utils import getAnnotatedShapes
import lattice2Markers as markers
import lattice2CompoundExplorer as LCE
from lattice2BaseFeature import assureProperty #assureProperty(self, selfobj, proptype, propname, defvalue, group, tooltip)
import logging

import math

__title__="latticeDowngrade module for FreeCAD"
__author__ = "DeepSOIC"
__url__ = ""

def getAllSeams(shape):
    '''getAllSeams(shape): extract all seam edges of a shape. Returns list of edges.'''
    # this is a hack.
    # Seam edges were found to be in wires that contain the seam edge twice.
    # See http://forum.freecadweb.org/viewtopic.php?f=3&t=15470#p122993 (post #7 in topic "Extra Line in Models")
    import itertools
    seams = []
    for w in shape.Wires:
        for (e1,e2) in itertools.combinations(w.childShapes(),2):
            if e1.isSame(e2):
                seams.append(e1)
    return seams


# -------------------------- common stuff --------------------------------------------------

def makeLatticeDowngrade(name):
    '''makeLatticeDowngrade(name): makes a latticeDowngrade object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _latticeDowngrade(obj)
    if FreeCAD.GuiUp:        
        _ViewProviderLatticeDowngrade(obj.ViewObject)
    return obj

allowed_attributes = {
  '.StartPoint'   : 'vector',
  '.EndPoint'     : 'vector',
  '.Construction' : 'bool'
}

example = """
# Write one instruction per line. Indentation is irrelevant but other whitespace is significant. Syntax is as follows:

# In the stack representations below, the topmost element is on the right.

# <instruction> : <stack before> : <stack after> : description
# QUOTE            : ...                 : ... closure     : quotes the following instructions until "QUOTE END" for later use via CALL, PARTIAL or a higher-order function like MAP
# END QUOTE                                             : ends quotation mode
# CALL             : ... closure         : ...UpdatedStack : calls the closure and lets it manipulate the stack (no protection). The closure's saved stack is appended, so its instructions start executing with the stack "... saved"
# PARTIAL          : ... arg closure     : ... closure'    : adds the arg on top of the saved stack of the closure
# DEBUG            : ...                 : ...             : prints the current stack
# MAP              : ... list closure    : ... list'       : calls the closure for each of the elements of the list. The closure's instructions are executed with the stack "... saved elt". After each call, the top of the stack is popped and stored in a list. This list is left as the top of the stack at the end
# FILTER           : ... list closure    : ... list'       : calls the closure for each of the elements of the list. The closure's instructions are executed with the stack "... saved elt". After each call, the top of the stack is popped and if it is true, the original element is added to a list. This list is left as the top of the stack at the end
# STR some text    : ...                 : ... string      : pushes "some text" on the stack. The entire line is pushed after removing the first four characters "STR "
# FLOAT 3.14       : ...                 : ... float       : pushes 3.14 on the stack
# INT 123          : ...                 : ... int         : pushes 123 on the stack
# BOOL True        : ...                 : ... bool        : pushes True on the stack. Booleans are True or False
# NOT              : ... bool            : ... bool        : pops the top of the stack which must be a boolean, and pushes back its negation
# EQUAL            : ... t t             : ... bool        : pops two elements, pushes True if top == bot, False otherwise. Comparing elements of different types will always return False.
# LT               : ... t t             : ... bool        : pops two elements, pushes True if top <  bot, False otherwise. Comparing elements of different types will always return False.
# GT               : ... t t             : ... bool        : pops two elements, pushes True if top >  bot, False otherwise. Comparing elements of different types will always return False.
# LE               : ... t t             : ... bool        : pops two elements, pushes True if top <= bot, False otherwise. Comparing elements of different types will always return False.
# GE               : ... t t             : ... bool        : pops two elements, pushes True if top >= bot, False otherwise. Comparing elements of different types will always return False.
# AND              : ... bool bool       : ... bool        : pops two booleans, pushes (top and bot)
# OR               : ... bool bool       : ... bool        : pops two booleans, pushes (top or bot)
# XOR              : ... bool bool       : ... bool        : pops two booleans, pushes (top xor bot)
# NAND             : ... bool bool       : ... bool        : pops two booleans, pushes (top nand bot)
# NOR              : ... bool bool       : ... bool        : pops two booleans, pushes (top nor bot)
# NXOR             : ... bool bool       : ... bool        : pops two booleans, pushes (top nxor bot)
# DROP             : ... t               : ...             : pops the top of the stack and discards it
# DUP              : ... t               : ... t t         : pops the top of the stack, and pushes it back twice (duplication of the top of the stack)
# SWAP             : ... t u             : ... u t         : pops two elements, and pushes them back in reverse order
# PAIR             : ... t u             : ... pair        : pops two elements, and pushes a pair containing these two elements
# UNPAIR           : ... pair            : ... t u         : pops a pair and pushes its two elements back onto the stack
# NIL              : ...                 : ... list        : pushes the empty list onto the stack
# CONS             : ... list t          : ... list        : pops two elements, adds the top at the head of the bot, and pushes back the new list
# UNCONS           : ... list            : ... list t      : pops the top of the stack which must be a list, and pushes back the tail of the list and its first element
# NOP              : ...                 : ...             : No operation (NOOP is also accepted)
# SET xyz          : ... t               : ...             : pops the top of the stack, and saves it as a global variable named xyz
# GET xyz          : ...                 : ... t           : pushes the contents of the global variable xyz on top of the stack
# .Annotations.xyz : ... annotated_shape : ... string      : gets the annotation from the given geometry element. Annotations are stored as dummy de-activated Block constraints named __theannotation.123 (where 123 is the constraint's ID) and some extra annotations are supplied by some Python objects (e.g. .Annotations.Geometry for sketches). A separate macro allows setting these annotations.
# .attribute       : ... geometry        : ... u           : gets the attribute from the object on the top of the stack. Allowed attributes are {allowed_attributes}

# The initial stack contains a list of sketch geometry elements.

QUOTE
  .Annotations.Geometry
  .Construction
  NOT
END QUOTE
FILTER
"""
example = example.format(allowed_attributes=",".join(sorted(["%s (%s)" % (k,v) for k,v in allowed_attributes.items()])))

def interpret_map(stack, env, closure, lst):
  result = []
  for elt in lst:
     stack, env = interpret(stack + closure[1] + [elt], env, closure[0])
     result.append(stack[-1])
     stack = stack[:-1]
  return (stack + [('list', result)], env)

def interpret_filter(stack, env, closure, lst):
  result = []
  for elt in lst:
     stack, env = interpret(stack + closure[1] + [elt], env, closure[0])
     if stack[-1][0] != 'bool':
       raise ValueError("closure passed as an argument to filter should return a bool, but it returned a " + str(stack[-1][0]))
     if stack[-1][1] == True:
       result.append(elt)
     elif stack[-1][1] == False:
       pass
     else:
       raise ValueError("internal error: invalid boolean value: " + repr(stack[-1][1]))
     stack = stack[:-1]
  return (stack + [('list', result)], env)

boolOperations = {
  'AND':  (lambda x, y: x and y),
  'OR':   (lambda x, y: x or  y),
  'XOR':  (lambda x, y: (x or y) and (not (x and y))),
  'NAND': (lambda x, y: not (x and y)),
  'NOR':  (lambda x, y: not (x or  y)),
  'NXOR': (lambda x, y: (x and y) or (not (x or y)))
}

def interpret(stack, env, program):
  quoting = 0
  for line in program:
    if line.strip() == '':
      pass # no-op

    # quotations
    elif quoting > 0:
      if stack[-1][0] != 'closure':
        raise ValueError("while in quote mode the top of the stack should be a closure")
      if line == 'END QUOTE':
        quoting = quoting - 1
      elif line == 'QUOTE':
        quoting = quoting + 1

      if quoting > 0: # if this wasn't the last 'END QUOTE', i.e. after decrementing we're still quoting, then add the instruction to the closure
        stack[-1] = ('closure', (stack[-1][1][0] + [line], stack[-1][1][1]))
      else:
        pass

    elif line == 'QUOTE':
      stack.append(('closure', ([],[])))
      quoting = 1

    # functions
    elif line == 'CALL':
      if stack[-1][0] != "closure":
        raise ValueError("CALL expected a closure")
      stack, env = interpret(stack[:-1] + stack[-1][1][1], env, stack[-1][1][0])
    elif line == 'PARTIAL':
      # push stack[-2] onto the closure's stack
      if stack[-1][0] != "closure":
        raise ValueError("PARTIAL expected a closure")
      stack = stack[:-2] + [('closure', (stack[-1][1][0], stack[-1][1][1] + [stack[-2]]))]
    elif line == 'MAP':
      if stack[-1][0] != "closure":
        raise ValueError("MAP expected a closure at the top of the stack")
      if stack[-2][0] != "list":
        raise ValueError("MAP expected a list as the second (deeper) element on the stack")
      closure = stack[-1][1]
      stack, env = interpret_map(stack[:-2], env, stack[-1][1], stack[-2][1])
    elif line == 'FILTER':
      if stack[-1][0] != "closure":
        raise ValueError("FILTER expected a closure at the top of the stack")
      if stack[-2][0] != "list":
        raise ValueError("FILTER expected a list as the second (deeper) element on the stack")
      closure = stack[-1][1]
      stack, env = interpret_filter(stack[:-2], env, stack[-1][1], stack[-2][1])

    elif line == 'DEBUG':
      print('stack:')
      for i,x in enumerate(reversed(stack)):
        print(str(i) + ": " + str(x))
    elif line.startswith('STR '):
      stack.append(("string", line[len('STR '):]))
    elif line.startswith('FLOAT '):
      stack.append(("float", float(line[len('FLOAT '):])))
    elif line.startswith('INT '):
      stack.append(("int", int(line[len('INT '):])))
    elif line.startswith('BOOL '):
      b = line[len('BOOL '):]
      if b != "True" and b != "False":
        raise ValueError("Invalid boolean literal, expected True or False")
      stack.append(("bool", line[len('BOOL '):] == "True"))
    elif line == 'NOT':
      if stack[-1][0] != "bool":
        raise ValueError("NOT expected a boolean at the top of the stack")
      stack = stack[:-1] + [("bool", not stack[-1][1])]
    elif line == 'EQUAL':
      stack = stack[:-2] + [("bool", stack[-1] == stack[-2])]
    elif line == 'LT':
      stack = stack[:-2] + [("bool", stack[-1] < stack[-2])]
    elif line == 'GT':
      stack = stack[:-2] + [("bool", stack[-1] > stack[-2])]
    elif line == 'LE':
      stack = stack[:-2] + [("bool", stack[-1] <= stack[-2])]
    elif line == 'GE':
      stack = stack[:-2] + [("bool", stack[-1] >= stack[-2])]
    elif line in boolOperations:
      if stack[-1][0] != "bool":
        raise ValueError(line + " expected a boolean at the top of the stack")
      if stack[-2][0] != "bool":
        raise ValueError(line + " expected a boolean as the second (deeper) element on the stack")
      stack = stack[:-2] + [("bool", boolOperations[line](stack[-1], stack[-2]))]
    elif line == 'DROP':
      stack = stack[:-1]
    elif line == 'DUP':
      stack.append(stack[-1])
    elif line == 'SWAP':
      stack = stack[:-2] + [stack[-1], stack[-2]]
    elif line == 'PAIR':
      stack = stack[:-2] + [("pair", stack[-1], stack[-2])]
    elif line == 'UNPAIR':
      if stack[-1][0] != "pair":
        raise ValueError("UNPAIR expected a pair")
      stack = stack[:-1] + [stack[-1][1][0], stack[-1][1][1]]
    elif line == 'NIL':
      stack.append(('list', []))
    elif line == 'CONS':
      if stack[-2][0] != "list":
        raise ValueError("CONS expected a list as the second (deeper) element on the stack")
      stack = stack[:-2] + [('list', [stack[-1]] + stack[-2][1])]
    elif line == 'UNCONS':
      if stack[-1][0] != "list":
        raise ValueError("UNCONS expected a list on the stack")
      stack = stack[:-1] + [('list', stack[-1][1][1:]), stack[-1][1][0]]
    elif line == 'NOP' or line == 'NOOP':
      pass
    elif line.startswith('SET '):
      env[line[len('SET '):]] = stack[-1]
      stack = stack[:-1]
    elif line.startswith('GET '):
      stack.append(env[line[len('GET '):]])
    elif line.startswith('.Annotations.'):
      annotationName = line[len('.Annotations.'):]
      if stack[-1][0] != "annotated_shape":
        raise ValueError(".Annotations expected an annotated shape")
      stack = stack[:-1] + [stack[-1][1][1].get(annotationName, ('none', None))]
    elif line in allowed_attributes.keys():
      if stack[-1][0] != "geometry":
        raise ValueError(line + " expected a geometry elemnt")
      stack = stack[:-1] + [(allowed_attributes[line], getattr(stack[-1][1][1], line[1:]))]
    else:
      raise ValueError('Unknown operation: "' + line + '", repr=' + repr(line) + ". empty after strip=" + str(line.strip() == '') + ", len=" + str(len(line)))
  return stack, env

def user_filter_old(filter, sketch):
  filter = [line.lstrip() for line in filter.split('\n')]
  filter = [line for line in filter if not line.startswith('#') and line != '']
  stack = [('list', [('annotated_shape', sh) for sh in getAnnotatedShapes(sketch)])]
  stack, env = interpret(stack, {}, filter)
  if len(stack) != 1:
    raise ValueError("The stack should contain a single element after applying the filter's operations.")
  if stack[0][0] != 'list':
    raise ValueError("The stack should contain a list after applying the filter's operations.")
  for i, (type, g) in enumerate(stack[0][1]):
    if type != 'annotated_shape':
      raise ValueError("The stack should contain a list of annotated shape elemnents after applying the filter's operations, wrong type for list element " + str(i) + " : " + str(type))
  return [shape for type,(shape,annotations) in stack[0][1]]

def parse(str):
  for c in str:
    if c == '(':
      pass
    elif c == 'TODO':
      pass

def user_filter(filter, sketch):
  filter = parse(filter)
  #… TODO
  stack = [('list', [('annotated_shape', sh) for sh in getAnnotatedShapes(sketch)])]
  stack, env = interpret(stack, {}, filter)
  if len(stack) != 1:
    raise ValueError("The stack should contain a single element after applying the filter's operations.")
  if stack[0][0] != 'list':
    raise ValueError("The stack should contain a list after applying the filter's operations.")
  for i, (type, g) in enumerate(stack[0][1]):
    if type != 'annotated_shape':
      raise ValueError("The stack should contain a list of annotated shape elemnents after applying the filter's operations, wrong type for list element " + str(i) + " : " + str(type))
  return [shape for type,(shape,annotations) in stack[0][1]]


class _latticeDowngrade:
    "The latticeDowngrade object"
    
    _DowngradeModeList = ['Leaves','CompSolids','Solids','Shells','OpenWires','Faces','Wires','Edges','SketchEdges','Seam edges','Non-seam edges','Vertices']
    
    def __init__(self,obj):
        self.Type = "latticeDowngrade"
        obj.addProperty("App::PropertyLink","Base","latticeDowngrade","Object to downgrade")
        
        obj.addProperty("App::PropertyEnumeration","Mode","latticeDowngrade","Type of elements to output.")
        obj.Mode = ['bypass'] + self._DowngradeModeList
        obj.Mode = 'bypass'

        obj.Proxy = self

        self.assureProperties(obj)

    def assureProperties(self, selfobj):
        assureProperty(selfobj, "App::PropertyStringList", "Filter", example.split('\n'), "latticeDowngrade", "Filter applied to the SubLink list")

    def execute(self,obj):
        rst = [] #variable to receive the final list of shapes
        shp = screen(obj.Base).Shape
        if obj.Mode == 'bypass':
            rst = [shp]
        elif obj.Mode == 'Leaves':
            rst = LCE.AllLeaves(shp)
        elif obj.Mode == 'CompSolids':
            rst = shp.CompSolids
        elif obj.Mode == 'Solids':
            rst = shp.Solids
        elif obj.Mode == 'Shells':
            rst = shp.Shells
        elif obj.Mode == 'OpenWires':
            openWires = []
            shells = shp.Shells
            for shell in shells:
                openEdges = shell.getFreeEdges().childShapes()
                if len(openEdges) > 1: # edges need to be fused into wires
                    clusters = Part.getSortedClusters(openEdges)
                    wires = [Part.Wire(cluster) for cluster in clusters]
                else: 
                    wires = openEdges
                openWires.extend(wires)
            rst = openWires
        elif obj.Mode == 'Faces':
            rst = shp.Faces
        elif obj.Mode == 'Wires':
            rst = shp.Wires
        elif obj.Mode == 'Edges':
            rst = shp.Edges
        elif obj.Mode == 'SketchEdges':
            rst = user_filter('\n'.join(obj.Filter), obj.Base)
        elif obj.Mode == 'Seam edges':
            rst = getAllSeams(shp)
        elif obj.Mode == 'Non-seam edges':
            seams = getAllSeams(shp)
            edges = shp.Edges
            rst = []
            for e in edges:
                bIsSeam = False
                for s in seams:
                    if e.isSame(s):
                        bIsSeam = True
                        break
                if not bIsSeam:
                    rst.append(e)
        elif obj.Mode == 'Vertices':
            rst = shp.Vertexes
        else:
            raise ValueError('Downgrade mode not implemented:'+obj.Mode)
        
        if len(rst) == 0:
            scale = 1.0
            if not screen(obj.Base).Shape.isNull():
                scale = screen(obj.Base).Shape.BoundBox.DiagonalLength/math.sqrt(3)
            if scale < DistConfusion * 100:
                scale = 1.0
            obj.Shape = markers.getNullShapeShape(scale)
            raise ValueError('Downgrade output is null') #Feeding empty compounds to FreeCAD seems to cause rendering issues, otherwise it would have been a good idea to output nothing.
        
        obj.Shape = Part.makeCompound(rst)
        return
        
        
class _ViewProviderLatticeDowngrade:
    "A View Provider for the latticeDowngrade object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return getIconPath("Lattice2_Downgrade.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def dumps(self):
        return None

    def loads(self,state):
        return None

    def claimChildren(self):
        weakparenting = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Lattice2").GetBool("WeakParenting", True)
        if weakparenting:
            return []
        return [screen(self.Object.Base)]

    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            screen(self.Object.Base).ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + str(err))
        return True


def CreateLatticeDowngrade(name, mode = "Wires"):
    FreeCAD.ActiveDocument.openTransaction("Create latticeDowngrade")
    FreeCADGui.addModule("lattice2Downgrade")
    FreeCADGui.addModule("lattice2Executer")
    FreeCADGui.doCommand("f = lattice2Downgrade.makeLatticeDowngrade(name = '"+name+"')")
    FreeCADGui.doCommand("f.Base = FreeCADGui.Selection.getSelection()[0]")
    FreeCADGui.doCommand("f.Mode = '"+mode+"'")    
    FreeCADGui.doCommand("f.Label = f.Mode + ' of ' + f.Base.Label")    
    if mode != 'OpenWires':
        FreeCADGui.doCommand("f.Base.ViewObject.hide()")
    else:
        FreeCADGui.doCommand("f.ViewObject.LineWidth = 6.0")
    FreeCADGui.doCommand("lattice2Executer.executeFeature(f)")
    FreeCADGui.doCommand("f = None")
    FreeCAD.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandLatticeDowngrade:
    "Command to create latticeDowngrade feature"
    
    mode = ''
    
    def __init__(self, mode = 'wires'):
        self.mode = mode
    
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2_Downgrade.svg"),
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Lattice2_Downgrade","Downgrade to ") + self.mode, # FIXME: not translation-friendly!
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Lattice2_Downgrade","Parametric Downgrade: downgrade and put results into a compound.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 1 :
            CreateLatticeDowngrade(name= "Downgrade", mode= self.mode)
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(translate("Lattice2_Downgrade", "Select a shape to downgrade, first!", None))
            mb.setWindowTitle(translate("Lattice2_Downgrade","Bad selection", None))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

_listOfSubCommands = []
for mode in _latticeDowngrade._DowngradeModeList: 
    cmdName = 'Lattice2_Downgrade' + mode
    if FreeCAD.GuiUp:
        FreeCADGui.addCommand(cmdName, _CommandLatticeDowngrade(mode))
    _listOfSubCommands.append(cmdName)
    

class GroupCommandLatticeDowngrade:
    def GetCommands(self):
        global _listOfSubCommands
        return tuple(_listOfSubCommands) # a tuple of command names that you want to group

    def GetDefaultCommand(self): # return the index of the tuple of the default command. This method is optional and when not implemented '0' is used  
        return 5

    def GetResources(self):
        return { 'MenuText': 'Parametric Downgrade', 'ToolTip': 'Parametric Downgrade: downgrade and pack results into a compound.'}
        
    def IsActive(self): # optional
        return activeBody() is None
        
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_Downgrade_GroupCommand',GroupCommandLatticeDowngrade())




exportedCommands = ['Lattice2_Downgrade_GroupCommand']

# -------------------------- /Gui command --------------------------------------------------
