from ditto.readers.synergi.synergi_mapper import SynergiMapper
from gdm.distribution.components.geometry_branch import GeometryBranch
from gdm.distribution.equipment.geometry_branch_equipment import GeometryBranchEquipment
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment
from gdm.distribution.equipment.concentric_cable_equipment import ConcentricCableEquipment
from gdm import PositiveDistance, Phase
from loguru import logger
from ditto.readers.synergi.length_units import length_units

class GeometryBranchMapper(SynergiMapper):
    def __init__(self, system):
        super().__init__(system)

    synergi_table = "InstSection"
    synergi_database = "Model"

    def parse(self, row, unit_type, section_id_sections, from_node_sections, to_node_sections):
        name = self.map_name(row)
        buses = self.map_buses(row, section_id_sections)
        length = self.map_length(row, unit_type)
        phases = self.map_phases(row)   
        conductors = self.map_conductors(row)
        geometry = self.map_geometry(row, conductors)
        return GeometryBranch(name=name,
                                       buses=buses,
                                       length=length,
                                       phases=phases,
                                       geometry=geometry,
                                       conductors=conductors)

    def map_name(self, row):
        return row["SectionId"]

    def map_buses(self, row, section_id_sections):
        section_id = str(row["SectionId"])
        section = section_id_sections[section_id]
        from_bus_name = section["FromNodeId"]
        to_bus_name = section["ToNodeId"]
        to_bus = None
        from_bus = None
        try:
            from_bus = self.system.get_component(component_type=DistributionBus,name=from_bus_name)
        except Exception as e:    
            pass

        try:
            to_bus = self.system.get_component(component_type=DistributionBus,name=to_bus_name)
        except:
            pass

        if from_bus is None:
            logger.warning(f"Line {section_id} has no from bus")
        if from_bus is None:
            logger.warning(f"Line {section_id} has no to bus")
        return [from_bus,to_bus]

    def map_length(self, row, unit_type):
        unit = length_units[unit_type]["MUL"]
        length = row["SectionLength_MUL"]
        return PositiveDistance(length, unit).to("m")

    def map_phases(self, row):
        input_phases = row["SectionPhases"].replace(" ","")
        phases = []
        for i in range(1,3):
            phases = []
            if 'A' in input_phases:
                phases.append(Phase.A)
            if 'B' in input_phases:  
                phases.append(Phase.B)
            if 'C' in input_phases:
                phases.append(Phase.C)
            if 'N' in input_phases:
                phases.append(Phase.N)
        return phases 
 

    def map_geometry(self, row, conductors):
        input_geometry = row["ConfigurationId"]
        phases = row["SectionPhases"].replace(" ","")
        num_phases = len(phases.replace("N",""))

        if isinstance(conductors[0], BareConductorEquipment):
            is_OH = True
        else:
            is_OH = False

        default_three_phase_OH_geometry = "Default_OH_3PH"
        default_single_phase_OH_geometry = "Default_OH_1PH"
        default_three_phase_UG_geometry = "Default_UG_3PH"
        default_single_phase_UG_geometry = "Default_UG_1PH"
        found_geometry = False
        geometry = None

        if input_geometry == "Unknown":
            pass
        else:
            try:
                geometry = self.system.get_component(component_type=GeometryBranchEquipment,name=input_geometry)
                if len(geometry.horizontal_positions) != len(phases):
                    logger.warning(f"Geometry {input_geometry} does not have the correct number of horizontal positions. Using default geometry")
                    found_geometry = False
            except Exception as e:
                found_geometry = False

        

        if not found_geometry: 
            logger.warning(f"Geometry {input_geometry} not found. Using default geometry")
            if num_phases == 3:
                if is_OH:
                    geometry = self.system.get_component(component_type=GeometryBranchEquipment,name=default_three_phase_OH_geometry)
                else:
                    geometry = self.system.get_component(component_type=GeometryBranchEquipment,name=default_three_phase_UG_geometry)
            else:
                if is_OH:
                    geometry = self.system.get_component(component_type=GeometryBranchEquipment,name=default_single_phase_OH_geometry)
                else:
                    geometry = self.system.get_component(component_type=GeometryBranchEquipment,name=default_single_phase_UG_geometry)

        return geometry

    def map_conductors(self, row):
        conductors = []
        phases = row["SectionPhases"].replace(" ","")
        phase_count = 1
        for phase in phases:
            conductor = None
            if phase == "N":
                conductor = row["NeutralConductorId"]
            elif phase_count == 1:
                conductor = row["PhaseConductorId"]
            else:    
                # Sample model has missing conductors for PhaseConductor2Id, PhaseConductor3Id
                conductor = row[f"PhaseConductor{phase_count}Id"]
                conductor = row["PhaseConductorId"]
            phase_count += 1
            if conductor != "Unknown":
                bare_equipment = None
                concentric_equipment = None
                try:
                    bare_equipment = self.system.get_component(component_type=BareConductorEquipment,name=conductor)
                except Exception as e:
                    pass
                try:
                    concentric_equipment = self.system.get_component(component_type=ConcentricCableEquipment,name=conductor)
                except Exception as e:
                    pass
                if bare_equipment is not None:
                    conductors.append(bare_equipment)
                elif concentric_equipment is not None:    
                    conductors.append(concentric_equipment)
                else:    
                    logger.warning(f"Conductor {conductor} not found. Skipping")
                    import pdb;pdb.set_trace()

        return conductors   




