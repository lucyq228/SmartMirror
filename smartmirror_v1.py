# smartmirror.py
# requirements
# requests, feedparser, traceback, Pillow

from tkinter import *  # python2 Tkinter
import locale
import threading
import time
import requests
import json
import traceback
# import feedparser
from PIL import Image, ImageTk
from contextlib import contextmanager
import time
import tkinter as tk
from tkinter import ttk  # progress bar
import datetime  # to show Pomodoro time only for today
#for google calendar
import pickle
import re
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

LOCALE_LOCK = threading.Lock()

ui_locale = ''  # e.g. 'fr_FR' fro French, '' as default
time_format = 12  # 12 or 24
date_format = "%b %d, %Y"  # check python doc for strftime() for options
news_country_code = 'us'
weather_api_token = 'a8bcdef20fcaedb10565c6fa9e6f921a'  # create account at https://darksky.net/dev/
weather_lang = 'en'  # see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_unit = 'us'  # see https://darksky.net/dev/docs/forecast for full list of unit parameters values
location_api_token = 'bfed3d1a918eb13cda098a760d493ea9'  # ipstack.com
latitude = None  # '41.6194' #None Set this if IP location lookup does not work for you (must be a string)
longitude = None  # '-87.8423' #None Set this if IP location lookup does not work for you (must be a string)
# xlarge_text_size = 58 #94 not used
large_text_size = 48  # 42 used for clock
medium_text_size = 28  # 28 used for temperature
small_text_size = 20  # 16 used for day
xsmall_text_size = 18  # 12 quote, time tracking, current temp in text
xxsmall_text_size = 13  # 12 temp forecast, timer,quote bttn

pic_location = "/home/pi/SmartMirror2.0/assets/"


# /home/pi/SmartMirror/assets/


# New hide mouse after 1 sec no movement
# import subprocess
# unclutter = subprocess.Popen(['unclutter','-idle', '1'])

@contextmanager
def setlocale(name):  # thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)


# maps open weather icons to
# icon reading is not impacted by the 'lang' parameter
icon_lookup = {
    'clear-day': pic_location + "Sun.png",  # clear sky day
    'wind': pic_location + "Wind.png",  # wind
    'cloudy': pic_location + "Cloud.png",  # cloudy day
    'partly-cloudy-day': pic_location + "PartlySunny.png",  # partly cloudy day
    'rain': pic_location + "Rain.png",  # rain day
    'snow': pic_location + "Snow.png",  # snow day
    'snow-thin': pic_location + "Snow.png",  # sleet day
    'fog': pic_location + "Haze.png",  # fog day
    'clear-night': pic_location + "Moon.png",  # clear sky night
    'partly-cloudy-night': pic_location + "PartlyMoon.png",  # scattered clouds night
    'thunderstorm': pic_location + "Storm.png",  # thunderstorm
    'tornado': pic_location + "Tornado.png",  # tornado
    'hail': pic_location + "Hail.png"  # hail
}


class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')

        self.clockFrm = Frame(self, bg="black")
        self.clockFrm.pack(side=TOP, anchor=N)  # anchor=W
        self.clockFrm2 = Frame(self.clockFrm, bg="black")
        self.clockFrm2.pack(side=RIGHT, anchor=N)
        # self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', large_text_size), fg="white", bg="black") #xlarge_text_size
        # self.temperatureLbl.pack(side=LEFT, anchor=N)
        # self.iconLbl = Label(self.degreeFrm, bg="black")
        # self.iconLbl.pack(side=LEFT, anchor=N, padx=20)

        # initialize time label
        self.time1 = ''
        # self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        # self.timeLbl.pack(side=TOP, anchor=E)
        self.timeLbl = Label(self.clockFrm, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=LEFT, anchor=N)

        # initialize day of week
        self.day_of_week1 = ''
        # self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white", bg="black")
        # self.dayOWLbl.pack(side=TOP, anchor=E)
        self.dayOWLbl = Label(self.clockFrm2, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white",
                              bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=S)  # anchor=E
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self.clockFrm2, text=self.date1, font=('Helvetica', small_text_size), fg="white",
                             bg="black")
        self.dateLbl.pack(side=TOP, anchor=S)  # side=TOP, anchor=E
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p')  # hour in 12h format
            else:
                time2 = time.strftime('%H:%M')  # hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timeLbl.after(200, self.tick)


class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = ''
        self.currently = ''
        self.icon = ''
        self.icon_d1 = ''
        self.icon_d2 = ''
        self.icon_d3 = ''
        self.icon_d4 = ''
        self.day_d1 = ''
        self.day_d2 = ''
        self.day_d3 = ''
        self.day_d4 = ''

        self.degreeFrm = Frame(self, bg="black")
        self.degreeFrm.pack(side=TOP, anchor=W)
        self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', medium_text_size), fg="white",
                                    bg="black")  # large_text_size #xlarge_text_size
        self.temperatureLbl.pack(side=LEFT, anchor=N)
        self.iconLbl = Label(self.degreeFrm, bg="black")
        self.iconLbl.pack(side=LEFT, anchor=N, padx=5)  # padx=20
        self.currentlyLbl = Label(self, font=('Helvetica', xxsmall_text_size), fg="white",
                                  bg="black")  # medium_text_size
        self.currentlyLbl.pack(side=TOP, anchor=W, padx=5)  # side=TOP
        # self.forecastLbl = Label(self, font=('Helvetica', xsmall_text_size), fg="white", bg="black") #small_text_size
        # self.forecastLbl.pack(side=TOP, anchor=W)
        self.locationLbl = Label(self, font=('Helvetica', xxsmall_text_size), fg="white", bg="black")  # small_text_size
        self.locationLbl.pack(side=TOP, anchor=W)

        # new next four days
        self.degreeFrm_d4 = Frame(self.degreeFrm, bg="black")
        self.degreeFrm_d4.pack(side=RIGHT, anchor=N, padx=20)
        self.dayLbl_d4 = Label(self.degreeFrm_d4, font=('Helvetica', xxsmall_text_size), fg="white",
                               bg="black")  # medium_text_size
        self.dayLbl_d4.pack(side=TOP, anchor=N)
        self.iconLbl_d4 = Label(self.degreeFrm_d4, bg="black")
        self.iconLbl_d4.pack(anchor=N, padx=5)  # side=LEFT, padx=20
        self.temperatureLbl_d4_H = Label(self.degreeFrm_d4, font=('Helvetica', xxsmall_text_size), fg="white",
                                         bg="black")  # large_text_size #xlarge_text_size
        self.temperatureLbl_d4_H.pack(anchor=N)  # side=LEFT,
        self.temperatureLbl_d4_L = Label(self.degreeFrm_d4, font=('Helvetica', xxsmall_text_size), fg="white",
                                         bg="black")  # large_text_size #xlarge_text_size
        self.temperatureLbl_d4_L.pack(anchor=N)  # side=LEFT,

        self.degreeFrm_d3 = Frame(self.degreeFrm, bg="black")
        self.degreeFrm_d3.pack(side=RIGHT, anchor=N, padx=20)
        self.dayLbl_d3 = Label(self.degreeFrm_d3, font=('Helvetica', xxsmall_text_size), fg="white",
                               bg="black")  # medium_text_size
        self.dayLbl_d3.pack(side=TOP, anchor=N)
        self.iconLbl_d3 = Label(self.degreeFrm_d3, bg="black")
        self.iconLbl_d3.pack(anchor=N, padx=5)  # side=LEFT, padx=20
        self.temperatureLbl_d3_H = Label(self.degreeFrm_d3, font=('Helvetica', xxsmall_text_size), fg="white",
                                         bg="black")  # large_text_size #xlarge_text_size
        self.temperatureLbl_d3_H.pack(anchor=N)  # side=LEFT,
        self.temperatureLbl_d3_L = Label(self.degreeFrm_d3, font=('Helvetica', xxsmall_text_size), fg="white",
                                         bg="black")  # large_text_size #xlarge_text_size
        self.temperatureLbl_d3_L.pack(anchor=N)  # side=LEFT,

        self.degreeFrm_d2 = Frame(self.degreeFrm, bg="black")
        self.degreeFrm_d2.pack(side=RIGHT, anchor=N, padx=20)
        self.dayLbl_d2 = Label(self.degreeFrm_d2, font=('Helvetica', xxsmall_text_size), fg="white",
                               bg="black")  # medium_text_size
        self.dayLbl_d2.pack(side=TOP, anchor=N)
        self.iconLbl_d2 = Label(self.degreeFrm_d2, bg="black")
        self.iconLbl_d2.pack(anchor=N, padx=5)  # side=LEFT, padx=20
        self.temperatureLbl_d2_H = Label(self.degreeFrm_d2, font=('Helvetica', xxsmall_text_size), fg="white",
                                         bg="black")  # large_text_size #xlarge_text_size
        self.temperatureLbl_d2_H.pack(anchor=N)  # side=LEFT,
        self.temperatureLbl_d2_L = Label(self.degreeFrm_d2, font=('Helvetica', xxsmall_text_size), fg="white",
                                         bg="black")  # large_text_size #xlarge_text_size
        self.temperatureLbl_d2_L.pack(anchor=N)  # side=LEFT,

        self.degreeFrm_d1 = Frame(self.degreeFrm, bg="black")
        self.degreeFrm_d1.pack(side=RIGHT, anchor=W, padx=20)
        self.dayLbl_d1 = Label(self.degreeFrm_d1, font=('Helvetica', xxsmall_text_size), fg="white",
                               bg="black")  # medium_text_size
        self.dayLbl_d1.pack(side=TOP, anchor=N)
        self.iconLbl_d1 = Label(self.degreeFrm_d1, bg="black")
        self.iconLbl_d1.pack(anchor=N, padx=5)  # side=LEFT, padx=20
        self.temperatureLbl_d1_H = Label(self.degreeFrm_d1, font=('Helvetica', xxsmall_text_size), fg="white",
                                         bg="black")  # large_text_size #xlarge_text_size
        self.temperatureLbl_d1_H.pack(anchor=N)  # side=LEFT,
        self.temperatureLbl_d1_L = Label(self.degreeFrm_d1, font=('Helvetica', xxsmall_text_size), fg="white",
                                         bg="black")  # large_text_size #xlarge_text_size
        self.temperatureLbl_d1_L.pack(anchor=N)  # side=LEFT,

        self.get_weather()

    def get_ip(self):
        try:
            ip_url = "http://jsonip.com/"
            req = requests.get(ip_url)
            ip_json = json.loads(req.text)
            return ip_json['ip']
        except Exception as e:
            traceback.print_exc()
            return "Error: %s. Cannot get ip." % e

    def get_weather(self):
        try:

            if latitude is None and longitude is None:
                # get location
                # location_req_url = "http://freegeoip.net/json/%s" % self.get_ip()
                location_req_url = "http://api.ipstack.com/%s?access_key=%s" % (self.get_ip(), location_api_token)
                r = requests.get(location_req_url)
                location_obj = json.loads(r.text)

                lat = location_obj['latitude']
                lon = location_obj['longitude']

                location2 = "%s, %s" % (location_obj['city'], location_obj['region_code'])

                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (
                    weather_api_token, lat, lon, weather_lang, weather_unit)
            else:
                location2 = ""
                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (
                    weather_api_token, latitude, longitude, weather_lang, weather_unit)

            r = requests.get(weather_req_url)
            weather_obj = json.loads(r.text)

            degree_sign = u'\N{DEGREE SIGN}'
            temperature2 = "%s%s" % (str(int(weather_obj['currently']['temperature'])), degree_sign)
            temperature2_d1_H = "%s%s" % (str(int(weather_obj['daily']['data'][1]['temperatureHigh'])), degree_sign)
            temperature2_d2_H = "%s%s" % (str(int(weather_obj['daily']['data'][2]['temperatureHigh'])), degree_sign)
            temperature2_d3_H = "%s%s" % (str(int(weather_obj['daily']['data'][3]['temperatureHigh'])), degree_sign)
            temperature2_d4_H = "%s%s" % (str(int(weather_obj['daily']['data'][4]['temperatureHigh'])), degree_sign)
            temperature2_d1_L = "%s%s" % (str(int(weather_obj['daily']['data'][1]['temperatureLow'])), degree_sign)
            temperature2_d2_L = "%s%s" % (str(int(weather_obj['daily']['data'][2]['temperatureLow'])), degree_sign)
            temperature2_d3_L = "%s%s" % (str(int(weather_obj['daily']['data'][3]['temperatureLow'])), degree_sign)
            temperature2_d4_L = "%s%s" % (str(int(weather_obj['daily']['data'][4]['temperatureLow'])), degree_sign)
            currently2 = weather_obj['currently']['summary']
            forecast2 = weather_obj["hourly"]["summary"]

            # next 4 days
            day_d1_2 = weather_obj["daily"]['data'][1]["time"]
            day_d1_2 = time.ctime(day_d1_2)[:3]
            day_d2_2 = weather_obj["daily"]['data'][2]["time"]
            day_d2_2 = time.ctime(day_d2_2)[:3]
            day_d3_2 = weather_obj["daily"]['data'][3]["time"]
            day_d3_2 = time.ctime(day_d3_2)[:3]
            day_d4_2 = weather_obj["daily"]['data'][4]["time"]
            day_d4_2 = time.ctime(day_d4_2)[:3]

            icon_id = weather_obj['currently']['icon']
            icon2 = None

            if icon_id in icon_lookup:
                icon2 = icon_lookup[icon_id]

            if icon2 is not None:
                if self.icon != icon2:
                    self.icon = icon2
                    image = Image.open(icon2)
                    image = image.resize((60, 60), Image.ANTIALIAS)  # image.resize((100, 100)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)
                    self.iconLbl.config(image=photo)
                    self.iconLbl.image = photo

                    # new
                    # self.iconLbl_d2.config(image=photo)
                    # self.iconLbl_d2.image = photo
            else:
                # remove image
                self.iconLbl.config(image='')

                # new
                # self.iconLbl_d2.config(image='')

            # new next 4 days
            icon_id_d1 = weather_obj["daily"]['data'][1]["icon"]
            icon2_d1 = None
            icon_id_d2 = weather_obj["daily"]['data'][2]["icon"]
            icon2_d2 = None
            icon_id_d3 = weather_obj["daily"]['data'][3]["icon"]
            icon2_d3 = None
            icon_id_d4 = weather_obj["daily"]['data'][4]["icon"]
            icon2_d4 = None

            if icon_id_d1 in icon_lookup:
                icon2_d1 = icon_lookup[icon_id_d1]
            if icon_id_d2 in icon_lookup:
                icon2_d2 = icon_lookup[icon_id_d2]
            if icon_id_d3 in icon_lookup:
                icon2_d3 = icon_lookup[icon_id_d3]
            if icon_id_d4 in icon_lookup:
                icon2_d4 = icon_lookup[icon_id_d4]

            if icon2_d1 is not None:
                if self.icon_d1 != icon2_d1:
                    self.icon_d1 = icon2_d1
                    image = Image.open(icon2_d1)
                    image = image.resize((30, 30), Image.ANTIALIAS)  # image.resize((100, 100)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)
                    self.iconLbl_d1.config(image=photo)
                    self.iconLbl_d1.image = photo
            else:
                # remove image
                self.iconLbl_d1.config(image='')

            if icon2_d2 is not None:
                if self.icon_d2 != icon2_d2:
                    self.icon_d2 = icon2_d2
                    image = Image.open(icon2_d2)
                    image = image.resize((30, 30), Image.ANTIALIAS)  # image.resize((100, 100)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)
                    self.iconLbl_d2.config(image=photo)
                    self.iconLbl_d2.image = photo
            else:
                # remove image
                self.iconLbl_d2.config(image='')

            if icon2_d3 is not None:
                if self.icon_d3 != icon2_d3:
                    self.icon_d3 = icon2_d3
                    image = Image.open(icon2_d3)
                    image = image.resize((30, 30), Image.ANTIALIAS)  # image.resize((100, 100)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)
                    self.iconLbl_d3.config(image=photo)
                    self.iconLbl_d3.image = photo
            else:
                # remove image
                self.iconLbl_d3.config(image='')

            if icon2_d4 is not None:
                if self.icon_d4 != icon2_d4:
                    self.icon_d4 = icon2_d4
                    image = Image.open(icon2_d4)
                    image = image.resize((30, 30), Image.ANTIALIAS)  # image.resize((100, 100)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)
                    self.iconLbl_d4.config(image=photo)
                    self.iconLbl_d4.image = photo
            else:
                # remove image
                self.iconLbl_d4.config(image='')

            if self.currently != currently2:
                self.currently = currently2
                self.currentlyLbl.config(text=currently2)

                # new
                # self.currentlyLbl_d2.config(text=currently2)

            # if self.forecast != forecast2:
            # self.forecast = forecast2
            # self.forecastLbl.config(text=forecast2)

            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperatureLbl.config(text=temperature2)

                # new
                self.temperatureLbl_d1_H.config(text=temperature2_d1_H)
                self.temperatureLbl_d2_H.config(text=temperature2_d2_H)
                self.temperatureLbl_d3_H.config(text=temperature2_d3_H)
                self.temperatureLbl_d4_H.config(text=temperature2_d4_H)
                self.temperatureLbl_d1_L.config(text=temperature2_d1_L)
                self.temperatureLbl_d2_L.config(text=temperature2_d2_L)
                self.temperatureLbl_d3_L.config(text=temperature2_d3_L)
                self.temperatureLbl_d4_L.config(text=temperature2_d4_L)

            if self.day_d1 != day_d1_2:
                self.day_d1 = day_d1_2
                self.dayLbl_d1.config(text=day_d1_2)
                self.dayLbl_d2.config(text=day_d2_2)
                self.dayLbl_d3.config(text=day_d3_2)
                self.dayLbl_d4.config(text=day_d4_2)

            if self.location != location2:
                if location2 == ", ":
                    self.location = "Cannot Pinpoint Location"
                    self.locationLbl.config(text="Cannot Pinpoint Location")
                else:
                    self.location = location2
                    self.locationLbl.config(text=location2)
        except Exception as e:
            traceback.print_exc()
            print("Error: %s. Cannot get weather." % e)

        self.after(600000, self.get_weather)

    @staticmethod
    def convert_kelvin_to_fahrenheit(kelvin_temp):
        return 1.8 * (kelvin_temp - 273) + 32


# Quote
class Quote(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.title = 'Sucess is not final. Failure is not fatal. \nIt is the courage to continue that counts.'
        self.quoteLbl = Label(self, text=self.title, font=('Helvetica', xsmall_text_size), fg="white", bg="black")
        self.quoteLbl.pack(anchor=N)


# Bottom Quote
class Quote_bottom(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.title = '经历  创造  拥有  忆起'
        self.quoteLbl = Label(self, text=self.title, font=('Helvetica', xxsmall_text_size), fg="white", bg="black")
        self.quoteLbl.pack(anchor=N)


# class News(Frame):
# def __init__(self, parent, *args, **kwargs):
# Frame.__init__(self, parent, *args, **kwargs)
# self.config(bg='black')
# self.title = 'News' # 'News' is more internationally generic
# self.newsLbl = Label(self, text=self.title, font=('Helvetica', small_text_size), fg="white", bg="black") #medium_text_size
# self.newsLbl.pack(side=TOP, anchor=W)
# self.headlinesContainer = Frame(self, bg="black")
# self.headlinesContainer.pack(side=TOP)
# self.get_headlines()

# def get_headlines(self):
# try:
# remove all children
# for widget in self.headlinesContainer.winfo_children():
# widget.destroy()
# if news_country_code == None:
# headlines_url = "https://news.google.com/news?ned=us&output=rss"
# else:
# headlines_url = "https://news.google.com/news?ned=%s&output=rss" % news_country_code

# feed = feedparser.parse(headlines_url)

# for post in feed.entries[0:5]:
# headline = NewsHeadline(self.headlinesContainer, post.title)
# headline.pack(side=TOP, anchor=W)
# except Exception as e:
# traceback.print_exc()
# print ("Error: %s. Cannot get news." % e)

# self.after(600000, self.get_headlines)


# class NewsHeadline(Frame):
# def __init__(self, parent, event_name=""):
# Frame.__init__(self, parent, bg='black')

# image = Image.open("/home/pi/SmartMirror/assets/Newspaper.png")#assets/Newspaper.png
# image = image.resize((25, 25), Image.ANTIALIAS)
# image = image.convert('RGB')
# photo = ImageTk.PhotoImage(image)

# self.iconLbl = Label(self, bg='black', image=photo)
# self.iconLbl.image = photo
# self.iconLbl.pack(side=LEFT, anchor=N)

# self.eventName = event_name
# self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', xsmall_text_size), fg="white", bg="black") #small_text_size
# self.eventNameLbl.pack(side=LEFT, anchor=N)


# class Calendar(Frame):
# def __init__(self, parent, *args, **kwargs):
# Frame.__init__(self, parent, bg='black')
# self.title = 'Calendar Events'
# self.calendarLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
# self.calendarLbl.pack(side=TOP, anchor=E)
# self.calendarEventContainer = Frame(self, bg='black')
# self.calendarEventContainer.pack(side=TOP, anchor=E)
# self.get_events()

# def get_events(self):
# TODO: implement this method
# reference https://developers.google.com/google-apps/calendar/quickstart/python

# remove all children
# for widget in self.calendarEventContainer.winfo_children():
# widget.destroy()

# calendar_event = CalendarEvent(self.calendarEventContainer)
# calendar_event.pack(side=TOP, anchor=E)
# pass


# class CalendarEvent(Frame):
# def __init__(self, parent, event_name="Event 1"):
# Frame.__init__(self, parent, bg='black')
# self.eventName = event_name
# self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
# self.eventNameLbl.pack(side=TOP, anchor=E)


# Timer
class Timer(Frame):
    def __init__(self, master, controller):  # *args, **kwargs
        Frame.__init__(self, master, bg='black')
        self.master = master

        self.state = False
        self.minutes = 25  # 25
        self.seconds = 0

        self.mins = 25  # 25
        self.secs = 0

        self.minutes_10 = 10
        self.seconds_10 = 0

        self.mins_10 = 10
        self.secs_10 = 0

        self.minutes_60 = 60
        self.seconds_60 = 0

        self.mins_60 = 60
        self.secs_60 = 0

        self.displayFrm = Frame(self, bg='black')
        self.displayFrm.pack(side=TOP, anchor=W, pady=10)  # pady =50

        # for text and next button
        self.displayFrm2 = Frame(self, bg='black')
        self.displayFrm2.pack(side=TOP, anchor=W)

        self.display = tk.Label(self.displayFrm, height=2, width=40, textvariable='',
                                font=('Helvetica', xsmall_text_size), bg='black', fg='gray')  # width=40,self.displayFrm
        self.display.config(text='00:00')
        self.display.pack(side=TOP, anchor=N)

        # progress bar & the style
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('Horizontal.TProgressbar', troughcolor='black', background='white')  # foreground='white',
        self.pb = ttk.Progressbar(self.displayFrm, style='Horizontal.TProgressbar', orient='horizontal',
                                  mode='determinate', length=500)  # length=455,self.displayFrm
        self.pb.pack(side=TOP, anchor=N)

        # buttons
        self.start_button = tk.Button(self.displayFrm, font=('Helvetica', xxsmall_text_size), bg='black', fg='white',
                                      text='Pomodoro', width=7, height=2, command=self.start)  # self.displayFrm
        self.start_button.pack(side=LEFT, anchor=E)

        self.start_button_10 = tk.Button(self.displayFrm, font=('Helvetica', xxsmall_text_size), bg='black', fg='white',
                                         text='10 mins', width=7, height=2, command=self.start_10)  # self.displayFrm
        self.start_button_10.pack(side=LEFT, anchor=E)

        self.start_button_60 = tk.Button(self.displayFrm, font=('Helvetica', xxsmall_text_size), bg='black', fg='white',
                                         text='60 mins', width=7, height=2, command=self.start_60)  # self.displayFrm
        self.start_button_60.pack(side=LEFT, anchor=E)

        self.pause_button = tk.Button(self.displayFrm, font=('Helvetica', xxsmall_text_size), bg='black', fg='white',
                                      text='Reset', width=7, height=2, command=self.reset,
                                      state='disabled')  # self.displayFrm
        self.pause_button.pack(side=LEFT, anchor=E)

        self.complete_button = tk.Button(self.displayFrm, font=('Helvetica', xxsmall_text_size), bg='black', fg='white',
                                         text='Complete', width=8, height=2, command=self.complete,
                                         state='disabled')  # self.displayFrm
        self.complete_button.pack(side=LEFT, anchor=E)

        # time tracking
        self.tracking_bttn = tk.Label(self.displayFrm2, bg='black', font=('Helvetica', xsmall_text_size), fg='white',
                                      text='Today\'s Pomodoro Time: 0 min', width=40, height=3)
        self.tracking_bttn.pack(side=TOP, anchor=N)
        self.min_init2 = 0

        # countdown
        self.countdown()

        # today's date for time tracking restart
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')


    def countdown(self):
        # Displays a clock starting at min:sec to 00:00, ex: 25:00 -> 00:00
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')  # check date when doing countdown

        if self.state == True:
            if self.secs < 10:
                if self.mins < 10:
                    self.display.config(text='0%d : 0%d | %d mins' % (self.mins, self.secs, self.min_init))
                else:
                    self.display.config(text='%d : 0%d | %d mins' % (self.mins, self.secs, self.min_init))
            else:
                if self.mins < 10:
                    self.display.config(text='0%d : %d | %d mins' % (self.mins, self.secs, self.min_init))
                else:
                    self.display.config(text='%d : %d | %d mins' % (self.mins, self.secs, self.min_init))

            # when complete:
            if (self.mins == 0) and (self.secs == 0):
                self.display.config(text="Complete!")
                self.complete_button['state'] = 'disabled'  # when complete, can only reset
                if self.today == self.today2:
                    self.min_init2 += self.min_init
                    self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: ' + str(self.min_init2) + ' mins'
                else:
                    self.today = datetime.datetime.today().strftime('%Y-%m-%d')
                    self.min_init2 = 0
                    self.min_init2 += self.min_init
                    self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: ' + str(self.min_init2) + ' mins'

                self.state = False
                self.minutes = 25  # 25
                self.seconds = 0

                # self.mins = 25  # 25
                # self.secs = 0

                self.minutes_10 = 10
                self.seconds_10 = 0

                # self.mins_10 = 10
                # self.secs_10 = 0

                self.minutes_60 = 60
                self.seconds_60 = 0

                # self.mins_60 = 60
                # self.secs_60 = 0

            else:
                if self.secs == 0:
                    self.mins -= 1
                    self.secs = 59
                else:
                    self.secs -= 1

                self.pb['value'] = self.mins * 60 + self.secs
                self.master.after(1000, self.countdown)
        else:
            self.master.after(100, self.countdown)

    def start(self):  # Pomodoro
        # check date when doing countdown
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')

        if self.state == False:
            self.state = True
            self.mins = self.minutes
            self.secs = self.seconds
            self.pb['value'] = 0
            self.pb['maximum'] = self.minutes * 60
            self.min_init = self.mins

            # clean up yesterday records
            if self.today != self.today2:
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: 0 min'

        if self.state == True:
            self.complete_button['state'] = 'normal'
            self.pause_button['state'] = 'normal'
            self.start_button['state'] = 'disabled'
            self.start_button_10['state'] = 'disabled'
            self.start_button_60['state'] = 'disabled'

    def start_10(self):
        # check date when doing countdown
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')

        if self.state == False:
            self.state = True
            self.mins = self.minutes_10
            self.secs = self.seconds_10
            self.pb['value'] = 0
            self.pb['maximum'] = self.minutes_10 * 60
            self.min_init = self.mins
            # clean up yesterday records
            if self.today != self.today2:
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: 0 min'

        if self.state == True:
            self.complete_button['state'] = 'normal'
            self.pause_button['state'] = 'normal'
            self.start_button['state'] = 'disabled'
            self.start_button_10['state'] = 'disabled'
            self.start_button_60['state'] = 'disabled'

    def start_60(self):
        # check date when doing countdown
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')

        if self.state == False:
            self.state = True
            self.mins = self.minutes_60
            self.secs = self.seconds_60
            self.pb['value'] = 0
            self.pb['maximum'] = self.minutes_60 * 60
            self.min_init = self.mins
            # clean up yesterday records
            if self.today != self.today2:
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: 0 min'

        if self.state == True:
            self.complete_button['state'] = 'normal'
            self.pause_button['state'] = 'normal'
            self.start_button['state'] = 'disabled'
            self.start_button_10['state'] = 'disabled'
            self.start_button_60['state'] = 'disabled'

    def reset(self):
        if self.state == True:
            self.state = False
            self.display.config(text='00:00')
            self.pb['value'] = 0
            self.pb['maximum'] = 0

            self.minutes = 25  # 25
            self.seconds = 0
            self.mins = 25  # 25
            self.secs = 0
            self.minutes_10 = 10
            self.seconds_10 = 0
            self.mins_10 = 10
            self.secs_10 = 0
            self.minutes_60 = 60
            self.seconds_60 = 0
            self.mins_60 = 60
            self.secs_60 = 0

            self.complete_button['state'] = 'disabled'
            self.pause_button['state'] = 'disabled'
            self.start_button['state'] = 'normal'
            self.start_button_10['state'] = 'normal'
            self.start_button_60['state'] = 'normal'

        else:
            # state is false, as timer is completed
            self.display.config(text='00:00')
            self.pb['value'] = 0
            self.pb['maximum'] = 0
            self.countdown()  # make countdown available

            # bttn unavailable so the user has to click 'reset' to start
            self.complete_button['state'] = 'disabled'
            self.pause_button['state'] = 'disabled'
            self.start_button['state'] = 'normal'
            self.start_button_10['state'] = 'normal'
            self.start_button_60['state'] = 'normal'

    def complete(self):
        self.today2 = datetime.datetime.today().strftime('%Y-%m-%d')

        if self.state == True:

            # clean up yesterday records
            if self.today != self.today2:
                self.min_init2 = 0
                self.min_init2 += self.min_init
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: ' + str(self.min_init2) + ' mins'
            else:
                self.min_init2 += self.min_init
                self.tracking_bttn['text'] = 'Today\'s Pomodoro Time: ' + str(self.min_init2) + ' mins'

            self.state = False
            self.display.config(text='00:00')
            self.pb['value'] = 0
            self.pb['maximum'] = 0

            self.minutes = 25  # 25
            self.seconds = 0
            self.mins = 25  # 25
            self.secs = 0
            self.minutes_10 = 10
            self.seconds_10 = 0
            self.mins_10 = 10
            self.secs_10 = 0
            self.minutes_60 = 60
            self.seconds_60 = 0
            self.mins_60 = 60
            self.secs_60 = 0

            # after clicking complte or reset, only the other three buttns available
            self.complete_button['state'] = 'disabled'
            self.pause_button['state'] = 'disabled'
            self.start_button['state'] = 'normal'
            self.start_button_10['state'] = 'normal'
            self.start_button_60['state'] = 'normal'

        else:
            # state is false, as timer is completed
            self.display.config(text='00:00')
            self.pb['value'] = 0
            self.pb['maximum'] = 0
            # self.countdown() #make countdown available

            self.start_button['state'] = 'normal'
            self.start_button_10['state'] = 'normal'
            self.start_button_60['state'] = 'normal'


class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.topFrame = Frame(self, background='black') #self.tk
        self.midFrame = Frame(self, background='black') #self.tk
        self.bottomFrame = Frame(self, background='black') #self.tk
        self.topFrame.pack(side=TOP, fill=BOTH, expand=YES)
        self.midFrame.pack(fill=BOTH, expand=YES)
        self.bottomFrame.pack(side=BOTTOM, fill=BOTH, expand=YES)
        
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=10, pady=60)  # padx=50, pady=60
        # quote
        self.quote = Quote(self.midFrame)
        self.quote.pack(anchor=N, padx=10, pady=10)  # padx=50,anchor=W, padx=100, pady=60
        # timer
        self.timer = Timer(self.midFrame, controller=Timer)
        self.timer.pack(anchor=N, padx=10, pady=10)  # padx=70, anchor=W, padx=100, pady=60
        # next button
        nextButton = tk.Button(self.midFrame, text=">>>>", font=('Helvetica', xxsmall_text_size), bg='black', fg='white',
                            borderwidth=0, command=lambda: controller.show_frame(PageTwo))
        nextButton.pack(anchor=N)
        # weather
        self.weather = Weather(self.midFrame)  # bottomFrame
        self.weather.pack(side=LEFT, anchor=N, padx=10, pady=(70, 5))  # pady=60
        # quote bottom
        self.quote_bottom = Quote_bottom(self.bottomFrame)
        self.quote_bottom.pack(anchor=N, padx=70)  # anchor=W, padx=100, pady=60

        # news
        # self.news = News(self.midFrame) #bottomFrame
        # self.news.pack(anchor=W, padx=10, pady=60) #side=LEFT, anchor=S, padx=100, pady=60
        # calender - removing for now
        # self.calender = Calendar(self.bottomFrame)
        # self.calender.pack(side = RIGHT, anchor=S, padx=100, pady=60)


# Connect to GoogleCalendar API
class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.topFrame = Frame(self, background='black')
        self.midFrame = Frame(self, background='black')
        self.bottomFrame = Frame(self, background='black')
        self.topFrame.pack(side=TOP, fill=BOTH, expand=YES)
        self.midFrame.pack(fill=BOTH, expand=YES)
        self.bottomFrame.pack(side=BOTTOM, fill=BOTH, expand=YES)
        
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=10, pady=60)  # padx=50, pady=60

        # add calendar module here
        """Shows basic usage of the Google Calendar API.
                Prints the start and name of the next 10 events on the user's calendar.
                """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')

        def retrieve(i):
            vars()['start' + str(i)] = events[i]['start'].get('dateTime', events[i]['start'].get('date'))
            vars()['summary' + str(i)] = events[i]['summary']
            vars()['end' + str(i)] = events[i]['end'].get('dateTime', events[i]['end'].get('date'))

            return vars()['start' + str(i)], vars()['summary' + str(i)], vars()['end' + str(i)]

        def format():
            eSummary = []
            eDate = []
            estartTime = []
            eendTime = []
            eDiff = []

            for i in range(9):
                vars()['start' + str(i)], vars()['summary' + str(i)], vars()['end' + str(i)] = retrieve(i)
                vars()['start' + str(i)] = re.sub('T', ' ', vars()['start' + str(i)])  # remove "T"
                vars()['end' + str(i)] = re.sub('T', ' ', vars()['end' + str(i)])  # remove "T"

                vars()['eventDate' + str(i)] = vars()['start' + str(i)][:10]  # store date
                vars()['dayDiff' + str(i)] = datetime.datetime.strptime(vars()['eventDate' + str(i)],
                                                                        "%Y-%m-%d") - datetime.datetime.today() # calculate days diff
                vars()['eventDate' + str(i)] = datetime.datetime.strptime(vars()['eventDate' + str(i)],
                                                                          "%Y-%m-%d").strftime(
                    "%a, %b %d")  # format date %Y
                vars()['startTime' + str(i)] = vars()['start' + str(i)][11:16]  # store time
                vars()['endTime' + str(i)] = vars()['end' + str(i)][11:16]  # store time

                # in case no "@" in event summary
                if '@' in str(vars()['summary' + str(i)]):
                    pass
                else:
                    vars()['summary' + str(i)] = vars()['summary' + str(i)] + " @ "

                eSummary.append(vars()['summary' + str(i)])
                eDate.append(vars()['eventDate' + str(i)])
                estartTime.append(vars()['startTime' + str(i)])
                eendTime.append(vars()['endTime' + str(i)])
                eDiff.append(str(vars()['dayDiff' + str(i)].days+1))

            return eSummary, eDiff, eDate, estartTime, eendTime

        colr = 'white'
        colr2 = 'white'
        tpadx = (20,0)

        self.calFrame0_1 = tk.Frame(self.midFrame, bg="black")
        self.calFrame0_1.pack(side='top', anchor='w', padx=tpadx, pady=(12, 0))
        self.calFrame0_2 = tk.Frame(self.midFrame, bg="black")
        self.calFrame0_2.pack(side='top', anchor='w', padx=tpadx, pady=(0, 15))

        self.calFrame1_1 = tk.Frame(self.midFrame, bg="black")
        self.calFrame1_1.pack(side='top', anchor='w',padx=tpadx,  pady=(12, 0))
        self.calFrame1_2 = tk.Frame(self.midFrame, bg="black")
        self.calFrame1_2.pack(side='top', anchor='w', padx=tpadx, pady=(0, 15))

        self.calFrame2_1 = tk.Frame(self.midFrame, bg="black")
        self.calFrame2_1.pack(side='top', anchor='w', padx=tpadx, pady=(12, 0))
        self.calFrame2_2 = tk.Frame(self.midFrame, bg="black")
        self.calFrame2_2.pack(side='top', anchor='w', padx=tpadx, pady=(0, 15))

        self.calFrame3_1 = tk.Frame(self.midFrame, bg="black")
        self.calFrame3_1.pack(side='top', anchor='w', padx=tpadx, pady=(12, 0))
        self.calFrame3_2 = tk.Frame(self.midFrame, bg="black")
        self.calFrame3_2.pack(side='top', anchor='w', padx=tpadx, pady=(0, 15))

        self.calFrame4_1 = tk.Frame(self.midFrame, bg="black")
        self.calFrame4_1.pack(side='top', anchor='w', padx=tpadx, pady=(12, 0))
        self.calFrame4_2 = tk.Frame(self.midFrame, bg="black")
        self.calFrame4_2.pack(side='top', anchor='w', padx=tpadx, pady=(0, 15))

        self.calFrame5_1 = tk.Frame(self.midFrame, bg="black")
        self.calFrame5_1.pack(side='top', anchor='n', padx=tpadx, pady=(12, 0))
        self.calFrame5_2 = tk.Frame(self.midFrame, bg="black")
        self.calFrame5_2.pack(side='top', anchor='n', padx=tpadx, pady=(0, 15))

        # self.calFrame6_1 = tk.Frame(self.midFrame, bg="black")
        # self.calFrame6_1.pack(side='top', anchor='w', padx=40, pady=(12, 0))
        # self.calFrame6_2 = tk.Frame(self.midFrame, bg="black")
        # self.calFrame6_2.pack(side='top', anchor='w', padx=40, pady=(0, 15))
        #
        # self.calFrame7_1 = tk.Frame(self.midFrame, bg="black")
        # self.calFrame7_1.pack(side='top', anchor='w', padx=40, pady=(12, 0))
        # self.calFrame7_2 = tk.Frame(self.midFrame, bg="black")
        # self.calFrame7_2.pack(side='top', anchor='w', padx=40, pady=(0, 15))
        #
        # self.calFrame8_1 = tk.Frame(self.midFrame, bg="black")
        # self.calFrame8_1.pack(side='top', anchor='w', padx=40, pady=(12, 0))
        # self.calFrame8_2 = tk.Frame(self.midFrame, bg="black")
        # self.calFrame8_2.pack(side='top', anchor='w', padx=40, pady=(0, 15))

        # event0
        self.event0 = tk.Label(self.calFrame0_1, bg='black', font=('Helvetica', xsmall_text_size), fg=colr,
                               text=(format()[0][0].split(' @')[0]))
        self.event0.pack(side='left', anchor='w')
        self.location0 = tk.Label(self.calFrame0_2, bg='black', font=('courier', xxsmall_text_size), fg=colr,
                                  text=("@ " + format()[0][0].split("@ ", 1)[1]))
        self.location0.pack(side='top', anchor='w')

        self.dDiff0 = tk.Label(self.calFrame0_2, bg='black', font=('courier', xxsmall_text_size), fg=colr,
                               text=("in " + format()[1][0] + " days."))
        self.dDiff0.pack(side='left', anchor='w')
        self.date0 = tk.Label(self.calFrame0_2, bg='black', font=('courier', xxsmall_text_size), fg=colr,
                              text=('on ' + format()[2][0]) + ".")
        self.date0.pack(side='left', anchor='w')
        self.starttime0 = tk.Label(self.calFrame0_2, bg='black', font=('courier', xxsmall_text_size), fg=colr,
                                   text=('at ' + format()[3][0] + " -"))
        self.starttime0.pack(side='left', anchor='w')
        self.endtime0 = tk.Label(self.calFrame0_2, bg='black', font=('courier', xxsmall_text_size), fg=colr,
                                 text=(format()[4][0]))
        self.endtime0.pack(side='left', anchor='w')

        # event1
        self.event1 = tk.Label(self.calFrame1_1, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
                               text=(format()[0][1].split(' @')[0]))
        self.event1.pack(side='left', anchor='w')
        self.location1 = tk.Label(self.calFrame1_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                  text=("@ " + format()[0][1].split("@ ", 1)[1]))
        self.location1.pack(side='top', anchor='w')

        self.dDiff1 = tk.Label(self.calFrame1_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                               text=("in " + format()[1][1] + " days."))
        self.dDiff1.pack(side='left', anchor='w')
        self.date1 = tk.Label(self.calFrame1_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                              text=('on ' + format()[2][1]) + ".")
        self.date1.pack(side='left', anchor='w')
        self.starttime1 = tk.Label(self.calFrame1_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                   text=('at ' + format()[3][1] + " -"))
        self.starttime1.pack(side='left', anchor='w')
        self.endtime1 = tk.Label(self.calFrame1_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                 text=(format()[4][1]))
        self.endtime1.pack(side='left', anchor='w')

        # event2
        self.event2 = tk.Label(self.calFrame2_1, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
                               text=(format()[0][2].split(' @')[0]))
        self.event2.pack(side='left', anchor='w')
        self.location2 = tk.Label(self.calFrame2_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                  text=("@ " + format()[0][2].split("@ ", 1)[1]))
        self.location2.pack(side='top', anchor='w')

        self.dDiff2 = tk.Label(self.calFrame2_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                               text=("in " + format()[1][2] + " days."))
        self.dDiff2.pack(side='left', anchor='w')
        self.date2 = tk.Label(self.calFrame2_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                              text=('on ' + format()[2][2]) + ".")
        self.date2.pack(side='left', anchor='w')
        self.starttime2 = tk.Label(self.calFrame2_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                   text=('at ' + format()[3][2] + " -"))
        self.starttime2.pack(side='left', anchor='w')
        self.endtime2 = tk.Label(self.calFrame2_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                 text=(format()[4][2]))
        self.endtime2.pack(side='left', anchor='w')

        # event3
        self.event3 = tk.Label(self.calFrame3_1, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
                               text=(format()[0][3].split(' @')[0]))
        self.event3.pack(side='left', anchor='w')
        self.location3 = tk.Label(self.calFrame3_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                  text=("@ " + format()[0][3].split("@ ", 1)[1]))
        self.location3.pack(side='top', anchor='w')

        self.dDiff3 = tk.Label(self.calFrame3_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                               text=("in " + format()[1][3] + " days."))
        self.dDiff3.pack(side='left', anchor='w')
        self.date3 = tk.Label(self.calFrame3_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                              text=('on ' + format()[2][3]) + ".")
        self.date3.pack(side='left', anchor='w')
        self.starttime3 = tk.Label(self.calFrame3_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                   text=('at ' + format()[3][3] + " -"))
        self.starttime3.pack(side='left', anchor='w')
        self.endtime3 = tk.Label(self.calFrame3_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                 text=(format()[4][3]))
        self.endtime3.pack(side='left', anchor='w')

        # event4
        self.event4 = tk.Label(self.calFrame4_1, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
                               text=(format()[0][4].split(' @')[0]))
        self.event4.pack(side='left', anchor='w')
        self.location4 = tk.Label(self.calFrame4_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                  text=("@ " + format()[0][4].split("@ ", 1)[1]))
        self.location4.pack(side='top', anchor='w')

        self.dDiff4 = tk.Label(self.calFrame4_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                               text=("in " + format()[1][4] + " days."))
        self.dDiff4.pack(side='left', anchor='w')
        self.date4 = tk.Label(self.calFrame4_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                              text=('on ' + format()[2][4]) + ".")
        self.date4.pack(side='left', anchor='w')
        self.starttime4 = tk.Label(self.calFrame4_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                   text=('at ' + format()[3][4] + " -"))
        self.starttime4.pack(side='left', anchor='w')
        self.endtime4 = tk.Label(self.calFrame4_2, bg='black', font=('courier', xxsmall_text_size), fg=colr2,
                                 text=(format()[4][4]))
        self.endtime4.pack(side='left', anchor='w')

        # # event5
        # self.event5 = tk.Label(self.calFrame5_1, bg='black', font=('Helvetica', small_text_size), fg=colr2,
        #                        text=(format()[0][5].split(' @')[0]))
        # self.event5.pack(side='left', anchor='s')
        # self.location5 = tk.Label(self.calFrame5_1, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                           text=("@ " + format()[0][5].split("@ ", 1)[1]))
        # self.location5.pack(side='left', anchor='s')
        #
        # self.dDiff5 = tk.Label(self.calFrame5_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                        text=("in " + format()[1][5] + " days ==>"))
        # self.dDiff5.pack(side='left', anchor='n')
        # self.date5 = tk.Label(self.calFrame5_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                       text=('on ' + format()[2][5]) + " ==>")
        # self.date5.pack(side='left', anchor='n')
        # self.starttime5 = tk.Label(self.calFrame5_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                            text=('at ' + format()[3][5] + "-"))
        # self.starttime5.pack(side='left', anchor='n')
        # self.endtime5 = tk.Label(self.calFrame5_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                          text=(format()[4][5]))
        # self.endtime5.pack(side='left', anchor='n')
        #
        # # event6
        # self.event6 = tk.Label(self.calFrame6_1, bg='black', font=('Helvetica', small_text_size), fg=colr2,
        #                        text=(format()[0][6].split(' @')[0]))
        # self.event6.pack(side='left', anchor='s')
        # self.location6 = tk.Label(self.calFrame6_1, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                           text=("@ " + format()[0][6].split("@ ", 1)[1]))
        # self.location6.pack(side='left', anchor='s')
        #
        # self.dDiff6 = tk.Label(self.calFrame6_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                        text=("in " + format()[1][6] + " days ==>"))
        # self.dDiff6.pack(side='left', anchor='n')
        # self.date6 = tk.Label(self.calFrame6_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                       text=('on ' + format()[2][6]) + " ==>")
        # self.date6.pack(side='left', anchor='n')
        # self.starttime6 = tk.Label(self.calFrame6_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                            text=('at ' + format()[3][6] + "-"))
        # self.starttime6.pack(side='left', anchor='n')
        # self.endtime6 = tk.Label(self.calFrame6_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                          text=(format()[4][6]))
        # self.endtime6.pack(side='left', anchor='n')
        #
        # # event7
        # self.event7 = tk.Label(self.calFrame7_1, bg='black', font=('Helvetica', small_text_size), fg=colr2,
        #                        text=(format()[0][7].split(' @')[0]))
        # self.event7.pack(side='left', anchor='s')
        # self.location7 = tk.Label(self.calFrame7_1, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                           text=("@ " + format()[0][7].split("@ ", 1)[1]))
        # self.location7.pack(side='left', anchor='s')
        #
        # self.dDiff7 = tk.Label(self.calFrame7_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                        text=("in " + format()[1][7] + " days ==>"))
        # self.dDiff7.pack(side='left', anchor='n')
        # self.date7 = tk.Label(self.calFrame7_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                       text=('on ' + format()[2][7]) + " ==>")
        # self.date7.pack(side='left', anchor='n')
        # self.starttime7 = tk.Label(self.calFrame7_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                            text=('at ' + format()[3][7] + "-"))
        # self.starttime7.pack(side='left', anchor='n')
        # self.endtime7 = tk.Label(self.calFrame7_2, bg='black', font=('Helvetica', xsmall_text_size), fg=colr2,
        #                          text=(format()[4][7]))
        # self.endtime7.pack(side='left', anchor='n')
        #

        button1 = tk.Button(self.calFrame5_2, text="<<<<", font=('Helvetica', xxsmall_text_size), bg='black', fg='white',
                            borderwidth=0, command=lambda: controller.show_frame(PageOne))
        button1.pack(side="left", anchor='w')

        self.bttn_frame2 = tk.Frame(self.calFrame5_2, bg="black")
        self.bttn_frame2.pack(side='left', anchor='e')
        button2 = tk.Button(self.bttn_frame2, text=">>>>", font=('Helvetica', xxsmall_text_size), bg='black', fg='white',
                            borderwidth=0, command=lambda: controller.show_frame(PageThree))
        button2.pack(side="right", anchor='e')

        # quote bottom
        self.quote_bottom = Quote_bottom(self.bottomFrame)
        self.quote_bottom.pack(anchor=N, padx=70)  # anchor=W, padx=100, pady=60


# connect to GoogleSheet API
class PageThree(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.topFrame = Frame(self, background='black')
        self.midFrame = Frame(self, background='black')
        self.bottomFrame = Frame(self, background='black')
        self.topFrame.pack(side=TOP, fill=BOTH, expand=YES)
        self.midFrame.pack(fill=BOTH, expand=YES)
        self.bottomFrame.pack(side=BOTTOM, fill=BOTH, expand=YES)
        
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=10, pady=60)  # padx=50, pady=60

        # google sheet API
        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

        # The ID and range of a sample spreadsheet.
        SAMPLE_SPREADSHEET_ID = '17oHHC0iFY5VCQsHAyYe22jrSUcriwmV5eWI9RzXDrdA'
        Python_RANGE_NAME = 'Python!$A$2:$B$100000'
        Pyspark_RANGE_NAME = 'Pyspark!A:B'
        Tensorflow_RANGE_NAME = 'Tensorflow!A:B'

        """Shows basic usage of the Sheets API.
            Prints values from a sample spreadsheet.
            """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token_googlesheet.pickle'):
            with open('token_googlesheet.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials_googlesheet.json', SCOPES)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token_googlesheet.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        python_result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                           range=Python_RANGE_NAME).execute()
        python_values = python_result.get('values', [])

        pyspark_result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                            range=Pyspark_RANGE_NAME).execute()
        pyspark_values = pyspark_result.get('values', [])

        tensorflow_result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                               range=Tensorflow_RANGE_NAME).execute()
        tensorflow_values = tensorflow_result.get('values', [])

        for row in python_values[0:]:
            if str(row[1]) == 'Y':
                self.label = tk.Label(self.midFrame, bg='black', font=('Helvetica', xxsmall_text_size), fg='white',
                                      text=str(row[0]))  # width=40, height=8
                self.label.pack(side='top', anchor='w', padx=(20,0))  # pady=10,
            else:
                pass

        button2 = tk.Button(self.bottomFrame, text="<<<<", font=('Helvetica', xxsmall_text_size), bg='black', fg='white',
                            borderwidth=0, command=lambda: controller.show_frame(PageTwo))
        button2.pack(side="top", anchor='n')

        # quote bottom
        self.quote_bottom = Quote_bottom(self.bottomFrame)
        self.quote_bottom.pack(anchor=N, padx=70)  # anchor=W, padx=100, pady=60

#
# class FullscreenWindow:
#
#     def __init__(self):
#         self.tk = Tk()
#         self.tk.configure(background='black')
#         self.topFrame = Frame(self.tk, background='black')
#         self.midFrame = Frame(self.tk, background='black')
#         self.bottomFrame = Frame(self.tk, background='black')
#         self.topFrame.pack(side=TOP, fill=BOTH, expand=YES)
#         self.midFrame.pack(fill=BOTH, expand=YES)
#         self.bottomFrame.pack(side=BOTTOM, fill=BOTH, expand=YES)
#         self.state = False
#         self.tk.bind("<Return>", self.toggle_fullscreen)
#         self.tk.bind("<Escape>", self.end_fullscreen)
#         # clock
#         self.clock = Clock(self.topFrame)
#         self.clock.pack(side=RIGHT, anchor=N, padx=10, pady=60)  # padx=50, pady=60
#         # quote
#         self.quote = Quote(self.midFrame)
#         self.quote.pack(anchor=N, padx=10, pady=10)  # padx=50,anchor=W, padx=100, pady=60
#         # timer
#         self.timer = Timer(self.midFrame, controller=Timer)
#         self.timer.pack(anchor=N, padx=10, pady=10)  # padx=70, anchor=W, padx=100, pady=60
#         # weather
#         self.weather = Weather(self.midFrame)  # bottomFrame
#         self.weather.pack(side=LEFT, anchor=N, padx=10, pady=(70, 5))  # pady=60
#         # quote bottom
#         self.quote_bottom = Quote_bottom(self.bottomFrame)
#         self.quote_bottom.pack(anchor=N, padx=70)  # anchor=W, padx=100, pady=60
#         # news
#         # self.news = News(self.midFrame) #bottomFrame
#         # self.news.pack(anchor=W, padx=10, pady=60) #side=LEFT, anchor=S, padx=100, pady=60
#         # calender - removing for now
#         # self.calender = Calendar(self.bottomFrame)
#         # self.calender.pack(side = RIGHT, anchor=S, padx=100, pady=60)
#
#     def toggle_fullscreen(self, event=None):
#         self.state = not self.state  # Just toggling the boolean
#         self.tk.attributes("-fullscreen", self.state)
#         return "break"
#
#     def end_fullscreen(self, event=None):
#         self.state = False
#         self.tk.attributes("-fullscreen", False)
#         return "break"


# Frame to include multi usage of the screen
class infoFrame(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self, background='black')

        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (PageOne, PageTwo, PageThree):
            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(PageOne)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


if __name__ == '__main__':
    # w = FullscreenWindow()
    w = infoFrame()
    app = Timer(w, controller=Timer) #w.tk
    w.attributes('-fullscreen', True) #full screen
    w.bind("<Escape>", lambda e: w.quit()) #quit program
    w.tk.mainloop()
