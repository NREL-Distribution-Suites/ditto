from pathlib import Path
from enum import IntEnum

from infrasys.quantities import ActivePower, Angle, Resistance, Voltage
from infrasys.location import Location
from infrasys.system import System
from gdm import DistributionSystem
from gdm import SequencePair
import opendssdirect as dss
from gdm import (
    DistributionTransformerEquipment,
    MatrixImpedanceBranchEquipment,
    PhaseVoltageSourceEquipment,
    DistributionVoltageSource,
    PhaseCapacitorEquipment,
    DistributionTransformer,
    VoltageSourceEquipment,
    MatrixImpedanceBranch,
    DistributionCapacitor,
    CapacitorEquipment,
    PhaseLoadEquipment,
    WindingEquipment,
    DistributionLoad,
    VoltageLimitSet,
    ThermalLimitSet,
    DistributionBus,
    GeometryBranch,
    ConnectionType,
    LoadEquipment,
    VoltageTypes,
    Phase,
)
from gdm.quantities import (
    PositiveResistancePULength,
    PositiveApparentPower,
    PositiveReactivePower,
    CapacitancePULength,
    PositiveResistance,
    ReactancePULength,
    PositiveReactance,
    PositiveDistance,
    PositiveCurrent,
    PositiveVoltage,
    ReactivePower,
    Reactance,
)
import numpy as np

from ditto.readers.reader import Reader

PHASE_MAPPER = {"1": Phase.A, "2": Phase.B, "3": Phase.C, "4": Phase.N}
UNIT_MAPPER = {0: "m", 1: "mi", 2: "kft", 3: "km", 4: "m", 5: "ft", 6: "in", 7: "cm"}
SEQUENCE_PAIRS = [SequencePair(1, 2), SequencePair(1, 3), SequencePair(2, 3)]


class LoadTypes(IntEnum):
    CONST_POWER = 1
    CONST_IMPEDANCE = 2
    CONST_CURRENT = 5
    ZIP = 8


class OpenDSS(Reader):
    """Class interface for OpenDSS case file reader"""

    def __init__(self, opendss_master_file: Path, crs: str | None = None) -> None:
        """Constructor for the OpenDSS reader

        Args:
            opendss_master_file (Path): Path to the OpenDSS master file
            crs (str | None, optional): Coordinate reference system name. Defaults to None.
        """

        self.system = DistributionSystem(auto_add_composed_components=True)
        self.opendss_master_file = opendss_master_file
        self.crs = crs
        self.read()

    def get_system(self) -> System:
        """Returns an instance of DistributionSystem

        Returns:
            System: Instance of DistributionSystem
        """

        return self.system

    def read(self):
        """Takes the master file path and returns instance of OpendssParser

        Raises:
            FileNotFoundError: Error raised if the file is not found
        """

        if not self.opendss_master_file.exists():
            msg = f"File not found: {self.opendss_master_file}"
            raise FileNotFoundError(msg)

        dss.Text.Command("Clear")
        dss.Basic.ClearAll()
        dss.Text.Command(f'Redirect "{self.opendss_master_file}"')
        buses = self.get_buses(crs=self.crs)

        self.system = System(name=dss.Circuit.Name(), auto_add_composed_components=False)

        self.system.components.add(*buses)
        caps = self.get_capacitors()
        self.system.components.add(*caps)
        loads = self.get_loads()
        self.system.components.add(*loads)
        voltage_sources = self.get_voltage_sources()
        self.system.components.add(*voltage_sources)
        branches = self.get_ac_lines()
        self.system.components.add(*branches)
        transformers = self.get_transformers()
        self.system.components.add(*transformers)

    def get_buses(self, crs: str = None) -> list[DistributionBus]:
        """Function to return list of all buses in opendss model.

        Args:
            dss_instance (dss): OpenDSS instance with models preloaded
            is_geo (bool): True if coordinate maps to geolocation
        Returns:
            List[Bus]: List of bus objects
        """
        buses = []

        for bus in dss.Circuit.AllBusNames():
            dss.Circuit.SetActiveBus(bus)
            nominal_voltage = dss.Bus.kVBase()

            loc = Location(x=dss.Bus.Y(), y=dss.Bus.X(), crs=crs)
            self.system.add_component(loc)

            limitsets = [
                VoltageLimitSet(
                    limit_type="min",
                    value=PositiveVoltage(nominal_voltage * 0.95, "kilovolt"),
                ),
                VoltageLimitSet(
                    limit_type="max",
                    value=PositiveVoltage(nominal_voltage * 1.05, "kilovolt"),
                ),
            ]
            self.system.add_components(*limitsets)
            buses.append(
                DistributionBus(
                    voltage_type=VoltageTypes.LINE_TO_GROUND.value,
                    name=bus,
                    nominal_voltage=PositiveVoltage(nominal_voltage, "kilovolt"),
                    phases=[PHASE_MAPPER[str(node)] for node in dss.Bus.Nodes()],
                    coordinate=loc,
                    voltagelimits=limitsets,
                )
            )
        return buses

    def get_capacitors(self) -> list[DistributionCapacitor]:
        """Function to return list of all buses in opendss model.

        Args:
            dss_instance (dss): OpenDSS instance with models preloaded
        Returns:
            List[Capacitor]: List of capacitor objects
        """
        capacitors = []
        flag = dss.Capacitors.First()
        while flag > 0:
            capacitor_name = dss.Capacitors.Name().lower()
            buses = dss.CktElement.BusNames()
            bus1 = buses[0].split(".")[0]
            num_phase = dss.CktElement.NumPhases()
            kvar_ = dss.Capacitors.kvar()
            ph_caps = []
            nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]

            for el in nodes:
                phase_capacitor = PhaseCapacitorEquipment(
                    name=f"{capacitor_name}_{el}",
                    rated_capacity=PositiveReactivePower(kvar_ / num_phase, "kilovar"),
                    num_banks=dss.Capacitors.NumSteps(),
                    num_banks_on=sum(dss.Capacitors.States()),
                    resistance=PositiveResistance(0, "ohm"),
                    reactance=PositiveReactance(0, "ohm"),
                )
                ph_caps.append(phase_capacitor)
            self.system.add_components(*ph_caps)

            capacitor_equipment = CapacitorEquipment(
                name=capacitor_name + "_equipment",
                phase_capacitors=ph_caps,
                connection_type=ConnectionType.DELTA
                if dss.Capacitors.IsDelta()
                else ConnectionType.STAR,
            )
            self.system.add_component(capacitor_equipment)

            capacitors.append(
                DistributionCapacitor(
                    name=capacitor_name,
                    bus=self.system.components.get(DistributionBus, bus1),
                    phases=[PHASE_MAPPER[el] for el in nodes],
                    controllers=[],
                    equipment=capacitor_equipment,
                )
            )
            flag = dss.Capacitors.Next()
        return capacitors

    def get_loads(self) -> list[DistributionLoad]:
        """Function to return list of all buses in opendss model.

        Args:
            dss_instance (dss): OpenDSS instance with models preloaded
        Returns:
            List[Capacitor]: List of capacitor objects
        """
        loads = []
        flag = dss.Loads.First()
        while flag > 0:
            load_name = dss.Loads.Name().lower()
            buses = dss.CktElement.BusNames()
            bus1 = buses[0].split(".")[0]
            num_phase = dss.CktElement.NumPhases()
            kvar_ = dss.Loads.kvar()
            kw_ = dss.Loads.kW()
            zip_params = dss.Loads.ZipV()
            model = dss.Loads.Model()
            ph_loads = []
            nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]

            for el in nodes:
                kw_per_phase = kw_ / num_phase
                kvar_per_phase = kvar_ / num_phase

                if model == LoadTypes.CONST_POWER:
                    load = PhaseLoadEquipment(
                        name=f"{load_name}_{el}",
                        p_real=ActivePower(kw_per_phase, "kilowatt"),
                        p_imag=ReactivePower(kvar_per_phase, "kilovar"),
                    )
                elif model == LoadTypes.CONST_CURRENT:
                    load = PhaseLoadEquipment(
                        name=f"{load_name}_{el}",
                        i_real=ActivePower(kw_per_phase, "kilowatt"),
                        i_imag=ReactivePower(kvar_per_phase, "kilovar"),
                    )
                elif model == LoadTypes.CONST_IMPEDANCE:
                    load = PhaseLoadEquipment(
                        name=f"{load_name}_{el}",
                        z_real=ActivePower(kw_per_phase, "kilowatt"),
                        z_imag=ReactivePower(kvar_per_phase, "kilovar"),
                    )
                elif model == LoadTypes.ZIP:
                    load = PhaseLoadEquipment(
                        name=f"{load_name}_{el}",
                        z_real=ActivePower(kw_per_phase * zip_params[0], "kilowatt"),
                        z_imag=ReactivePower(kvar_per_phase * zip_params[3], "kilovar"),
                        i_real=ActivePower(kw_per_phase * zip_params[1], "kilowatt"),
                        i_imag=ReactivePower(kvar_per_phase * zip_params[4], "kilovar"),
                        p_real=ActivePower(kw_per_phase * zip_params[2], "kilowatt"),
                        p_imag=ReactivePower(kvar_per_phase * zip_params[5], "kilovar"),
                    )
                else:
                    msg = f"Invalid load model types passed. valid options are {LoadTypes}"
                    raise ValueError(msg)
                self.system.add_component(load)
                ph_loads.append(load)

            load_equipment = LoadEquipment(
                name=load_name,
                phase_loads=ph_loads,
                connection_type=ConnectionType.DELTA
                if dss.Loads.IsDelta()
                else ConnectionType.STAR,
            )
            self.system.add_components(load_equipment)

            loads.append(
                DistributionLoad(
                    name=load_name,
                    bus=self.system.components.get(DistributionBus, bus1),
                    phases=[PHASE_MAPPER[el] for el in nodes],
                    equipment=load_equipment,
                )
            )

            flag = dss.Loads.Next()
        return loads

    def get_voltage_sources(self) -> list[DistributionVoltageSource]:
        voltage_sources = []
        flag = dss.Vsources.First()
        while flag:
            soure_name = dss.Vsources.Name().lower()
            buses = dss.CktElement.BusNames()
            bus1 = buses[0].split(".")[0]
            num_phase = dss.CktElement.NumPhases()
            nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]
            angle = dss.Vsources.AngleDeg()
            angles = [Angle(angle + i * (360.0 / num_phase), "degree") for i in range(num_phase)]
            phase_slacks = []
            phase_src_properties = {}
            for ppty in ["r0", "r1", "x0", "x1"]:
                command_str = f"? vsource.{soure_name}.{ppty}"
                result = dss.run_command(command_str)
                phase_src_properties[ppty] = float(result)

            for node, angle in zip(nodes, angles):
                voltage = Voltage(dss.Vsources.BasekV() * dss.Vsources.PU(), "kilovolt")
                phase_slack = PhaseVoltageSourceEquipment(
                    name=f"{soure_name}_{node}",
                    r0=Resistance(phase_src_properties["r0"], "ohm"),
                    r1=Resistance(phase_src_properties["r1"], "ohm"),
                    x0=Reactance(phase_src_properties["x0"], "ohm"),
                    x1=Reactance(phase_src_properties["x1"], "ohm"),
                    angle=angle,
                    voltage=voltage / 1.732 if num_phase == 3 else voltage,
                )
                phase_slacks.append(phase_slack)
            self.system.add_components(*phase_slacks)

            slack_equipment = VoltageSourceEquipment(
                name=soure_name,
                sources=phase_slacks,
            )
            self.system.add_components(slack_equipment)

            voltage_source = DistributionVoltageSource(
                name=soure_name,
                bus=self.system.components.get(DistributionBus, bus1),
                phases=[PHASE_MAPPER[el] for el in nodes],
                equipment=slack_equipment,
            )
            voltage_sources.append(voltage_source)
            flag = dss.Vsources.Next()
        return voltage_sources

    def get_ac_lines(
        self,
    ) -> list[MatrixImpedanceBranch | GeometryBranch]:
        """Function to return list of all line segments in opendss model.

        Args:
            dss_instance (dss): OpenDSS instance with models preloaded
        Returns:
            List: List of line segment metadata object
        """

        edges = []
        flag = dss.Lines.First()
        while flag > 0:
            if not dss.Lines.IsSwitch():
                section_name = dss.CktElement.Name().lower()
                buses = dss.CktElement.BusNames()
                bus1, bus2 = buses[0].split(".")[0], buses[1].split(".")[0]
                num_phase = dss.CktElement.NumPhases()
                nodes = ["1", "2", "3"] if num_phase == 3 else buses[0].split(".")[1:]
                if dss.Lines.Geometry():
                    edges.append(
                        self._build_branch_using_geometry(
                            section_name, bus1, bus2, nodes, num_phase
                        )
                    )
                else:
                    edges.append(
                        self._build_branch_using_martices(
                            section_name, bus1, bus2, nodes, num_phase
                        )
                    )
                    ...
            flag = dss.Lines.Next()
        return edges

    def _build_branch_using_geometry(
        self, section_name: str, bus1: str, bus2: str, nodes: list[str], num_phase: int
    ) -> GeometryBranch:
        raise NotImplementedError("Geometry line type not yet implemented")
        branch = []
        return branch

    def _build_branch_using_martices(
        self, section_name: str, bus1: str, bus2: str, nodes: list[str], num_phase: int
    ) -> MatrixImpedanceBranch:
        thermal_limits = ThermalLimitSet(
            limit_type="max",
            value=PositiveCurrent(dss.Lines.EmergAmps(), "ampere"),
        )
        self.system.add_component(thermal_limits)
        cmd = f"? {section_name}.units"
        length_units = dss.run_command(cmd)
        matrix_branch_equipment = MatrixImpedanceBranchEquipment(
            name=section_name + "_equipment",
            r_matrix=PositiveResistancePULength(
                np.reshape(np.array(dss.Lines.RMatrix()), (num_phase, num_phase)),
                f"ohm/{length_units}",
            ),
            x_matrix=ReactancePULength(
                np.reshape(np.array(dss.Lines.XMatrix()), (num_phase, num_phase)),
                f"ohm/{length_units}",
            ),
            c_matrix=CapacitancePULength(
                np.reshape(np.array(dss.Lines.CMatrix()), (num_phase, num_phase)),
                f"nanofarad/{length_units}",
            ),
            ampacity=PositiveCurrent(dss.Lines.NormAmps(), "ampere"),
            loading_limit=thermal_limits,
        )
        self.system.add_component(matrix_branch_equipment)

        branch = MatrixImpedanceBranch(
            name=section_name,
            buses=[
                self.system.components.get(DistributionBus, bus1),
                self.system.components.get(DistributionBus, bus2),
            ],
            length=PositiveDistance(dss.Lines.Length(), UNIT_MAPPER[dss.Lines.Units()]),
            phases=[PHASE_MAPPER[node] for node in nodes],
            equipment=matrix_branch_equipment,
            is_closed=dss.CktElement.Enabled(),
        )
        return branch

    def get_transformers(self) -> list[DistributionTransformer]:
        """return a list of DistributionTransformer objects

        Returns:
            list [DistributionTransformer]: list of distribution transformers
        """
        transformers = []
        flag = dss.Transformers.First()
        while flag > 0:
            all_reactances = [
                dss.Transformers.Xhl(),
                dss.Transformers.Xht(),
                dss.Transformers.Xlt(),
            ]
            number_windings = dss.Transformers.NumWindings()
            winding_phases = []
            xfmr_buses = []
            windings = []
            for wdg_index, bus_name in zip(range(number_windings), dss.CktElement.BusNames()):
                dss.Transformers.Wdg(wdg_index + 1)
                bus = bus_name.split(".")[0]
                num_phase = dss.CktElement.NumPhases()
                nodes = ["1", "2", "3"] if num_phase == 3 else bus.split(".")[1:]
                winding_phases.append([PHASE_MAPPER[node] for node in nodes])
                xfmr_buses.append(self.system.components.get(DistributionBus, bus))
                nominal_voltage = (
                    dss.Transformers.kV() / 1.732 if num_phase == 3 else dss.Transformers.kV()
                )
                winding = WindingEquipment(
                    rated_power=PositiveApparentPower(dss.Transformers.kVA(), "kilova"),
                    num_phases=num_phase,
                    connection_type=ConnectionType.DELTA
                    if dss.Transformers.IsDelta()
                    else ConnectionType.STAR,
                    nominal_voltage=PositiveVoltage(nominal_voltage, "kilovolt"),
                    resistance=dss.Transformers.R(),
                    is_grounded=False,  # TODO @aadil
                )
                windings.append(winding)
            self.system.add_components(*windings)

            coupling_sequences = SEQUENCE_PAIRS[:1] if number_windings == 2 else SEQUENCE_PAIRS
            reactances = all_reactances[:1] if number_windings == 2 else all_reactances
            no_load_loss_pct, full_load_loss_pct = self._xfmr_pct_loss_components()

            dist_transformer = DistributionTransformerEquipment(
                name=dss.Transformers.Name().lower(),
                pct_no_load_loss=no_load_loss_pct,
                pct_full_load_loss=full_load_loss_pct,
                windings=windings,
                coupling_sequences=coupling_sequences,
                winding_reactances=reactances,
                is_center_tapped=self._is_center_tapped(),
            )
            self.system.add_component(dist_transformer)

            transformer = DistributionTransformer(
                name=dss.Transformers.Name().lower(),
                buses=xfmr_buses,
                winding_phases=winding_phases,
                equipment=dist_transformer,
            )
            transformers.append(transformer)
            flag = dss.Transformers.Next()

        return transformers

    def _xfmr_pct_loss_components(self):
        loss_vector = dss.Transformers.LossesByType()
        full_load_loss_kva = (loss_vector[2] + 1j * loss_vector[3]) / 1000
        no_load_loss_kva = (loss_vector[4] + 1j * loss_vector[5]) / 1000
        full_load_loss_pct = abs(full_load_loss_kva) / dss.Transformers.kVA() * 100
        no_load_loss_pct = abs(no_load_loss_kva) / dss.Transformers.kVA() * 100
        return no_load_loss_pct, full_load_loss_pct

    def _is_center_tapped(self):
        # TODO: implment the correct logic here
        return False
