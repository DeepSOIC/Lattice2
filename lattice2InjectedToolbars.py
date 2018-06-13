import FreeCAD as App

def findToolbar(name, label, workbench, create = False):
    """findToolbar(name, label, workbench, create= False): returns tuple "User parameter:BaseApp/Workbench/Global/Toolbar", "toolbar_group_name"."""
    tb_root = "User parameter:BaseApp/Workbench/{workbench}/Toolbar".format(workbench= workbench)
    pp = App.ParamGet(tb_root)
    if pp.HasGroup(name):
        return [tb_root, name]
    
    for i in range(10):
        g = 'Custom_'+str(i)
        if pp.HasGroup(g) and pp.GetGroup(g).GetString('Name') == label:
            return [tb_root, g]
    if create:
        return [tb_root, name]
    return None

def findGlobalToolbar(name, label, create = False):
    return findToolbar(name, label, 'Global', create)

def findPDToolbar(name, label, create = False):
    return findToolbar(name, label, 'PartDesignWorkbench', create)

def registerPDToolbar():
    creating_anew = not isPDRegistered()
    p = App.ParamGet('/'.join(findPDToolbar('Lattice2',"Lattice2 PartDesign", create= True)))
    p.SetString("Name", "Lattice2 PartDesign")
    import lattice2PDPatternCommand as PDPattern
    for cmd in PDPattern.exportedCommands:
        p.SetString(cmd, "FreeCAD")
    if creating_anew:
        p.SetBool("Active", 1)

def isPDRegistered():
    return findPDToolbar('Lattice2',"Lattice2 PartDesign")
