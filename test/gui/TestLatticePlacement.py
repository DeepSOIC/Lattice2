import unittest

import FreeCAD as App

import lattice2ArrayFromShape
import lattice2Placement


class TestLatticePlacement(unittest.TestCase):
    """ Unit tests for single lattice placement objects in FreeCAD. """

    def setUp(self):
        self.doc = App.newDocument("TestLatticePlacement")

    def tearDown(self):
        App.closeDocument(self.doc.Name)

    def _test_common(self, placement, expectedPlacementName, identifier):
        self.assertIsNotNone(placement, msg=f"Placement {identifier} not found")
        self.assertEqual(expectedPlacementName, placement.Name,
                         msg=f"Placement name mismatch for {identifier}")
        self.assertEqual(1, placement.NumElements, msg=f"Placement NumElements mismatch for {identifier}")

    def test_basic_single_lattice_placement(self):
        """ Test creation and rotation of basic single lattice placement objects. """
        # Uses Yaw-Pitch-Roll (ZYX) rotation convention
        placementChoices = {
            "Custom": App.Rotation(0, 0, 0),
            "XY plane": App.Rotation(0, 0, 0),
            "XZ plane": App.Rotation(0, 0, 90),
            "YZ plane": App.Rotation(90, 0, 90),
        }

        for placementChoice, rotation in placementChoices.items():
            placementName = f"{placementChoice.replace(' ', '_')}_Placement"
            placement = lattice2Placement.makeLatticePlacement(name=placementName)
            placement.PlacementChoice = placementChoice
            self.doc.recompute()

            placement = self.doc.getObject(placementName)

            self._test_common(placement, placementName, placementChoice)
            self.assertEqual(placementChoice, placement.PlacementChoice,
                             msg=f"PlacementChoice mismatch for {placementName}")
            self.assertTrue(
                placement.Placement.Rotation.isSame(rotation, 0.1),  # Allow small tolerance for rounding errors
                msg=f"Placement rotation mismatch for {placementName}")

    def test_single_lattice_placement_along_axis(self):
        """ Test basic creation and rotation of single lattice placement objects along specific axes.

            Mimics default values for "along X", "along Y", and "along Z" single placements from GUI buttons.
        """

        # Key: The single placement name
        # Value: Tuple of XDir_wanted and expected position in Yaw-Pitch-Roll (ZYX) rotation convention
        alongAxisOptions = {
            "along X": (App.Vector(1, 0, 0), App.Rotation(0, 0, 0)),
            "along Y": (App.Vector(0, 1, 0), App.Rotation(90, 0, 0)),
            "along Z": (App.Vector(0, 0, 1), App.Rotation(0, -90, 180)),
        }

        defaultPriority = "XZY"

        for alongAxis, rotationTuple in alongAxisOptions.items():
            placementName = f"Lattice_Placement_{alongAxis.replace(' ', '_')}"
            placement = lattice2Placement.makeLatticePlacementAx(placementName)
            placement.XDir_wanted = rotationTuple[0]
            placement.Priority = defaultPriority
            self.doc.recompute()

            placement = self.doc.getObject(placementName)

            self._test_common(placement, placementName, alongAxis)
            self.assertEqual(rotationTuple[0], placement.XDir_actual, msg=f"XDir_actual mismatch for {placementName}")
            self.assertTrue(placement.Placement.Rotation.isSame(rotationTuple[1], 0.1),
                            msg=f"Placement rotation mismatch for {placementName}")

    def test_single_lattice_placement_euler_angles(self):
        """ Test basic creation and rotation of single lattice placement objects using Euler angles."""

        # Test rotations in Yaw-Pitch-Roll (ZYX) convention
        testRotations = [
            (0, 0, 0),
            (45, 30, 60),
            (90, 45, 30),
            (180, 90, 45),
            (-45, -30, -60),
        ]

        for testRotation in testRotations:
            angleNames = [str(angle).replace('-', 'neg') for angle in testRotation]
            placementName = f"Lattice_Placement_Euler_{'_'.join(angleNames)}"
            placement = lattice2Placement.makeLatticePlacementEuler(placementName)
            placement.Yaw = testRotation[0]
            placement.Pitch = testRotation[1]
            placement.Roll = testRotation[2]
            self.doc.recompute()

            placement = self.doc.getObject(placementName)

            self._test_common(placement, placementName, f"Euler_{'_'.join(angleNames)}")
            self.assertTrue(placement.Placement.Rotation.isSame(App.Rotation(*testRotation), 0.1),
                            msg=f"Placement rotation mismatch for {placementName}")

    def test_lattice_placement_from_shape(self):
        """ Test creation and of single lattice placement objects from shape geometry.

            Mimics default values for the following "Placement of shape" GUI buttons:
            "copy object Placement", "center of bounding box", "center of mass", and "inertial axis system".
        """
        cube = self.doc.addObject("Part::Box", "BaseCube")
        cube.Placement.Base = App.Vector(50, 100, 150)
        self.doc.recompute()

        positionChoices = {
            "child": cube.Placement.Base,  # Copy object Placement
            "child.CenterOfMass": cube.Shape.CenterOfMass,  # Center of mass
            "child.CenterOfBoundBox": cube.Shape.BoundBox.Center,  # Center of bounding box
            "child.Vertex": cube.Shape.Vertexes[0].Point,  # Inertial axis system
        }

        for translateMode, expectedPosition in positionChoices.items():
            placementName = f"Lattice_Placement_From_Shape_{translateMode.replace('.', '_')}"
            placement = lattice2ArrayFromShape.makeLatticeArrayFromShape(placementName)
            placement.ShapeLink = cube
            placement.TranslateMode = translateMode
            placement.TranslateElementIndex = 1  # Index is decremented by 1 to reference vertex
            placement.ExposePlacement = True
            self.doc.recompute()

            placement = self.doc.getObject(placementName)

            self._test_common(placement, placementName, translateMode)
            self.assertEqual(expectedPosition, placement.Placement.Base,
                             msg=f"Placement base position mismatch for {placementName}")
