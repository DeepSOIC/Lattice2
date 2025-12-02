import unittest
import FreeCAD as App

import lattice2BaseFeature


class Lattice2GuiTestCase(unittest.TestCase):
    """ Custom TestCase base class for lattice2 GUI tests in FreeCAD. """

    def getPositionAlongVector(self, startPoint, directionVector, distance):
        """ Calculate a position along a given direction vector from the lattice array's base point.

        Args:
            startPoint: The starting point (FreeCAD.Vector) of the translation.
            directionVector: The direction vector (FreeCAD.Vector) to move along.
            distance: The distance to move along the direction vector.

        Returns:
            FreeCAD.Vector representing the calculated position.
        """
        directionVector = App.Vector(directionVector)  # Make a copy to avoid modifying the original
        unitDirection = directionVector.normalize()
        offsetVector = unitDirection.multiply(distance)
        return startPoint.add(offsetVector)

    def checkPlacements(self, latticeArray, expectedPlacements, tolerance=0.001, identifier="array", sortFunc=None):
        """ Test helper to compare generated placements against expected placements.
            Number of placements and individual placement values are compared.

        Args:
            latticeArray: The Lattice2 array object to get placements from.
            expectedPlacements: A list of expected placement objects to compare against.
            tolerance: The tolerance for placement comparison. Defaults to 0.1.
            identifier: An optional identifier string for error messages. Defaults to "array".
            sortFunc: Optional function to sort placements before comparison.
        """
        actualPlacements = lattice2BaseFeature.getPlacementsList(latticeArray)
        if sortFunc:
            actualPlacements.sort(key=sortFunc)
            expectedPlacements.sort(key=sortFunc)
        self.assertEqual(len(expectedPlacements), len(actualPlacements),
                         f"Unexpected number of placements generated.\nExpected: {len(expectedPlacements)}\nActual: {len(actualPlacements)}")
        for i, placement in enumerate(actualPlacements):
            expectedPlacement = expectedPlacements[i]
            self.assertTrue(placement.isSame(expectedPlacement, tolerance),
                            f"Placement mismatch at index {i} for {identifier}.\nExpected: {expectedPlacement}\nActual: {placement}")
