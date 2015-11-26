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
__Help__ = 'Install as a workbench - copy everything to path/to/FreeCAD/Mod/Lattice2'
__Author__ = 'DeepSOIC'
__Version__ = '2'
__Status__ = 'alpha'
__Requires__ = 'freecad 0.16.5155'
__Communication__ = 'vv.titov@gmail.com; DeepSOIC on FreeCAD forum'



class Lattice2Workbench (Workbench): 
    MenuText = 'Lattice2'
    def __init__(self):
        # Hack: obtain path to Lattice by loading a dummy Py module
        import os
        import lattice2Dummy
        self.__class__.Icon = os.path.dirname(lattice2Dummy.__file__) + u"/PyResources/icons/Lattice2.svg".replace("/", os.path.sep)
    
    def Initialize(self):
        cmdsArrayTools = []
        cmdsCompoundTools = []
        cmdsMiscTools = []
        
        import lattice2Placement as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import lattice2LinearArray as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import lattice2PolarArray as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import lattice2ArrayFromShape as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        
        import lattice2Invert as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import lattice2JoinArrays as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import lattice2ArrayFilter as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import lattice2ProjectArray as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        import lattice2Resample as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands        
        
        import lattice2Apply as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands
        import lattice2Compose as mod
        cmdsArrayTools = cmdsArrayTools + mod.exportedCommands
        import lattice2Downgrade as mod
        
        cmdsCompoundTools = cmdsCompoundTools + mod.exportedCommands
        import CompoundFilter as mod
        cmdsCompoundTools = cmdsCompoundTools + mod.exportedCommands
        import FuseCompound as mod
        cmdsCompoundTools = cmdsCompoundTools + mod.exportedCommands
        import lattice2Inspect as mod
        cmdsCompoundTools = cmdsCompoundTools + mod.exportedCommands
        import lattice2BoundBox as mod
        cmdsMiscTools = cmdsMiscTools + mod.exportedCommands
        import lattice2ShapeString as mod
        cmdsMiscTools = cmdsMiscTools + mod.exportedCommands
        import lattice2SubstituteObject as mod
        cmdsMiscTools = cmdsMiscTools + mod.exportedCommands
        
        self.appendToolbar('Lattice2ArrayTools', cmdsArrayTools)
        self.appendToolbar('Lattice2CompoundTools', cmdsCompoundTools)
        self.appendToolbar('Lattice2MiscTools', cmdsMiscTools)
        #FreeCADGui.addIconPath( '' )
        #FreeCADGui.addPreferencePage( '','Lattice2' )
        self.appendMenu('Lattice2', cmdsArrayTools)
        self.appendMenu('Lattice2', cmdsCompoundTools)
        self.appendMenu('Lattice2', cmdsMiscTools)

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


Gui.addWorkbench(Lattice2Workbench())

