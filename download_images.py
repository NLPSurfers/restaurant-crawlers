import time
import random
import json
import requests
import base64
import io
from tqdm import tqdm
from fake_useragent import UserAgent

def download(info_path, output_path):
    ua = UserAgent()
    
    with open(info_path, "r") as read_file:
        infos = json.load(read_file)
    
    image_infos = []
    for info in tqdm(infos):
        image_info = {}
        image_info["name"] = info["name"]
        image_info["url"] = info["url"]
        images = []
        for image_url in info["image_url"]:
            
            is_done = False
            image_data = b""
            time.sleep(.2 + random.uniform(.3, 1.3))
            headers = {'User-Agent': ua.random}
            
            while not is_done:
                
                try:
                    response = requests.get(image_url, stream=True, headers=headers, timeout=5)
                except:
                    print("request timeout")
                    continue
                
                if not response.ok:
                    print(response)
                    continue
                    
                for block in response.iter_content(1024):
                    if not block:
                        break
                    image_data += block
                image_data = base64.b64encode(image_data).decode("utf-8")
                images.append(image_data)
                is_done = True
        image_info["images"] = images
        image_infos.append(image_info)
        
    with open(output_path, "w") as write_file:
        json.dump(image_infos, write_file)

if __name__ == "__main__":
    
    info_path = "data/tripadvisor_restaurant_infos.json"
    output_path = "data/tripadvisor_restaurant_images.json"
    
    ua = UserAgent()
    
    with open(info_path, "r") as read_file:
        infos = json.load(read_file)
    
    image_info = {}
    for info in tqdm(infos):
        image_info["name"] = info["name"]
        image_info["url"] = info["url"]
        images = []
        for image_url in info["image_url"]:
            
            is_done = False
            image_data = b""
            time.sleep(.2 + random.uniform(.3, 1.3))
            headers = {'User-Agent': ua.random}
            
            while not is_done:
                
                try:
                    response = requests.get(image_url, stream=True, headers=headers, timeout=5)
                except:
                    print("request timeout")
                    continue
                
                if not response.ok:
                    print(response)
                    continue
                    
                for block in response.iter_content(1024):
                    if not block:
                        break
                    image_data += block
                image_data = base64.b64encode(image_data).decode("utf-8")
                images.append(image_data)
                is_done = True
        image_info["images"] = images
    
    with open(output_path, "w") as write_file:
        json.dump(image_info, write_file)
        