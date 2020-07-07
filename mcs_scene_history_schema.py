from typing import Dict, Any

_scene_history_schema = {
    "mappings": {
        "history": {
            "properties": {
                "eval": {"type": "keyword"},
                "performer": {"type": "keyword"},
                "name": {"type": "keyword"},
                "steps": {
                    "properties": {
                        "stepNumber": {"type": "integer"},
                        "action": {"type": "keyword"},
                        "args": {"type": "dynamic"}
                    }
                },
                "score": {
                    "properties": {
                        "classification": {"type": "keyword"},
                        "confidence": {"type": "double"}
                    }
                }
            }
        }
    }
}

def get_scene_history_schema() -> Dict[str, Any]:
    return _scene_history_schema