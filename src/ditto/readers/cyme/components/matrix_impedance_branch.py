from gdm.quantities import Distance
from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.distribution.equipment.matrix_impedance_branch_equipment import MatrixImpedanceBranchEquipment
from gdm.distribution.components.matrix_impedance_branch import MatrixImpedanceBranch
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.enums import Phase


class MatrixImpedanceBranchMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Network'
    cyme_section = 'UNDERGROUNDLINE SETTING'

    def parse(self, row, section_id_sections):
        name = self.map_name(row)
        buses = self.map_buses(row,section_id_sections)
        length = self.map_length(row)
        phases = self.map_phases(row, section_id_sections)
        equipment = self.map_equipment(row, phases)
        try:
            return MatrixImpedanceBranch(name=name,
                                buses=buses,
                                length=length,
                                phases=phases,
                                equipment=equipment)
        except Exception as e:
            print(f"Error creating GeometryBranch {name}: {e}")
            print(buses)
            return None

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
        length = Distance(float(row['Length']),'mile').to('km')
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

    def map_equipment(self, row, phases):
        line_id = row['LineCableID']
        equipment_name = f"{line_id}_{len(phases)}"
        line = self.system.get_component(component_type=MatrixImpedanceBranchEquipment, name=equipment_name)
        return line