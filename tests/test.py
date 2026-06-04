import pytest
from pathlib import Path
from fly_in.map_parser import MapParser, MapParsingError
from fly_in.map_types import Node


def create_map(tmp_path: Path, content: str) -> str:
    """create temp file to test maps"""
    file_path = tmp_path / "test_map.txt"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


class TestMapParserValid:
    def test_minimal_valid_map(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0
end_hub: goal 10 10"""

        with MapParser(create_map(tmp_path, content)) as parser:
            assert parser.nb_drones == 5
            assert parser.start_hub is not None
            assert parser.start_hub.name == "start"
            assert parser.end_hub is not None
            assert len(parser.hubs) == 2
            assert len(parser.connections) == 0

    def test_valid_map_with_metadata_and_comments(self,
                                                  tmp_path: Path) -> None:
        content = """# comment
nb_drones: 42

start_hub: start 0 0 [color=green max_drones=10]
hub: roof_1 3 4 [zone=restricted color=cyan]   # testtest
end_hub: goal 10 10 [color=yellow]

connection: start-roof_1 [max_link_capacity=2]
connection: roof_1-goal"""

        with MapParser(create_map(tmp_path, content)) as parser:
            assert parser.nb_drones == 42
            assert len(parser.hubs) == 3
            assert len(parser.connections) == 2

            roof: Node | None = None
            for hub in parser.hubs:
                if hub.name == "roof_1":
                    roof = hub
            assert roof is not None
            assert roof.metadata.zone \
                and roof.metadata.zone.name == "RESTRICTED"

    def test_negative_coordinates(self, tmp_path: Path) -> None:
        content = """nb_drones: 1
start_hub: start -5 -10
end_hub: end 5 10"""

        with MapParser(create_map(tmp_path, content)) as parser:
            assert parser.start_hub and parser.start_hub.x == -5
            assert parser.start_hub and parser.start_hub.y == -10


class TestMapParserInvalid:
    def test_missing_nb_drones_on_first_line(self, tmp_path: Path) -> None:
        content = """start_hub: start 0 0
nb_drones: 5
end_hub: goal 10 10"""
        with pytest.raises(MapParsingError) as exc_info:
            with MapParser(create_map(tmp_path, content)):
                pass
        assert "first line" in str(exc_info.value.error).lower()

    def test_duplicate_hub_names(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0
hub: start 1 1
end_hub: goal 10 10"""
        with pytest.raises(MapParsingError) as exc_info:
            with MapParser(create_map(tmp_path, content)):
                pass
        assert "taken" in str(exc_info.value.error)

    def test_duplicate_coordinates(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0
end_hub: goal 0 0"""
        with pytest.raises(MapParsingError) as exc_info:
            with MapParser(create_map(tmp_path, content)):
                pass
        assert "coords" in str(exc_info.value.error).lower()

    def test_invalid_zone_type(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0 [zone=magical_zone]
end_hub: goal 10 10"""
        with pytest.raises(MapParsingError):
            with MapParser(create_map(tmp_path, content)):
                pass

    def test_connection_unknown_hub(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0
end_hub: goal 10 10
connection: start-ghost_hub"""
        with pytest.raises(MapParsingError) as exc_info:
            with MapParser(create_map(tmp_path, content)):
                pass
        assert "must be in hubs" in str(exc_info.value.error).lower()

    def test_duplicate_connection(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: a 0 0
end_hub: b 10 10
connection: a-b
connection: b-a"""
        with pytest.raises(MapParsingError) as exc_info:
            with MapParser(create_map(tmp_path, content)):
                pass
        assert "already exists" in str(exc_info.value.error).lower()

    def test_invalid_metadata_syntax(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0 [color green]
end_hub: goal 10 10"""
        with pytest.raises(MapParsingError) as exc_info:
            with MapParser(create_map(tmp_path, content)):
                pass
        assert "format" in repr(exc_info.value.error).lower()

    def test_missing_end_hub(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0"""
        with pytest.raises(MapParsingError) as exc_info:
            with MapParser(create_map(tmp_path, content)):
                pass
        assert "missing key 'end_hub'" in str(exc_info.value.error).lower()

    def test_connection_without_dash(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0
end_hub: goal 10 10
connection: startgoal"""
        with pytest.raises(MapParsingError):
            with MapParser(create_map(tmp_path, content)):
                pass

    def test_metadata_not_last(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0
end_hub: goal 10 10 [color=green] test
connection: start-goal"""
        with pytest.raises(MapParsingError):
            with MapParser(create_map(tmp_path, content)):
                pass

    def test_metadata_in_wrong_key(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0
end_hub: goal 10 10 [max_link_capacity=1]
connection: start-goal"""
        with pytest.raises(MapParsingError):
            with MapParser(create_map(tmp_path, content)):
                pass

    def test_metadata_in_wrong_key2(self, tmp_path: Path) -> None:
        content = """nb_drones: 5
start_hub: start 0 0
end_hub: goal 10 10 [max_drones=1]
connection: start-goal [max_drones=1 max_link_capacity=1]"""
        with pytest.raises(MapParsingError):
            with MapParser(create_map(tmp_path, content)):
                pass