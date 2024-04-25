from abc import ABC, abstractproperty


#TODO: Define a BaseMapper class one level up from this?
class OpenDSSMapper(ABC):
    phase_map = { 'A': '.1',
              'B': '.2',
              'C': '.3',
              'N': '.0',
              'S1': '.1',
              'S2': '.2'
    }
    length_units_map = { "meter": "m",
              "mile": "mi", 
              "feet": "ft", 
              "foot": "ft", 
              "kilometer": "km", 
              "inch": "in", 
              "centimeter": "cm"
    }


    def __init__(self, model):
        self.model = model
        self.opendss_dict = {}
        self.substation = ''
        self.feeder = ''

        @abstractproperty
        def opendss_file():
            """Return the OpenDSS file."""
            pass

        @abstractproperty
        def altdss_name():
            """Return the name of the AltDSS class which defines the object."""
            pass

        @abstractproperty
        def altdss_composition_name():
            """Return the name of the AltDSS class which constructs the object through composition"""
            pass

    def map_common(self):
        return

    def map_uuid(self):
        return

    def map_system_uuid(self):
        return

    def map_belongs_to(self):
        distribution_component = self.model.belongs_to
        if distribution_component is not None:
            if distribution_component.substation is not None:
                self.substation = distribution_component.substation.name
            if distribution_component.feeder is not None:
                self.feeder = distribution_component.feeder.name

    def populate_opendss_dictionary(self):
        #Should not be populating an existing dictionary. Assert error if not empty
        assert(len(self.opendss_dict) ==0)
        self.map_common()
        for field in self.model.model_fields:
            mapping_function = getattr(self,'map_'+field)
            mapping_function()
