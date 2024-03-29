#!/usr/bin/python3

import os
import random
import json

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
from scrape.core.normalize_filename import strip_accents


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
    "https://www.radionatturner.com/rev-pressure-edits",
]

PASSWORD = os.environ.get("RADIO_NAT_TURNER_PASSWORD")

PROGRESS_BARS = ProgressBars()

FAILURES = []


class Writer:
    """
    Context manager for handling download writes
    """

    def __init__(self, filename, response, directory=None):
        self.filename = filename
        self.response = response
        self.size = int(response.headers.get("content-length", "0").strip())
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


def get_track_filename(track_url: str):
    _ = os.path.basename(urlparse(track_url).path)
    return url2pathname(_).replace("+", " ")


class RadioNatTurner:
    def __init__(self, url: str):
        self.browser = webdriver.Firefox()
        self.url = url
        self.folder_name = f"data{urlparse(self.url).path}"
        if not os.path.isdir(self.folder_name):
            os.mkdir(self.folder_name)

    def login(self):
        self.browser.get(self.url)
        self.browser.set_window_size(200, 200)
        print(f"{Style.RESET_ALL}signing in @ {Fore.YELLOW}{self.url}")
        password_input = self.browser.find_element_by_class_name("password-input")
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)

    def scrape(self):
        """
        Make it do what it do baby
        """
        self.login()

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "audio-block"))
        )

        tracks = self.browser.find_elements_by_class_name("audio-block")
        _ = f"{Fore.YELLOW}{len(tracks)}{Style.RESET_ALL}"
        print(f"found {_} tracks")
        print(f"saving to {Fore.YELLOW}{self.folder_name}")

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

            # Already exists?
            track_filename = get_track_filename(track_url)
            if os.path.isfile(f"{self.folder_name}/{track_filename}"):
                _ = f"{Fore.LIGHTBLUE_EX}{track_filename}"
                print(f"{Fore.BLUE}...skipping {_}{Fore.BLUE} [already saved]")
                filecounter.update(1)
                continue

            # Get file as stream
            response = requests.get(track_url, stream=True)

            if not response.ok:

                # 429 Too Many Requests
                if response.status_code == 429:
                    print(
                        f"{Fore.WHITE}{Back.RED} 😈 429 - Too Many Requests. Restarting {self.folder_name} {Style.RESET_ALL}"
                    )
                    self.browser.close()
                    self.browser = webdriver.Firefox()
                    return self.scrape()

                # Push any other failure data to FAILURES array and continue
                failure = {
                    "response": f"{response.status_code} {response.reason}",
                    "title": title,
                    "artist": artist,
                    "track_url": track_url,
                    "track_filename": track_filename,
                }
                print(
                    f"{Fore.RED}{artist} - {title} failed: {response.status_code} {response.reason}{Style.RESET_ALL} 😢"
                )
                FAILURES.append(failure)
                continue

            # Save file to disk
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

    for failure in FAILURES:
        msg = f"💀 {failure.get('artist')} - {failure.get('title')} failed! 💀"
        print(f"{Back.RED}{Fore.WHITE} {msg} {Style.RESET_ALL}")
        print(f"{Fore.RED}{json.dumps(failure)}")
