from pathlib import Path

from gdm.distribution.equipment import MatrixImpedanceBranchEquipment
from gdm.distribution.controllers import RegulatorController
from gdm.distribution import DistributionSystem
from gdm.distribution.components import (
    DistributionComponentBase,
    DistributionVoltageSource,
    DistributionTransformer,
    MatrixImpedanceBranch,
    DistributionCapacitor,
    DistributionRegulator,
    MatrixImpedanceSwitch,
    DistributionLoad,
    DistributionBus,
)
from loguru import logger
from rdflib import Graph
import pandas as pd


from ditto.readers.cim_iec_61968_13.queries import (
    query_distribution_regulators,
    query_regulator_controllers,
    query_transformer_windings,
    query_load_break_switches,
    query_power_transformers,
    query_distribution_buses,
    query_line_segments,
    query_line_codes,
    query_capacitors,
    query_source,
    query_loads,
)
import ditto.readers.cim_iec_61968_13 as cim_mapper
from ditto.readers.reader import AbstractReader


class Reader(AbstractReader):
    # NOTE:  Do not change sequnce of the component types below.
    component_types: DistributionComponentBase = [
        DistributionBus,
        DistributionLoad,
        DistributionCapacitor,
        DistributionVoltageSource,
        RegulatorController,
        MatrixImpedanceBranchEquipment,
        MatrixImpedanceBranch,
        DistributionTransformer,
        DistributionRegulator,
        MatrixImpedanceSwitch,
    ]

    def __init__(self, cim_file: str | Path):
        cim_file = Path(cim_file)
        assert cim_file.exists(), f"{cim_file} does not exist"
        self.system = DistributionSystem(auto_add_composed_components=True)
        self.graph = Graph()
        self.graph.parse(cim_file, format="xml")

    def read(self):
        datasets: dict[DistributionComponentBase, pd.DataFrame] = {}
        logger.debug("Querying for distribution buses...")
        datasets[DistributionBus] = query_distribution_buses(self.graph)

        logger.debug("Querying for AC line segments...")
        datasets[MatrixImpedanceBranch] = query_line_segments(self.graph)

        logger.debug("Querying for line codes...")
        datasets[MatrixImpedanceBranchEquipment] = query_line_codes(self.graph)

        logger.debug("Querying for loads...")
        datasets[DistributionLoad] = query_loads(self.graph)

        logger.debug("Querying for capacitors...")
        datasets[DistributionCapacitor] = query_capacitors(self.graph)

        logger.debug("Querying for transformers...")
        xfmr_data = query_power_transformers(self.graph)
        logger.debug("Querying for transformer windings...")
        winding_data = query_transformer_windings(self.graph)
        datasets[DistributionTransformer] = self._build_xfmr_dataset(xfmr_data, winding_data)

        logger.debug("Querying for regulators...")
        regulator_data = query_distribution_regulators(self.graph)
        datasets[DistributionRegulator] = self._build_xfmr_dataset(regulator_data)

        logger.debug("Querying for sources...")
        datasets[DistributionVoltageSource] = query_source(self.graph)

        logger.debug("Querying for regulator controllers...")
        datasets[RegulatorController] = query_regulator_controllers(self.graph)

        logger.debug("Querying for load break switches...")
        datasets[MatrixImpedanceSwitch] = query_load_break_switches(self.graph)

        datasets[DistributionBus] = self._set_bus_phases(datasets)

        for component_type in self.component_types:
            mapper_name = component_type.__name__ + "Mapper"
            components = []
            if component_type in datasets:
                try:
                    mapper = getattr(cim_mapper, mapper_name)(self.system)
                    logger.debug(f"Buliding components for {component_type.__name__}")
                except AttributeError as _:
                    logger.warning(f"Mapper for {mapper_name} not found. Skipping")
                if datasets[component_type].empty:
                    logger.warning(
                        f"Dataframe for {component_type.__name__} is empty. Check query."
                    )
                for _, row in datasets[component_type].iterrows():
                    model_entry = mapper.parse(row)
                    components.append(model_entry)
            else:
                logger.warning(f"Dataframe for {component_type.__name__} not found. Skipping")
            self.system.add_components(*components)
        logger.info("System summary: ", self.system.info())

    def _build_xfmr_dataset(
        self, xfmr_data: pd.DataFrame, winding_df: pd.DataFrame = pd.DataFrame()
    ) -> pd.DataFrame:
        xfmrs = xfmr_data["xfmr"].unique()
        xfms = []
        for xfmr in xfmrs:
            xfmr_df = xfmr_data[xfmr_data["xfmr"] == xfmr]
            xfmr_df.pop("xfmr")
            windings = xfmr_df.pop("winding").unique()
            buses = xfmr_df.pop("bus").unique()
            xfmr_df = xfmr_df.drop_duplicates()
            wdgs = []
            for winding, (_, winding_data) in zip(windings, xfmr_df.iterrows()):
                winding_data.index = [f"wdg_{winding}_" + c for c in winding_data.index]
                wdgs.append(winding_data)
            wdgs = pd.concat(wdgs)
            wdgs["bus_1"] = buses[0]
            wdgs["bus_2"] = buses[1]
            wdgs["xfmr"] = xfmr
            for _, wdg_coupling_data in winding_df.iterrows():
                xfmr_ends = {wdg_coupling_data["xfmr_end_1"], wdg_coupling_data["xfmr_end_2"]}
                intersection = xfmr_ends.intersection(wdgs.to_list())
                if intersection:
                    wdgs["r0"] = wdg_coupling_data["r0"]
                    wdgs["r1"] = wdg_coupling_data["r1"]
                    wdgs["x0"] = wdg_coupling_data["x0"]
                    wdgs["x1"] = wdg_coupling_data["x1"]
                    wdgs["winding"] = wdg_coupling_data["winding"]
            xfms.append(wdgs)

        xfmr_dataset = pd.DataFrame(xfms)
        return xfmr_dataset

    def _set_bus_phases(
        self, df_dict: dict[DistributionComponentBase, pd.DataFrame]
    ) -> pd.DataFrame:
        all_phases = []
        bus_df = df_dict.pop(DistributionBus)
        for _, bus_data in bus_df.iterrows():
            bus_name = bus_data["bus"]
            phases = []

            for df_type in df_dict:
                df = df_dict[df_type]
                bus_subset = {"bus", "bus_1", "bus_2"}
                phase_subset = {"phase", "phases_1", "phases_2"}

                bus_cols = bus_subset.intersection(df.columns)
                phase_cols = phase_subset.intersection(df.columns)

                if isinstance(df, pd.DataFrame) and len(bus_cols) and len(phase_cols):
                    for bus_col in bus_subset:
                        if bus_col in df.columns:
                            filt_data = df[df[bus_col] == bus_name]
                            if not filt_data.empty:
                                for phase_col in phase_subset:
                                    phase_list = filt_data.get(
                                        phase_col, default=pd.Series()
                                    ).to_list()
                                    phase_list = [
                                        phase.replace(",", "").replace("N", "")
                                        for phase in phase_list
                                        if phase is not None
                                    ]
                                    phase_list = [
                                        list(phase) for phase in phase_list if len(phase) >= 1
                                    ]
                                    for ph_lst in phase_list:
                                        phases.extend(ph_lst)

            phases = set(phases)
            phases = phases.difference({None})
            phases = [phase for phase in list(phases) if len(phase) == 1]
            phases = sorted(phases)
            if not phases:
                phases = ["A", "B", "C"]
            all_phases.append(",".join(phases))

        bus_df["phase"] = all_phases
        return bus_df

    def get_system(self) -> DistributionSystem:
        return self.system
