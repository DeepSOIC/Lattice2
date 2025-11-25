import unittest

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher

import lattice2AttachablePlacement


class TestLatticeAttachment(unittest.TestCase):
    def setUp(self):
        self.doc = App.newDocument("TestLatticeAttachment")

    def tearDown(self):
        App.closeDocument(self.doc.Name)

    def test_attached_placement(self):
        """ Test creation of a single attached placement object."""
        cube = self.doc.addObject("Part::Box", "Cube")
        cube.Placement.Base = App.Vector(30, 50, 10)

        placementName = "Attached_Placement"
        placement = lattice2AttachablePlacement.makeAttachablePlacement(name=placementName)
        lattice2AttachablePlacement.editNewAttachment(placement)

        # Confirm attachment dialog is open
        attachmentDialog = Gui.Control.activeTaskDialog()
        self.assertIsNotNone(attachmentDialog, msg="Attachment dialog not found")
        attachmentDialog.reject()

        mapMode = "ObjectXY"
        placement.AttachmentSupport = ((cube,))
        self.doc.recompute()
        placement.MapMode = mapMode
        self.doc.recompute()

        placement = self.doc.getObject(placementName)
        self.assertIsNotNone(placement, msg=f"Placement {placementName} not found")
        self.assertEqual(1, placement.NumElements)
        self.assertEqual(cube.Placement.Base, placement.Placement.Base)
        self.assertEqual(cube.Name, placement.AttachmentSupport[0][0].Name)
        self.assertEqual(mapMode, placement.MapMode)

    def test_array_attached_placement(self):
        """ Test creation of array attached placement objects."""
        sketch = self.doc.addObject("Sketcher::SketchObject", "Sketch")
        # Make a few identical L shapes as done in the wiki
        numInstances = 8
        for i in range(numInstances):
            sketch.addGeometry(Part.LineSegment(App.Vector(0, i, 0), App.Vector(10, i, 0)))  # Horizontal line
            sketch.addGeometry(Part.LineSegment(App.Vector(10, i, 0), App.Vector(10, i + 10, 0)))  # Vertical line
            sketch.addConstraint(
                Sketcher.Constraint('Coincident', 2 * i, 2, 2 * i + 1, 1))  # Vertical line start to horizontal line end

        attachedPlacementName = "Attached_Placement"
        attachedPlacement = lattice2AttachablePlacement.makeAttachablePlacement(name=attachedPlacementName)
        attachedPlacement.AttachmentSupport = [(sketch, "Edge5"), (sketch, "Edge6")]
        self.doc.recompute()
        attachedPlacement.MapMode = "InertialCS"
        self.doc.recompute()

        arrayPlacementName = "Array_Attached_Placement"
        arrayPlacement = lattice2AttachablePlacement.makeLatticeAttachedPlacementSubsequence(name=arrayPlacementName)
        arrayPlacement.Base = attachedPlacement
        arrayPlacement.CycleMode = "Open"
        self.doc.recompute()

        arrayPlacement = self.doc.getObject(arrayPlacementName)
        self.assertIsNotNone(arrayPlacement, msg=f"Placement {arrayPlacementName} not found")
        self.assertEqual(numInstances - 2, arrayPlacement.NumElements)  # Should only have placements for edges 3 to 8

        arrayPlacement.CycleMode = "Periodic"  # Allows looping back to first instance
        self.doc.recompute()

        self.assertEqual(numInstances, arrayPlacement.NumElements)  # Now should have placements for all instances
