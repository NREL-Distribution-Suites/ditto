from ditto.readers.cim_iec_61968_13.reader import Reader


def test_query_aclinesegment(ieee13_node_xml_file):
    cim_reader = Reader(ieee13_node_xml_file)
    cim_reader.read()
