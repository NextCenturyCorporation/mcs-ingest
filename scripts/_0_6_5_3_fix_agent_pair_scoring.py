import mcs_history_ingest

def rescore_passive_agents(mongoDB, client, db_string):
    results_collection = mongoDB["eval_6_results"]
    scenes_collection = mongoDB["eval_6_scenes"]

    # This will only get NYU agent tasks, "seeing leads to knowing" has
    #   a test_type of "passive" 
    history_files = results_collection.find({"test_type": "agents"})

    for history_record in history_files:
        paired_record = mcs_history_ingest.return_agency_paired_history_item(
                    client, db_string, history_record)

        if paired_record:
            # Determine which pair item is correct (1), the correct pair
            #   item should have a higher classification to be correct
            if paired_record["score"]["ground_truth"] == 1:
                mcs_history_ingest.update_agency_scoring(paired_record, history_record)
            else:
                mcs_history_ingest.update_agency_scoring(history_record, paired_record)

            mcs_history_ingest.update_agency_paired_history_item(
                client, db_string, paired_record)

        results_collection.replace_one({"_id": history_record["_id"]}, history_record)
        