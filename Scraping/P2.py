import googleapiclient.discovery
import os
from dotenv import load_dotenv
import time

load_dotenv()

def get_comments(video_id, api_key=None):
    if api_key is None:
        api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YouTube API key is required")

    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    all_comments = []

    # Get all top-level comments
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        textFormat="plainText",
        maxResults=100,
        order="time"   # ensures all comments are retrieved, not just "relevant"
    )

    while request:
        response = request.execute()
        for item in response.get("items", []):
            # Top-level comment
            top_comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"].strip()
            if top_comment:
                all_comments.append(top_comment)

            # Get ALL replies for this top-level comment
            parent_id = item["id"]
            replies = get_replies(youtube, parent_id)
            for reply in replies:
                all_comments.append(f"↳ {reply}")

        # Pagination
        request = youtube.commentThreads().list_next(request, response)
        time.sleep(0.1)  # be gentle with API quota

    print(f"✅ Collected {len(all_comments)} comments (including replies)")
    return all_comments


def get_replies(youtube, parent_id):
    """Fetch all replies for a given top-level comment (handles pagination)."""
    replies = []
    request = youtube.comments().list(
        part="snippet",
        parentId=parent_id,
        textFormat="plainText",
        maxResults=100
    )

    while request:
        response = request.execute()
        for item in response.get("items", []):
            reply_text = item["snippet"]["textDisplay"].strip()
            if reply_text:
                replies.append(reply_text)
        request = youtube.comments().list_next(request, response)
        time.sleep(0.1)

    return replies


# Example usage
if __name__ == "__main__":
    video_id = "YOUR_VIDEO_ID_HERE"  # Replace with actual video ID
    comments = get_all_comments(video_id)

    # Save to file
    with open(f"comments_{video_id}.txt", "w", encoding="utf-8") as f:
        for i, comment in enumerate(comments, 1):
            f.write(f"{i}. {comment}\n")

    print(f"📂 Comments saved to comments_{video_id}.txt")
