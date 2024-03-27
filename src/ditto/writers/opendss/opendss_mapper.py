from abc import ABC, abstractmethod


#TODO: Define a BaseMapper class one level up from this?
class OpenDSSMapper(ABC):

    def __init__(self, model):
        self.model = model
        self.opendss_dict = {}
        self.altdss_name = None
        self.opendss_file = None
        self.substation = ''
        self.feeder = ''

#        opendss_class = Line_common

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
        for field in self.model.model_fields:
            mapping_function = getattr(self,'map_'+field)
            mapping_function()
