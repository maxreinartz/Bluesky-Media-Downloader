"""Fetches posts from Bluesky and downloads media from them."""

import sys, os, requests
from dotenv import load_dotenv
from atproto import Client
from atproto_identity.resolver import IdResolver

load_dotenv()

account = "";
max_posts = 25;

def fetch_posts(account, max_posts):
  """
  Fetches posts from the given account and downloads media from them.

  Args:
    account (str): The account to fetch posts from.
    max_posts (int): The maximum number of posts to fetch.
  """
  client = Client()
  # Login via app token from .env
  print(f"Logging in as {os.getenv('BSKY_USERNAME')}")
  client.login(os.getenv('BSKY_USERNAME'), os.getenv('BSKY_APP_TOKEN'))
  # Resolve the account to a DID
  user_did = IdResolver().handle.resolve(account)
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
      
      response = client.get_author_feed(user_did, limit=limit, cursor=cursor)
      feed.extend(response.feed)
      cursor = response.cursor
      fetched_posts += len(response.feed)
      if not cursor:
        print("No more posts to fetch.")
        break
  else:
    posts = client.get_author_feed(user_did, limit=max_posts)
    feed = posts.feed

  return feed

def dowload_media(posts):
  """
  Downloads media from the given posts.

  Args:
    posts (list): The list of posts to download media from.

  Returns:
    Total number of media downloaded.
  """

  total_media = 0
  new_media = 0
  dowloaded_media = 0

  for post in posts:
    for view_image in post.post.embed.images:
      total_media += 1
      img_url = view_image.fullsize
      filename = f"{post.post.record.created_at.replace(':', '-')}_{post.post.uri.split('/')[-1]}_{img_url.split('@')[0][-5:]}.{img_url.split('@')[-1]}"
      filepath = os.path.join(account, filename)
      if not os.path.exists(account):
        os.makedirs(account)
      if not os.path.exists(filepath):
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
          with open(filepath, 'wb') as f:
            for chunk in response.iter_content(1024):
              f.write(chunk)
          print(f"Downloaded {filename} | {dowloaded_media}/{total_media}")
          dowloaded_media += 1
          new_media += 1
        else:
          print(f"Failed to download {img_url}")
          # Save the failed url to a file
          with open("failed_urls.txt", "a") as f:
            f.write(f"{img_url}\n")
      else:
        print(f"{filepath} already exists, skipping download")
        dowloaded_media += 1
  
  return dowloaded_media, new_media, total_media

def main():
  print("========================================")
  print("Bluesky Media Downloader")
  print("By @maxreinartz.dev")
  print("========================================")
  print(f"Fetching {max_posts} post(s) from {account}")
  
  posts = fetch_posts(account, max_posts)
  # print(posts)
  print(f"Fetched {len(posts)} post(s) from {account}")
  print("Removing posts without media...")
  # Filter out posts without media
  posts = [post for post in posts if post.post.record.embed and getattr(post.post.record.embed, "images", None)]
  print(f"Found {len(posts)} post(s) with media")
  print("Beginning to download media")
  downloaded, new, total = dowload_media(posts)
  print(f"Downloaded {downloaded}/{total} media files, {new} newly downloaded")

if __name__ == '__main__':
  """
  Args:
    account (str): The account to fetch posts from.
    max_posts (int): The maximum number of posts to fetch.
  """
  # Get arguments from command line
  if len(sys.argv) <= 2:
    print("Not enough arguments.")
    print("Usage: python main.py <account> [max_posts]")
    sys.exit(1)

  account = sys.argv[1]
  if(sys.argv[2].isnumeric()):
    max_posts = int(sys.argv[2])
  else:
    print("Max posts must be a number.")
    print("Usage: python main.py <account> [max_posts]")
    sys.exit(1)

  main();