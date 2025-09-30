
from gdm.quantities import Distance, Current, ResistancePULength, ReactancePULength, CapacitancePULength
from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.distribution.equipment.matrix_impedance_branch_equipment import MatrixImpedanceBranchEquipment
from gdm.distribution.components.matrix_impedance_branch import MatrixImpedanceBranch
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.enums import Phase




class MatrixImpedanceBranchMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Network'
    cyme_section = 'SECTION'

    def parse(self, row, used_sections, section_id_sections):

        name = self.map_name(row)
        if name in used_sections:
            return None
        buses = self.map_buses(row,section_id_sections)
        length = self.map_length()
        phases = self.map_phases(row, section_id_sections)
        equipment = self.map_equipment(row, phases)

        try:
            return MatrixImpedanceBranch.model_construct(name=name,
                                buses=buses,
                                length=length,
                                phases=phases,
                                equipment=equipment)
        except Exception as e:
            print(f"Error creating MatrixImpedanceBranch {name}: {e}")
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

    def map_length(self):
        length = Distance(float(1.0),'m')
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
        default_matrix = [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
        matrix = [row[:len(phases)] for row in default_matrix[:len(phases)]]
        r_matrix = ResistancePULength(
            matrix,
            "ohm/mi",
        )
        x_matrix = ReactancePULength(
            matrix,
            "ohm/mi",
        )
        c_matrix = CapacitancePULength(
            matrix,
            "nanofarad/mi",
        )
        ampacity = Current(600.0, "A")
        line = MatrixImpedanceBranchEquipment.model_construct(name=row['SectionID'],
                                               r_matrix=r_matrix,
                                               x_matrix=x_matrix,
                                               c_matrix=c_matrix,
                                               ampacity=ampacity
                                               )
        return line