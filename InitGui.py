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

__Comment__ = 'Advanced array tools and parametric compounding tools'
__Web__ = 'http://forum.freecadweb.org/viewtopic.php?f=22&t=12464'
__Wiki__ = ''
__Icon__  = ''
__Help__ = 'Install as a workbench - copy everything to path/to/FreeCAD/Mod/Lattice'
__Author__ = 'DeepSOIC'
__Version__ = '0'
__Status__ = 'alpha'
__Requires__ = 'freecad 0.16.5155'
__Communication__ = 'vv.titov@gmail.com; DeepSOIC on FreeCAD forum'



class LatticeWorkbench (Workbench): 
    MenuText = 'Lattice'
    def __init__(self):
        # Hack: obtain path to Lattice by loading a dummy Py module
        import os
        import latticeDummy
        self.__class__.Icon = os.path.dirname(latticeDummy.__file__) + u"/PyResources/icons/Lattice.svg".replace("/", os.path.sep)
    
    def Initialize(self):
        cmdsArrayTools = []
        cmdsCompoundTools = []
        cmdsMiscTools = []
        
        import latticePlacement
        cmdsArrayTools = cmdsArrayTools + latticePlacement.exportedCommands        
        import latticePolarArray
        cmdsArrayTools = cmdsArrayTools + latticePolarArray.exportedCommands        
        import latticeCompose
        cmdsArrayTools = cmdsArrayTools + latticeCompose.exportedCommands
        import latticeDowngrade
        cmdsCompoundTools = cmdsCompoundTools + latticeDowngrade.exportedCommands
        import CompoundFilter
        cmdsCompoundTools = cmdsCompoundTools + CompoundFilter.exportedCommands
        import FuseCompound
        cmdsCompoundTools = cmdsCompoundTools + FuseCompound.exportedCommands
        import latticeBoundBox
        cmdsMiscTools = cmdsMiscTools + latticeBoundBox.exportedCommands
        
        self.appendToolbar('LatticeArrayTools', cmdsArrayTools)
        self.appendToolbar('LatticeCompoundTools', cmdsCompoundTools)
        self.appendToolbar('LatticeMiscTools', cmdsMiscTools)
        #FreeCADGui.addIconPath( '' )
        #FreeCADGui.addPreferencePage( '','Lattice' )
        self.appendMenu('Lattice', cmdsArrayTools)
        self.appendMenu('Lattice', cmdsCompoundTools)
        self.appendMenu('Lattice', cmdsMiscTools)

    def Activated(self):
        pass

 	Icon = """
 			/* XPM */
 			static const char *test_icon[]={
 			"16 16 2 1",
 			"a c #000000",
 			". c None",
 			".....#.....#....",
 			".....#.....#....",
 			".....#.....#....",
 			".....#.....#....",
 			"################",
 			".....#.....#....",
 			".....#.....#....",
 			".....#.....#....",
 			".....#.....#....",
 			"################",
 			".....#.....#....",
 			".....#.....#....",
 			".....#.....#....",
 			".....#.....#....",
 			"................",
 			"................"};
 			"""


Gui.addWorkbench(LatticeWorkbench())

