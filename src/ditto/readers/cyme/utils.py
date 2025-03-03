import pandas as pd

def read_cyme_data(cyme_file, cyme_section):
    all_data = []
    headers = None
    with open(cyme_file) as f:
        reading = False
        for line in f:
            if line.startswith(f"[{cyme_section}]"):
                reading = True
                continue
            if reading:
                if line.startswith(f"FORMAT_{cyme_section.replace(' ','')}"):
                    line_header = line.split("=")[1].strip()
                    headers = line_header.split(",")
                    continue
                elif line.startswith("FORMAT") or line.startswith("FEEDER"):
                    # For SECTION Feeder headers
                    continue
                elif line.strip() == "":
                    reading = False
                    break
                else:
                    try:
                        line = line.strip()
                        all_data.append(line.split(","))
                    except:
                        raise Exception(f"Failed to parse line: {line}")

    data = pd.DataFrame(all_data, columns=headers)
    return data
