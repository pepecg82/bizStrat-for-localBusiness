#!/usr/bin/env python
import os
from random import randint
from pydantic import BaseModel
from crewai.flow import Flow, listen, start, and_
from crews.poem_crew.poem_crew import LocalBoostCrew
from tools.utilities import (
    get_placeID,
    get_place_info,
    get_high_rat_revs,
    get_low_rat_revs,
    get_comps_data,
)
from dotenv import load_dotenv

load_dotenv()
print("Google Maps")
gmaps_api_key = os.environ["GOOGLE_MAPS_KEY"]


class LocalBoostState(BaseModel):
    plc_id: str = ""
    gMapsURI: str = ""
    biz_name: str = ""
    biz_address: str = ""
    biz_rating: str = ""
    biz_rating_count: int = 1
    get_high_rating_reviews: list = []
    get_low_rating_reviews: list = []
    get_competitors_info: list = []
    competitors_high_rating_reviews: list = []
    competitors_low_rating_reviews: list = []
    strat_doc: str = ""
    user_biz_name: str = ""


class LocalBoostFlow(Flow[LocalBoostState]):

    @start()
    def get_placeID(self):
        print(
            "Get Place ID"
        )  # it all strats with the business name, set in utilities.py
        biz_name_user = self.state.user_biz_name
        print("Business Name: ", biz_name_user)
        plc_id = get_placeID(biz_name_user)
        self.state.plc_id = plc_id

    @listen(get_placeID)
    def get_place_info(self):
        print("Get Place Info")
        place_info = get_place_info(gmaps_api_key, self.state.plc_id)
        self.state.gMapsURI = place_info["googleMapsUri"]
        self.state.biz_name = place_info["displayName"]["text"]
        self.state.biz_address = place_info["formattedAddress"]
        self.state.biz_rating = place_info["rating"]
        self.state.biz_rating_count = place_info["userRatingCount"]

    @listen(get_place_info)
    def get_high_rating_reviews(self):
        print("Get High rating reviews")
        get_high_rating_reviews = get_high_rat_revs(self.state.gMapsURI)
        self.state.get_high_rating_reviews = get_high_rating_reviews

    @listen(get_place_info)
    def get_low_rating_reviews(self):
        print("Get Low rating reviews")
        get_low_rating_reviews = get_low_rat_revs(self.state.gMapsURI)
        self.state.get_low_rating_reviews = get_low_rating_reviews

    @listen(get_place_info)
    def get_comps_data(self):
        print("Get Competitors information")
        get_competitors_info = get_comps_data(self.state.gMapsURI, self.state.biz_name)
        self.state.get_competitors_info = get_competitors_info
        # puts all competitors high rating reviews in one list and low rating reviews in another
        for i in range(len(self.state.get_competitors_info)):
            self.state.competitors_high_rating_reviews.extend(
                self.state.get_competitors_info[i]["high_rating_revs"]
            )
            self.state.competitors_low_rating_reviews.extend(
                self.state.get_competitors_info[i]["low_rating_revs"]
            )

    @listen(and_(get_high_rating_reviews, get_low_rating_reviews, get_comps_data))
    def generate_stratDoc(self):
        print("Creating Strategy Document")
        result = (
            LocalBoostCrew()
            .crew()
            .kickoff(
                inputs={
                    "high_rating_reviews": self.state.get_high_rating_reviews,
                    "low_rating_reviews": self.state.get_low_rating_reviews,
                    "comps_high_rating_reviews": self.state.competitors_high_rating_reviews,
                    "comps_low_rating_reviews": self.state.competitors_low_rating_reviews,
                    "biz_name": self.state.biz_name,
                }
            )
        )

        # print("Report Generated", result.raw)
        self.state.strat_doc = result

    @listen(generate_stratDoc)
    def save_stratDoc(self):
        print("Saving Strategy Document")
        # all_task_outputs = self.state.strat_doc.tasks_output
        # for i in range(len(all_task_outputs)):
        # print(i + 1, all_task_outputs[i], "\n")
        with open("stratDoc.md", "w", encoding="utf-8") as f:
            f.write(self.state.strat_doc.raw)

        return self.state.strat_doc


def kickoff(user_biz_name):
    print("kickoff", user_biz_name)
    localBoost_flow = LocalBoostFlow()
    localBoost_flow.state.user_biz_name = user_biz_name
    # poem_flow.context["user_biz_name"] = user_biz_name
    return localBoost_flow.kickoff()


def plot():
    localBoost_flow = LocalBoostFlow()
    localBoost_flow.plot()


if __name__ == "__main__":
    kickoff()
