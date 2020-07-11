from typing import Dict, Any

_scene_history_schema = {
    "mappings": {
        "history": {
            "properties": {
                "eval": {"type": "keyword"},
                "performer": {"type": "keyword"},
                "name": {"type": "keyword"},
                "testType": {"type": "keyword"},
                "steps": {
                    "properties": {
                        "stepNumber": {"type": "integer"},
                        "action": {"type": "keyword"},
                        "args": {"type": "object"}
                    }
                },
                "score": {
                    "properties": {
                        "classification": {"type": "keyword"},
                        "confidence": {"type": "double"},
                        "adjusted_confidence": {"type": "double"},
                        "score": {"type": "integer"},
                        "score_description": {"type": "keyword"},
                        "ground_truth": {"type": "integer"}
                    }
                },
                "scene": {
                    "properties": {
                        "answer_choice": {"type": "keyword"},
                        "observation": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "domain_list": {"type": "keyword"},
                        "type_list": {"type": "keyword"},
                        "task_list": {"type": "keyword"},
                        "info_list": {"type": "keyword"},
                        "series_id": {"type": "keyword"},
                        "num_objects": {"type": "integer"},
                        "num_occluders": {"type": "integer"},
                        "num_context_objects": {"type": "integer"},
                        "objects": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "info": {"type": "keyword"},
                                "novel_color": {"type": "boolean"},
                                "novel_combination": {"type": "boolean"},
                                "novel_shape": {"type": "boolean"},
                                "goal_string": {"type": "keyword"},
                                "shape": {"type": "keyword"},
                                "is_occluder": {"type": "boolean"}
                            }
                        }
                    }
                }
            }
        }
    }
}

def get_scene_history_schema() -> Dict[str, Any]:
    return _scene_history_schema