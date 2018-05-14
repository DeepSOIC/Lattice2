import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
from lattice2Common import *

class CommandBasicTutorial:
    "opens basic tutorial"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2.svg"),
                'MenuText': "Help! Basic tutorial",
                'ToolTip': "Open basic tutorial (available offline)"}
        
    def Activated(self):
        try:
            import os
            import lattice2Dummy
            tutorial_pdf = os.path.dirname(lattice2Dummy.__file__) + "/ExampleProjects/Lattice2WorkbenchBasicTutorial.pdf".replace("/", os.path.sep)

            import webbrowser
            webbrowser.open(tutorial_pdf)
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        return True
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_Help_BasicTutorial', CommandBasicTutorial())


class CommandOpenManual:
    "opens wiki"
    def GetResources(self):
        return {'Pixmap'  : getIconPath("Lattice2.svg"),
                'MenuText': "Help! Open Wiki",
                'ToolTip': "Open Lattice2 documentation (on the web)"}
        
    def Activated(self):
        try:
            import webbrowser
            webbrowser.open('https://github.com/DeepSOIC/Lattice2/wiki')
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        return True
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_Help_OpenManual', CommandOpenManual())

exportedCommands = ['Lattice2_Help_BasicTutorial', 'Lattice2_Help_OpenManual']
