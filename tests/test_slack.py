import json
import unittest
from semantic_search_engine.slack.slack import (
    extract_zip, 
    users, 
    channels,
    channel_messages,
    channel_dir,
    all_channels
)
import os
import shutil
import requests
from io import BytesIO
import shelve

class TestSlack(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        response = requests.get("https://github.com/iCog-Labs-Dev/slack-export-data/archive/refs/heads/main.zip")
        extract_zip(BytesIO(response.content))
        os.rename("temp/slack-export-data-main", "temp/slack-export-data")
        shelve.open("shelve", "c").close()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree("temp")
        os.remove("shelve")

    def test_extract_zip(self):
        temp_exists = os.path.exists("temp")
        self.assertTrue(temp_exists, "The temp path does not exist")

        if temp_exists:  # check if the directory is not empty
            self.assertNotEqual(os.listdir("temp"), [])

    def test_users(self):
        user = {
            "id" : "U05CQ93C3FZ",  
            "name" : "tollanberhanu",
            "is_bot" : False,
            "real_name" : "Tollan",
            "avatar" : "https://secure.gravatar.com/avatar/dd543bd963dd804efd74338821d2f1f1.jpg?s=192&d=https%3A%2F%2Fa.slack-edge.com%2Fdf10d%2Fimg%2Favatars%2Fava_0009-192.png",
            "email" : "tollanberhanu@gmail.com",
        } 
        users()
        make_dict_test(self, user)

    def test_channels(self):
        channel = {
            "id" : "C05D1SE01B7",
            "name" : "random",
            "members" : [
                "U05CQ93C3FZ",
                "U05D1SQDNSH",
                "U05D4M7RGQ3",
                "U05DHDPL4FK"
            ],
            "purpose" : {
                "value": "This channel is for... well, everything else. It’s a place for team jokes, spur-of-the-moment ideas, and funny GIFs. Go wild!",
                "creator": "U05DHDPL4FK",
                "last_set": 1687165577
            },
            "type" : "public",
        }
        channels()
        channel_id = channel["id"]
        make_dict_test(self, channel)

    def test_channel_messages(self):
        test_channel_file = os.getcwd() + '/temp/slack-export-data/general/2023-06-19.json'
        channel_id = "C05D77W3N76"

        with open(test_channel_file, "r") as json_file:
            objs = json.load(json_file)

        channels()  # upload channels
        results = channel_messages(channel_id, objs)

        make_message_test(self, objs, results)


    def test_channel_dir(self):
        test_channel_dir = os.getcwd() + '/temp/slack-export-data/general/'
        channel_id = "C05D77W3N76"

        objs = []
        for files in os.listdir(test_channel_dir):
            with open(test_channel_dir + files, "r") as json_file:
                objs += json.load(json_file)
        

        channels()  # set up channels
        results = channel_dir(channel_id)

        make_message_test(self, objs, results)

    def test_all_channels(self):
        test_dir = os.getcwd() + "/temp/slack-export-data/"

        temp_walk = os.walk(test_dir)
        next(temp_walk)
        objs = []
        for folder, subfolders, files in temp_walk:
            for file in files:
                with open(folder + "/" + file) as json_file:
                    objs += json.load(json_file)

        channels()  # set up channels
        results = all_channels()

        make_message_test(self, objs, results)

# HELPER FUNCTIONS
def make_dict_test(slf, dict_to_test):
    _id = dict_to_test["id"]
    for k,v in dict_to_test.items():
        with shelve.open("shelve", "r") as d:
            slf.assertEqual(d.get(_id)[k], v)

def make_message_test(slf, msgs, results):
        msgs = list(filter(lambda x : (x.get("client_msg_id") != None), msgs))
        
        for i,msg in enumerate(msgs):
            result = results[i]
            
            if msg.get("client_msg_id", False): 
                slf.assertEqual(result["text"], msg["text"], "text dont match")


