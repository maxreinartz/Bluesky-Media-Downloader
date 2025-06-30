# Bluesky Media Downloader
Download media (images and videos) from Bluesky with this simple CLI tool. Media can be downloaded from users' posts, likes, and feeds. Uses ffmpeg to convert .m3u8 to .mp4.

## Instructions

1. Make an .env file containing the following details
- BSKY_USERNAME: Your Bluesky account's username
- BSKY_APP_TOKEN: An app token for the account. Get an app token by going to Settings > Privacy and Security > App Passwords

  Example:
```
BSKY_USERNAME="myaccount.com"
BSKY_APP_TOKEN="abcd-efgh-ijkl-mnop"
```
2. Run the command
```
python main.py <account (str)> <max_posts (int | str)> <posts_likes_feeds (str)>
```
```
# Examples
python main.py frieren.websunday.net all posts
python main.py frieren.websunday.net 25 likes
python main.py frieren.websunday.net 10 feeds # all is not supported for feeds
```

## LICENSE

This project is licensed under the MIT License.