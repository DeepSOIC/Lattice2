# all imports are in command's activated(), for to speed up FC startup
import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui

class CommandLatticePDPattern:
    "Command to create Lattice PartDesign Pattern feature"
    def GetResources(self):
        import lattice2_rc
        return {'Pixmap'  : ":/icons/Lattice2_PDPattern.svg",
                'MenuText': "Lattice PartDesign Pattern",
                'Accel': "",
                'ToolTip': "Lattice PartDesign Pattern command. Replicates partdesign features at every placement in array."}
        
    def Activated(self):
        from lattice2Common import infoMessage, msgError, activeBody
        from lattice2PDPattern import cmdPDPattern
        try:
            if len(FreeCADGui.Selection.getSelection())==0:
                infoMessage("Lattice PartDesign Pattern",
                    "Lattice PartDesign Pattern command. Replicates partdesign features at every placement in array.\n\n"
                    "Please select features to repeat, reference placement (optional), and target placement/array. \n\n"
                    "You can use features from another body. Then, reference placement is required. You can also select a body (a \"template body\"), then all features from that body will be replicated.\n\n"
                    "Please observe scope restrictions. Reference placement must be in same body the original features are in; target placement/array must be in active body. You can create Lattice Arrays "
                    "right in PartDesign bodies, but you can't drag them in after the fact. You can import arrays of placements from elsewhere using a Shapebinder, or Part-o-Magic Ghost.")
                return
            if activeBody() is None:
                infoMessage("Lattice PartDesign Pattern", "No active body. Please, activate a body, first.")
            cmdPDPattern()
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False
            
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Lattice2_PDPattern', CommandLatticePDPattern())
    
exportedCommands = ['Lattice2_PDPattern']
