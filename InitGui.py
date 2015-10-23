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
    def Initialize(self):
        commandslist0 = []
        commandslist1 = []
        commandslist2 = []
        
        import latticePolarArray
        commandslist0 = commandslist0 + latticePolarArray.exportedCommands        
        import latticeDowngrade
        commandslist1 = commandslist1 + latticeDowngrade.exportedCommands
        import CompoundFilter
        commandslist1 = commandslist1 + CompoundFilter.exportedCommands
        import FuseCompound
        commandslist1 = commandslist1 + FuseCompound.exportedCommands
        import latticeBoundBox
        commandslist2 = commandslist2 + latticeBoundBox.exportedCommands
        
        self.appendToolbar('LatticeArrayTools', commandslist0)
        self.appendToolbar('LatticeCompoundTools', commandslist1)
        self.appendToolbar('LatticeMiscTools', commandslist2)
        #FreeCADGui.addIconPath( '' )
        #FreeCADGui.addPreferencePage( '','Lattice' )
        self.appendMenu('Lattice', commandslist0)
        self.appendMenu('Lattice', commandslist1)
        self.appendMenu('Lattice', commandslist2)

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

