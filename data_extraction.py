import requests


def extract_data(user, videos_num):
    """Acquiring the videos and arranging
    the view numbers in a list (reversing as
    the original order is newer first)"""

    url = "https://tiktok.p.rapidapi.com/live/user/feed"
    querystring = {"username":user, "limit":videos_num}

    headers = {
        'x-rapidapi-key': "PRIVATE",
        'x-rapidapi-host': "tiktok.p.rapidapi.com"
        }

    response = requests.request("GET", url, headers=headers, params=querystring)
    videos = response.json()['media']

    video_views = list([video['statistics']['playCount'] for video in videos])
    video_times = list([int(video['create_time']) for video in videos])
    video_views.reverse()
    video_times.reverse()

    followers =  videos[0]['author']['followers']
    total_likes = videos[0]['author']['heartCount']
    user_id = videos[0]['author']['uniqueId']

    return [video_views, video_times, followers, total_likes, user_id]
