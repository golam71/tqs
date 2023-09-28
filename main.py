import multiprocessing
import requests
from bs4 import BeautifulSoup
import re
import logging
import os
import json
from flask import Flask
import time

# Define constants
TAFSIR_NO = 109
TOTAL_SURAH_COUNT = 114

# Configure logging
logging.basicConfig(level=logging.ERROR)


def get_ayat_count(surah_number):
  api_url = f"https://api.alquran.cloud/v1/surah/{surah_number}"
  try:
    response = requests.get(api_url)
    response.raise_for_status()
    data = response.json()
    if 'data' in data and 'numberOfAyahs' in data['data']:
      return data['data']['numberOfAyahs']
  except requests.exceptions.RequestException as e:
    print(f"Error fetching Ayat count for Surah {surah_number}: {e}")
  except Exception as e:
    print(f"An unexpected error occurred: {e}")
  return None


def get_all_text(url):
 
  try:
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    font_tags = soup.select("font[color='black']")
    merged_text = ""

    for font_tag in font_tags:
      text = font_tag.text.strip()
      if text:
        merged_text += text + ' '

    return merged_text
  except requests.exceptions.RequestException as e:
    print(f"Error fetching URL {url}: {e}")
  except Exception as e:
    print(f"An unexpected error occurred: {e}")
  return ""


def get_all_pages(url):
  try:
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    u_tags = soup.select('u')
    largest_one_digit_number = None

    for u_tag in u_tags:
      text = u_tag.get_text()
      one_digit_numbers = re.findall(r'\b[1-9]\b', text)

      if one_digit_numbers:
        number = int(one_digit_numbers[0])

        if largest_one_digit_number is None or number > largest_one_digit_number:
          largest_one_digit_number = number

    return largest_one_digit_number
  except requests.exceptions.RequestException as e:
    print(f"Error fetching URL {url}: {e}")
  except Exception as e:
    print(f"An unexpected error occurred: {e}")
  return None


def fetch_and_save_text(surah_number, tafsir_number, tafsir_directory):

  ayah_count = get_ayat_count(surah_number)

  if ayah_count is None:
    print(f"Error fetching Ayat count for Surah {surah_number}")
    return

  surah_directory = os.path.join(tafsir_directory, str(surah_number))
  if not os.path.exists(surah_directory):
    os.makedirs(surah_directory)

  for ayah_number in range(1, ayah_count + 1):
    page_number = 1
   
    url = f"https://www.altafsir.com/Tafasir.asp?tMadhNo=0&tTafsirNo={tafsir_number}&tSoraNo={surah_number}&tAyahNo={ayah_number}&tDisplay=yes&Page={page_number}&UserProfile=0&LanguageId=2"

    pages = get_all_pages(url)
    if pages is None:
      pages = 1  # Default to 1 page if page count is not found

    merged_text = ""

    # Loop over all pages and merge the text
    for page in range(1, pages + 1):
      url = f"https://www.altafsir.com/Tafasir.asp?tMadhNo=0&tTafsirNo={tafsir_number}&tSoraNo={surah_number}&tAyahNo={ayah_number}&tDisplay=yes&Page={page}&UserProfile=0&LanguageId=2"
      page_text = get_all_text(url)
      if page_text:
        merged_text += page_text + ' '

    if not merged_text.strip():
      merged_text = "No tafsir found."

    ayah_data = {
      "text": merged_text.strip()
    }  # Create a dictionary to store Ayah data
    print(f"Surah: {surah_number}, Ayah: {ayah_number}/{ayah_count}"
          )  # Print progress

    # Save the current Ayah data to a JSON file
    ayah_filename = os.path.join(surah_directory, f"{ayah_number}.json")
    with open(ayah_filename, 'w', encoding='utf-8') as json_file:
      json.dump(ayah_data, json_file, ensure_ascii=False)


def main():
  # Create a directory for storing the tafsir files
  tafsir_directory = f"tafsir{TAFSIR_NO}"
  if not os.path.exists(tafsir_directory):
    os.makedirs(tafsir_directory)

  for surah_number in range(3, TOTAL_SURAH_COUNT + 1):
    fetch_and_save_text(surah_number, TAFSIR_NO, tafsir_directory)

  print(f"Data collection completed.")


#flask code is only to keep the functionality of pinging so it doesn't go to sleep
app = Flask(__name__)


@app.route('/')
def hello_world():
  return 'Hello, World!'


def run_flask():
  app.run(host='0.0.0.0', port=81)


if __name__ == "__main__":
  # Start the main() function in a separate process
  main_process = multiprocessing.Process(target=main)
  main_process.start()

  # Start the Flask application in a separate process
  flask_process = multiprocessing.Process(target=run_flask)
  flask_process.start()

  # Wait for both processes to finish
  main_process.join()
  flask_process.join()
