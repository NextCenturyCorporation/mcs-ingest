field_mapping = {
    "mcs_history.Evaluation 4 Results": "eval_4_results",
    "mcs_history.Evaluation 3.75 Results": "eval_3_75_results",
    "mcs_history.Evaluation 3.5 Results": "eval_3_5_results",
    "mcs_history.Evaluation 3 Results": "eval_3_results",
    "mcs_history.Evaluation 2 Results": "eval_2_results",
    "mcs_scenes.Evaluation 4 Scenes": "eval_4_scenes",
    "mcs_scenes.Evaluation 3.75 Scenes": "eval_3_75_scenes",
    "mcs_scenes.Evaluation 3.5 Scenes": "eval_3_5_scenes",
    "mcs_scenes.Evaluation 3 Scenes": "eval_3_scenes",
    "mcs_scenes.Evaluation 2 Scenes": "eval_2_scenes"
}

def update_saved_queries(mongoDB):
    saved_queries_collection = mongoDB["savedQueries"]
    all_documents = saved_queries_collection.find({})
    
    for document in all_documents:
        # Update the saved tabs object fieldTypes
        for tab in document["user"]["queryBuilderState"]["queryTabs"]:
            for tab_query_obj in tab["tabQueryObj"]:
                if tab_query_obj["fieldType"] in field_mapping:
                    tab_query_obj["fieldType"] = field_mapping[tab_query_obj["fieldType"]]
        
        # Update queryObj of saved query
        for query in document["queryObj"]:
            if query["fieldType"] in field_mapping:
                query["fieldType"] = field_mapping[query["fieldType"]]

        # Saved updated object
        saved_queries_collection.replace_one({"_id": document["_id"]}, document)        
