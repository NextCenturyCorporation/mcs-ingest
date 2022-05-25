slices_to_correct = ["C1", "C2", "F1", "F2", "I1", "I2", "L1", "L2"]

def update_slice_info(mongoDB):
    eval_4_scenes = mongoDB["eval_4_scenes"]
    
    for slice_id in slices_to_correct:
        # Pull the incorrect slice description out
        # Mongo does not allow for push and pull on same update
        result = eval_4_scenes.update_many(
            {
                "goal.sceneInfo.tertiaryType": "collisions",
                "goal.sceneInfo.id": [slice_id]
            }, {
                "$pull": {
                    "goal.sceneInfo.slices": "occluder reveals empty scene"
                }
            }
        )

        print("Removed from slice array.", result) 

        # Push the correct slice description
        result = eval_4_scenes.update_many(
            {
                "goal.sceneInfo.tertiaryType": "collisions",
                "goal.sceneInfo.id": [slice_id]
            }, {
                "$push": {
                    "goal.sceneInfo.slices": "occluder reveals second object behind path"
                }
            }
        )

        print("Added to slice array.", result)    