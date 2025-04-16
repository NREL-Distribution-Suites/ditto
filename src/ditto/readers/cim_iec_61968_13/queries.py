from functools import reduce

from rdflib.query import Result
from loguru import logger
from rdflib import Graph
import pandas as pd

import numpy as np


def add_prefixes(query: str, graph: Graph) -> str:
    prefixes = ""
    for prefix_name, url in graph.namespaces():
        prefix = f"PREFIX {prefix_name}: <{str(url)}>\n"
        prefixes += prefix
    return prefixes + query


def query_to_df(results: Result, columns: list[str]):
    data = []
    for row in results:
        row_data = {}
        for column, value in zip(columns, row):
            try:
                new_value = value.value
            except Exception as _:
                new_value = value

            if isinstance(new_value, str) and "http" in new_value:
                if "," in new_value:
                    new_value = new_value.split(",")
                    if "." in new_value[0]:
                        new_value = [v.split(".")[-1] for v in new_value]
                elif "." in new_value:
                    new_value = new_value.split(".")[-1]
                else:
                    new_value = new_value
                new_value = ",".join(new_value) if isinstance(new_value, list) else new_value

            row_data[column] = new_value
        data.append(row_data)
    data = pd.DataFrame(data)
    data = data.drop_duplicates()

    return data


def query_line_codes(graph: Graph) -> pd.DataFrame:
    columns = ["line_code", "phase_count", "r", "x", "b", "row", "column", "ampacity"]

    sparql_query_ac_line_segment = """
    SELECT  ?line_code ?phase_count ?r ?x ?b ?row ?column ?ampacity
    WHERE {
        ?term rdf:type cim:Terminal .
        ?term cim:Terminal.ConductingEquipment ?line .
        ?term cim:ACDCTerminal.OperationalLimitSet ?oplimset .
        ?line cim:ACLineSegment.PerLengthImpedance ?pu_phs_imp .
        # ?pu_phs_imp rdf:type cim:PerLengthPhaseImpedance .
        ?pu_phs_imp cim:IdentifiedObject.name ?line_code .
        ?pu_phs_imp cim:PerLengthPhaseImpedance.conductorCount ?phase_count .
        ?phase_imp_data rdf:type cim:PhaseImpedanceData .
        ?phase_imp_data cim:PhaseImpedanceData.PhaseImpedance ?pu_phs_imp .
        ?phase_imp_data cim:PhaseImpedanceData.r ?r .
        ?phase_imp_data cim:PhaseImpedanceData.x ?x .
        ?phase_imp_data cim:PhaseImpedanceData.b ?b .
        ?phase_imp_data cim:PhaseImpedanceData.row ?row .
        ?phase_imp_data cim:PhaseImpedanceData.column ?column .
        ?curr_lim_set rdf:type cim:CurrentLimit .
        ?curr_lim_set cim:OperationalLimit.OperationalLimitSet ?oplimset .
        ?curr_lim_set cim:CurrentLimit.value ?ampacity .
    }
    """
    data = query_to_df(graph.query(add_prefixes(sparql_query_ac_line_segment, graph)), columns)

    data_set = {}
    for line_code in data["line_code"].unique():
        filt_data = data[data["line_code"] == line_code]
        line_code_filt = filt_data["line_code"].unique()[0]
        phase_count_filt = filt_data["phase_count"].unique()[0]
        ampacities = filt_data["ampacity"].unique()
        filt_data = filt_data[filt_data["ampacity"] == ampacities[0]]
        r = pd.pivot_table(
            filt_data, values="r", index=["row"], columns=["column"], aggfunc="sum"
        ).values
        x = pd.pivot_table(
            filt_data, values="x", index=["row"], columns=["column"], aggfunc="sum"
        ).values
        b = pd.pivot_table(
            filt_data, values="b", index=["row"], columns=["column"], aggfunc="sum"
        ).values
        row_indices, col_indices = np.tril_indices(r.shape[0])
        r_lower = r[row_indices, col_indices].tolist()
        x_lower = x[row_indices, col_indices].tolist()
        b_lower = b[row_indices, col_indices].tolist()

        ampacities = [float(ampacity) for ampacity in ampacities]
        data_set[line_code_filt] = {
            "line_code": line_code_filt,
            "phase_count": phase_count_filt,
            "r": r_lower,
            "x": x_lower,
            "b": b_lower,
            "ampacity_normal": min(ampacities),
            "ampacity_emergency": max(ampacities),
        }
    return pd.DataFrame(data_set).T


def query_load_break_switches(graph: Graph) -> pd.DataFrame:
    columns = [
        "switch_name",
        "capacity",
        "ratedCurrent",
        "normally_open",
        "is_open",
        "voltage",
        "bus",
    ]

    query = """
    SELECT  ?switch_name ?capacity ?ratedCurrent ?normally_open ?is_open ?voltage ?node_name
    WHERE {
        ?switch rdf:type cim:LoadBreakSwitch  .
        ?switch cim:IdentifiedObject.name ?switch_name .
        ?switch cim:ProtectedSwitch.breakingCapacity ?capacity .
        ?switch cim:Switch.ratedCurrent ?ratedCurrent .
        ?switch cim:Switch.normalOpen ?normally_open .
        ?switch cim:Switch.open ?is_open .
        ?switch cim:ConductingEquipment.BaseVoltage ?basevoltage .
        ?basevoltage cim:BaseVoltage.nominalVoltage ?voltage .
        ?term cim:Terminal.ConductingEquipment ?switch .
        ?term cim:Terminal.ConnectivityNode ?node .
        ?node cim:IdentifiedObject.name ?node_name .

    }
    """
    data = query_to_df(graph.query(add_prefixes(query, graph)), columns)
    data_set = []
    for line_name in data["switch_name"].unique():
        filt_data = data[data["switch_name"] == line_name]
        buses = filt_data["bus"].unique()
        reduced_data = filt_data.drop_duplicates()
        reduced_data["bus_1"] = buses[0]
        reduced_data["bus_2"] = buses[1]
        data_set.append(reduced_data)
    data = pd.concat(data_set)
    data.drop("bus", axis=1, inplace=True)
    data = data.drop_duplicates()
    return data


def query_line_segments(graph: Graph) -> pd.DataFrame:
    columns = ["line", "voltage", "length", "bus", "phase_count", "line_code", "phase"]

    query = """
    SELECT  ?line_name ?voltage ?length ?node_name ?phase_count ?line_code ?phase
    WHERE {
        ?line rdf:type cim:ACLineSegment .
        ?line cim:IdentifiedObject.name ?line_name .
        ?line cim:ConductingEquipment.BaseVoltage ?basevoltage .
        ?basevoltage cim:BaseVoltage.nominalVoltage ?voltage .
        ?line cim:Conductor.length ?length .
        ?line_phase cim:ACLineSegmentPhase.ACLineSegment ?line .
        ?line_phase cim:ACLineSegmentPhase.phase ?phase .
        ?term rdf:type cim:Terminal .
        ?term cim:Terminal.ConductingEquipment ?line .
        ?term cim:Terminal.ConnectivityNode ?node .
        ?node cim:IdentifiedObject.name ?node_name .
        ?line cim:ACLineSegment.PerLengthImpedance ?puimp .
        ?puimp cim:PerLengthPhaseImpedance.conductorCount ?phase_count .
        ?puimp cim:IdentifiedObject.name ?line_code .

    }
    """
    data = query_to_df(graph.query(add_prefixes(query, graph)), columns)

    data_set = []
    for line_name in data["line"].unique():
        filt_data = data[data["line"] == line_name]
        buses = filt_data["bus"].unique()
        bus_phases = {}
        for bus in buses:
            filt_data_bus = filt_data[filt_data["bus"] == bus]
            phases = filt_data_bus["phase"].to_list()
            bus_phases[bus] = phases
        reduced_data = filt_data[["line", "voltage", "length", "phase_count", "line_code"]]
        reduced_data = reduced_data.drop_duplicates()
        reduced_data["bus_1"] = buses[0]
        reduced_data["phases_1"] = ",".join(bus_phases[buses[0]])
        reduced_data["bus_2"] = buses[1]
        reduced_data["phases_2"] = ",".join(bus_phases[buses[1]])
        data_set.append(reduced_data)

    data_set = pd.concat(data_set)
    return data_set


def query_distribution_buses(graph: Graph) -> pd.DataFrame:
    locations_columns = ["x", "y", "location_id"]

    query_locations = """
    SELECT  ?x ?y ?location_id
    WHERE {
        ?point rdf:type cim:PositionPoint .
        ?point cim:PositionPoint.xPosition ?x.
        ?point cim:PositionPoint.yPosition ?y.
        ?point cim:PositionPoint.Location ?location .
        ?location cim:IdentifiedObject.mRID ?location_id .
    }
    """
    locations = query_to_df(graph.query(add_prefixes(query_locations, graph)), locations_columns)
    location_dict = {}
    for location in locations["location_id"].unique():
        loc = locations[locations["location_id"] == location]
        coordinates = [(x, y) for x, y in zip(loc["x"], loc["y"])]
        location_dict[location] = coordinates

    columns = [
        "term_name",
        "node",
        "equipment",
        "xfmr_voltage",
        "line_voltage",
        "reg_loc_id",
        "xfmr_loc_id",
        "line_loc_id",
    ]

    query = """
    SELECT ?term_name ?node_name ?equip_name ?xfmr_voltage ?line_voltage ?reg_loc_id ?xfmr_loc_id ?line_loc_id
    WHERE {
        ?node rdf:type cim:ConnectivityNode .
        ?term cim:Terminal.ConnectivityNode ?node .
        ?term cim:IdentifiedObject.name ?term_name .
        ?term cim:Terminal.ConnectivityNode ?node .
        ?node cim:IdentifiedObject.name ?node_name .
        ?term cim:Terminal.ConductingEquipment ?equip .
        ?equip cim:IdentifiedObject.name ?equip_name .

        OPTIONAL {
            ?xfmr cim:TransformerEnd.Terminal ?term.
            ?xfmr cim:IdentifiedObject.name ?TransformerEnd.
            ?xfmr cim:TransformerEnd.BaseVoltage ?xfmr_base_voltage .
            ?xfmr_base_voltage cim:BaseVoltage.nominalVoltage ?xfmr_voltage .
            ?xfmr_tank cim:TransformerTank.PowerTransformer ?equip .
            ?xfmr_tank cim:PowerSystemResource.Location ?xfmr_location .
            ?xfmr_location cim:IdentifiedObject.mRID ?xfmr_loc_id.
        } .

        OPTIONAL {
            ?reg_control cim:RegulatingControl.Terminal ?term .
            ?reg_control cim:PowerSystemResource.Location ?reg_location.
            ?reg_location cim:IdentifiedObject.mRID ?reg_loc_id.
        } .

        OPTIONAL {
            ?equip cim:PowerSystemResource.Location ?line_location .
            ?line_location cim:IdentifiedObject.mRID ?line_loc_id .
            ?equip cim:ConductingEquipment.BaseVoltage ?line_base_voltage .
            ?line_base_voltage cim:BaseVoltage.nominalVoltage ?line_voltage .
        }.

    }
    # GROUP BY ?equip_name ?TransformerEnd
    """
    data = query_to_df(graph.query(add_prefixes(query, graph)), columns)
    node_voltage_df = _get_bus_base_voltages(data)
    node_coordinates = _get_bus_coordinates(data, location_dict)
    final_data = pd.concat([node_coordinates, node_voltage_df], axis=1)
    final_data["bus"] = final_data.index
    return final_data


def _get_bus_coordinates(loc_df: pd.DataFrame, location_dict: dict) -> pd.DataFrame:
    filt_data = loc_df[["node", "reg_loc_id", "xfmr_loc_id", "line_loc_id"]]
    df_grouped = filt_data.groupby("node", as_index=False).agg(
        {
            "reg_loc_id": lambda x: list(filter(None, x)),
            "xfmr_loc_id": lambda x: list(filter(None, x)),
            "line_loc_id": lambda x: list(filter(None, x)),
        }
    )
    df_grouped["merged_ids"] = df_grouped.apply(
        lambda row: row["reg_loc_id"] + row["xfmr_loc_id"] + row["line_loc_id"], axis=1
    )
    df_grouped = df_grouped[["node", "merged_ids"]]
    coordinate_map = {}
    coordinates_to_be_corrected = {}
    for _, row in df_grouped.iterrows():
        node = row["node"]
        ids = row["merged_ids"]
        coordinates = []

        for cood_id in ids:
            coordinates.append(set(location_dict[cood_id]))
        result = reduce(lambda x, y: x & y, coordinates)
        if len(result) == 1:
            coordinate_map[node] = list(result)[0]
        else:
            coordinates_to_be_corrected[node] = result

    coordinate_map_fix = {}
    for node_unknown, coordinates in coordinates_to_be_corrected.items():
        for _, coordinate in coordinate_map.items():
            if coordinate in coordinates:
                coordinates.remove(coordinate)
                if len(coordinates) == 1:
                    coordinate_map_fix[node_unknown] = list(coordinates)[0]
                else:
                    logger.warning(
                        f"Node {node_unknown} has more than 1 location. Please correct this manually"
                    )

    coordinate_map = {**coordinate_map, **coordinate_map_fix}
    final_coordinate_map = {}
    for node, coordinate in coordinate_map.items():
        final_coordinate_map[node] = {"x": coordinate[0], "y": coordinate[1]}

    return pd.DataFrame(final_coordinate_map).T


def _get_bus_base_voltages(data: pd.DataFrame) -> pd.DataFrame:
    filt_data = data[["node", "xfmr_voltage", "line_voltage"]]
    filt_data_arr = filt_data.values
    filt_data_arr = np.where(filt_data_arr is None, 0.0, filt_data_arr)
    filt_data = pd.DataFrame(filt_data_arr, columns=filt_data.columns)
    dtype_mapping = {"node": str, "xfmr_voltage": float, "line_voltage": float}
    filt_data = filt_data.astype(dtype_mapping)
    filt_data["rated_voltage"] = filt_data[["xfmr_voltage", "line_voltage"]].max(axis=1)
    filt_data = filt_data[["node", "rated_voltage"]]
    filt_data.drop_duplicates(inplace=True)
    filt_data_final = filt_data.groupby("node", as_index=False)["rated_voltage"].max()
    filt_data_final.index = filt_data_final["node"]
    filt_data_final.drop("node", axis=1, inplace=True)
    return filt_data_final


def query_distribution_regulators(graph: Graph) -> pd.DataFrame:
    columns = [
        "xfmr",
        "apparent_power",
        "rated_voltage",
        "per_resistance",
        "conn",
        "angle",
        "winding",
        "bus",
        "xfmr_end",
        "phase",
        "max_tap",
        "min_tap",
        "neutral_tap",
        "normal_tap",
        "dv",
        "current_tap",
        "z_1_leakage",
        "z_0_leakage",
        "z_1_loadloss",
        "z_0_loadloss",
    ]

    query = """
    SELECT ?xfmr_name ?apparent_power ?rated_voltage ?per_resistance ?conn ?angle ?winding ?node_name
        ?xfmr_end_name ?phases ?max_tap ?min_tap ?neutral_tap ?normal_tap ?dv ?current_tap
        ?z_1_leakage ?z_0_leakage ?z_1_loadloss ?z_0_loadloss
    WHERE {
        ?xfmr rdf:type cim:TransformerTank .
        ?xfmr cim:TransformerTank.TransformerTankInfo ?xfmr_info .
        ?xfmr cim:IdentifiedObject.name ?xfmr_name .

        ?xfmr cim:TransformerTank.PowerTransformer ?pwr_xfmr .
        ?xfmr_end rdf:type cim:TransformerEndInfo .

        ?xfmr_end cim:TransformerEndInfo.TransformerTankInfo ?xfmr_info .
        ?xfmr_end cim:TransformerEndInfo.ratedS ?apparent_power .
        ?xfmr_end cim:TransformerEndInfo.ratedU ?rated_voltage .
        ?xfmr_end cim:TransformerEndInfo.r ?per_resistance .
        ?xfmr_end cim:TransformerEndInfo.connectionKind ?conn .
        ?xfmr_end cim:TransformerEndInfo.phaseAngleClock ?angle .
        ?xfmr_end cim:TransformerEndInfo.endNumber ?winding .
        ?xfmr_end cim:IdentifiedObject.name ?xfmr_end_name .
        ?term rdf:type cim:Terminal .
        ?term cim:Terminal.ConductingEquipment ?pwr_xfmr .
        ?term cim:Terminal.ConnectivityNode ?node .
        ?node cim:IdentifiedObject.name ?node_name .


        ?xfmr_tank_end rdf:type cim:TransformerTankEnd  .
        ?xfmr_tank_end cim:TransformerTankEnd.TransformerTank ?xfmr .
        OPTIONAL {
            ?xfmr_tank_end cim:TransformerTankEnd.orderedPhases ?phases .
        } .

        OPTIONAL {
            ?tap_chgr rdf:type  cim:RatioTapChanger .
            ?tap_chgr cim:RatioTapChanger.TransformerEnd ?xfmr_tank_end .
            ?tap_chgr cim:TapChanger.highStep ?max_tap .
            ?tap_chgr cim:TapChanger.lowStep ?min_tap .
            ?tap_chgr cim:TapChanger.neutralStep ?neutral_tap .
            ?tap_chgr cim:TapChanger.normalStep ?normal_tap .
            ?tap_chgr cim:RatioTapChanger.stepVoltageIncrement ?dv .
            ?tap_chgr cim:TapChanger.step ?current_tap .
        } .

        OPTIONAL {
            ?sc_test cim:ShortCircuitTest.EnergisedEnd ?xfmr_end .
            ?sc_test cim:ShortCircuitTest.leakageImpedance ?z_1_leakage .
            ?sc_test cim:ShortCircuitTest.leakageImpedanceZero ?z_0_leakage .
            ?sc_test cim:ShortCircuitTest.loss ?z_1_loadloss .
            ?sc_test cim:ShortCircuitTest.lossZero ?z_0_loadloss .
        } .


    }

    """
    return query_to_df(graph.query(add_prefixes(query, graph)), columns)


def query_power_transformers(graph: Graph) -> pd.DataFrame:
    columns = [
        "xfmr",
        "apparent_power",
        "rated_voltage",
        "vector_group",
        "per_resistance",
        "conn",
        "angle",
        "winding",
        "bus",
        "xfmr_end",
    ]

    query = """
    SELECT  ?xfmr_name ?apparent_power ?rated_voltage ?vector_group ?per_resistance
        ?conn ?angle ?winding ?node_name ?xfmr_end_name
    WHERE {
        ?xfmr rdf:type cim:PowerTransformer .
        ?xfmr cim:IdentifiedObject.name ?xfmr_name .
        ?xfmr cim:PowerTransformer.vectorGroup ?vector_group .
        ?xfmr_end cim:PowerTransformerEnd.PowerTransformer ?xfmr .
        ?xfmr_end cim:PowerTransformerEnd.ratedS ?apparent_power .
        ?xfmr_end cim:PowerTransformerEnd.ratedU ?rated_voltage .
        ?xfmr_end cim:PowerTransformerEnd.r ?per_resistance .
        ?xfmr_end cim:PowerTransformerEnd.connectionKind ?conn .
        ?xfmr_end cim:PowerTransformerEnd.phaseAngleClock ?angle .
        ?xfmr_end cim:TransformerEnd.endNumber ?winding .
        ?xfmr_end cim:IdentifiedObject.name ?xfmr_end_name .
        ?term cim:Terminal.ConductingEquipment ?xfmr .
        ?term cim:Terminal.ConnectivityNode ?node .
        ?node cim:IdentifiedObject.name ?node_name .
    }
    """
    return query_to_df(graph.query(add_prefixes(query, graph)), columns)


def query_transformer_windings(graph: Graph) -> pd.DataFrame:
    columns = ["winding", "r1", "x1", "r0", "x0", "xfmr_end_1", "xfmr_end_2"]

    query = """
    SELECT  ?winding_name ?r1 ?x1 ?r0 ?x0 ?xfmr_end_name_1 ?xfmr_end_name_2
    WHERE {
        ?xfmr_imp rdf:type cim:TransformerMeshImpedance  .
        ?xfmr_imp cim:IdentifiedObject.name ?winding_name .

        ?xfmr_imp cim:TransformerMeshImpedance.r ?r1 .
        ?xfmr_imp cim:TransformerMeshImpedance.x ?x1 .
        ?xfmr_imp cim:TransformerMeshImpedance.r0 ?r0 .
        ?xfmr_imp cim:TransformerMeshImpedance.x0 ?x0 .

        ?xfmr_imp cim:TransformerMeshImpedance.FromTransformerEnd ?xfmr_end_1 .
        ?xfmr_imp cim:TransformerMeshImpedance.ToTransformerEnd ?xfmr_end_2 .

        ?xfmr_end_1 cim:IdentifiedObject.name ?xfmr_end_name_1 .
        ?xfmr_end_2 cim:IdentifiedObject.name ?xfmr_end_name_2 .
    }
    """
    return query_to_df(graph.query(add_prefixes(query, graph)), columns)


def query_capacitors(graph: Graph) -> pd.DataFrame:
    columns = [
        "capacitor",
        "rated_voltage",
        "conn",
        "bus",
        "b1",
        "g1",
        "b0",
        "g0",
        "phase",
        "steps",
    ]

    query = """
    SELECT  ?cap_name ?rated_voltage ?conn ?node_name ?b1 ?g1 ?b0 ?g0 ?phase ?steps
    WHERE {
        ?cap rdf:type cim:LinearShuntCompensator  .
        ?cap cim:IdentifiedObject.name ?cap_name .
        ?cap cim:ShuntCompensator.phaseConnection ?conn .
        ?cap cim:ConductingEquipment.BaseVoltage ?base_voltage .
        ?base_voltage cim:BaseVoltage.nominalVoltage ?rated_voltage .
        ?term rdf:type cim:Terminal .
        ?term cim:Terminal.ConductingEquipment ?cap .
        ?term cim:Terminal.ConnectivityNode ?node .
        ?node cim:IdentifiedObject.name ?node_name .
        ?cap cim:LinearShuntCompensator.bPerSection ?b1 .
        ?cap cim:LinearShuntCompensator.gPerSection ?g1 .
        ?cap cim:LinearShuntCompensator.b0PerSection ?b0 .
        ?cap cim:LinearShuntCompensator.g0PerSection ?g0 .
        ?cap cim:ShuntCompensator.sections ?steps .

        OPTIONAL {
            ?phs_cap rdf:type cim:LinearShuntCompensatorPhase .
            ?phs_cap cim:ShuntCompensatorPhase.ShuntCompensator ?cap .
            ?phs_cap cim:ShuntCompensatorPhase.phase ?phase .
        } .

    }

    """
    return query_to_df(graph.query(add_prefixes(query, graph)), columns)


def query_source(graph: Graph) -> pd.DataFrame:
    columns = [
        "source",
        "rated_voltage",
        "src_voltage",
        "src_angle",
        "r1",
        "x1",
        "r0",
        "x0",
        "bus",
    ]

    query = """
    SELECT  ?src_name ?rated_voltage ?src_voltage ?src_angle ?r1 ?x1 ?r0 ?x0 ?node_name
    WHERE {
        ?src rdf:type cim:EnergySource .
        ?src cim:IdentifiedObject.name ?src_name .

        ?src cim:EnergySource.nominalVoltage ?rated_voltage .
        ?src cim:EnergySource.voltageMagnitude ?src_voltage .
        ?src cim:EnergySource.voltageAngle ?src_angle .

        ?src cim:EnergySource.r ?r1 .
        ?src cim:EnergySource.x ?x1 .
        ?src cim:EnergySource.r0 ?r0 .
        ?src cim:EnergySource.x0 ?x0 .

        ?term rdf:type cim:Terminal .
        ?term cim:Terminal.ConductingEquipment ?src .
        ?term cim:Terminal.ConnectivityNode ?node .
        ?node cim:IdentifiedObject.name ?node_name .
    }

    """
    return query_to_df(graph.query(add_prefixes(query, graph)), columns)


def query_loads(graph: Graph) -> pd.DataFrame:
    columns = [
        "load",
        "active power",
        "reactive power",
        "rated_voltage",
        "grounded",
        "phase",
        "conn",
        "bus",
        "z_p",
        "i_p",
        "p_p",
        "z_q",
        "i_q",
        "p_q",
        "p_exp",
        "q_exp",
    ]

    query = """
    SELECT  ?load_name ?p ?q ?rated_voltage ?is_grounded ?phase ?conn ?node_name ?z_p ?i_p ?p_p ?z_q ?i_q ?p_q ?p_exp ?q_exp
    WHERE {
        ?load rdf:type cim:EnergyConsumer .
        ?load cim:IdentifiedObject.name ?load_name .
        ?load cim:EnergyConsumer.p ?p .
        ?load cim:EnergyConsumer.q ?q .
        ?load cim:EnergyConsumer.phaseConnection ?conn .
        ?load cim:ConductingEquipment.BaseVoltage ?base_voltage .
        ?base_voltage cim:BaseVoltage.nominalVoltage ?rated_voltage .
        ?load cim:EnergyConsumer.grounded ?is_grounded .
        OPTIONAL {
            ?phs_load rdf:type cim:EnergyConsumerPhase .
            ?phs_load cim:EnergyConsumerPhase.EnergyConsumer ?load .
            ?phs_load cim:EnergyConsumerPhase.phase ?phase .
        } .

        ?term rdf:type cim:Terminal .
        ?term cim:Terminal.ConductingEquipment ?load .
        ?term cim:Terminal.ConnectivityNode ?node .
        ?node cim:IdentifiedObject.name ?node_name .

        ?load cim:EnergyConsumer.LoadResponse ?zip_params .
        ?zip_params cim:LoadResponseCharacteristic.pConstantImpedance ?z_p .
        ?zip_params cim:LoadResponseCharacteristic.pConstantCurrent ?i_p .
        ?zip_params cim:LoadResponseCharacteristic.pConstantPower ?p_p .
        ?zip_params cim:LoadResponseCharacteristic.qConstantImpedance ?z_q .
        ?zip_params cim:LoadResponseCharacteristic.qConstantCurrent ?i_q .
        ?zip_params cim:LoadResponseCharacteristic.qConstantPower ?p_q .
        ?zip_params cim:LoadResponseCharacteristic.pVoltageExponent ?p_exp .
        ?zip_params cim:LoadResponseCharacteristic.qVoltageExponent ?q_exp .
    }
    """
    return query_to_df(graph.query(add_prefixes(query, graph)), columns)


def query_regulator_controllers(graph: Graph) -> pd.DataFrame:
    columns = [
        "regulator",
        "neutral_voltage",
        "initial_delay",
        "subsequent_delay",
        "ltc_flag",
        "enabled",
        "pt_ratio",
        "ct_ratio",
        "ct_rating",
        "mode",
        "bus",
        "phase",
        "target",
        "deadband",
        "ldc",
        "line_drop_r",
        "line_drop_x",
        "reversible",
        "max_voltage",
        "min_voltage",
    ]

    query = """
    SELECT  ?regulator ?neutral_voltage ?initial_delay ?subsequent_delay ?ltc_flag ?enabled
            ?pt_ratio ?ct_ratio ?ct_rating ?mode ?bus_name ?phase ?target ?deadband ?ldc ?line_drop_r
            ?line_drop_x ?reversible ?max_voltage ?min_voltage
    WHERE {
        ?tap_changer rdf:type cim:RatioTapChanger .
        ?tap_changer cim:IdentifiedObject.name ?regulator .
        ?tap_changer cim:TapChanger.neutralU ?neutral_voltage .
        ?tap_changer cim:TapChanger.initialDelay ?initial_delay .
        ?tap_changer cim:TapChanger.subsequentDelay ?subsequent_delay .
        ?tap_changer cim:TapChanger.ltcFlag ?ltc_flag .
        ?tap_changer cim:TapChanger.controlEnabled ?enabled .
        ?tap_changer cim:TapChanger.ptRatio ?pt_ratio .
        ?tap_changer cim:TapChanger.ctRatio ?ct_ratio .
        ?tap_changer cim:TapChanger.ctRating ?ct_rating .
        ?tap_changer cim:TapChanger.TapChangerControl ?controller.
        ?controller cim:RegulatingControl.mode ?mode .
        ?controller cim:RegulatingControl.Terminal ?term .
        ?term cim:Terminal.ConnectivityNode ?bus .
        ?bus cim:IdentifiedObject.name ?bus_name .
        ?controller cim:RegulatingControl.monitoredPhase ?phase .
        ?controller cim:RegulatingControl.targetValue ?target .
        ?controller cim:RegulatingControl.targetDeadband ?deadband .
        ?controller cim:TapChangerControl.lineDropCompensation ?ldc .
        ?controller cim:TapChangerControl.lineDropR ?line_drop_r .
        ?controller cim:TapChangerControl.lineDropX ?line_drop_x .
        ?controller cim:TapChangerControl.reversible ?reversible .
        ?controller cim:TapChangerControl.maxLimitVoltage ?max_voltage .
        ?controller cim:TapChangerControl.minLimitVoltage ?min_voltage .
    }
    """
    return query_to_df(graph.query(add_prefixes(query, graph)), columns)
