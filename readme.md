# What is Lattice2 workbench
Lattice Workbench is a plug-in module (workbench) for FreeCAD.

The workbench purpose is working with placements and arrays of placements. It is a sort of assembly workbench, but with emphasis on arrays. There are no constraints and relations, there are just arrays of placements that can be generated, combined, transformed, superimposed and populated with shapes. 

Ever wondered how to create a protractor with FreeCAD? That's the aim of the workbench (including tick labeling). Also, exploded assemblies can be made with the workbench.

Additionally, the workbench features a few general-purpose tools, such as parametric downgrade, bounding boxes, shape info tool, and tools for working with collections of shapes (compounds).

One of the big design goals of the workbench is being as parametric as possible.

# Highlights
![Lattice2-FreeCAD-wormcutter](https://raw.githubusercontent.com/wiki/DeepSOIC/Lattice2/gallery/worm-cutter-done.png)

![Lattice2-FreeCAD-placement-interpolator](https://raw.githubusercontent.com/wiki/DeepSOIC/Lattice2/gallery/placement_interpolator_fixed.png)

Take a look at other examples in the [Gallery of screenshots](https://github.com/DeepSOIC/Lattice2/wiki/Gallery).

Let's have a glance over the most important capabilities that the workbench adds to FreeCAD:

* Re-use arrays as many times as you need. Unlike Draft array, which directly generates the array of shapes, lattice array tools generate arrays of placements. These can later be populated with shapes, as many times as necessary, without having to set up another array.

* Elements of array can be different. Unlike Draft Arrays, which always generate a set of equal shapes, Lattice arrays can be used to arrange a set of different shapes. Pack the shapes to be arranged into a Compound, and use Lattice [Populate with children](https://github.com/DeepSOIC/Lattice2/wiki/Feature-PopulateChildren) feature to arrange them.

* Arrays of placements can be combined, inverted, generated from existing shape arrangements, made from individual placements, projected onto shapes, filtered, etc. This allows to produce complex arrangements without scripting.

* single placements can be used for primitive assembling of parts.

* linear arrays and polar arrays can have their axes linked to edges of shapes

* parametric explode commands allow extraction of specific elements of arrays, without losing parametric relation to the original. 

* [ParaSeries](https://github.com/DeepSOIC/Lattice2/wiki/Feature-ParaSeries) feature allows to generate a series of parts with some parameter varied over a list of values.

# Why Lattice2, not just Lattice?
Lattice2 was created at the moment when breaking changes needed to be made, but there were a few things made with Lattice. So, it was decided to keep the workbench in that time's state indefinitely as version 1.0, and start development of a new version.

The goal was to be able to have both Lattice v1 and v2 in a single FreeCAD installation. So a new repository was started, and all the files were renamed to start with 'lattice2' or otherwise differ from those of Lattice v1.

# What's changed in Lattice2

* Population tools now have 'move' mode: a placement/set of placements can be supplied to treat as origins of the objects being populated

* Experimental recompute controlling tools were added

* Most icons were redesigned to follow a concept

* Lattice workbench can now be imported from Py console all at once, like that: `import Lattice2`

* ParaSeries feature was added, which can create a series of parts by changing some parameter of the model.

# Download/install
repository: https://github.com/DeepSOIC/Lattice2

Lattice2 WB requires FreeCAD no less than v0.16.5155.

The workbench is OS independent, it should work on any system FreeCAD can be run on. If you find that it doesn't - that is a bug. Please make an issue.  

Lattice2 is written in FreeCAD's Python, and must be run from within FreeCAD. It requires no compilation, and can be installed by copying the repository to a special location.

# Manual install: 
1. Scroll to the top of the page, and click 'download zip' button

2. Unpack the contents into a "Lattice2" folder created in \Path\to\FreeCAD\Mod, and restart FreeCAD. <br>
Note that InitGui.py (and the rest of .py files) should end up directly under Mod\Lattice2 (not under nested directory like Mod\Lattice2\Lattice2).

After you install the workbench, it should appear at the bottom of list of workbench selector in FreeCAD.

# Automated installation:
* Lattice2 workbench is packaged to Launchpad in the Ubuntu FreeCAD Community PPA (thanks to @abdullahtahiriyo). 
* Lattice2 can be installed via [FreeCAD addons installer macro](https://github.com/FreeCAD/FreeCAD-addons)
* Lattice2 can be installed via @microelly's [Plugin Loader](https://github.com/microelly2/freecad-pluginloader)


# License
Lattice workbench is licenced under LGPL V2, just like FreeCAD. For more info, see copying.lib file in the repository.

# Getting Help

Documentation: see [Lattice2 wiki](https://github.com/DeepSOIC/Lattice2/wiki) on Github. As the word "wiki" suggests, you can help by editing the documentation.

If you need help on something specific, you can ask a question on [FreeCAD forum](http://forum.freecadweb.org/index.php) (there is no Lattice forum yet...). You can also ask me directly.

If you have found a bug, report it [here, in Github's issue tracker for Lattice2](https://github.com/DeepSOIC/Lattice2/issues). You can also post ideas for new features there, as well as plain questions.

If you have fixed a bug, or implemented a new feature you think suits the workbench, or whatever - feel free to make a pull-request here on github.

# Status
This version can be considered a release candidate. I will take care to not make breaking changes, but new functionality may keep coming.

