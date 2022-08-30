__doc__ = 'module that registers preference page'

allSettings = """
Mod/Lattice2
WeakParenting False
MarkerColor #ffb300 (255,179,0)

Mod/Lattice2/Autosize
MarkerAdj 1.0
FeatureAdj 1.0
ModelAdj 1.0
AutoPosition True

Mod/Lattice2/Warnings
PopUpWarn True
PopUpErr True
LengthMismatch True
ParaSeriesRecompute True
"""

def addPreferences():
    import os
    import FreeCADGui as Gui

    # ## this works
    # import PySide.QtCore as qtc
    # 
    # ret = \
    # qtc.QResource.registerResource(os.path.dirname(__file__) + '/ui/pref/pref.rcc'.replace('/', os.path.sep))
    # 
    # if not ret:
    #     raise RuntimeError('Loading Lattice2/ui/pref/pref.rcc returned False, not loaded?')
    # 
    # Gui.addPreferencePage(':/ui/lattice2-pref-general.ui','Lattice2')

    ## but this is better for now    
    Gui.addPreferencePage(os.path.dirname(__file__) + '/ui/pref/lattice2-pref-general.ui'.replace('/', os.path.sep),"Lattice2")
    
    # ## interactive!
    # Gui.addPreferencePage(MyPrefPage,'Lattice2')
    
  
# # interactive version - not now, as it requires manual parameter read/write  
# from PySide import QtGui
# 
# class MyPrefPage:
#     form = None # the widget
#     
#     def __init__(self, parent=None):
#         import FreeCADGui as Gui
#         self.form = Gui.PySideUic.loadUi(':/ui/lattice2-pref-general.ui')
#         self.form.setWindowTitle("window title")
#         
#         #debug:
#         global prefpage
#         prefpage = self.form
#         
#     def saveSettings(self):
#         print ("saveSettings")
#     def loadSettings(self):
#         print ("loadSettings")
# 

addPreferences()
