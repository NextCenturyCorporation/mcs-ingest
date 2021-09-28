admin_user_names = [
    "rartiss",
    "bpippin",
    "mtschellenberg",
    "kdrumm",
    "dwetherby"
]


def add_admins(mongoDB):
    collection = mongoDB["users"]
    for admin_user in admin_user_names:
        search_value = {'username': admin_user}
        set_value = {"$set": {'admin': True}}
        collection.update_one(search_value, set_value)

    print("Admin users were successfully added!")
