from typing import Dict, Any

_scene_schema = {
    "mappings": {
        "scenes": {
            "properties": {
                "eval": {"type": "keyword"},
                "performer": {"type": "keyword"},
                "name": {"type": "keyword"},
                "ceilingMaterial": {"type": "keyword"},
                "floorMaterial": {"type": "keyword"},
                "wallMaterial": {"type": "keyword"},
                "wallColors": {"type": "keyword"},
                "performerStart": {
                    "properties": {
                        "position": {
                            "properties": {
                                "x": {"type": "double"},
                                "y": {"type": "double"},
                                "z": {"type": "double"}
                            }
                        },
                        "rotation": {
                            "properties": {
                                "y": {"type": "double"}
                            }
                        }
                    }
                },
                "objects": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "info": {"type": "keyword"},
                        "novel_color": {"type": "boolean"},
                        "novel_combination": {"type": "boolean"},
                        "novel_shape": {"type": "boolean"},
                        "kinematic": {"type": "boolean"},
                        "structure": {"type": "boolean"},
                        "mass": {"type": "double"},
                        "dimensions": {
                            "properties": {
                                "x": {"type": "double"},
                                "y": {"type": "double"},
                                "z": {"type": "double"}
                            }
                        },
                        "moveable": {"type": "boolean"},
                        "pickupable": {"type": "boolean"},
                        "receptacle": {"type": "boolean"},
                        "stackTarget": {"type": "boolean"},
                        "original_location": {
                            "properties": {
                                "position": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                },
                                "rotation": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                },
                                "bounding_box": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                }
                            }
                        },
                        "shows": {
                            "properties": {
                                "position": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                },
                                "stepBegin": {"type": "integer"},
                                "scale": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                },
                                "rotation": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                },
                                "bounding_box": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                }
                            }
                        },
                        "materialCategory": {"type": "keyword"},
                        "materials_list": {"type": "keyword"},
                        "materials": {"type": "keyword"},
                        "salientMaterials": {"type": "keyword"},
                        "info_string": {"type": "keyword"},
                        "goal_string": {"type": "keyword"},
                        "shape": {"type": "keyword"},
                        "forces": {
                            "properties": {
                                "stepBegin": {"type": "integer"},
                                "stepEnd": {"type": "integer"},
                                "vector": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                }
                            }
                        },
                        "shows": {
                            "properties": {
                                "stepBegin": {"type": "integer"},
                                "position": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                },
                                "scale": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                }
                            }
                        },
                        "moves": {
                            "properties": {
                                "stepBegin": {"type": "integer"},
                                "stepEnd": {"type": "integer"},
                                "vector": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                }
                            }
                        },
                        "rotates": {
                            "properties": {
                                "stepBegin": {"type": "integer"},
                                "stepEnd": {"type": "integer"},
                                "vector": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                }
                            }
                        },
                        "intphys_option": {
                            "properties": {
                                "y": {"type": "double"},
                                "force": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                },
                                "position_by_step": {"type": "double"},
                                "position_y": {"type": "double"},
                                "occluder_indices": {"type": "double"},
                                "is_occluder": {"type": "boolean"}
                            }
                        },
                        "torques": {
                            "properties": {
                                "stepBegin": {"type": "integer"},
                                "stepEnd": {"type": "integer"},
                                "vector": {
                                    "properties": {
                                        "x": {"type": "double"},
                                        "y": {"type": "double"},
                                        "z": {"type": "double"}
                                    }
                                }
                            }
                        }
                    }
                },
                "goals": {
                    "properties": {
                        "category": {"type": "keyword"},
                        "domain_list": {"type": "keyword"},
                        "type_list": {"type": "keyword"},
                        "task_list": {"type": "keyword"},
                        "description": {"type": "keyword"},
                        "metadata": {
                            "properties": {
                                "objects": {"type": "keyword"}
                            }
                        },
                        "last_step": {"type": "integer"},
                        "action_list": {"type": "nested"},
                        "info_list": {"type": "keyword"},
                        "series_id": {"type": "keyword"},
                        "metadata": {
                            "properties" : {
                                "target_1" : {
                                    "properties": {
                                        "id": {"type": "keyword"},
                                        "info": {"type": "keyword"},
                                        "match_image": {"type": "boolean"},
                                        "image_name": {"type": "keyword"}
                                    }
                                },
                                "relationship": {"type": "keyword"}
                            }
                        }
                    }
                },
                "answer": {
                    "properties": {
                        "choice": {"type": "keyword"},
                        "actions": {
                            "properties": {
                                "action": {"type": "keyword"},
                                "params": {"type": "object"}
                            }
                        }
                    }
                },
                "observation": {"type": "boolean"}
            }
        }
    }
}

def get_scene_schema() -> Dict[str, Any]:
    return _scene_schema