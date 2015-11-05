#***************************************************************************
#*                                                                         *
#*   copyright (c) 2015 - victor titov (deepsoic)                          *
#*                                               <vv.titov@gmail.com>      *  
#*                                                                         *
#*   this program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the gnu lesser general public license (lgpl)    *
#*   as published by the free software foundation; either version 2 of     *
#*   the license, or (at your option) any later version.                   *
#*   for detail see the licence text file.                                 *
#*                                                                         *
#*   this program is distributed in the hope that it will be useful,       *
#*   but without any warranty; without even the implied warranty of        *
#*   merchantability or fitness for a particular purpose.  see the         *
#*   gnu library general public license for more details.                  *
#*                                                                         *
#*   you should have received a copy of the gnu library general public     *
#*   license along with this program; if not, write to the free software   *
#*   foundation, inc., 59 temple place, suite 330, boston, ma  02111-1307  *
#*   usa                                                                   *
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
        
        import latticePlacement as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import latticeLinearArray as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import latticePolarArray as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import latticeArrayFromShape as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        
        import latticeInvert as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import latticeJoinArrays as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        
        import latticeApply as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands
        import latticeCompose as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands
        import latticeDowngrade as mod
        
        cmdsCompoundTools = cmdsCompoundTools + mod.exportedCommands
        import CompoundFilter as mod
        cmdsCompoundTools = cmdsCompoundTools + mod.exportedCommands
        import FuseCompound as mod
        cmdsCompoundTools = cmdsCompoundTools + mod.exportedCommands
        import latticeInspect as mod
        cmdsCompoundTools = cmdsCompoundTools + mod.exportedCommands
        import latticeBoundBox as mod
        cmdsMiscTools = cmdsMiscTools + mod.exportedCommands
        import latticeShapeString as mod
        cmdsMiscTools = cmdsMiscTools + mod.exportedCommands
        
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

