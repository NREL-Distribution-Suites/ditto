from infrasys import Component

from ditto.readers.opendss.common import hash_model, get_equipment_from_catalog


class MockComponent1(Component):
    field_1: str
    field_2: int


class MockComponent2(Component):
    field_1: MockComponent1


class MockComponent3(Component):
    field_1: list[MockComponent1]


def test_model_hash():
    model_1 = MockComponent1(field_1="test", field_2=0, name="test_1")
    model_2 = MockComponent1(field_1="test", field_2=0, name="test_2")
    model_2_a = MockComponent1(field_1="different", field_2=0, name="test_2")

    assert hash_model(model_1) == hash_model(model_2)
    assert hash_model(model_1) != hash_model(model_2_a)

    model_3 = MockComponent2(name="test_3", field_1=model_1)
    model_4 = MockComponent2(name="test_4", field_1=model_2)
    model_4_a = MockComponent2(name="test_4", field_1=model_2_a)

    assert hash_model(model_3) == hash_model(model_4)
    assert hash_model(model_3) != hash_model(model_4_a)

    model_5 = MockComponent3(name="test_5", field_1=[model_1])
    model_6 = MockComponent3(name="test_6", field_1=[model_2])
    model_6_a = MockComponent3(name="test_6", field_1=[model_2_a])

    assert hash_model(model_5) == hash_model(model_6)
    assert hash_model(model_5) != hash_model(model_6_a)


def test_model_from_catalog():
    catalog = {}

    model_1 = MockComponent1(field_1="test", field_2=0, name="test_1")
    model_2 = MockComponent1(field_1="test", field_2=0, name="test_2")

    model_a = get_equipment_from_catalog(model_1, catalog)
    model_b = get_equipment_from_catalog(model_2, catalog)

    assert len(catalog) == 1
    assert model_a == model_b
