#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 18 16:21:57 2018
@author: zihua.mai
"""

from flask import Flask, request
import pprint
from datetime import datetime
import dateutil.parser
import requests
import json

names = {"70B3D5499CAB57AB": "desk_lidar",
"70B3D5499D470B81": "desk_infrared",
"70B3D5499BF6D450": "desk_ultrasonic"}

app = Flask(__name__)
@app.route("/", methods=['POST'])
def index():
    payload,deveui = getpayload()
    data = query_latest("desk", names[deveui]) #query to kibana to get the last payload

    parsed_data = parse(payload,data) #process the data
    updatedata(parsed_data, deveui) #post the data

    return("SUCCESS")


def getpayload():

    data = json.loads(request.data)

    payload = data["DevEUI_uplink"]["payload_hex"]
    deveui = data["DevEUI_uplink"]["DevEUI"]

    return(payload,deveui)


def parse(payload, data):
    total_mins = 0
    usage = 0
    height = int(payload, 16)

    if ( height >= 80): #getting the current state
        state = 'up'
        #error handling using try when no data in kibana initially
        #KEVIN GLASSON APPROVED
        try:
            if (data['_source']['status'] == 'down'): #current state is not equal to last state
                last = dateutil.parser.parse(data['_source']['time'])
                #print("LAST_TYPE {}".format(type(last)))
                now = dateutil.parser.parse(datetime.utcnow().isoformat())
                #print("NOW_TYPE {}".format(type(now)))
                durationn = now - last
                total_mins = durationn.total_seconds() / 60
                usage = data['_source']['uptime']
                print(total_mins)


            if (data['_source']['status'] == 'up'): #current state equal to previous state
                last = dateutil.parser.parse(data['_source']['time'])
                # print("LAST_TYPE {}".format(type(last)))
                now = dateutil.parser.parse(datetime.utcnow().isoformat())
                # print("NOW_TYPE {}".format(type(now)))
                durationn = now - last
                usage = durationn.total_seconds() / 60 +  data['_source']['uptime']

                total_mins = data['_source']['time_in_last_state']
        except TypeError:
            print("first time use")
            total_mins = 0


    #getting the current state, compare the current state with last state and determine the duration of up time
    if (height < 80):
        state = 'down'
        try:
            if (data['_source']['status'] == 'up'): #current state is not equal to last state
                last = dateutil.parser.parse(data['_source']['time'])
                # print("LAST_TYPE {}".format(type(last)))
                now = dateutil.parser.parse(datetime.utcnow().isoformat())
                # print("NOW_TYPE {}".format(type(now)))
                durationn = now - last
                # print("DURATION: {}".format(durationn))
                total_mins = durationn.total_seconds() / 60
                usage = data['_source']['uptime'] + total_mins

                print(total_mins)

            if (data['_source']['status'] == 'down'): #current state equal to previous state
                total_mins = data['_source']['time_in_last_state']
                usage = data['_source']['uptime']
        except TypeError:
            print("first time use")
            total_mins = 0




    #function to reset uptime
    try:
        now = dateutil.parser.parse(datetime.utcnow().isoformat())
        last = dateutil.parser.parse(data['_source']['time'])
        
        if (now.date() != last.date()):
            uptime = 0
    except TypeError:
        print("first time usaage")

    #putting all the data into dictionary
    parsed_data = {
            "time": datetime.utcnow().isoformat(),
            "height":int(payload, 16),
            "status": state,
            "time_in_last_state": total_mins,
            "uptime": usage
            }
    return (parsed_data)


def updatedata(parsed_data,deveui):

    url = "http://10.0.10.173:9200/desk/{}".format(names[deveui])

    #payload = "{\"height\": 70,\n\"time\": \"2018-07-18T07:36:29.894992\"}\n"
    headers = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache",
            }

    response = requests.request("POST", url, data=json.dumps(parsed_data), headers=headers)

    print(response.text)

def query_latest(index, unique):
    print("index: {} \nunique: {}".format(index, unique))
    """ Return the latest document for each unique item in the index.

    Arguments:
        index -- the index to search
        unique -- the field that will be unique
        field -- check that this field exists
    """

    q = {
        "query": {
            "bool":{
                "must":[
                    {"match":{"_type":unique}}]
            }
        },
        "size": 0,
        "aggs": {
            "uniq_type": {
                "terms": {
                    "field": "_type",
                    "size": 100000
                },
                "aggs": {
                    "latest": {
                        "top_hits": {
                            "size": 1,
                            "sort": [{
                                "time": {
                                    "order": "desc"
                                }
                            }]
                        }
                    }
                }
            }
        }
    }

    headers = {
        'Content-Type': "application/json",
        'Cache-Control': "no-cache"
    }

    url = "http://10.0.10.173:9200/{}/_search".format(index.lower())

    response = requests.request("POST", url, json=q, headers=headers)
    if (len(response.json()["aggregations"]["uniq_type"]["buckets"]) == 0):
        return None
    else:
        return (response.json()["aggregations"]["uniq_type"]["buckets"][0]["latest"]["hits"]["hits"][0])
