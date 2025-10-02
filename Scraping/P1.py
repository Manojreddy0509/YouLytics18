def get_vid(url):
    if "v=" in url:
        vid = url.split("v=")[1]
        return vid.split("&")[0]
    elif "youtu.be/" in url:
        vid = url.split("youtu.be/")[1]
        return vid.split("?")[0]
    else:
        return None
    
    
# url="https://youtu.be/j4dMnAPZu70"
# video_id=get_vid(url)
# print(video_id)

