######################################################################
# BioSimSpace: Making biomolecular simulation a breeze!
#
# Copyright: 2017-2018
#
# Authors: Lester Hedges <lester.hedges@gmail.com>
#
# BioSimSpace is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# BioSimSpace is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BioSimSpace. If not, see <http://www.gnu.org/licenses/>.
#####################################################################

"""
Tools for visualising molecular systems.
Author: Lester Hedges <lester.hedges@gmail.com>
"""

import Sire as _Sire

from BioSimSpace import _is_notebook

from ..Process._process import Process as _Process
from .._SireWrappers import System as _System

import nglview as _nglview
import os as _os
import shutil as _shutil
import tempfile as _tempfile
import warnings as _warnings

__all__ = ["View"]

class View():
    """A class for handling interactive molecular visualisations."""

    def __init__(self, handle):
        """Constructor.

           Positional arguments
           --------------------

           handle : BioSimSpace.Process, BioSimSpace._SireWrappers.System
               A handle to a process or system.
        """

        # Make sure we're running inside a Jupyter notebook.
        if not _is_notebook():
            _warnings.warn("You can only use BioSimSpace.Notebook.View from within a Jupyter notebook.")
            return None

        # Check the handle.

        # BioSimSpace process.
        if isinstance(handle, _Process):
            self._handle = handle
            self._is_process = True

        # BioSimSpace system.
        elif type(handle) is _System:
            self._handle = handle._getSireSystem()
            self._is_process = False

        else:
            raise TypeError("The handle must be of type 'BioSimSpace.Process' or 'BioSimSpace._SireWrappers.System'.")

        # Create a temporary workspace for the view object.
        self._tmp_dir = _tempfile.TemporaryDirectory()
        self._work_dir = self._tmp_dir.name

        # Zero the number of views.
        self._num_views = 0

    def system(self, gui=True):
        """View the entire molecular system.

           Keyword arguments
           -----------------

           gui : bool
               Whether to display the gui.
        """

        # Make sure we're running inside a Jupyter notebook.
        if not _is_notebook():
            return None

        # Get the latest system from the process.
        if self._is_process:
            system = self._handle.getSystem()._getSireSystem()

            # No system.
            if system is None:
                return

        else:
            system = self._handle

        # Create and return the view.
        return self._create_view(system, gui=gui)

    def molecules(self, indices=None, gui=True):
        """View specific molecules.

           Keyword arguments
           -----------------

           indices : [ int ], range
               A list of molecule indices.

           gui : bool
               Whether to display the gui.
        """

        # Make sure we're running inside a Jupyter notebook.
        if not _is_notebook():
            return None

        # Return a view of the entire system.
        if indices is None:
            return self.system(gui=gui)

        # Convert single indices to a list.
        if isinstance(indices, range):
            indices = list(indices)
        elif type(indices) is not list:
            indices = [indices]

        # Check that the indices is a list of integers.
        if not all(isinstance(x, int) for x in indices):
            raise TypeError("'indices' must be a 'list' of type 'int'")

        # Get the latest system from the process.
        if self._is_process:
            system = self._handle.getSystem()._getSireSystem()

            # No system.
            if system is None:
                return

        else:
            system = self._handle

        # Extract the molecule numbers.
        molnums = system.molNums()

        # Create a new system.
        s = _Sire.System.System("BioSimSpace System")
        m = _Sire.Mol.MoleculeGroup("all")

        # Loop over all of the indices.
        for index in indices:
            if index < 0 or index > len(molnums):
                raise ValueError("Molecule index is out of range!")

            # Add the molecule.
            m.add(system[molnums[index]])

        # Add all of the molecules to the system.
        s.add(m)

        # Create and return the view.
        return self._create_view(s, gui=gui)

    def molecule(self, index=0, gui=True):
        """View a specific molecule.

           Keyword arguments
           -----------------

           index : int
               The molecule index.

           gui : bool
               Whether to display the gui.
        """

        # Make sure we're running inside a Jupyter notebook.
        if not _is_notebook():
            return None

        # Check that the index is an integer.
        if type(index) is not int:
            raise TypeError("'index' must be of type 'int'")

        # Get the latest system from the process.
        if self._is_process:
            system = self._handle.getSystem()._getSireSystem()

            # No system.
            if system is None:
                return

        else:
            system = self._handle

        # Extract the molecule numbers.
        molnums = system.molNums()

        # Make sure the index is valid.
        if index < 0 or index > len(molnums):
            raise ValueError("Molecule index is out of range!")

        # Create a new system and add a single molecule.
        s = _Sire.System.System("BioSimSpace System")
        m = _Sire.Mol.MoleculeGroup("all")
        m.add(system[molnums[index]])
        s.add(m)

        # Create and return the view.
        return self._create_view(s, gui=gui)

    def reload(self, index=None, gui=True):
        """Reload a particular view.

           Keyword arguments
           -----------------

           index : int
               The view index.

           gui : bool
               Whether to display the gui.
        """

        # Make sure we're running inside a Jupyter notebook.
        if not _is_notebook():
            return None

        # Return if there are no views.
        if self._num_views == 0:
            return

        # Default to the most recent view.
        if index is None:
            index = self._num_views - 1

        # Check that the index is an integer.
        elif type(index) is not int:
            raise TypeError("'index' must be of type 'int'")

        # Make sure the view index is valid.
        if index < 0 or index >= self._num_views:
            raise ValueError("View index (%d) is out of range: [0-%d]" % (index, self._num_views-1))

        # Create and return the view.
        return self._create_view(view=index, gui=gui)

    def nViews(self):
        """Return the number of views."""
        return self._num_views

    def savePDB(self, file, index=None):
        """Save a specific view as a PDB file.

           Positional arguments
           --------------------

           file : str
               The name of the file to write to.


           Keyword arguments
           -----------------

           index : int
               The view index.
        """

        # Make sure we're running inside a Jupyter notebook.
        if not _is_notebook():
            return None

        # Default to the most recent view.
        if index is None:
            index = self._num_views - 1

        # Check that the index is an integer.
        elif type(index) is not int:
            raise TypeError("'index' must be of type 'int'")

        # Make sure the view index is valid.
        if index < 0 or index >= self._num_views:
            raise ValueError("View index (%d) is out of range: [0-%d]" % (index, self._num_views-1))

        # Copy the file to the chosen location.
        _shutil.copyfile("%s/view_%04d.pdb" % (self._work_dir, index), file)

    def reset(self):
        """Reset the object, clearing all view files."""

        # Glob all of the view PDB structure files.
        files = _glob.glob("%s/*.pdb" % self._work_dir)

        # Remove all of the files.
        for file in files:
            _os.remove(file)

        # Reset the number of views.
        self._num_views = 0

    def _create_view(self, system=None, view=None, gui=True):
        """Helper function to create the NGLview object.

           Keyword arguments
           -----------------

           system : Sire.System.System
               A Sire molecular system.

           view : int
               The index of an existing view.

           gui : bool
               Whether to display the gui.
        """

        if system is None and view is None:
            raise ValueError("Both 'system' and 'view' cannot be 'None'.")

        elif system is not None and view is not None:
            raise ValueError("One of 'system' or 'view' must be 'None'.")

        # Make sure gui flag is valid.
        if gui not in [True, False]:
            gui = True

        # Default to the most recent view.
        if view is None:
            index = self._num_views
        else:
            index = view

        # Create the file name.
        filename = "%s/view_%04d.pdb" % (self._work_dir, index)

        # Increment the number of views.
        if view is None:
            self._num_views += 1

        # Create a PDB object and write to file.
        if system is not None:
            try:
                pdb = _Sire.IO.PDB2(system)
                pdb.writeToFile(filename)
            except:
                raise IOError("Failed to write system to 'PDB' format.") from None

        # Create the NGLview object.
        view = _nglview.show_file(filename)

        # Return the view and display it.
        return view.display(gui=gui)
