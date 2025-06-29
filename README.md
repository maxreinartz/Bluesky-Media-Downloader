# Bluesky Media Downloader
Download media from Bluesky with this simple CLI tool.

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
python main.py <account (str)> <max_posts (int | str)> <posts_likes (str)>
```
```
# Example
python main.py frieren.websunday.net 10 posts
```

## LICENSE

This project is licensed under the MIT License.