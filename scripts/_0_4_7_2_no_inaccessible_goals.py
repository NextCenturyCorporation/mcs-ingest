# Scene goal ids provied by Brenden Lake - wants them excluded from scoring.
goal_id_array = ["000007ebe", "000009ebe", "000023ebe", "000024ebe", "000029ebe", "000032ebe", "000034ebe", "000036ebe", 
    "000041ebe", "000043ebe", "000047ebe", "000056ebe", "000066ebe", "000072ebe", "000073ebe", "000076ebe", "000080ebe", 
    "000081ebe", "000082ebe", "000091ebe", "000092ebe", "000094ebe", "000095ebe", "000102ebe", "000105ebe", "000106ebe", 
    "000119ebe", "000121ebe", "000122ebe", "000124ebe", "000126ebe", "000128ebe", "000129ebe", "000131ebe", "000137ebe", 
    "000140ebe", "000141ebe", "000155ebe", "000175ebe", "000189ebe", "000193ebe", "000198ebe", "000200ebe", "000202ebe", 
    "000203ebe", "000205ebe", "000207ebe", "000210ebe", "000211ebe", "000213ebe", "000214ebe", "000227ebe", "000230ebe", 
    "000232ebe", "000236ebe", "000240ebe", "000245ebe", "000251ebe", "000253ebe", "000256ebe", "000263ebe", "000269ebe", 
    "000270ebe", "000281ebe", "000297ebe", "000301ebe", "000302ebe", "000304ebe", "000312ebe", "000313ebe", "000314ebe", 
    "000316ebe", "000317ebe", "000319ebe", "000323ebe", "000327ebe", "000334ebe", "000337ebe", "000349ebe", "000353ebe", 
    "000366ebe", "000369ebe", "000371ebe", "000386ebe", "000388ebe", "000390ebe", "000395ebe", "000400ebe", "000401ebe", 
    "000407ebe", "000408ebe", "000409ebe", "000418ebe", "000426ebe", "000428ebe", "000437ebe", "000440ebe", "000448ebe", 
    "000451ebe", "000469ebe", "000471ebe", "000475ebe", "000479ebe", "000481ebe", "000490ebe", "000495ebe", "000496ebe", 
    "000501ebe", "000502ebe", "000504ebe", "000506ebe", "000510ebe", "000519ebe", "000530ebe", "000546ebe", "000552ebe", 
    "000554ebe", "000555ebe", "000561ebe", "000568ebe", "000572ebe", "000582ebe", "000587ebe", "000592ebe", "000607ebe", 
    "000608ebe", "000609ebe", "000614ebe", "000615ebe", "000617ebe", "000619ebe", "000633ebe", "000640ebe", "000643ebe", 
    "000657ebe", "000659ebe", "000663ebe", "000667ebe", "000673ebe", "000678ebe", "000690ebe", "000695ebe", "000700ebe", 
    "000701ebe", "000706ebe", "000712ebe", "000725ebe", "000729ebe", "000730ebe", "000734ebe", "000739ebe", "000741ebe", 
    "000744ebe", "000752ebe", "000754ebe", "000755ebe", "000758ebe", "000781ebe", "000789ebe", "000791ebe", "000794ebe", 
    "000797ebe", "000801ebe", "000804ebe", "000823ebe", "000827ebe", "000837ebe", "000839ebe", "000847ebe", "000849ebe", 
    "000858ebe", "000862ebe", "000864ebe", "000868ebe", "000870ebe", "000873ebe", "000874ebe", "000876ebe", "000877ebe", 
    "000879ebe", "000880ebe", "000891ebe", "000901ebe", "000904ebe", "000906ebe", "000914ebe", "000916ebe", "000923ebe", 
    "000924ebe", "000928ebe", "000932ebe", "000934ebe", "000938ebe", "000943ebe", "000947ebe", "000949ebe", "000955ebe", 
    "000956ebe", "000972ebe", "000990ebe", "000991ebe", "000993ebe", "000996ebe", "000997ebe", "000999ebe"]

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