import json

from project.logger import logger
from project.wfc.pattern import MetaPattern, Pattern
from project.wfc.repository import ValidationResult, repository
from project.wfc.rules import NeighborRuleSet


class Factory:
    def __init__(self, json_path: str) -> None:
        with open(json_path, "r") as f:
            data = json.load(f)
            self.images_folder = data["images_folder"]
            self.data = data["patterns"]

    def create_patterns(self) -> list[MetaPattern]:
        """Creates patterns and rules from JSON data"""
        patterns_data = {p["id"]: p for p in self.data}
        meta_patterns = [
            MetaPattern(
                uid=pattern_data["id"],
                name=pattern_data["name"],
                is_walkable=pattern_data["is_walkable"],
                tags=set(pattern_data["tags"]),
                weight=pattern_data["weight"],
                patterns=tuple(
                    [
                        Pattern(
                            image_path=f"{self.images_folder}{pattern["image_path"]}",
                            weight=pattern["weight"],
                        )
                        for pattern in pattern_data.get("patterns", [])
                    ]
                ),
            )
            for pattern_data in self.data
        ]
        repository.register_patterns(meta_patterns)

        for pattern in meta_patterns:
            rules = self.create_rules(patterns_data[pattern.uid]["rules"])
            pattern.rules = rules

        validation = repository.validate_patterns()
        if validation.result == ValidationResult.SUCCESS:
            logger.info(validation)
        else:
            logger.error(validation)

        return meta_patterns

    def create_rules(self, rules: dict[str, list[str | int]]) -> NeighborRuleSet:
        """Create a NeighborRuleSet based on the JSON rules"""

        def rules_handler(options: list[str | int]):
            results = []
            for op in options:
                if isinstance(op, str):
                    results.extend(repository.handle_text_rule(op))
                else:
                    results.append(repository.get_pattern_by_uid(op))
            return results

        return NeighborRuleSet(
            allowed_up=rules_handler(rules.get("up", [])),
            allowed_down=rules_handler(rules.get("down", [])),
            allowed_left=rules_handler(rules.get("left", [])),
            allowed_right=rules_handler(rules.get("right", [])),
        )
