from ditto.readers.cyme.cyme_mapper import CymeMapper
from ditto.readers.cyme.equipment.matrix_impedance_recloser_equipment import MatrixImpedanceRecloserEquipmentMapper
from gdm.distribution.components.matrix_impedance_recloser import MatrixImpedanceRecloser
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.controllers.distribution_recloser_controller import DistributionRecloserController
from gdm.quantities import Distance
from gdm.distribution.enums import Phase

class MatrixImpedanceRecloserMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Network'
    cyme_section = 'RECLOSER SETTING'

    def parse(self, row, section_id_sections, equipment_data):

        name = self.map_name(row)
        buses = self.map_buses(row, section_id_sections)
        length = self.map_length(row)
        phases = self.map_phases(row, section_id_sections)
        is_closed = self.map_is_closed(row, phases)
        controller = self.map_controller(row)
        equipment = self.map_equipment(row, phases, equipment_data)

        return MatrixImpedanceRecloser(
            name=name,
            buses=buses,
            length=length,
            phases=phases,
            is_closed=is_closed,
            controller=controller,
            equipment=equipment
        )

    def map_name(self, row):
        name = row['SectionID']
        return name
    
    def map_buses(self, row, section_id_sections):
        section_id = str(row['SectionID'])
        section = section_id_sections[section_id]
        from_bus_name = section['FromNodeID']
        to_bus_name = section['ToNodeID']
        
        from_bus = self.system.get_component(component_type=DistributionBus, name=from_bus_name)
        to_bus = self.system.get_component(component_type=DistributionBus, name=to_bus_name)
        return [from_bus, to_bus]

    def map_length(self, row):
        length = Distance(0.001,'km')
        return length
    
    def map_phases(self, row, section_id_sections):
        section_id = str(row['SectionID'])
        section = section_id_sections[section_id]
        phase = section['Phase']
        phases = []
        if 'A' in phase:
            phases.append(Phase.A)
        if 'B' in phase:
            phases.append(Phase.B)
        if 'C' in phase:
            phases.append(Phase.C)
        return phases
    
    def map_is_closed(self, row, phases):
        is_closed = []
        for phase in phases:
            if row['ConnectionStatus'] == '0':
                is_closed.append(True)
            else:
                is_closed.append(False)
        return is_closed
    
    def map_controller(self, row):
        return DistributionRecloserController.example()
    

    def map_equipment(self, row, phases,equipment_data):
        recloser_id = row['EqID']
        mapper = MatrixImpedanceRecloserEquipmentMapper(self.system)
        equipment_row = equipment_data.loc[recloser_id]
        if equipment_row is not None:
            equipment = mapper.parse(equipment_row, phases)
            if equipment is not None:
                return equipment
        return None




