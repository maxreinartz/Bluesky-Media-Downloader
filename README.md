# Bluesky Media Downloader
Download images from Bluesky with this simple cli tool.

## Instructions

1. Make an .env file containing the following details
- BSKY_USERNAME, your bluesky username
- BSKY_APP_TOKEN, an app token for said account

  Example:
```
BSKY_USERNAME="myaccount.com"
BSKY_APP_TOKEN="abcd-efgh-ijkl-mnop"
```
2. Run the command
```
python main.py <account (str)> <max_posts (int)> <posts_likes (str)>
```
```
# Example
python main.py frieren.websunday.net 10 posts
```

## LICENSE

This project is licensed under the MIT License.