from scorecard import Scorecard

def update_tool_use_test_types_and_scorecard(mongoDB):
    results_collection = mongoDB["eval_6_results"]
    scenes_collection = mongoDB["eval_6_scenes"]

    # Update tertiaryType in Scene Collection
    scenes_collection.update_many({"goal.sceneInfo.tertiaryType": "tool use",
        "goal.sceneInfo.id": {"$regex": "1", "$options": 'i'}}, [{"$set": {"goal.sceneInfo.tertiaryType": "symmetric tool use"}}])
    scenes_collection.update_many({"goal.sceneInfo.tertiaryType": "tool use",
        "goal.sceneInfo.id": {"$regex": "2", "$options": 'i'}}, [{"$set": {"goal.sceneInfo.tertiaryType": "tool choice"}}])
    scenes_collection.update_many({"goal.sceneInfo.tertiaryType": "tool use",
        "goal.sceneInfo.id": {"$regex": "3", "$options": 'i'}}, [{"$set": {"goal.sceneInfo.tertiaryType": "asymmetric tool use"}}])
    print("Updated Scenes Tertiary type for tool use.")

    # Update the Scorecard for Tool Use
    history_files = results_collection.find({"category_type": "tool use"})
    for history_record in history_files:
        scene = scenes_collection.find_one({"name": history_record["name"]})
        
        scorecard = Scorecard(history_record, scene)
        scorecard.calc_correct_platform_side()

        history_record["score"]["scorecard"]["correct_platform_side"] = scorecard.get_correct_platform_side()
        results_collection.replace_one({"_id": history_record["_id"]}, history_record)
    print("Updated Tool Use Scorecard correct platform side")

    # Update category_type in History Collection
    results_collection.update_many({"category_type": "tool use",
        "scene_goal_id": {"$regex": "1", "$options": 'i'}}, [{"$set": {"category_type": "symmetric tool use"}}])
    results_collection.update_many({"category_type": "tool use",
        "scene_goal_id": {"$regex": "2", "$options": 'i'}}, [{"$set": {"category_type": "tool choice"}}])
    results_collection.update_many({"category_type": "tool use",
        "scene_goal_id": {"$regex": "3", "$options": 'i'}}, [{"$set": {"category_type": "asymmetric tool use"}}])
    print("Updated Results category type for tool use.")
