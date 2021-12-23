# Scene goal ids provied by Brenden Lake - wants them excluded from scoring. Extras in addition to _0_4_7_2
goal_id_array = ["000047eee","000057eee","000067eee","000096eee","000099eee","000104eee","000111eee","000119eee","000124eee",
    "000125eee","000147eee","000163eee","000180eee","000196eee","000207eee","000212eee","000225eee","000247eee","000262eee",
    "000282eee","000317eee","000330eee","000346eee","000349eee","000357eee","000362eee","000411eee","000415eee","000417eee",
    "000426eee","000434eee","000435eee","000437eee","000441eee","000442eee","000446eee","000463eee","000464eee","000466eee",
    "000468eee","000472eee","000474eee","000487eee","000488eee","000490eee","000497eee","000513eee","000519eee","000528eee",
    "000540eee","000544eee","000548eee","000557eee","000565eee","000571eee","000573eee","000575eee","000579eee","000591eee",
    "000606eee","000610eee","000613eee","000639eee","000649eee","000660eee","000662eee","000678eee","000682eee","000684eee",
    "000686eee","000713eee","000722eee","000733eee","000739eee","000740eee","000749eee","000763eee","000773eee","000779eee",
    "000791eee","000798eee","000812eee","000822eee","000823eee","000829eee","000831eee","000844eee","000866eee","000872eee",
    "000879eee","000901eee","000905eee","000906eee","000917eee","000919eee","000920eee","000931eee","000932eee","000936eee",
    "000938eee","000939eee","000953eee","000954eee","000958eee","000961eee","000964eee","000982eee","000983eee","000994eee",
    "000995eee","000165gse","000199gse","000263gse","000270gse","000296gse","000361gse","000415gse","000424gse","000466gse",
    "000530gse","000564gse","000575gse"]

def update_score_worth(mongoDB):
    history_collection = mongoDB["mcs_history"]
    for goal_id in goal_id_array:
        result = history_collection.update_many(
            {
                "eval": "Evaluation 4 Results",
                "scene_goal_id": goal_id
            }, [{
                "$set": {
                    'score.weighted_score': 0,
                    'score.weighted_score_worth': 0
                }
            }])

        print("Update " + str(goal_id) + ".", result)