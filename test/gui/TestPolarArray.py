import math

import lattice2BaseFeature
import lattice2PolarArray2
from test.gui.Lattice2GuiTestCase import Lattice2GuiTestCase

import FreeCAD as App


class TestPolarArray(Lattice2GuiTestCase):
    def setUp(self):
        self.doc = App.newDocument("TestPolarArray")

    def tearDown(self):
        App.closeDocument(self.doc.Name)

    def test_polar_array_orient_mode(self):
        """ Test that orient mode rotates placements correctly in a polar array.

            This will use a placement at the first 45 degree position in the array to verify correct orientation.
        """

        angle = 45
        radius = 10
        lattice = lattice2PolarArray2.make()
        lattice.GeneratorMode = "SpanN"
        lattice.Count = 1
        lattice.SpanStart = angle
        lattice.SpanEnd = angle
        lattice.EndInclusive = True
        lattice.Radius = radius
        self.doc.recompute()

        position = App.Vector(radius * math.cos(math.radians(angle)),
                              radius * math.sin(math.radians(angle)),
                              0)

        # Rotations are in Yaw-Pitch-Roll (ZYX) convention
        orientModeOptions = {
            "Zero": App.Rotation(0, 0, 0),
            "Static": App.Rotation(0, 0, 0),
            "Radial": App.Rotation(angle, 0, 0),
            "Vortex": App.Rotation(90 + angle, 0, 0),
            "Centrifuge": App.Rotation(90 + angle, 0, -90),
            "Launchpad": App.Rotation(angle, -90, 180),
            "Dominoes": App.Rotation(90 + angle, -90, 0)
        }

        for orientMode, rotation in orientModeOptions.items():
            lattice.OrientMode = orientMode
            self.doc.recompute()

            self.checkPlacements(lattice, [App.Placement(position, rotation)], identifier=f"OrientMode: {orientMode}")

    def _get_expected_placements(self, count, spanStart, step, radius):
        expectedPlacements = []
        for i in range(count):
            angle = spanStart + step * i
            position = App.Vector(radius * math.cos(math.radians(angle)),
                                  radius * math.sin(math.radians(angle)),
                                  0)
            rotation = App.Rotation(angle, 0, 0)
            expectedPlacements.append(App.Placement(position, rotation))

        return expectedPlacements

    def test_span_n_polar_array(self):
        """ Test creation of a polar array using SpanN generator mode. """
        count = 8
        spanStart = 60
        spanEnd = 130
        radius = 20

        lattice = lattice2PolarArray2.make()
        lattice.GeneratorMode = "SpanN"
        lattice.Count = count
        lattice.SpanStart = spanStart
        lattice.SpanEnd = spanEnd
        lattice.EndInclusive = True
        lattice.Radius = radius
        lattice.OrientMode = "Radial"
        self.doc.recompute()

        step = (spanEnd - spanStart) / (count - 1)  # Count is end-exclusive
        self.assertEqual(step, lattice.Step, msg="Unexpected Step angle value")
        expectedPlacements = self._get_expected_placements(count - 1, spanStart, step, radius)

        # Specifically check last placement is exactly at the end point of the span (end-inclusive)
        expectedPlacements.append(App.Placement(
            App.Vector(radius * math.cos(math.radians(spanEnd)),
                       radius * math.sin(math.radians(spanEnd)),
                       0),
            App.Rotation(spanEnd, 0, 0)
        ))

        self.checkPlacements(lattice, expectedPlacements)

    def test_n_step_polar_array(self):
        """ Test creation of a polar array using N-Step generator mode. """
        count = 10
        step = 15
        spanStart = 42
        radius = 5

        lattice = lattice2PolarArray2.make()
        lattice.GeneratorMode = "StepN"
        lattice.Count = count
        lattice.SpanStart = spanStart
        lattice.Step = step
        lattice.EndInclusive = False
        lattice.Radius = radius
        lattice.OrientMode = "Radial"
        self.doc.recompute()

        expectedPlacements = self._get_expected_placements(count, spanStart, step, radius)
        self.checkPlacements(lattice, expectedPlacements)

    def test_span_step_polar_array(self):
        """ Test creation of a polar array using Span-Step generator mode. """
        step = 20
        spanStart = 10
        spanEnd = 100
        radius = 15

        lattice = lattice2PolarArray2.make()
        lattice.GeneratorMode = "SpanStep"
        lattice.SpanStart = spanStart
        lattice.SpanEnd = spanEnd
        lattice.Step = step
        lattice.EndInclusive = True
        lattice.Radius = radius
        lattice.OrientMode = "Radial"
        self.doc.recompute()

        expectedCount = ((spanEnd - spanStart) // step) + 1  # Add 1 for first element
        expectedPlacements = self._get_expected_placements(expectedCount, spanStart, step, radius)
        self.checkPlacements(lattice, expectedPlacements)

    def test_random_polar_array(self):
        """ Test creation of a polar array using Random generator mode. """
        spanStart = 40
        spanEnd = 180
        radius = 8
        count = 12

        lattice = lattice2PolarArray2.make()
        lattice.GeneratorMode = "Random"
        lattice.SpanStart = spanStart
        lattice.SpanEnd = spanEnd
        lattice.Count = count
        lattice.Radius = radius
        lattice.OrientMode = "Radial"
        self.doc.recompute()

        self.assertEqual(count, lattice.NumElements, msg="NumElements does not match Count value")

        # Verify all placements are within the specified span
        placements = lattice2BaseFeature.getPlacementsList(lattice)
        for i, placement in enumerate(placements):
            angle = math.degrees(math.atan2(placement.Base.y, placement.Base.x))
            if angle < 0:
                angle += 360
            self.assertGreaterEqual(angle, spanStart,
                                    msg=f"Placement at index {i} has angle {angle} below SpanStart")
            self.assertLessEqual(angle, spanEnd,
                                 msg=f"Placement at index {i} has angle {angle} above SpanEnd")
