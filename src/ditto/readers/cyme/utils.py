import pandas as pd
from gdm.distribution.components.distribution_feeder import DistributionFeeder

def read_cyme_data(cyme_file, cyme_section, node_feeder_map = None, parse_feeders=False):
    all_data = []
    headers = None
    with open(cyme_file) as f:
        reading = False
        feeder_id = None
        feeder_object_map = {}
        for line in f:
            if line.startswith(f"[{cyme_section}]"):
                reading = True
                continue
            if reading:
                if line.startswith(f"FORMAT_{cyme_section.replace(' ','')}"):
                    line_header = line.split("=")[1].strip()
                    headers = line_header.split(",")
                    continue
                elif line.startswith("FORMAT") or line.startswith("FEEDER") or line.startswith("SUBSTATION"):
                    if parse_feeders:
                        if line.startswith("FEEDER"):
                            feeder_id = line.split(",")[0].split("=")[1].strip()
                        else:
                            feeder_id = None
                    # For SECTION Feeder headers
                    continue
                elif line.strip() == "":
                    reading = False
                    break
                else:
                    try:
                        line = line.strip()
                        line_data = line.split(",")
                        if parse_feeders and (feeder_id is not None):
                            if cyme_section == 'SECTION':
                                node1 = line_data[1].strip()
                                node2 = line_data[3].strip()
                                feeder = feeder_object_map.get(feeder_id, DistributionFeeder(name = feeder_id))
                                node_feeder_map[node1] = feeder
                                node_feeder_map[node2] = feeder
                                feeder_object_map[feeder_id] = feeder
                        all_data.append(line.split(","))
                    except:
                        raise Exception(f"Failed to parse line: {line}")

    data = pd.DataFrame(all_data, columns=headers)
    return data
