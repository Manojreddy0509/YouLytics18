import googleapiclient.discovery
import os
from dotenv import load_dotenv
import time

load_dotenv()

def get_comments(video_id, api_key=None, max_comments=200):
    if api_key is None:
        api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YouTube API key is required")

    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        all_comments = []

        # Get all top-level comments
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100,
            order="relevance"   # Changed to relevance to get better quality comments first
        )

        while request and len(all_comments) < max_comments:
            response = request.execute()
            for item in response.get("items", []):
                # Stop if we reached the limit
                if len(all_comments) >= max_comments:
                    break

                # Top-level comment
                top_comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"].strip()
                if top_comment:
                    all_comments.append(top_comment)

                # Get replies if we still have room
                if len(all_comments) < max_comments:
                    parent_id = item["snippet"]["topLevelComment"]["id"]
                    # Limit replies per comment to avoid deep rabbit holes
                    replies = get_replies(youtube, parent_id, max_replies=5) 
                    for reply in replies:
                        if len(all_comments) >= max_comments:
                            break
                        all_comments.append(f"↳ {reply}")

            # Pagination
            if len(all_comments) < max_comments:
                request = youtube.commentThreads().list_next(request, response)
                # break if no next page
                if not request: 
                    break
                time.sleep(0.1)  # be gentle with API quota
            else:
                break

        print(f"✅ Collected {len(all_comments)} comments (Limit: {max_comments})")
        return all_comments

    except Exception as e:
        print(f"⚠️ Error fetching comments: {e}")
        # Return whatever we have so far instead of failing completely
        return all_comments


def get_replies(youtube, parent_id, max_replies=5):
    """Fetch replies for a given top-level comment (limited)."""
    replies = []
    try:
        request = youtube.comments().list(
            part="snippet",
            parentId=parent_id,
            textFormat="plainText",
            maxResults=max_replies  # Only fetch a few replies
        )

        # We only take the first page of replies to be fast
        response = request.execute()
        for item in response.get("items", []):
            reply_text = item["snippet"]["textDisplay"].strip()
            if reply_text:
                replies.append(reply_text)
            
        return replies
    except Exception:
        return []


# Example usage
if __name__ == "__main__":
    video_id = "YOUR_VIDEO_ID_HERE"  # Replace with actual video ID
    comments = get_all_comments(video_id)

    # Save to file
    with open(f"comments_{video_id}.txt", "w", encoding="utf-8") as f:
        for i, comment in enumerate(comments, 1):
            f.write(f"{i}. {comment}\n")

    print(f"📂 Comments saved to comments_{video_id}.txt")
