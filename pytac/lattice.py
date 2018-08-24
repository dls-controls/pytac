"""Representation of a lattice object which contains all the elements of the
    machine.
"""
import numpy
import pytac
from pytac.exceptions import LatticeException, DeviceException, FieldException, HandleException


class Lattice(object):
    """Representation of a lattice.

    Represents a lattice object that contains all elements of the ring. It has
    a name and a control system to be used for unit conversion.

    **Attributes:**

    Attributes:
        name (str): The name of the lattice.

    .. Private Attributes:
           _lattice (list): The list of all the element objects in the lattice.
           _cs (ControlSystem): The control system used to store the values on
                                 a PV.
           _energy (int): The total energy of the lattice.
           _model (Model): A pytac model object associated with the lattice.
    """
    def __init__(self, name, energy):
        """.. The constructor method for the class, called whenever a 'Lattice'
               object is constructed.

        Args:
            name (str): The name of the lattice.
            energy (int): The total energy of the lattice.

        **Methods:**
        """
        self.name = name
        self._lattice = []
        self._energy = energy
        self._models = {}
        self._uc = {}

    def set_model(self, model, model_type):
        """Add a model to the lattice.

        Args:
            model (Model): instance of Model.
            model_type (str): EpicsModel or ATModel.
        """
        self._models[model_type] = model

    def get_fields(self):
        """Get the fields defined on the lattice.

        Includes all fields defined by all models.

        Returns:
            set: A sequence of all the fields defined on the lattice.
        """
        fields = set()
        for model in self._models:
            fields.update(self._models[model].get_fields())
        return fields

    def add_device(self, field, device, uc):
        """Add device and unit conversion objects to a given field.

        A DeviceModel must be set before calling this method.

        Args:
            field (str): The key to store the unit conversion and device
                          objects.
            device (Device): The device object used for this field.
            uc (UnitConv): The unit conversion object used for this field.

        Raises:
            KeyError: if no DeviceModel is set.
        """
        self._models[pytac.LIVE].add_device(field, device)
        self._uc[field] = uc

    def get_device(self, field):
        """Get the device for the given field.

        A DeviceModel must be set before calling this method.

        Args:
            field (str): The lookup key to find the device on the lattice.

        Returns:
            Device: The device on the given field.

        Raises:
            KeyError: if no DeviceModel is set.
        """
        return self._models[pytac.LIVE].get_device(field)

    def get_unitconv(self, field):
        """Get the unit conversion option for the specified field.

        Args:
            field (str): The field associated with this conversion.

        Returns:
            UnitConv: The object associated with the specified field.

        Raises:
            KeyError: if no unit conversion object is present.
        """
        return self._uc[field]

    def get_value(self, field, handle=pytac.RB, units=pytac.ENG,
                  model=pytac.LIVE):
        """Get the value for a field on the lattice.

        Args:
            field (str): The requested field.
            handle (str): pytac.SP or pytac.RB.
            units (str): pytac.ENG or pytac.PHYS returned.
            model (str): pytac.LIVE or pytac.SIM.

        Returns:
            float: The value of the requested field

        Raises:
            DeviceException: if there is no device on the given field.
            FieldException: if the lattice does not have the specified field.
        """
        try:
            model = self._models[model]
            value = model.get_value(field, handle)
            return self._uc[field].convert(value, origin=model.units,
                                           target=units)
        except KeyError:
            raise DeviceException('No model type {} on lattice {}'.format(model,
                                                                          self))
        except FieldException:
            raise FieldException('No field {} on lattice {}'.format(field, self))

    def set_value(self, field, value, handle=pytac.SP, units=pytac.ENG,
                  model=pytac.LIVE):
        """Set the value for a field.

        This value can be set on the machine or the simulation.

        Args:
            field (str): The requested field.
            value (float): The value to set.
            handle (str): pytac.SP or pytac.RB.
            units (str): pytac.ENG or pytac.PHYS.
            model (str): pytac.LIVE or pytac.SIM.

        Raises:
            DeviceException: if arguments are incorrect.
            FieldException: if the lattice does not have the specified field.
        """
        if handle != pytac.SP:
            raise HandleException('Must write using {}'.format(pytac.SP))
        try:
            model = self._models[model]
        except KeyError:
            raise DeviceException('No model type {} on lattice {}'.format(model,
                                                                          self))
        try:
            value = self._uc[field].convert(value, origin=units, target=model.units)
            model.set_value(field, value)
        except KeyError:
            raise FieldException('No field {} on lattice {}'.format(model, self))
        except FieldException:
            raise FieldException('No field {} on lattice {}'.format(field, self))

    def get_energy(self):
        """Function to get the total energy of the lattice.

        Returns:
            int: energy of the lattice.
        """
        return self._energy

    def __getitem__(self, n):
        """Get the (n + 1)th element of the lattice - i.e. index 0 represents
        the first element in the lattice.

        Args:
            n (int): index.

        Returns:
            Element: indexed element.
        """
        return self._lattice[n]

    def __len__(self):
        """The number of elements in the lattice.

        When using the len function returns the number of elements in
        the lattice.

        Returns:
            int: The number of elements in the lattice.
        """
        return len(self._lattice)

    def get_length(self):
        """Returns the length of the lattice.

        Returns:
            float: The length of the lattice.
        """
        total_length = 0
        for e in self._lattice:
            total_length += e.length
        return total_length

    def add_element(self, element):
        """Append an element to the lattice.

        Args:
            element (Element): element to append.
        """
        self._lattice.append(element)

    def get_elements(self, family=None, cell=None):
        """Get the elements of a family from the lattice.

        If no family is specified it returns all elements. Elements are
        returned in the order they exist in the ring.

        Args:
            family (str): requested family.
            cell (int): restrict elements to those in the specified cell.

        Returns:
            list: list containing all elements of the specified family.
        """
        elements = []
        if family is None:
            elements = self._lattice

        for element in self._lattice:
            if family in element.families:
                elements.append(element)

        if cell is not None:
            elements = [e for e in elements if e.cell == cell]

        return elements

    def get_all_families(self):
        """Get all families of elements in the lattice.

        Returns:
            set: all defined families.
        """
        families = set()
        for element in self._lattice:
            families.update(element.families)

        return families

    def get_s(self, elem):
        """Find the s position of an element in the lattice.

        Note that the given element must exist in the lattice.

        Args:
            elem (Element): The element that the position is being asked for.

        Returns:
            float: The position of the given element.

        Raises:
            LatticeException: if element doesn't exist in the lattice.
        """
        s_pos = 0
        for el in self._lattice:
            if el is not elem:
                s_pos += el.length
            else:
                return s_pos
        raise LatticeException('Element {} not in lattice {}'.format(elem, self))

    def get_family_s(self, family):
        """Get s positions for all elements from the same family.

        Args:
            family (str): requested family.

        Returns:
            list: list of s positions for each element.
        """
        elements = self.get_elements(family)
        s_positions = []
        for element in elements:
            s_positions.append(self.get_s(element))
        return s_positions

    def get_element_devices(self, family, field):
        """Get devices for a specific field for elements in the specfied
        family.

        Typically all elements of a family will have devices associated with
        the same fields - for example, BPMs each have a device for fields 'x'
        and 'y'.

        Args:
            family (str): family of elements.
            field (str): field specifying the devices.

        Returns:
            list: devices for specified family and field.
        """
        elements = self.get_elements(family)
        devices = []
        for element in elements:
            try:
                devices.append(element.get_device(field))
            except KeyError:
                pass

        return devices

    def get_element_device_names(self, family, field):
        """Get the names for devices attached to a specific field for elements
        in the specfied family.

        Typically all elements of a family will have devices associated with
        the same fields - for example, BPMs each have a device for fields 'x'
        and 'y'.

        Args:
            family (str): family of elements.
            field (str): field specifying the devices.

        Returns:
            list: device names for specified family and field.
        """
        devices = self.get_element_devices(family, field)
        return [device.name for device in devices]

    def get_element_values(self, family, field, handle, dtype=None):
        """Get all values for a family and field.

        Args:
            family (str): family to request the values of.
            field (str): field to request values for.
            handle (str): pytac.RB or pytac.SP.
            dtype (numpy.dtype): if None, return a list. If not None, return a
                                  numpy array of the specified type.

        Returns:
            list or numpy array: sequence of values.
        """
        elements = self.get_elements(family)
        values = [element.get_value(field, handle) for element in elements]
        if dtype is not None:
            values = numpy.array(values, dtype=dtype)
        return values

    def set_element_values(self, family, field, values):
        """Sets the values for a family and field.

        The PVs are determined by family and device. Note that only setpoint
        PVs can be modified.

        Args:
            family (str): family on which to set values.
            field (str):  field to set values for.
            values (sequence): A list of values to assign.

        Raises:
            LatticeException: if the given list of values doesn't match the
                               number of elements in the family.
        """
        elements = self.get_elements(family)
        if len(elements) != len(values):
            raise LatticeException("Number of elements in given array must be"
                                   " equal to the number of elements in the "
                                   "family")
        for element, value in zip(elements, values):
            element.set_value(field, value)
