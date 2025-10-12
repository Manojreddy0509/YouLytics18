def get_vid(url):
    if "v=" in url:
        # normal YouTube URL
        vid = url.split("v=")[1]
        return vid.split("&")[0]
    elif "youtu.be/" in url:
        # shortened URL
        vid = url.split("youtu.be/")[1]
        return vid.split("?")[0]
    elif "youtube.com/shorts/" in url:
        # YouTube Shorts URL
        vid = url.split("youtube.com/shorts/")[1]
        return vid.split("?")[0]
    else:
        return None



