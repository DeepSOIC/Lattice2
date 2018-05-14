#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Victor Titov (DeepSOIC)                          *
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

__title__="Group command for Lattice Series features"
__author__ = "DeepSOIC"
__url__ = ""
__doc__ = "Group command for Lattice Series features"

import lattice2ParaSeries as ParaSeries
import lattice2TopoSeries as TopoSeries

import FreeCAD as App
if App.GuiUp:
    import FreeCADGui

class CommandSeriesGroup:
    def GetCommands(self):
        return tuple(ParaSeries.exportedCommands + TopoSeries.exportedCommands)

    def GetDefaultCommand(self): # return the index of the tuple of the default command. 
        return 0

    def GetResources(self):
        return { 'MenuText': 'Series features:', 
                 'ToolTip': 'Series features (group): features that collect permutations of an object by changing dependent objects.'}
        
    def IsActive(self): # optional
        return App.ActiveDocument is not None

if App.GuiUp:
    FreeCADGui.addCommand('Lattice2_Series_GroupCommand',CommandSeriesGroup())

exportedCommands = ['Lattice2_Series_GroupCommand']

