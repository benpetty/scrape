#!/usr/bin/python3

import os
import random

from urllib.parse import urlparse
from urllib.request import url2pathname

import requests

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from colorama import Fore, Back, Style

from scrape.core.progress_bars import ProgressBars


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

PROGRESS_BARS = ProgressBars()


class Writer:
    """
    Context manager for handling download writes
    """

    def __init__(self, filename, response, directory=None):
        self.filename = filename
        self.response = response
        self.size = int(response.headers.get("content-length").strip())
        self.dest = os.path.join(directory, filename) if directory else filename
        self.status = self.fileobj = None
        print(f"{Fore.CYAN}Downlading {self.filename} size={self.size}")

    def __enter__(self):
        self.status = PROGRESS_BARS.manager.counter(
            total=self.size,
            desc=self.filename,
            unit="bytes",
            leave=False,
            bar_format=PROGRESS_BARS.get_bar_formats("x11_colors"),
        )
        self.fileobj = open(self.dest, "wb")
        return self

    def __exit__(self, *args):
        self.fileobj.close()
        self.status.close()
        print(f"{Fore.GREEN} Downladed {self.filename} ✅")

    def write(self):
        """
        Write to local file and update progress bar
        """
        CHUNK_SIZE = 1024
        for chunk in self.response.iter_content(CHUNK_SIZE):
            self.fileobj.write(chunk)
            self.status.update(CHUNK_SIZE)


class RadioNatTurner:
    def __init__(self, url: str):
        self.browser = webdriver.Firefox()
        self.url = url
        self.folder_name = f"data{urlparse(self.url).path}"
        if not os.path.isdir(self.folder_name):
            os.mkdir(self.folder_name)

    def login(self):
        self.browser.get(self.url)
        print(f"signing in to {self.url}")
        password_input = self.browser.find_element_by_class_name("password-input")
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)

    def scrape(self):
        self.login()

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "audio-block"))
        )

        tracks = self.browser.find_elements_by_class_name("audio-block")
        print(f"found {len(tracks)} tracks")
        print(f"saving to {self.folder_name}")

        filecounter = PROGRESS_BARS.manager.counter(
            total=len(tracks),
            desc=self.folder_name,
            unit="files",
            bar_format=PROGRESS_BARS.get_bar_formats("red_on_white"),
        )

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
            if os.path.isfile(f"{self.folder_name}/{track_filename}"):
                _ = f"{Fore.LIGHTBLUE_EX}{track_filename}"
                print(f"{Fore.BLUE}...skipping {_}{Fore.BLUE} [already saved]")
                filecounter.update(1)
                continue
            response = requests.get(track_url, stream=True)

            with Writer(
                track_filename,
                response,
                self.folder_name,
            ) as writer:
                writer.write()

            filecounter.update(1)


def main():
    print(f"{Fore.LIGHTRED_EX}Scraping Radio Nat Turner record pool {Style.RESET_ALL}")

    for url in URLS:
        print(f"{Fore.CYAN} - {url}{Style.RESET_ALL}")

    for url in URLS:
        RadioNatTurner(url).scrape()
