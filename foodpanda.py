import os
import re
import json
import time
import emoji
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import random

def search_for_restaurants(driver, pos, wait=2):
    x, y = pos
    url = f"https://www.foodpanda.com.tw/restaurants/new?lat={y}&lng={x}&vertical=restaurants"

    print(f"# access url: {url}")
    driver.get(url)
    time.sleep(wait+random.uniform(0, 1))
    
    lenOfPage = driver.execute_script("var lenOfPage=document.body.scrollHeight;return lenOfPage;")
    
    try:
        banner = driver.find_element_by_xpath("//div [@data-testid = 'location-event-banner'] /div /div /span [contains(@class, 'message-text')]")
        print(f"banner: {banner.text}")    
    except:
        pass
    
    restaurant_links = set()
    print(f"# length of page: {lenOfPage}")
    current_position = 1000
    while current_position < lenOfPage:    
         # scroll down
        current_position = lenOfPage - 1000 # fast scroll to end of page
        driver.execute_script(f"window.scrollTo(0, {current_position})")
        time.sleep(wait+random.uniform(0, 1)) # wait for restaurants to load
        # current_position = current_position + 1000        
        lenOfPage = driver.execute_script("var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        print(f"# page progress: {current_position} /{lenOfPage}")
        
        # hits "暫時無營業" and the item contains "即將重新營業"
        elems = driver.find_elements_by_xpath("//li [contains(@data-testid, 'vendor-')] /a /figure /span /span [contains(., '即將重新營業')]")
        if lenOfPage == current_position + 1000 or len(elems) > 0:
           break
    
    # get restaurant links witch is still operating
    list_elems = driver.find_elements_by_xpath("//li [contains(@data-testid, 'vendor-')] /a /figure /span /span [not(contains(., '即將重新營業'))] /ancestor::a")
    for elem in list_elems:
        href = elem.get_attribute('href')
        restaurant_links.add(href)
            
    print(f"# n_restaurants: {len(restaurant_links)}")
        
    return restaurant_links

def parse_restaurant(driver, url, wait=2):
    
    info = {"url": url}
    
    print(f"# access url : {url}")
    driver.get(url)
    time.sleep(wait+random.uniform(0, 1))
    
    # parse vendor info
    elem = driver.find_element_by_xpath("//button [@class = 'vendor-info-main-details'] /h1")
    name = elem.text
    elem = driver.find_element_by_xpath("//span [@id = 'vendor-rating']")
    rating = elem.text
    buget_h = driver.find_elements_by_xpath("//span [@data-testid = 'vendor-buget-symbol-highlighted']")
    buget_n = driver.find_elements_by_xpath("//span [@data-testid = 'vendor-buget-symbol-normal']")
    buget = len(buget_h)*2 + len(buget_n)*1
    elems = driver.find_elements_by_xpath("//li [@data-testid = 'vendor-characteristic-list-item'] /span")
    characteristics = [elem.text for elem in elems]
    elems = driver.find_elements_by_xpath("//div [@class = 'box-flex deal-content'] /p [@data-testid = 'vendor-discount-title']")
    deals = [elem.text for elem in elems]
    
    info["name"] = name
    info["rating"] = rating
    info["buget"] = buget
    info["characteristics"] = characteristics
    info["deals"] = deals
    
    scroll_whole_page(driver, 1000, wait)
    
    # parse menu info
    # 1. parse categories
    categories = driver.find_elements_by_xpath("//div [@class = 'dish-category-section']")
    print(f"# n categories: {len(categories)}")    
    menu = []
    for category in categories:
        menu_category = {}
        # 2. parse category name
        name = category.find_element_by_xpath(".// h2 [@class = 'dish-category-title']").text
        # 3. parse category descriptions
        try:
            description = category.find_element_by_xpath(".// p [@class = 'dish-category-description']").text
        except:
            print(f"# {name} has no category description")
            description = ""
        # 4. parse dishes in category 
        dishes = category.find_elements_by_xpath(".// ul [@class = 'dish-list'] /li [@class = 'dish-card'] /button [@class = 'product-button-overlay']")
        dishes = [dish.get_attribute("aria-label") for dish in dishes]
        
        menu_category["name"] = name
        menu_category["description"] = description
        menu_category["dishes"] = []
        for dish in dishes:
            name, price = dish.split(",")
            found = re.findall(r"\$(.*?)-", price.replace(" ", ""))
            price = int(found[0])
            item = {"name": name, "price": price}
            menu_category["dishes"].append(item)
        menu.append(menu_category)
    
    info["menu"] = menu
    
    # parse review
    driver.execute_script(f"window.scrollTo(0, 0)") # scroll top for button clicking
    info_button = driver.find_element_by_xpath("//button [contains(@aria-label, '餐廳資訊')]")
    info_button.click()
    time.sleep(wait+random.uniform(0, 1))
    review_button = driver.find_element_by_xpath("//button [ @data-testid = 'vendor-info-modal-reviews-btn']")
    review_button.click()
    time.sleep(wait+random.uniform(0, 1))
    # scroll throgh reviews
    scroll_whole_page(driver, 1000, 3)
    review_blocks = driver.find_elements_by_xpath("//div [@data-testid = 'vendor-info-modal-no-review-block']")
    print(f"# n reviews: {len(review_blocks)}")
    
    reviews = []
    for review_block in review_blocks:
        rating = review_block.find_element_by_xpath(".//span [contains(@class, 'rating-label')]")
        elems = review_block.find_elements_by_xpath(".//p [contains(@class, 'cl-neutral-secondary')]")
        date, review = elems
        reviews.append({"rating": rating.text, "date": date.text, "review": emoji.demojize(review.text)})
    
    info["reviews"] = reviews   
    
    return info

def scroll_whole_page(driver, buffer=1000, wait=3):

    lenOfPage = driver.execute_script("var lenOfPage=document.body.scrollHeight;return lenOfPage;")
    print(f"# length of page: {lenOfPage}")    
    current_position = buffer
    while current_position < lenOfPage:    
        # scroll down
        current_position = lenOfPage - buffer # fast scroll to end of page
        driver.execute_script(f"window.scrollTo(0, {current_position})")
        time.sleep(wait+random.uniform(0, 1)) # wait for restaurants to load
        # current_position = current_position + 1000
        lenOfPage = driver.execute_script("var lenOfPage=document.body.scrollHeight;return lenOfPage;")        
        print(f"# page progress: {current_position} /{lenOfPage}")
        
        if lenOfPage == current_position + buffer:
            break
    
   
if __name__ == "__main__":
    
    pos = (121.471591, 25.124800)
    output_dir = "./data"
    filepath = os.path.join(output_dir, "foodpanda.json")
    failedpath = os.path.join(output_dir, "nopanda.json")
    
    driver = webdriver.Edge(EdgeChromiumDriverManager().install())
    
    print("Part 1: crawl nearby restaurants")
    t0 = time.time()
    links = search_for_restaurants(driver, pos)
    print("Part 1: Time Elapsed: {:.4f}".format(time.time() - t0))
    
    print("Part2: crawl each restaurants for infos")
    t0 = time.time()
    infos = []
    failed = []
    for link in links:
        try:
            infos.append(parse_restaurant(driver, link))
        except:
            print(f"link failed: {link}")
            failed.append(link)
    print("Part 2: Time Elapsed: {:.4f}".format(time.time() - t0))
    
    with open(filepath, "w") as write_file:
        json.dump(infos, write_file)
    
    with open(failedpath, "w") as write_file:
        json.dump(failed, write_file)
    
    driver.close()