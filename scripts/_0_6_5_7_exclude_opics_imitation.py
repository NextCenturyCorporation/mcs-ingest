# OPICS was able to retrieve ball from ceiling 
# This patch rescores their imitation task where ball was retrieved from ceiling
# weighted_score and weighted_score_worth are set to 0


import mcs_history_ingest

scene_file_names = ["foxtrot_0002_03",
    "foxtrot_0002_06",
    "foxtrot_0002_09",
    "foxtrot_0002_10",
    "foxtrot_0002_12",
    "foxtrot_0003_03",
    "foxtrot_0003_08",
    "foxtrot_0004_01",
    "foxtrot_0004_12",
    "foxtrot_0005_02",
    "foxtrot_0005_06",
    "foxtrot_0005_08",
    "foxtrot_0005_09",
    "foxtrot_0006_06",
    "foxtrot_0006_08",
    "foxtrot_0006_10",
    "foxtrot_0006_11",
    "foxtrot_0007_03",
    "foxtrot_0007_07",
    "foxtrot_0007_11",
    "foxtrot_0007_12",
    "foxtrot_0009_07",
    "foxtrot_0009_09",
    "foxtrot_0012_06",
    "foxtrot_0012_08",
    "foxtrot_0013_01",
    "foxtrot_0017_02",
    "foxtrot_0017_12",
    "foxtrot_0018_02",
    "foxtrot_0018_04",
    "foxtrot_0019_01",
    "foxtrot_0019_02",
    "foxtrot_0019_09",
    "foxtrot_0019_12",
    "foxtrot_0020_02",
    "foxtrot_0020_03",
    "foxtrot_0021_09",
    "foxtrot_0024_02",
    "foxtrot_0024_06",
    "foxtrot_0024_07",
    "foxtrot_0024_08",
    "foxtrot_0024_10",
    "foxtrot_0024_11"]

def rescore_opics_imitation_task(mongoDB):
    results_collection = mongoDB["eval_6_results"]

    print("Begin looping through scene file names.")

    for history_file_name in scene_file_names:

        result = results_collection.update_many(
            {
                "category_type": "imitation task", "performer": "OPICS", "name": history_file_name
            },             
            [{
                "$set": {
                    'score.weighted_score': 0,
                    'score.weighted_score_worth': 0
                }
            }])

        print("Update " + history_file_name + ".", result)    
