#!/usr/bin/python3

import os
import random

from urllib.parse import urlparse
from urllib.request import url2pathname

import enlighten
import requests

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from colorama import Fore, Back, Style


URLS = [
    "https://www.radionatturner.com/brazil/",
    "https://www.radionatturner.com/dance-music/",
    "https://www.radionatturner.com/disco/",
    "https://www.radionatturner.com/funksoulrb/",
    "https://www.radionatturner.com/hip-hop/",
    "https://www.radionatturner.com/international-sounds/",
    "https://www.radionatturner.com/mf-doom",
    "https://www.radionatturner.com/new-school-funksoulrb/",
    "https://www.radionatturner.com/reggae/",
    "https://www.radionatturner.com/rock/",
]

PASSWORD = os.environ.get("RADIO_NAT_TURNER_PASSWORD")

MANAGER = enlighten.get_manager()

# Standard bar format
std_bar_format = (
    "{desc}{desc_pad}{percentage:3.0f}%|{bar}| "
    + "{count:{len_total}d}/{total:d} "
    + "[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]"
)

bar_formats = [
    # Red text
    MANAGER.term.red(std_bar_format),
    # Red on white background
    MANAGER.term.red_on_white(std_bar_format),
    # X11 colors
    MANAGER.term.peru_on_seagreen(std_bar_format),
    # RBG text
    MANAGER.term.color_rgb(2, 5, 128)(std_bar_format),
    # RBG background
    MANAGER.term.on_color_rgb(255, 190, 195)(std_bar_format),
]


class Writer(object):
    """
    Context manager for handling download writes
    """

    def __init__(self, filename, size, directory=None):
        self.filename = filename
        self.size = size
        self.dest = os.path.join(directory, filename) if directory else filename
        self.status = self.fileobj = None

    def __enter__(self):
        self.status = MANAGER.counter(
            total=self.size,
            desc=self.filename,
            unit="bytes",
            leave=False,
            bar_format=bar_formats[2],
        )
        self.fileobj = open(self.dest, "wb")
        return self

    def __exit__(self, *args):
        self.fileobj.close()
        self.status.close()

    def write(self, response):
        """
        Write to local file and update progress bar
        """
        CHUNK_SIZE = 1024
        for byte in response.iter_content(CHUNK_SIZE):
            self.fileobj.write(byte)
            self.status.update(CHUNK_SIZE)


class RadioNatTurner:
    def __init__(self):
        self.browser = webdriver.Firefox()

    def login(self, url: str):
        self.browser.get(url)
        print(f"logging into {url}")
        password_input = self.browser.find_element_by_class_name("password-input")
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)

    def scrape(self, url: str):
        self.login(url)

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "audio-block"))
        )

        tracks = self.browser.find_elements_by_class_name("audio-block")
        print(f"found {len(tracks)} tracks")

        filecounter = MANAGER.counter(
            total=len(tracks),
            desc="Downloading",
            unit="files",
            bar_format=bar_formats[1],
        )

        folder_name = f"data{urlparse(url).path}"
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        print(f"saving to {folder_name}")

        for track in tracks:
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "title"))
            )

            title = track.find_element_by_class_name("title").text
            artist = track.find_element_by_class_name("artistName").text
            track_url = (
                track.find_element_by_class_name("secondary-controls")
                .find_element_by_class_name("download")
                .find_element_by_tag_name("a")
                .get_property("href")
                .split("?")[0]
            )

            _ = os.path.basename(urlparse(track_url).path)
            track_filename = url2pathname(_).replace("+", " ")
            if os.path.isfile(f"{folder_name}/{track_filename}"):
                print(Fore.BLUE + f"skipping {track_filename} - already saved")
                filecounter.update(1)
                continue
            response = requests.get(track_url, stream=True)

            with Writer(
                track_filename,
                int(response.headers.get("content-length").strip()),
                folder_name,
            ) as writer:
                writer.write(response)

            print(Fore.GREEN + f"{artist} - {title}")
            filecounter.update(1)


def main():
    print(Fore.LIGHTRED_EX + "Scraping Radio Nat Turner record pool" + Style.RESET_ALL)

    for url in URLS:
        print(Fore.RED + url + Style.RESET_ALL)

    for url in URLS:
        RadioNatTurner().scrape(url)
