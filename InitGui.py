class LatticeWorkbench (Workbench): 
    MenuText = 'Lattice'
    def Initialize(self):
        commandslist=[]

        import FuseCompound
        commandslist = commandslist + FuseCompound.exportedCommands
        import CompoundFilter
        commandslist = commandslist + CompoundFilter.exportedCommands
        import latticeBoundBox
        commandslist = commandslist + latticeBoundBox.exportedCommands

        self.appendToolbar('Lattice', commandslist)
        self.treecmdList = ['importPart', 'updateImportedPartsCommand']
        #FreeCADGui.addIconPath( '' )
        #FreeCADGui.addPreferencePage( '','Lattice' )
        self.appendMenu('Lattice', commandslist)

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

