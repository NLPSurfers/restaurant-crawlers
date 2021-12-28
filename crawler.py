import os
import json
from tripadvisor import crawl
from download_images import download

def combine(info_path, image_path, output_path):
    with open(info_path, "r") as read_file:
        infos = json.load(read_file)
    with open(image_path, "r") as read_file:
        images = json.load(read_file)
        
    url2images = {image["url"]: image["images"] for image in images}
    
    for info in infos:
        info["images"] = url2images[info["url"]]
    
    with open(output_path, "w") as write_file:
        json.dump(infos, write_file)
    
class TripAdvisorCrawler:

    def __init__(self, output_dir, skip_searching_restaurants=False):
        self.output_dir = output_dir
        self.link_path = os.path.join(output_dir, "tripadvisor_restaurants_beitou.json")
        self.info_path = os.path.join(output_dir, "tripadvisor_restaurant_infos.json")
        self.failed_path = os.path.join(output_dir, "tripadvisor_parse_fails.json")
        self.image_path = os.path.join(output_dir, "tripadvisor_restaurant_images.json")
        self.output_path = os.path.join(output_dir, "tripadvisor_restaurant_info_images.json")
        self.url = "https://www.tripadvisor.com.tw/Restaurants-g13806427-Beitou_Taipei.html"    
        self.skip_searching_restaurants = skip_searching_restaurants
        
    def update(self):
        crawl(self.url, self.link_path, self.info_path, self.failed_path, self.skip_searching_restaurants)
        download(self.info_path, self.image_path)
        combine(self.info_path, self.image_path, self.output_path)
        
if __name__ == "__main__":
    crawler = TripAdvisorCrawler("./data")
    crawler.update()