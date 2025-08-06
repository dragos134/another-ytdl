import subprocess
import os
from datetime import datetime
from yt_dlp import YoutubeDL

LINKS_FILE = 'links.txt'
GLOBAL_ARCHIVE = 'global_archive.txt'
ARCHIVE_FOLDER = 'archive'

def create_date_folder():
    today = datetime.now().strftime('%d-%m-%Y')
    folder_path = os.path.join(ARCHIVE_FOLDER, today)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path, today

def load_global_archive():
    if not os.path.exists(GLOBAL_ARCHIVE):
        return set()
    with open(GLOBAL_ARCHIVE, 'r', encoding='utf-8') as f:
        return set(line.split(' - ')[0].strip() for line in f if line.strip())

def save_to_global_archive(link, title, date):
    with open(GLOBAL_ARCHIVE, 'a', encoding='utf-8') as f:
        f.write(f"{link} - {title} - {date}\n")

def save_to_daily_archive(log_path, link):
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(link + '\n')

def extract_video_entries(link):
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',  # so it doesn't download now
        'force_generic_extractor': False,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            if 'entries' in info:
                return [entry['url'] for entry in info['entries']]
            else:
                return [info['webpage_url']]
    except Exception as e:
        print(f"Failed to extract info for {link}: {e}")
        return []

def download_video(link, output_format, output_dir):
    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
    date = datetime.now().strftime('%d-%m-%Y')

    common_opts = {
        'outtmpl': output_template,
        'noplaylist': False,
        'quiet': False,
        'no_warnings': True,
        'ignoreerrors': True,
    }

    if output_format == 'mp3':
        ydl_opts = {
            **common_opts,
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',
            }]
        }
    else:
        ydl_opts = {
            **common_opts,
            'format': 'best[ext=mp4]/best'
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(link, download=True)
            if result is None:
                return None
            if 'title' in result:
                return result['title']
            elif isinstance(result, list) and 'title' in result[0]:
                return result[0]['title']
    except Exception as e:
        print(f"Error downloading {link}: {e}")
    return None

def main():
    output_format = input("Enter desired format (mp3 or mp4): ").strip().lower()
    if output_format not in ['mp3', 'mp4']:
        print("Invalid format. Use 'mp3' or 'mp4'.")
        return

    if not os.path.exists(LINKS_FILE):
        print(f"No {LINKS_FILE} file found.")
        return

    with open(LINKS_FILE, 'r', encoding='utf-8') as f:
        raw_links = [line.strip() for line in f if line.strip()]

    if not raw_links:
        print("No links found in links.txt.")
        return

    downloaded_links = load_global_archive()
    date_folder, date_str = create_date_folder()
    daily_log_path = os.path.join(date_folder, 'downloaded-list.txt')

    new_links = []

    for raw_link in raw_links:
        entries = extract_video_entries(raw_link)
        for entry_url in entries:
            if entry_url not in downloaded_links:
                new_links.append(entry_url)
            else:
                print(f"Skipping already downloaded: {entry_url}")

    if not new_links:
        print("No new videos to download.")
        return

    for idx, link in enumerate(new_links, 1):
        print(f"Downloading ({idx}/{len(new_links)}): {link}")
        title = download_video(link, output_format, date_folder)
        if title:
            save_to_global_archive(link, title, date_str)
            save_to_daily_archive(daily_log_path, link)
        else:
            with open('failed.txt', 'a', encoding='utf-8') as fail_log:
                fail_log.write(link + '\n')

    open(LINKS_FILE, 'w').close()
    print("All downloads complete.")

if __name__ == '__main__':
    main()
