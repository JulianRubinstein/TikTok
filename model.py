import time
from scipy import stats
from extract_data import extract_data

#Reject outlier videos and videos from last two days
def reject_outliers(video_views, video_times, outlier_sensitivity, videos_for_virality, num_days):

    #Internal variables
    current_time = time.time()
    days = 60*60*24 * num_days
    odds_of_virality = 0
    x_filtered = []
    video_views_filtered = []

    #Creating a list of the filtered videos and the video grid
    for index, value in enumerate(video_views):

        if ((current_time - video_times[index]) > days):
            if (stats.zscore(video_views)[index] < outlier_sensitivity):
                video_views_filtered.append(value)
                x_filtered.append(index)

            #Counting number of viral videos from past 10 videos and converting to odds of virality
            elif(len(video_views)-index < videos_for_virality):
                odds_of_virality += 1/videos_for_virality

    return [x_filtered,video_views_filtered, odds_of_virality]

#Fitting the model to filtered data
def fit_model(x_filtered, video_views_filtered, video_views):

    x=[i for i in range(len(video_views))]
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_filtered, video_views_filtered)
    next_video_views = slope*(len(video_views)) + intercept

    return [slope, intercept, p_value, next_video_views, x]

#Create a dictionary to send to the api request
def create_data(x, video_views, x_filtered, video_views_filtered, slope, intercept, p_value, next_video_views, odds_of_virality, outlier_sensitivity, followers, total_likes, user_id):
    data = {"video number":x,
            "video views":video_views,
            "filtered video number":x_filtered,
            "filtered video views":video_views_filtered,
            "odds of viral video":odds_of_virality,
            "slope":slope,
            "intercept":intercept,
            "p value":p_value,
            "predicted views":next_video_views,
            "outlier senitivity":outlier_sensitivity,
            "follower count":followers,
            "total likes":total_likes,
            "user name":user_id
            }
    return data

#The main function which calls all other functions
def model(user):

    #Default variables
    videos_num = 101 #Number of videos wanted
    videos_for_virality = 10 #Number of videos to check for virality
    num_days = 2 #Num of days to ignore

    #Defining list of various sensitivies and number of videos to check back.
    sensitivities = [0.1*i for i in range(1,11)]
    result_list = [10*i for i in range(1,11)]
    p_values=[]
    values=[]

    #Extracting the data using the tiktokapi
    video_views, video_times, followers, total_likes, user_id = extract_data(user, videos_num)

    #Checking the p_value for various video numbers and sensitivities
    for result in result_list:
        for outlier_sensitivity in sensitivities:
            video_views = video_views[-result:]
            video_times = video_times[-result:]
            x_filtered, video_views_filtered, odds_of_virality = reject_outliers(video_views, video_times, outlier_sensitivity, videos_for_virality, num_days)
            slope, intercept, p_value, next_video_views, x = fit_model(x_filtered, video_views_filtered, video_views)
            values.append((result, outlier_sensitivity))
            p_values.append(p_value)

    #Choosing the video with best p_value
    result, outlier_sensitivity = values[p_values.index(max(p_values))]

    #Using the relevant part of the data according to above p_value (without re-extracting the data for perfomance purposes)
    video_views = video_views[-result:]
    video_times = video_times[-result:]

    #Refiting the data with the best p_value and creating the data that will be sent to the client
    x_filtered, video_views_filtered, odds_of_virality = reject_outliers(video_views, video_times, outlier_sensitivity, videos_for_virality, num_days)
    slope, intercept, p_value, next_video_views, x = fit_model(x_filtered, video_views_filtered, video_views)
    data = create_data(x, video_views, x_filtered, video_views_filtered, slope, intercept, p_value, next_video_views, odds_of_virality, outlier_sensitivity, followers, total_likes, user_id)

    #Returning the data
    return data
