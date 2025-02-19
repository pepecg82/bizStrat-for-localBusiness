import googlemaps
import pandas as pd
import requests
import os
import json
import csv  # CSV library that helps us save our result
import time
import sqlite3

from selenium import webdriver
from webdriver_manager.chrome import (
    ChromeDriverManager,
)  # Automatically download the web driver binaries
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import (
    By,
)  # Util that helps to select elements with XPath


from dotenv import load_dotenv

load_dotenv()


def get_placeID(place_name):
    """
    Gets placeID from Places API with a business name.
    Note that, if business has more than 1 locations, there's no way to differentiate them.
    Places API will pull the first one.
    The right way to do this is with Places API, but it costs. https://developers.google.com/maps/documentation/places/web-service/op-overview
    """
    # place_name = "Taqueria Morales"  # pass a unique business name, to ensure you get the right business info.

    # gmaps.places retrieves only some of the place details, including the place_id.
    # place_id is what we actually need to search for the place and retrieve all its information.
    gmaps_api_key = os.environ["GOOGLE_MAPS_KEY"]
    gmaps = googlemaps.Client(gmaps_api_key)
    place_details = gmaps.places(place_name)

    # Gets place_id from place_details and stores it in plc_id
    plc_id = place_details["results"][0]["place_id"]

    return plc_id


def get_place_info(api_key, plc_id):
    """
    Gets the following data from place: displayName.text,formattedAddress,rating,userRatingCount,
    #primaryType,types and googleMapsUri.
    You can choose which values to pull in fields field in 'params' below
    Returns a 'data' json
    """

    url = "https://places.googleapis.com/v1/places/" + plc_id

    params = {
        "fields": [
            "displayName.text,formattedAddress,rating,userRatingCount,googleMapsUri"
        ],
        # "fields": '*',
        "key": api_key,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        return data

    else:
        print("Failed to make the request.")

        return 0, 0


def chrome_settings():
    """
    sets Chrome to run headless or headful
    return options
    """
    # change to True if want to run headless
    headless = False

    if headless == True:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")  # Run selenium under headless mode
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
        )
        print("Running Headless Chrome...")
        return options
    else:
        options = Options()
        options.headless = True
        # options.add_experimental_option("prefs", {"intl.accept_languages": "es"}) ###### Uncomment this and the line below if want to have Chrome display website in spanish
        # options.add_argument("--lang=es")
        print("Running Headful Chrome...")
        return options


def get_high_rat_revs(googleMapsUri):
    """
    Gets the top 'num_revs' highest rated reviews. Change the number of reviews in num_revs
    Returns 'highest_rating_reviews' list
    """
    num_revs = 10
    options = chrome_settings()

    # Initialize the driver instance
    driver = webdriver.Chrome(
        options=options, service=ChromeService(ChromeDriverManager().install())
    )

    # Wait up to 10 seconds for a condition to be met before throwing an exception
    wait = WebDriverWait(driver, 10)

    # Gets place URI
    driver.get(googleMapsUri)

    input("Press Enter once you've finished inspecting...")

    # Clicks on 'Reviews'
    wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//*[@id='QA0Szd']/div/div/div[1]/div[2]/div/div[1]/div/div/div[3]/div/div/button[2]/div[2]/div[2]",
            )
        )
    ).click()

    input("Press Enter once you've finished inspecting...")

    # Clicks on 'Sort'
    try:
        menu_bt = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//*[@id='QA0Szd']/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[7]/div[2]/button",
                )
            )
        )
    except:
        menu_bt = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//*[@id='QA0Szd']/div/div/div[1]/div[2]/div/div[1]/div/div/div[4]/div[7]/div[2]/button",
                )
            )
        )
    menu_bt.click()

    # Clicks 'Highest rating' ([3])
    recent_rating_bt = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='action-menu']/div[3]"))
    )
    recent_rating_bt.click()

    time.sleep(2)  # waits 2 seconds for everything to load correctly

    i = 1  #  controls the Xpath for the 'more' button and the actual review, it increments by 4 at the end of each loop
    highest_rating_reviews = []  # initialize list where reviews will be saved in
    for c in range(1, num_revs + 1):

        # more_btn_path - "More" button expands window to see full review. Not all reviews have a "More" button. See 'more_btn_present' below
        more_btn_path = (
            "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[9]/div["
            + str(i)
            + "]/div/div/div[4]/div[2]/div/span[2]/button"
        )
        btn = (By.XPATH, more_btn_path)

        # user_rev_path - This is the actual review
        user_rev_path = (
            "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[9]/div["
            + str(i)
            + "]/div/div/div[4]/div[2]/div/span[1]"
        )

        ##Check if the 'more' button exists
        more_btn_present = len(driver.find_elements(By.XPATH, more_btn_path)) > 0

        # if it does, click on it and get the review text
        if more_btn_present:
            recent_rating_bt = wait.until(EC.element_to_be_clickable(btn))
            recent_rating_bt.click()

        review_locator = (By.XPATH, user_rev_path)
        user_review = wait.until(EC.presence_of_element_located(review_locator))
        user_review = user_review.text
        highest_rating_reviews.append(user_review)

        i += 4

    driver.close()

    return highest_rating_reviews


def get_low_rat_revs(googleMapsUri):
    """
    Gets the top 10 lowest rated reviews. Change the number of reviews in num_revs
    Returns 'lowest_rating_reviews' list
    """
    num_revs = 10
    options = chrome_settings()

    # Initialize the driver instance
    driver = webdriver.Chrome(
        options=options, service=ChromeService(ChromeDriverManager().install())
    )

    # Wait up to 10 seconds for a condition to be met before throwing an exception
    wait = WebDriverWait(driver, 10)

    # Gets place URI
    driver.get(googleMapsUri)

    # Clicks on 'Reviews'
    wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//*[@id='QA0Szd']/div/div/div[1]/div[2]/div/div[1]/div/div/div[3]/div/div/button[2]/div[2]/div[2]",
            )
        )
    ).click()

    input("Press Enter once you've finished inspecting...")

    # Clicks on 'Sort'
    try:
        menu_bt = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//*[@id='QA0Szd']/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[7]/div[2]/button",
                )
            )
        )
    except:
        menu_bt = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//*[@id='QA0Szd']/div/div/div[1]/div[3]/div/div[1]/div/div/div[5]/div[7]/div[2]/button",
                )
            )
        )
    menu_bt.click()

    # Clicks 'Lowest rating' ([4])
    recent_rating_bt = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='action-menu']/div[4]"))
    )
    recent_rating_bt.click()

    time.sleep(2)  # waits 2 seconds for everything to load correctly

    i = 1  #  controls the Xpath for the 'more' button and the actual review, it increments by 4 at the end of each loop
    lowest_rating_reviews = []  # initialize list where reviews will be saved in
    for c in range(1, num_revs + 1):

        # more_btn_path - "More" button expands window to see full review. Not all reviews have a "More" button. See 'more_btn_present' below
        more_btn_path = (
            "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[9]/div["
            + str(i)
            + "]/div/div/div[4]/div[2]/div/span[2]/button"
        )
        btn = (By.XPATH, more_btn_path)

        # user_rev_path - This is the actual review
        user_rev_path = (
            "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[9]/div["
            + str(i)
            + "]/div/div/div[4]/div[2]/div/span[1]"
        )

        ##Check if the 'more' button exists
        more_btn_present = len(driver.find_elements(By.XPATH, more_btn_path)) > 0

        # if it does, click on it and get the review text
        if more_btn_present:
            recent_rating_bt = wait.until(EC.element_to_be_clickable(btn))
            recent_rating_bt.click()

        review_locator = (By.XPATH, user_rev_path)
        user_review = wait.until(EC.presence_of_element_located(review_locator))
        user_review = user_review.text
        lowest_rating_reviews.append(user_review)

        i += 4

    driver.close()

    return lowest_rating_reviews


def get_comps_data(googleMapsUri, og_place):
    """
    Gets 5 competitors highest and lowest rating reviews
    """
    options = chrome_settings()

    # Initialize the driver instance
    driver = webdriver.Chrome(
        options=options, service=ChromeService(ChromeDriverManager().install())
    )

    # Wait up to 10 seconds for a condition to be met before throwing an exception
    wait = WebDriverWait(driver, 5)

    # Gets place URI
    driver.get(googleMapsUri)

    # Finds and click POI Category button
    cat_btn_path = "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button"
    cat_btn_loc = (By.XPATH, cat_btn_path)
    wait.until(EC.element_to_be_clickable((cat_btn_loc))).click()

    time.sleep(5)

    # scroll down to make sure 5 POIs are shown
    div_to_scroll = driver.find_element(
        By.XPATH,
        "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]",
    )
    driver.execute_script("arguments[0].scrollBy(0,500)", div_to_scroll)

    # Initialize list to save competitors data
    competitors_all_data = []
    total_poi_collected = 0
    # define how many competitors you want to get reviews from. Below you will be able to set how many reviews you want from each competitor. The more you get, the better the
    # insights you'll get. Note that more competitors and reviews will increase input tokens and overall processing time
    number_of_competitors = 5

    i = 3

    while total_poi_collected < number_of_competitors:

        print(total_poi_collected + 1)

        if total_poi_collected == 0:
            time.sleep(4)

        # Gets competitor card in order to click it to display full information panel. Will use later
        comp_card = (
            By.XPATH,
            "//*[@id='QA0Szd']/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]/div["
            + str(i)
            + "]/div/a",
        )

        # Gets the name of the competitor
        comp_name_loc = (
            By.XPATH,
            "//*[@id='QA0Szd']/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]/div["
            + str(i)
            + "]/div/div[2]/div[4]/div[1]/div/div/div[2]/div[1]/div[2]",
        )
        comp_name = wait.until(EC.presence_of_element_located(comp_name_loc)).text

        # Gets the total number of reviews of the competitor
        reviews_total_loc = (
            By.XPATH,
            "//*[@id='QA0Szd']/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]/div["
            + str(i)
            + "]/div/div[2]/div[4]/div[1]/div/div/div[2]/div[3]/div/span[2]/span/span[2]",
        )
        reviews_total = wait.until(
            EC.presence_of_element_located(reviews_total_loc)
        ).text
        reviews_total = reviews_total.replace("(", "")
        reviews_total = reviews_total.replace(",", "")
        reviews_total = reviews_total.replace(")", "")

        # Checks if the competitor is the original business; if it is, discard it and move to the next
        if comp_name == og_place:
            i += 2
            continue
        # We want businesses with 20 or more reviews, if competitor has less than 20, discard it and move to the next
        elif int(reviews_total) < 20:
            i += 2
            continue
        else:
            # Clicks on competitor card (comp_card) in order to show menu to the right
            click_elem_loc = wait.until(EC.element_to_be_clickable((comp_card)))
            driver.execute_script("arguments[0].click()", click_elem_loc)

            time.sleep(4)

            # Gets competitor address
            comp_address = (By.XPATH, "//div[contains(@class, 'Io6YTe')]")
            comp_address = wait.until(EC.presence_of_element_located(comp_address)).text
            # print("Competitor Address: ", comp_address)

            # Gets competitor rating
            rating_comp_loc = (By.XPATH, "//div[@class='F7nice ']/span[1]/span[1]")
            rating_comp = wait.until(
                EC.presence_of_element_located(rating_comp_loc)
            ).text
            # print("Competitor Rating: ", rating_comp)

            # Clicks on "share"
            share_btn = (
                By.XPATH,
                "//*[@id='QA0Szd']/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[4]/div[5]/button",
            )
            wait.until(EC.element_to_be_clickable((share_btn))).click()

            time.sleep(1.5)

            # Gets competitor URI from modal
            uri_comp_loc = (
                By.XPATH,
                "//*[@id='modal-dialog']/div/div[2]/div/div[2]/div/div/div/div[3]/div[2]/div[2]/input",
            )
            uri_comp = wait.until(
                EC.presence_of_element_located(uri_comp_loc)
            ).get_attribute("value")

            # Closes modal
            close_mod_btn = (
                By.XPATH,
                "//*[@id='modal-dialog']/div/div[2]/div/button/span",
            )
            wait.until(EC.element_to_be_clickable((close_mod_btn))).click()

            # Saves competitor data
            new_comp_data = {
                "comp_name": comp_name,
                "address_comp": comp_address,
                "rating_comp": rating_comp,
                "reviews_total": reviews_total,
                "uri_comp": uri_comp,
            }

            #####################################################################
            # Saves competitors highest rating reviews
            #####################################################################

            # Clicks on "Reviews"
            comp_revs = (
                By.XPATH,
                "//*[@id='QA0Szd']/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[3]/div/div/button[2]",
            )
            wait.until(EC.element_to_be_clickable((comp_revs))).click()

            time.sleep(2)

            # Click on 'Sort'
            try:
                menu_bt = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//*[@id='QA0Szd']/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]/div[7]/div[2]/button",
                        )
                    )
                )
            except:
                menu_bt = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//*[@id='QA0Szd']/div/div/div[1]/div[3]/div/div[1]/div/div/div[5]/div[7]/div[2]/button",
                        )
                    )
                )
            menu_bt.click()

            # Clicks on Highest rating ([3])
            highest_rating_bt = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[2]/div[3]/div[3]/div[1]/div[3]")
                )
            )
            highest_rating_bt.click()

            time.sleep(3)

            count = 1
            new_comp_highest_revs = []
            number_of_reviews = 4  # set how many reviews you want from each competitor. The more you get, the better the
            # insights you'll get. Note that more reviews will increase input tokens and overall processing time

            # this 'for' goes through the first 5 highest rating reviews
            for c in range(1, number_of_reviews):

                # more_btn_path - "More" button expands window to see full review. Not all reviews have a "More" button. See "try" below
                more_btn_path = (
                    "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]/div[9]/div["
                    + str(count)
                    + "]/div/div/div[4]/div[2]/div/span[2]/button"
                )
                btn = (By.XPATH, more_btn_path)

                # user_rev_path - This is the actual review
                user_rev_path = (
                    "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]/div[9]/div["
                    + str(count)
                    + "]/div/div/div[4]/div[2]/div/span"
                )

                # Check if the "More" button exists
                more_btn_present = (
                    len(driver.find_elements(By.XPATH, more_btn_path)) > 0
                )

                # if it does, click on it and get the review text
                if more_btn_present:
                    recent_rating_bt = wait.until(EC.element_to_be_clickable(btn))
                    recent_rating_bt.click()

                review_locator = (By.XPATH, user_rev_path)
                try:
                    user_review = wait.until(
                        EC.presence_of_element_located(review_locator)
                    )
                except:
                    continue
                user_review = user_review.text

                count += 4

                # Stores review in a competitor-specific list
                # at the end, new_comp_highest_revs will only have 5 reviews
                new_comp_highest_revs.append(user_review)

            # Updates 'new_comp_data' created above, adds a new item 'high_rating_revs', with the previously collected reviews 'new_comp_highest_revs'
            new_comp_data.update({"high_rating_revs": new_comp_highest_revs})

            #####################################################################
            # Saves competitors lowest rating reviews
            #####################################################################

            # Clicks on 'Sort'
            try:
                menu_bt = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//*[@id='QA0Szd']/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]/div[7]/div[2]/button",
                        )
                    )
                )
            except:
                menu_bt = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//*[@id='QA0Szd']/div/div/div[1]/div[3]/div/div[1]/div/div/div[5]/div[7]/div[2]/button",
                        )
                    )
                )
            menu_bt.click()

            # Clicks on lowest rating ([4])
            lowest_rating_bt = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[2]/div[3]/div[3]/div[1]/div[4]")
                )
            )
            lowest_rating_bt.click()

            time.sleep(3)

            count = 1
            new_comp_lowest_revs = []

            # this 'for' goes through the first 5 lowest rating reviews
            for c in range(1, number_of_reviews):

                # more_btn_path - "More" button expands window to see full review. Not all reviews have a "More" button. See "try" below
                more_btn_path = (
                    "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]/div[9]/div["
                    + str(count)
                    + "]/div/div/div[4]/div[2]/div/span[2]/button"
                )
                btn = (By.XPATH, more_btn_path)

                # user_rev_path - This is the actual review
                user_rev_path = (
                    "/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]/div[9]/div["
                    + str(count)
                    + "]/div/div/div[4]/div[2]/div/span"
                )

                # Check if the "More" button exists
                more_btn_present = (
                    len(driver.find_elements(By.XPATH, more_btn_path)) > 0
                )

                # if it does, click on it and get the review text
                if more_btn_present:
                    recent_rating_bt = wait.until(EC.element_to_be_clickable(btn))
                    recent_rating_bt.click()

                review_locator = (By.XPATH, user_rev_path)
                try:
                    user_review = wait.until(
                        EC.presence_of_element_located(review_locator)
                    )
                except:
                    continue
                user_review = user_review.text

                count += 4

                # Stores review in a competitor-specific list
                # at the end, new_comp_highest_revs will only have 5 reviews
                new_comp_lowest_revs.append(user_review)

            # Updates 'new_comp_data' created above, adds a new item 'high_rating_revs', with the previously collected reviews 'new_comp_highest_revs'
            new_comp_data.update({"low_rating_revs": new_comp_lowest_revs})

            # Adds new competitor data to 'competitors_all_data'
            competitors_all_data.append(new_comp_data)

            total_poi_collected += 1

        i += 2

    driver.close()

    return competitors_all_data
