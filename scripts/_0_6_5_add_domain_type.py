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

def add_domain_type_field(mongoDB):
    for eval_number in eval_numbers:
        results_collection = mongoDB["eval_" + eval_number + "_results"]

        for item in passive_objects:
            results_collection.update_many({"category_type": item}, [{"$set": {"domain_type": "passive objects"}}])
        for item in interactive_objects:
            results_collection.update_many({"category_type": item}, [{"$set": {"domain_type": "interactive objects"}}])
        for item in passive_agents:
            results_collection.update_many({"category_type": item}, [{"$set": {"domain_type": "passive agents"}}])
        for item in interactive_agents:
            results_collection.update_many({"category_type": item}, [{"$set": {"domain_type": "interactive agents"}}])
        for item in interactive_places:
            results_collection.update_many({"category_type": item}, [{"$set": {"domain_type": "interactive places"}}])
        for item in interactive:
            results_collection.update_many({"category_type": item}, [{"$set": {"domain_type": "interactive"}}])

        print("Updated Domain Types for Eval " + str(eval_number) + ".")

        results_collection.create_index([("domain_type", 1), ("category", 1)])
        results_collection.create_index([("domain_type", 1), ("metadata", 1)])

        scenes_collection = mongoDB["eval_" + eval_number + "_scenes"]
        scenes_collection.create_index([("domain_type", 1), ("metadata", 1)])
        
        print("Created Domain Type Indexes for Eval " + str(eval_number) + ".")
