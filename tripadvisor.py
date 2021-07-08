import os
import re
import time
import json
import emoji
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from opencc import OpenCC

def search_for_restaurants(driver, url, wait=2):
    
    print(f"# access url: {url}")
    driver.get(url)
    time.sleep(wait+random.uniform(0, 1))
    
    current_page = 1
    DoNextPage = True
    links = set()
    
    while DoNextPage:
        
        print(f"current page: {current_page}")
        
        # parse restaurant list
        restaurants = driver.find_elements_by_xpath("//div [@id = 'EATERY_SEARCH_RESULTS'] /div /div [@data-test-target = 'restaurants-list'] /div [contains(@data-test, 'list_item')]")
        for restaurant in restaurants:
        
            # skip no review restaurants
            try:                
                no_review = restaurant.find_element_by_xpath(".//span /div /div /div /div /div /span /span /a [contains(., '該餐廳暫無評論，快來寫下第一篇')]")
                if no_review:
                    continue
            except:
                pass
            
            link = restaurant.find_element_by_xpath(".//span /div /div /div /div /span /a")
            link = link.get_attribute('href')
            links.add(link)
            
        try:
            next_page = driver.find_element_by_xpath("//div [contains(@class, 'deckTools')] /div /a [contains(., '下一步')]")
            href = next_page.get_attribute('href')
            print(href)
        except:
            DoNextPage = False
            break
            
        if href == None:
            DoNextPage = False
            break
            
        driver.get(href)
        time.sleep(wait+random.uniform(0, 1))
        current_page += 1
    
    return links

def parse_restaurant(driver, link, wait=2):
    info = {}
    
    cc = OpenCC("s2twp")
    
    print(f"# access link: {link}")
    driver.get(link)
    time.sleep(wait+random.uniform(0, 1))
    
    # parse restaurant info
    name = driver.find_element_by_xpath("//h1 [@data-test-target = 'top-info-header']")
    name = cc.convert(name.text)
    location = driver.find_element_by_xpath("//div [@data-test-target = 'restaurant-detail-info'] /div /span /span /a")
    location = cc.convert(location.text)
    
    info["url"] = link
    info["name"] = name
    info["location"] = location
    
    overviews = driver.find_elements_by_xpath("//div [@data-tab = 'TABS_OVERVIEW'] /div /div")
    # parse total rating    
    overall_rating = overviews[0].find_element_by_xpath(".//div /div /div /span")
    overall_rating = overall_rating.text
    n_ratings = overviews[0].find_element_by_xpath(".//div /div /div /a")
    m = re.match(r'^([0-9]+)', n_ratings.text)
    n_ratings = int(m.groups()[0])
    
    try:
        ratings = overviews[0].find_elements_by_xpath(".//div /div /div /div")
        ratings = [r.find_element_by_xpath(".//span /span").get_attribute("class") for r in ratings]
        ratings = [r.split("_")[-1] for r in ratings]
        ratings = {"food": ratings[0], "service": ratings[1],"price": ratings[2], "env": ratings[3]}
    except:
        ratings = {}
    
    
    info["rating"] = {"overall": overall_rating, "count": n_ratings, "details": ratings}
    
    # parse characteristics
    try:
        sections = overviews[1].find_elements_by_xpath(".//div /div /div /div /div")
        characteristics = [s.text for s in sections]
    except:
        characteristics = []
    
    # parse image links
    try:
        open_images = driver.find_elements_by_xpath("//div [@class ='see_all_count_wrap' and @data-tab = 'TABS_PHOTOS' and @onclick]")
        open_images[-1].click()
        
        time.sleep(wait+random.uniform(0, 1))
        
        # crawl only the latest images (48)
        image_links = []
        
        # image fewer than 5
        image_items = driver.find_elements_by_xpath("//div [@class = 'photos inHeroList'] /div [contains(@class, 'tinyThumb')] /img")
        if len(image_items) == 0:
            # image more than 5
            image_items = driver.find_elements_by_xpath("//div [@class = 'albumGridItem'] /div [@class = 'photoGridImg'] /div [@class = 'fillSquare'] /img")
            
            
        for image_item in image_items:
            image_link = image_item.get_attribute('src')
            if image_link is None:
                image_link = image_item.get_attribute('data-lazyurl')
            #print(image_link)
            image_links.append(image_link)
        
    except:
        image_links = []
        
    driver.back()
    
    print(f"# images: {len(image_links)}")
    info["images"] = image_links
    
    info["characteristics"] = characteristics
    
    # parse reviews and corresponding ratings    
    DoNextPage = True
    current_page = 1
    review_list = []
    
    while DoNextPage:
        
        print(f"current review page: {current_page}")
        
        # parse review list
        reviews = driver.find_elements_by_xpath("//div [@id = 'REVIEWS'] /div /div [contains(@class, 'listContainer')] /div /div [@class = 'review-container']")
        for review in reviews:
            
            review_item = {}
            
            review_sections = review.find_elements_by_xpath(".//div /div /div /div [contains(@class, 'ui_column')]")
            
            # reviewer info
            try:
                user_info = review_sections[0].find_element_by_xpath(".//div /div [@class = 'member_info']")
                user_id = user_info.find_element_by_xpath(".//div /div [contains(@class, 'info_text')] /div")
                user_id = user_id.text
            
                try:
                    user_reviews = user_info.find_element_by_xpath(".//div /div /div[contains(@class, 'reviewerBadge')] /span")
                    m = re.match(r'^([0-9]+)', user_reviews.text.replace(",", ""))
                    user_reviews = int(m.groups()[0])
                except:
                    # translated reviews with different format
                    user_reviews = user_info.find_element_by_xpath(".//div /div[contains(@class, 'memberBadgingNoText')] /span [@class = 'badgetext']")
                    user_reviews = int(user_reviews.text.replace(",", ""))
            
            except:
                
                user_id = "anonymous"
                user_reviews = 1                
            
            review_item["user_id"] = user_id
            review_item["user_reviews"] = user_reviews
            
            # review text and rating
            try:
                rating = review_sections[1].find_element_by_xpath(".//span").get_attribute("class")
                rating = rating.split("_")[-1]
            except:
                rating = ""
            
            try:
                quote = review_sections[1].find_element_by_xpath(".//div [@class = 'quote'] /a /span").text
                quote = emoji.demojize(quote)            
            except:
                quote = ""
                
            try:
                summary = review_sections[1].find_elements_by_xpath(".//div [contains(@data-prwidget-name, 'reviews_text_summary')] /div /p")
                summary = "".join([s.text for s in summary])
                summary = emoji.demojize(summary) 
            except:
                summary = ""
            
            try:
                date = review_sections[1].find_element_by_xpath(".//div [contains(@data-prwidget-name, 'reviews_stay_date')]").text
                date = cc.convert(date)
                m = re.search(r'([0-9]+)\w([0-9]+)\w', date)
                date = list(m.groups())
                date = [int(d) for d in date]
            except:
                date = []
            
            review_item["rating"] = rating
            review_item["quote"] = quote
            review_item["summary"] = summary
            review_item["date"] = date
            
            review_list.append(review_item)
            
        try:
            next_page = driver.find_element_by_xpath("//div [@id = 'REVIEWS'] /div /div [contains(@class, 'listContainer')] /div [@class = 'mobile-more'] /div /div /a [contains(., '下一步')]")
            href = next_page.get_attribute('href')
            print(href)
        except:
            DoNextPage = False
            break
            
        if href == None:
            DoNextPage = False
            break
        
        driver.get(href)
        time.sleep(wait+random.uniform(0, 1))
        current_page += 1        
    
    info["reviews"] = review_list
    
    return info

if __name__ == "__main__":
    
    output_dir = "./data"
    linkpath = os.path.join(output_dir, "tripadvisor_restaurants_beitou.json")
    filepath = os.path.join(output_dir, "tripadvisor_restaurant_infos.json")
    failedpath = os.path.join(output_dir, "tripadvisor_parse_fails.json")
    skip_searching_restaurants = True
    
    url = "https://www.tripadvisor.com.tw/Restaurants-g13806427-Beitou_Taipei.html"    
    driver = webdriver.Edge(EdgeChromiumDriverManager().install())
    
    if not skip_searching_restaurants:
    
        t0 = time.time()    
        links = search_for_restaurants(driver, url)    
        print("Part 1: Time Elapsed: {:.4f}".format(time.time() - t0))
        
        print(f"n_restaurants: {len(links)}")
        with open(linkpath, "w") as write_file:
            json.dump(list(links), write_file)
    
    else:
    
        with open(linkpath, "r") as read_file:
            links = json.load(read_file)
    
    t0 = time.time()
    """
    #links = ["https://www.tripadvisor.com.tw/Restaurant_Review-g13808671-d6952032-Reviews-Le_Cafe_Hotel_Royal_Nikko_Taipei-Zhongshan_District_Taipei.html"]
    links = ["https://www.tripadvisor.com.tw/Restaurant_Review-g13806451-d6133115-Reviews-21_Worker_House_Chilled_Noodles-Datong_Taipei.html"]
    for link in links:
        parse_restaurant(driver, link)
    """
    infos = []
    failed = []
    for link in links:
        try:
            infos.append(parse_restaurant(driver, link))
        except:
            print(f"link failed: {link}")
            failed.append(link)
    print("Part 2: Time Elapsed: {:.4f}".format(time.time() - t0))
    
    print("*"*20)
    print(f"# done: {len(infos)}")
    print(f"# fails: {len(failed)}")
    print("*"*20)
    
    with open(filepath, "w") as write_file:
        json.dump(infos, write_file)
    
    with open(failedpath, "w") as write_file:
        json.dump(failed, write_file)
    
    driver.close()