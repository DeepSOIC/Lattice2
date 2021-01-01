# Lattice2 Workbench
[![Total alerts](https://img.shields.io/lgtm/alerts/g/DeepSOIC/Lattice2.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/DeepSOIC/Lattice2/alerts/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/DeepSOIC/Lattice2.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/DeepSOIC/Lattice2/context:python)  

Lattice Workbench is a plug-in module/addon (workbench) for FreeCAD.

It's purpose is working with placements and arrays of placements. It functions similar to what an Assembly workbench does, but with emphasis on arrays. There are **no** constraints and relations, there are just arrays of placements that can be generated, combined, transformed, superimposed, and populated with shapes. 

Ever wondered how to create a protractor with FreeCAD? That's the aim of this workbench (including tick labeling). Also, exploded assemblies can be made with this workbench.

Additionally, the workbench features a few general-purpose tools, such as parametric downgrade, bounding boxes, shape info tool, and tools for working with collections of shapes (compounds).

One of the big design goals of the workbench is being as parametric as possible.

## Getting started

Follow through the [Basic Tutorial](https://github.com/DeepSOIC/Lattice2/wiki/Basic-Tutorial) to get the basic concept of Lattice2.

## Highlights
![Lattice2-FreeCAD-wormcutter](https://raw.githubusercontent.com/wiki/DeepSOIC/Lattice2/gallery/worm-cutter-done.png)

![Lattice2-FreeCAD-placement-interpolator](https://raw.githubusercontent.com/wiki/DeepSOIC/Lattice2/gallery/placement_interpolator_fixed.png)

Take a look at other examples in the [Gallery of screenshots](https://github.com/DeepSOIC/Lattice2/wiki/Gallery).

## Features
Let's have a glance over the most important capabilities that the workbench adds to FreeCAD:

* Re-use arrays as many times as you need. Unlike Draft array, which directly generates the array of shapes, lattice array tools generate arrays of placements. These can later be populated with shapes, as many times as necessary, without having to set up another array.  
* Extends PartDesign workflow, offering a way to reuse a sequence of features in arbitrary bodies and places.  
* Elements of array can be different. Unlike Draft Arrays, which always generate a set of equal shapes, Lattice arrays can be used to arrange a set of different shapes. Pack the shapes to be arranged into a Compound, and use Lattice [Populate with children](https://github.com/DeepSOIC/Lattice2/wiki/Feature-PopulateChildren) feature to arrange them.  
* Arrays of placements can be combined, inverted, generated from existing shape arrangements, made from individual placements, projected onto shapes, filtered, etc. This allows to produce complex arrangements without scripting.  
* Single placements can be used for primitive assembling of parts.  
* linear arrays and polar arrays can have their axes linked to edges of shapes  
* [ParaSeries](https://github.com/DeepSOIC/Lattice2/wiki/Feature-ParaSeries) feature allows to generate a series of parts with some parameter varied over a list of values.  

## Why Lattice2, not just Lattice?
Lattice2 was created at the moment when breaking changes needed to be made to Lattice, but there were a few things made with Lattice. So, it was decided to keep the workbench in that time's state indefinitely as version 1.0, and start development of a new version.

The goal was to allow editing old projects made with Lattice v1, by having both versions installed at the same time. So a new repository was started, and all the files were renamed to start with 'lattice2' or otherwise differ from those of Lattice v1. 

Lattice3 (if ever) will be a standalone repository, for the same reasons.

## Installation

### Prerequisites

* FreeCAD >= `v0.16.5155`  
* PartDesign tools require `v0.17+`  
* Both Py2/Qt4 and Py3/Qt5 builds are supported.

The workbench is OS independent, it should work on any system FreeCAD can be run on. If you find that it doesn't - that is a bug. Please open an ticket in the [issue queue](https://github.com/DeepSOIC/Lattice2/issues).  

**Note:** Lattice2 is written in FreeCAD's Python, and **must be run from within FreeCAD**. It requires no compilation, and can be installed by copying the repository to a special location.

### Automated install

There are several options to automate installation of this workbench.  
* The **most recommended method** is to use FreeCAD's built-in [Addon Manager](https://github.com/FreeCAD/FreeCAD-addons#1-builtin-addon-manager) (Tools > Addon manager).  
* Another method; Lattice2 workbench is packaged to Launchpad in the Ubuntu FreeCAD Community PPA (thanks to @abdullahtahiriyo). 
* Lattice2 can be installed via @microelly's [Plugin Loader](https://github.com/microelly2/freecad-pluginloader) (this option is deprecated).

**Note:** Any of the above options will require a restart of FreeCAD in order for the workbench to function.

### Manual install

<details>
  <summary>Expand this section if you prefer to manually install Lattice2</summary>
  
1. Download the workbench. There are several ways to do this, you can choose either:  
  * Scroll to the top of the page, and click 'clone or download' -> 'download zip' button  
  * `git clone https://github.com/DeepSOIC/Lattice2`
2. If you downloaded the .zip, unpack the archive and rename it to `Lattice2`. If you used `git clone` then ignore this step. 
3. Move the newly created `Lattice2` directory to where your default FreeCAD install directory is located:  
  * Windows: (sytem-wide install) `%AppData%\FreeCAD\Mod\Lattice2`  
  * Windows: (for individual installs)
    `C:\Program Files\FreeCAD\Mod\Lattice2`
  * Linux: `~/.FreeCAD/Mod/Lattice2`  
  * MacOS: `~/.FreeCAD/Mod/Lattice2`  
3. Restart FreeCAD  

**Important Note:** Make sure that `InitGui.py` (and the rest of `.py` files) end up directly under `Mod\Lattice2` directory (**not** under nested directory like `Mod\Lattice2\Lattice2`).

</details>

## Usage

After installing the workbench and restarting FC, Lattice2 should now appear in the workbench dropdown menu. It will be listed down towards the bottom of list. Now, you can familiarize yourself with Lattice2 through the [Basic Tutorial](https://github.com/DeepSOIC/Lattice2/wiki/Basic-Tutorial).

Side Note: If you want to install the workbench for development, `git clone` the repository wherever you like, and make a symlink in where FreeCAD can pick it up as an add-on. 

## Status

The workbench is stable. I will take care to not make breaking changes, and some new functionality may keep coming.

If you make your FreeCAD project using Lattice2, all further changes to the project must be done with Lattice2 installed, even if you don't touch the relevant features. Otherwise, the parametric features in the project will lose their bound functionality, and will not recompute, even if you install Lattice2 later. This is the case for all add-ons in FreeCAD, not just Lattice2.

## Getting Help

For Documentation see the [Lattice2 wiki](https://github.com/DeepSOIC/Lattice2/wiki) on Github. As the word "wiki" suggests, you can help by editing the documentation.

If you need help on something specific, you can ask a question on [FreeCAD forum](http://forum.freecadweb.org/) (there is no Lattice forum yet...). You can also ask me directly. **Note:** If you post to the forum, please add this to your post so that I get a notification:  
`[quote=DeepSOIC user_id=3888]Ding![/quote]`

NEW!: [Github Discussions for Lattice2](https://github.com/DeepSOIC/Lattice2/discussions) are enabled, you are welcome to ask questions and post random thoughts there!

## Contributing

If you have found a bug or are requesting a new feature, please first check to see if it has been previously reported already on the [Lattice2 Github repo issue tracker](https://github.com/DeepSOIC/Lattice2/issues). If not, feel free to open a ticket.

If you have fixed a bug or implemented a new feature you think suits the workbench, feel free to make a pull-request on Github.

## License

Lattice workbench is licensed under LGPL V2, just like FreeCAD. For more info, see [copying.lib](copying.lib) file in this repository.
