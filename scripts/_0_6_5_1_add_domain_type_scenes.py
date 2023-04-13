# This list is only for Evaluation 5 and earlier tests types
#   New Evaluation 6 Tasks will be ingested correctly when
#   the evaluation is run.
#   This List was obtained doing a "distinct" on the dbs
#   and then matched to list provided by psychs.

# Some older evals had _ in between the words (hence while it appears
#   to have duplicates)
passive_objects = [
    "object_permanence",
	"shape_constancy",
	"spatio_temporal_continuity",
    "object permanence",
	"shape constancy",
	"spatio temporal continuity",
    "gravity support",
    "collisions"
]
interactive_objects = [
    "interactive object permanence",
	"moving target prediction",
    "solidity",
    "support relations",
	"tool use"
]
passive_agents = [
    "agents efficient action irrational",
	"agents efficient action path lure",
	"agents efficient action time control",
	"agents inaccessible goal",
	"agents instrumental action blocking barriers",
	"agents instrumental action inconsequential barriers",
	"agents instrumental action no barriers",
	"agents multiple agents",
	"agents object preference"
]
interactive_agents = ["agent identification"]
interactive_places = [
    "container",
    "holes",
    "lava",
    "obstacle",
	"occluder",
	"ramp",
    "spatial elimination",
    "reorientation",
    "retrieval_container",
	"retrieval_obstacle",
	"retrieval_occluder"
]
# This is to not create confusion with Eval 2 Tasks
interactive = [
    "retrieval",
	"transferral",
	"traversal"
]

# Previous Evaluation List
eval_numbers = ["2", "3", "3_5", "3_75", "4", "5"]

def add_domain_type_field_scenes(mongoDB):
    for eval_number in eval_numbers:
        scenes_collection = mongoDB["eval_" + eval_number + "_scenes"]

        for item in passive_objects:
            scenes_collection.update_many({"goal.sceneInfo.tertiaryType": item}, [{"$set": {"goal.sceneInfo.domainType": "passive objects"}}])
        for item in interactive_objects:
            scenes_collection.update_many({"goal.sceneInfo.tertiaryType": item}, [{"$set": {"goal.sceneInfo.domainType": "interactive objects"}}])
        for item in passive_agents:
            scenes_collection.update_many({"goal.sceneInfo.tertiaryType": item}, [{"$set": {"goal.sceneInfo.domainType": "passive agents"}}])
        for item in interactive_agents:
            scenes_collection.update_many({"goal.sceneInfo.tertiaryType": item}, [{"$set": {"goal.sceneInfo.domainType": "interactive agents"}}])
        for item in interactive_places:
            scenes_collection.update_many({"goal.sceneInfo.tertiaryType": item}, [{"$set": {"goal.sceneInfo.domainType": "interactive places"}}])
        for item in interactive:
            scenes_collection.update_many({"goal.sceneInfo.tertiaryType": item}, [{"$set": {"goal.sceneInfo.domainType": "interactive"}}])

        print("Updated Domain Types for Eval Scenes " + str(eval_number) + ".")

