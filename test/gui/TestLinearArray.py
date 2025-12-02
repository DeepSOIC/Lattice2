import unittest

import FreeCAD as App
import Part

import lattice2BaseFeature
import lattice2LinearArray
from test.gui.Lattice2GuiTestCase import Lattice2GuiTestCase


class TestLinearArray(Lattice2GuiTestCase):
    def setUp(self):
        self.doc = App.newDocument("TestLinearArray")

    def tearDown(self):
        App.closeDocument(self.doc.Name)

    def test_linked_object_array(self):
        """ Test creation of a linear array linked to an object.

            This test uses the SpanN generator mode to verify that the span length is correctly
            derived from the linked object's geometry."""
        sketch = self.doc.addObject("Sketcher::SketchObject", "Sketch")
        # Make an edge at an angle
        sketch.addGeometry(
            Part.LineSegment(App.Vector(10, 5, 0), App.Vector(20, 10, 5))
        )
        self.doc.recompute()
        targetEdge = sketch.Shape.Edges[0]

        arrayName = "Linear_Array_Linked_Object"
        count = 5
        latticeArray = lattice2LinearArray.makeLinearArray(arrayName)
        latticeArray.Count = count
        latticeArray.Link = sketch
        latticeArray.SubLink = (sketch, "Edge1")
        latticeArray.GeneratorMode = "SpanN"
        self.doc.recompute()

        dirVector = (targetEdge.Vertexes[1].Point - targetEdge.Vertexes[0].Point).normalize()
        expectedStartPoint = App.Vector(targetEdge.Vertexes[0].Point)

        self.assertEqual(dirVector, latticeArray.Dir, msg=f"Array direction does not match linked edge direction")
        self.assertEqual(expectedStartPoint, latticeArray.Point,
                         msg=f"Start point does not match linked edge start point")
        self.assertEqual(targetEdge.Length, latticeArray.SpanEnd, msg="Span end does not match linked edge length")
        step = targetEdge.Length / (count - 1)
        # expectedPlacements = [App.Placement(self.getPositionAlongVector(expectedStartPoint, dirVector, step * i), App.Rotation(dirVector)) for i in range(count)]
        expectedPlacements = []
        rotation = App.Rotation(App.Vector(1, 0, 0), dirVector)  # Rotation in terms of aligning X axis to dirVector
        for i in range(count):
            position = self.getPositionAlongVector(expectedStartPoint, dirVector, step * i)
            expectedPlacements.append(App.Placement(position, rotation))
        self.checkPlacements(latticeArray, expectedPlacements)

    def test_array_offset(self):
        """ Test creation of a linear array with an offset applied.

            The offset is expressed as a fraction of the step between elements.
         """
        spanStart = 2.0
        spanEnd = 12.0
        count = 6
        offset = 1.5  # Offset by 1.5 times the step between elements
        arrayName = "Linear_Array_Offset"
        latticeArray = lattice2LinearArray.makeLinearArray(arrayName)
        latticeArray.GeneratorMode = "SpanN"
        latticeArray.SpanStart = spanStart
        latticeArray.SpanEnd = spanEnd
        latticeArray.Count = count
        latticeArray.Offset = offset
        self.doc.recompute()

        expectedStep = (spanEnd - spanStart) / (count - 1)  # Should remain unchanged
        self.assertAlmostEqual(expectedStep, latticeArray.Step,
                               msg="Step value does not match calculated space between elements")
        expectedFirstPlacementPosition = spanStart + offset * expectedStep
        expectedLastPlacementPosition = spanEnd + offset * expectedStep
        expectedPlacements = []
        for i in range(count - 1):
            position = expectedFirstPlacementPosition + i * expectedStep
            expectedPlacements.append(App.Placement(App.Vector(position, 0, 0), App.Rotation()))
        # Specifically check last placement is exactly at the end point of the span plus offset
        expectedPlacements.append(App.Placement(App.Vector(expectedLastPlacementPosition, 0, 0), App.Rotation()))
        self.checkPlacements(latticeArray, expectedPlacements)

    def test_span_n_array(self):
        """ Test creation of a linear array with span N. """
        spanStart = 5.0
        spanEnd = 20.5
        count = 6
        arrayName = "Linear_Array_Span_N"
        latticeArray = lattice2LinearArray.makeLinearArray(arrayName)
        latticeArray.GeneratorMode = "SpanN"
        latticeArray.SpanStart = spanStart
        latticeArray.SpanEnd = spanEnd
        latticeArray.Count = count
        self.doc.recompute()

        latticeArray = self.doc.getObject(arrayName)
        self.assertIsNotNone(latticeArray, msg=f"Linear array not found")
        # Calculate expected space between elements
        expectedSpaceBetween = (spanEnd - spanStart) / (count - 1)
        for valueIndex in range(1, latticeArray.NumElements):
            actualSpaceBetween = float(latticeArray.Values[valueIndex]) - float(latticeArray.Values[valueIndex - 1])
            self.assertAlmostEqual(expectedSpaceBetween, actualSpaceBetween,
                                   msg=f"Space between elements is not consistent at index {valueIndex}")
        # Allow small tolerance for floating point arithmetic
        self.assertAlmostEquals(expectedSpaceBetween, latticeArray.Step,
                                msg="Step value does not match calculated space between elements")
        expectedPlacements = []
        for i in range(count - 1):
            position = spanStart + i * expectedSpaceBetween
            expectedPlacements.append(App.Placement(App.Vector(position, 0, 0), App.Rotation()))
        # Specifically check last placement is exactly at the end point of the span
        expectedPlacements.append(App.Placement(App.Vector(spanEnd, 0, 0), App.Rotation()))
        self.checkPlacements(latticeArray, expectedPlacements)

    def test_n_step_array(self):
        """ Test creation of a linear array with N elements and specified step. """
        step = 4.5
        count = 8
        arrayName = "Linear_Array_N_Step"
        latticeArray = lattice2LinearArray.makeLinearArray(arrayName)
        latticeArray.GeneratorMode = "StepN"
        latticeArray.Step = step
        latticeArray.Count = count
        self.doc.recompute()

        latticeArray = self.doc.getObject(arrayName)
        self.assertIsNotNone(latticeArray, msg=f"Linear array not found")
        self.assertEqual(count, latticeArray.NumElements,
                         msg="NumElements does not match Count value")
        for valueIndex in range(1, latticeArray.NumElements):
            actualSpaceBetween = float(latticeArray.Values[valueIndex]) - float(latticeArray.Values[valueIndex - 1])
            self.assertAlmostEqual(step, actualSpaceBetween,
                                   msg=f"Space between elements is not consistent at index {valueIndex}")
        expectedPlacements = []
        for i in range(count):
            position = i * step
            expectedPlacements.append(App.Placement(App.Vector(position, 0, 0), App.Rotation()))
        self.checkPlacements(latticeArray, expectedPlacements)

    def test_span_step_array(self):
        """ Test creation of a linear array with specified span and step. """
        step = 3.2
        spanStart = 3.5
        spanEnd = 16.3
        arrayName = "Linear_Array_Span_Step"
        latticeArray = lattice2LinearArray.makeLinearArray(arrayName)
        latticeArray.GeneratorMode = "SpanStep"
        latticeArray.Step = step
        latticeArray.SpanStart = spanStart
        latticeArray.SpanEnd = spanEnd
        self.doc.recompute()

        latticeArray = self.doc.getObject(arrayName)
        self.assertIsNotNone(latticeArray, msg=f"Linear array not found")
        expectedCount = int((spanEnd - spanStart) / step) + 1
        self.assertEqual(expectedCount, latticeArray.NumElements,
                         msg="NumElements does not match calculated count from SpanStart, SpanEnd,  and Step")
        expectedPlacements = []
        for i in range(expectedCount):
            position = spanStart + i * step
            expectedPlacements.append(App.Placement(App.Vector(position, 0, 0), App.Rotation()))
        self.checkPlacements(latticeArray, expectedPlacements)

    def test_random_array(self):
        """ Test creation of a linear array with random distribution. """
        spanStart = 10.3
        spanEnd = 53.5
        count = 50
        arrayName = "Linear_Array_Random"
        latticeArray = lattice2LinearArray.makeLinearArray(arrayName)
        latticeArray.GeneratorMode = "Random"
        latticeArray.SpanStart = spanStart
        latticeArray.SpanEnd = spanEnd
        latticeArray.Count = count
        self.doc.recompute()

        latticeArray = self.doc.getObject(arrayName)
        self.assertIsNotNone(latticeArray, msg=f"Linear array not found")
        self.assertEqual(count, latticeArray.NumElements,
                         msg="NumElements does not match Count value")
        actualPlacements = lattice2BaseFeature.getPlacementsList(latticeArray)
        actualPlacements.sort(key=lambda p: p.Base.x)  # Sort placements by X position
        self.assertGreaterEqual(actualPlacements[0].Base.x, spanStart,
                                msg="Some placements are less than SpanStart")
        self.assertLessEqual(actualPlacements[-1].Base.x, spanEnd,
                             msg="Some placements are greater than SpanEnd")
