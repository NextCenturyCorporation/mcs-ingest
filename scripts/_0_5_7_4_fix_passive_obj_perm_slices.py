slices_to_correct = ["A3", "B3", "C3", "D3", "E3", "F3", "G3", "H3", "I3"]

def update_slice_info_passive_obj_perm(mongoDB):
    eval_5_scenes = mongoDB["eval_5_scenes"]
    eval_5_results = mongoDB["eval_5_results"]
    
    for slice_id in slices_to_correct:
        # Pull the incorrect slice description out of scene records
        # Mongo does not allow for push and pull on same update
        result = eval_5_scenes.update_many(
            {
                "goal.sceneInfo.tertiaryType": "object permanence",
                "goal.sceneInfo.id": [slice_id]
            }, {
                "$pull": {
                    "goal.sceneInfo.slices": "setup move across whole scene"
                }
            }
        )

        print("Removed from slice array for scenes.", result) 

        # Push the correct slice description onto scene records
        result = eval_5_scenes.update_many(
            {
                "goal.sceneInfo.tertiaryType": "object permanence",
                "goal.sceneInfo.id": [slice_id]
            }, {
                "$push": {
                    "goal.sceneInfo.slices": "setup falls behind an occluder"
                }
            }
        )

        print("Added to slice array for scenes.", result)    

        # Pull the incorrect slice description out of result records
        # Mongo does not allow for push and pull on same update
        result = eval_5_results.update_many(
            {
                "category_type": "object permanence",
                "scene_goal_id": [slice_id]
            }, {
                "$pull": {
                    "slices": "setup move across whole scene"
                }
            }
        )

        print("Removed from slice array for results.", result) 

        # Push the correct slice description onto result records
        result = eval_5_results.update_many(
            {
                "category_type": "object permanence",
                "scene_goal_id": [slice_id]
            }, {
                "$push": {
                    "slices": "setup falls behind an occluder"
                }
            }
        )

        print("Added to slice array for results.", result)    
