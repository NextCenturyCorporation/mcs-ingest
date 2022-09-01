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

        # Push the correct slice description onto scene records
        result = eval_5_scenes.update_many(
            {
                "goal.sceneInfo.tertiaryType": "object permanence",
                "goal.sceneInfo.id": [slice_id]
            }, {
                "$push": {
                    "goal.sceneInfo.slices": {
                        "$each": ["setup falls behind an occluder"],
                        "$position": 0
                    }
                }
            }
        )

        # Update setup tag
        result = eval_5_scenes.update_many(
            {
                "goal.sceneInfo.tertiaryType": "object permanence",
                "goal.sceneInfo.id": [slice_id]
            }, [{
                "$set": {
                   "goal.sceneInfo.setup": "falls behind an occluder"
                }
            }]
        )

        print("Updated slices/tags for object permanence scenes " + str(slice_id) + ".", result)

        # Pull the incorrect slice description out of result records
        # Mongo does not allow for push and pull on same update
        result = eval_5_results.update_many(
            {
                "category_type": "object permanence",
                "scene_goal_id": slice_id
            }, {
                "$pull": {
                    "slices": "setup move across whole scene"
                }
            }
        )

        # Push the correct slice description onto result records
        result = eval_5_results.update_many(
            {
                "category_type": "object permanence",
                "scene_goal_id": slice_id
            }, {
                "$push": {
                    "slices": {
                        "$each": ["setup falls behind an occluder"],
                        "$position": 0
                    }
                }
            }
        )

        print("Updated slices/tags for object permanence results " + str(slice_id) + ".", result)
