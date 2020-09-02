from typing import Dict, Any

_scene_history_schema = {
    "mappings": {
        "history": {
            "properties": {
                "eval": {"type": "keyword"},
                "performer": {"type": "keyword"},
                "name": {"type": "keyword"},
                "test_type": {"type": "keyword"},
                "scene_num": {"type": "keyword"},
                "scene_part_num": {"type": "keyword"},
                "url_string": {"type": "keyword"},
                "category": {"type": "keyword"},
                "category_type": {"type": "keyword"},
                "category_pair": {"type": "keyword"},
                "flags": {
                    "properties": {
                        "remove": {"type": "boolean"},
                        "interest": {"type": "boolean"}
                    }
                },
                "step_counter": {"type": "integer"},
                "steps": {
                    "properties": {
                        "stepNumber": {"type": "integer"},
                        "action": {"type": "keyword"},
                        "args": {"type": "object"},
                        "output": {
                            "properties": {
                                "return_status": {"type": "keyword"},
                                "reward": {"type": "integer"}
                            }
                        }
                    }
                },
                "score": {
                    "properties": {
                        "classification": {"type": "keyword"},
                        "confidence": {"type": "double"},
                        "adjusted_confidence": {"type": "double"},
                        "score": {"type": "integer"},
                        "score_description": {"type": "keyword"},
                        "ground_truth": {"type": "integer"},
                        "mse": {"type": "double"},
                        "performer_steps": {"type": "integer"},
                        "goal_ideal_steps": {"type": "integer"}
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
                        "num_interior_walls": {"type": "integer"},
                        "num_confusors": {"type": "integer"},
                        "num_obstructors": {"type": "integer"},
                        "has_novel_color": {"type": "keyword"},
                        "has_novel_shape": {"type": "keyword"},
                        "has_novel_combination": {"type": "keyword"},
                        "objects": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "info": {"type": "keyword"},
                                "novel_color": {"type": "boolean"},
                                "novel_combination": {"type": "boolean"},
                                "novel_shape": {"type": "boolean"},
                                "goal_string": {"type": "keyword"},
                                "shape": {"type": "keyword"},
                                "is_occluder": {"type": "boolean"},
                                "descriptors": {"type": "keyword"}
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