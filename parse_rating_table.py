import json
from tqdm import tqdm
import numpy as np
import time

if __name__ == "__main__":
    
    json_file = "./data/tripadvisor_restaurant_infos.json"
    parsed_table_file = "./data/rating_table.json"
    
    # load json
    t0 = time.time()
    with open(json_file, "r") as read_file:
        infos = json.load(read_file)
    print("load time: {:.2f} sec".format(time.time() - t0))
    print("# restaurants: {}".format(len(infos)))
    
    # parse unique restuarants
    t0 = time.time()
    urls = [info["url"] for info in infos]
    unique_url = np.unique(urls)
    print("item parse time: {:.2f} sec".format(time.time() - t0))
    print("# unique_url: {}".format(len(unique_url)))
    
    #print(np.argwhere(unique_url == unique_url[3])[0,0].item())
    
    # parse unique users
    t0 = time.time()
    users = [review["user_id"] for info in infos for review in info["reviews"] if review["user_id"]!="anonymous"]
    print("# reviews: {}".format(len(users)))
    unique_users = np.unique(users)
    print("user parse time: {:.2f} sec".format(time.time() - t0))
    print("# users: {}".format(len(unique_users)))
    
    # parse required user_id, item_id and rating
    t0 = time.time()
    rating_table = [{"user_id": np.argwhere(unique_users == review["user_id"])[0,0].item(),
                                "item_id": np.argwhere(unique_url == info["url"])[0,0].item(), 
                                "rating": int(review["rating"])/50} for info in tqdm(infos) for review in info["reviews"] if review["user_id"]!="anonymous"]
    print("reviews parse time: {:.2f} sec".format(time.time() - t0))
    
    with open(parsed_table_file, "w") as write_file:
        json.dump(rating_table, write_file)