from selenium import webdriver
from selenium.webdriver.common.by import By
from pushbullet import Pushbullet
from datetime import datetime
import time


class Prayer:
    def __init__(self, name, hour=None, minute=None):
        self.name = name
        self.hour = hour
        self.reminder_hour = None
        self.minute = minute
        self.reminder_minute = None
        self.active = True

    def update_time(self, time):
        """
        Updates the time the prayer is at
        :param time: string
        :return: None
        """
        self.hour, self.minute = Prayer.format_time(time)

    def update_reminder_time(self, offset):
        """
        Updates reminder time by offsetting the prayer time
        :param offset: int
        :return: None
        """
        if self.minute < offset:
            self.reminder_hour = (self.hour - 1 - (self.minute // 60)) % 24
            self.reminder_minute = (self.minute - offset) % 60
        else:
            self.reminder_hour = self.hour
            self.reminder_minute = self.minute - offset

    def check(self, time, token, offset):
        """
        Checks if the current time is after the reminder time and if so sends a notif
        :param time: datetime.datetime object
        :param token: string
        :param offset: int
        :return: None
        """
        current_hour = int(time.hour)+1%24
        current_minute = int(time.minute)
        if self.active:
            if (self.reminder_hour == current_hour) and (self.minute >= current_minute >= self.reminder_minute):
                self.active = False
                print(f"{self.name} in {offset} minutes!")
                while True:
                    try:
                        devices = Pushbullet(token)
                        push = devices.push_note(f"Prayer Reminder", f"{self.name} at {self.hour}:{self.minute}! Less than {offset} minutes!")
                        break
                    except Exception as e:
                        print(e)

    def reset(self):
        """
        Resets the prayer back to active
        :return: None
        """
        self.active = True

    def __repr__(self):
        """
        Creates a string with all the attributes of the prayer
        :return: string
        """
        return f"{self.name} - {self.hour}:{self.minute} - {self.reminder_hour}:{self.reminder_minute}"

    @staticmethod
    def format_time(time):
        """
        Formats 12 hour time into 24 hour time
        :param time: string
        :return: int, int
        """
        hour = int(time[:-6])
        minute = int(time[-5:-3])
        if time[-2:] == "pm":
            hour += 12
        return hour, minute


def get_raw_times():
    """
    Scrapes the prayer times from the masjid's website into creates a list of them
    :return: List of strings
    """
    raw_times = []
    while True:
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument('--disable-blink-features=AutomationControlled')
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(30)
            driver.get("https://masjidalfarouq.org.uk/%22")
            raw_times = driver.find_elements(By.CLASS_NAME, "ds-time")
            raw_times = [raw_times[2].text, raw_times[5].text, raw_times[7].text, raw_times[9].text, raw_times[11].text]
            driver.quit()
            break
        except Exception as e:
            print(e)
        time.sleep(1)
    return raw_times


def get_prayers():
    """
    Instantiates each of the five daily prayers into a list
    :return: List of Prayer objects
    """
    prayers = []
    fajr = Prayer("Fajr")
    zuhr = Prayer("Zuhr")
    asr = Prayer("Asr")
    maghrib = Prayer("Maghrib")
    isha = Prayer("Isha")
    prayers.append(fajr)
    prayers.append(zuhr)
    prayers.append(asr)
    prayers.append(maghrib)
    prayers.append(isha)
    return prayers


def main():
    OFFSET = 15
    TOKEN = "**********************"
    prayers = get_prayers()
    raw_times = get_raw_times()
    print(raw_times)

    for raw_time, prayer in zip(raw_times, prayers):
        prayer.update_time(raw_time)
        prayer.update_reminder_time(OFFSET)
        print(prayer)

    while True:
        time.sleep(2)
        current_time = datetime.now()
        if (((int(current_time.hour)+1) % 24) == 1) and not prayers[4].active:
            raw_times = get_raw_times()
            for raw_time, prayer in zip(raw_times, prayers):
                prayer.reset()
                prayer.update_time(raw_time)
                prayer.update_reminder_time(OFFSET)

        for prayer in prayers:
            prayer.check(current_time, TOKEN, OFFSET)


if __name__ == "__main__":
    main()
