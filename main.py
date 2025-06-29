"""Fetches posts from Bluesky and downloads media from them."""

import sys, os, requests
from dotenv import load_dotenv
from atproto import Client
from atproto_identity.resolver import IdResolver

load_dotenv()

version = "1.3"
account = ""
user_did = ""
user_feed = ""
max_posts = 25
posts_likes_feeds = ""

def fetch_posts(max_posts, posts_likes_feeds, client):
  """
  Fetches posts from the given account and downloads media from them.

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
      folder_name = f"{account}_{posts_likes_feeds}"
      filepath = os.path.join(folder_name, filename)
      if not os.path.exists(folder_name):
        os.makedirs(folder_name)
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
  global account, max_posts, posts_likes_feeds, user_did, user_feed

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
  posts = [post for post in posts if post.post.record.embed and getattr(post.post.record.embed, "images", None)]
  print(f"Found {len(posts)} post(s) with media")
  print("Beginning to download media")
  downloaded, new, total = dowload_media(posts)
  print(f"Downloaded {downloaded}/{total} media files, {new} newly downloaded")

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