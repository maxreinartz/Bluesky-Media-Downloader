"""Fetches posts from Bluesky and downloads media from them."""

import sys, os, asyncio, aiohttp, time, ffmpeg
from dotenv import load_dotenv
from atproto import Client
from atproto_identity.resolver import IdResolver

load_dotenv()

version = "1.5"
account = ""
user_did = ""
user_feed = ""
max_posts = 25
posts_likes_feeds = ""
downloaded_m3u8 = []

def fetch_posts(max_posts, posts_likes_feeds, client):
  """
  Fetches posts from the given account and returns them.

  Args:
    account (str): The account to fetch posts from.
    max_posts (int): The maximum number of posts to fetch.
    posts_likes_feeds (str): The type of feed to fetch, either 'likes' or 'posts'.
  """
  # print(f"{account}, {user_did}")
  # Get the feed of the account (posts)
  feed = []
  if max_posts > 100:
    cursor = None
    fetched_posts = 0
    while True:
      # Check if fetched_posts is within 100 of max_posts, if so, set limit to max_posts - fetched_posts
      if max_posts - fetched_posts <= 100:
        limit = max_posts - fetched_posts
        if limit <= 0:
          break
      else:
        limit = 100
      
      if posts_likes_feeds == "posts":
        response = client.get_author_feed(user_did, limit=limit, cursor=cursor)
      elif posts_likes_feeds == "likes":
        response = client.app.bsky.feed.get_actor_likes({'actor': user_did, 'limit': limit, 'cursor': cursor})
      elif posts_likes_feeds == "feeds":
        response = client.app.bsky.feed.get_feed({'feed': user_feed, 'limit': limit, 'cursor': cursor})

      feed.extend(response.feed)
      cursor = response.cursor
      fetched_posts += len(response.feed)
      if not cursor:
        print("No more posts to fetch.")
        break
  else:
    if posts_likes_feeds == "posts":
      posts = client.get_author_feed(user_did, limit=max_posts)
    elif posts_likes_feeds == "likes":
      posts = client.app.bsky.feed.get_actor_likes({'actor': user_did, 'limit': max_posts})
    elif posts_likes_feeds == "feeds":
      posts = client.app.bsky.feed.get_feed({'feed': user_feed, 'limit': max_posts})
    
    feed = posts.feed

  return feed

async def dowload_media(posts):
  """
  Downloads media from the given posts.

  Args:
    posts (list): The list of posts to download media from.

  Returns:
    Total number of media downloaded.
  """

  async with aiohttp.ClientSession() as session:
    tasks = []
    total_media = 0
    new_media = 0
    dowloaded_media = 0

    # * DEBUG - Write posts to file
    #with open("posts.txt", "w", encoding="utf-8") as f:
    #  for post in posts:
    #    f.write(f"{post}\n")

    for post in posts:
      # Check if the post has an embed with images or video
      if hasattr(post.post.embed, 'images') and post.post.embed.images:
        for view_image in post.post.embed.images:
          total_media += 1
          img_url = view_image.fullsize
          filename = f"{post.post.record.created_at.replace(':', '-')}_{post.post.uri.split('/')[-1]}_{img_url.split('@')[0][-5:]}.{img_url.split('@')[-1]}"
          folder_name = f"{account}_{posts_likes_feeds}"
          filepath = os.path.join(folder_name, filename)
          if not os.path.exists(folder_name):
            os.makedirs(folder_name)
          if not os.path.exists(filepath):
            tasks.append(download_media(session, img_url, filepath, filename))
            sys.stdout.write(f"\r{' ' * 80}\rScheduled {filename} | {dowloaded_media}/{total_media}")
            sys.stdout.flush()
          else:
            sys.stdout.write(f"\r{' ' * 80}\r{filename} already exists, skipping download")
            sys.stdout.flush()
            dowloaded_media += 1
      elif hasattr(post.post.embed, 'playlist') and post.post.embed.playlist:
        total_media += 1
        video_url = post.post.embed.playlist
        filename = f"{post.post.record.created_at.replace(':', '-')}_{post.post.uri.split('/')[-1]}.m3u8"
        folder_name = f"{account}_{posts_likes_feeds}"
        filepath = os.path.join(folder_name, filename)
        if not os.path.exists(folder_name):
          os.makedirs(folder_name)
        if not os.path.exists(filepath):
          tasks.append(download_media(session, video_url, filepath, filename))
          sys.stdout.write(f"\r{' ' * 80}\rScheduled {filename} | {dowloaded_media}/{total_media}")
          sys.stdout.flush()
        else:
          sys.stdout.write(f"\r{' ' * 80}\r{filename} already exists, skipping download")
          sys.stdout.flush()
          dowloaded_media += 1

    print()
    results = await asyncio.gather(*tasks)
    for result in results:
      if(result == 0):
        dowloaded_media += 1
        new_media += 1
  
  return dowloaded_media, new_media, total_media

async def download_media(session, url, filepath, filename):
  """
  Downloads an image from the given URL and saves it to the specified filepath.

  Args:
    session (aiohttp.ClientSession): The aiohttp session to use for the request.
    url (str): The URL of the image to download.
    filepath (str): The path where the image should be saved.
  """
  async with session.get(url) as response:
    with open(filepath, 'wb') as f:
      if response.status != 200:
        print(f"Failed to download {url}: {response.status}")
        return None
      content = await response.read()
      f.write(content)
      downloaded_m3u8.append(f"{filepath};{url.replace('playlist.m3u8', '')}") if url.endswith(".m3u8") else None
      # Clear the terminal line
      sys.stdout.write(f"\r{' ' * 80}\rDownloaded {filename}...")
      sys.stdout.flush()
      return 0

def main():
  global account, max_posts, posts_likes_feeds, user_did, user_feed

  start_time = time.time()

  print("========================================")
  print(f"Bluesky Media Downloader [{version}]")
  print("By @maxreinartz.dev")
  print("========================================")

  # Create a client instance
  client = Client()
  # Login via app token from .env
  print(f"Logging in as {os.getenv('BSKY_USERNAME')}")
  client.login(os.getenv('BSKY_USERNAME'), os.getenv('BSKY_APP_TOKEN'))
  # Resolve the account to a DID
  user_did = IdResolver().handle.resolve(account)
  if not user_did:
    print(f"Could not resolve account {account} to a DID. Please check the account name.")
    sys.exit(1)
  account_string = client.get_profile(user_did).display_name + f" [{account}]"

  if(posts_likes_feeds == "feeds"):
    feeds = client.app.bsky.feed.get_actor_feeds({'actor': user_did})
    if not feeds.feeds:
      print(f"No feeds found for {account_string}.")
      sys.exit(1)
    print(f"Found {len(feeds.feeds)} feeds for {account_string}")
    print("Available feeds:")
    for i, feed in enumerate(feeds.feeds):
      print(f"{i+1}. {feed.display_name} - {feed.description}")
    feed_choice = input("Enter the number of the feed you want to download media from: ")
    try:
      feed_choice = int(feed_choice) - 1
      if feed_choice < 0 or feed_choice >= len(feeds.feeds):
        print("Invalid feed choice.")
        sys.exit(1)
      user_feed = feeds.feeds[feed_choice].uri
      print(f"Selected feed {feeds.feeds[feed_choice].display_name}")
    except ValueError:
      print("Invalid input. Please enter a number.")
      sys.exit(1)

  if(max_posts == -1):
    if(posts_likes_feeds == "feeds"):
      print(f"All is not supported for feeds. Defaulting to 100 posts.")
      max_posts = 100
    else:
      max_posts = client.get_profile(user_did).posts_count
      print(f"Fetching all posts from the account ({max_posts} posts)")

  print(f"Fetching {max_posts} post(s) from {account_string}'s {posts_likes_feeds}")
  posts = fetch_posts(max_posts, posts_likes_feeds, client)
  # print(posts)
  print(f"Fetched {len(posts)} post(s) from {account_string}'s {posts_likes_feeds}")
  print("Removing posts without media...")
  # Filter out posts without media
  posts = [post for post in posts if post.post.record.embed and (getattr(post.post.record.embed, "images", None) or getattr(post.post.record.embed, "video", None))]
  print(f"Found {len(posts)} post(s) with media")
  print("Beginning to download media")
  downloaded, new, total = asyncio.run(dowload_media(posts))
  end_time = time.time()
  print(f"\nDownloaded {downloaded}/{total} media files, {new} newly downloaded. Took {end_time - start_time:.2f} seconds")

  if downloaded_m3u8:
    print("Downloaded m3u8 files:")
    for m3u8 in downloaded_m3u8:
      print(f"- {m3u8}")
    print("Would you like to convert the m3u8 files to mp4? (y/n)")
    convert_choice = input().strip().lower()
    if convert_choice == 'y':
      for m3u8 in downloaded_m3u8:
        m3u8_parts = m3u8.split(';')
        filepath = m3u8_parts[0]
        url = m3u8_parts[1]
        if os.path.exists(filepath):
          with open(filepath, 'r') as f:
            m3u8_content = f.read()
          m3u8_lines = [line for line in m3u8_content.splitlines() if line and not line.startswith('#')]
          if m3u8_lines:
            for line in m3u8_lines:
              full_url = f"{url}{line}"
              mp4_filename = f"{filepath.replace('.m3u8', '')}_{line.split('/')[0]}.mp4"
              print(f"Converting {full_url} to {mp4_filename}")
              ffmpeg.input(full_url).output(mp4_filename, c='copy').run()
          else:
            print(f"No valid lines found in {filepath}. Skipping conversion.")
  else:
    print("No m3u8 files downloaded.")


if __name__ == '__main__':
  """
  Args:
    account (str): The account to fetch posts from.
    max_posts (int | str): The maximum number of posts to fetch.
    posts_likes_feeds (str): The type of feed to fetch, either 'likes', 'posts', or 'feeds'.
  """
  # Get arguments from command line
  if len(sys.argv) <= 3:
    print("Not enough arguments.")
    print("Usage: python main.py <account> [max_posts] [posts_likes_feeds]")
    sys.exit(1)

  if len(sys.argv) > 4:
    print("Too many arguments.")
    print("Usage: python main.py <account> [max_posts] [posts_likes_feeds]")
    sys.exit(1)

  account = sys.argv[1]
  if(sys.argv[2].isnumeric() and int(sys.argv[2]) > 0):
    max_posts = int(sys.argv[2])
  else:
    if(sys.argv[2].lower() == "all"):
      max_posts = -1
    else:
      print("Max posts must be a positive number or 'all'.")
      print("Usage: python main.py <account> [max_posts]")
      sys.exit(1)

  if(len(sys.argv) > 3):
    posts_likes_feeds = sys.argv[3].lower()
    if posts_likes_feeds not in ["likes", "posts", "feeds"]:
      print("Feed type must be either 'likes', 'posts', or 'feeds'.")
      print("Usage: python main.py <account> [max_posts] [posts_likes_feeds]")
      sys.exit(1)

  main();