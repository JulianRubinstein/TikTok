from TikTokApi import TikTokApi
from TikTokApi.browser import set_async
import time
import matplotlib.pyplot as plt
from scipy import stats
from flask import Flask, request, jsonify
from flask_restful import Api, Resource

#Setting the TikTok API
set_async()
tiktokapi = TikTokApi()

#Acquiring the videos and arranging the view numbers in a list (reversing as the original order is newer first)
def extract_data(tiktokapi, user, videos_num):
    videos = tiktokapi.byUsername(username=user, count=videos_num)
    video_views = list([video['stats']['playCount'] for video in videos])
    video_times = list([video['createTime'] for video in videos])
    video_views.reverse()
    video_times.reverse()
    return [video_views, video_times]

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
    next_video_views = int(slope*(len(video_views)) + intercept)

    return [slope, intercept, p_value, next_video_views, x]

#Printing data for internal use
def print_model(x, slope, intercept, video_views, x_filtered, video_views_filtered, user, odds_of_virality, next_video_views, p_value, result, outlier_sensitivity):

     #Bulding figure
     plt.figure()
     plt.plot(x, [slope*k + intercept for k in x], label = "Fitted model")
     plt.scatter(len(video_views),slope*(len(video_views)) + intercept, label = "Next video prediction")
     plt.scatter(x,video_views, label='Ignored data')
     plt.scatter(x_filtered,video_views_filtered, label='Fitted data')
     plt.title("Views vs Video: " + user)
     plt.xlabel('Video')
     plt.ylabel('Number of views')
     plt.legend()

     #Printing data
     print("The odds to go viral are " + str(int(odds_of_virality*100)) + "%")
     if (next_video_views>0):
         print("The predicted views for the next video are " + str(next_video_views))
     else:
         print("The predicted views for the next video are below zero")
     print("The p value is: " + str(p_value) + " (above 0.05 is reccomended)")
     print("The number videos chosen: " + str(result))
     print(" The outlier sensitivity of: " + str(outlier_sensitivity))
     return None

#Create a dictionary to send to the api request
def create_data(x, video_views, x_filtered, video_views_filtered, slope, intercept, p_value, next_video_views, odds_of_virality, outlier_sensitivity):
    data = {"x":x,
            "video_views":video_views,
            "x_filtered":x_filtered,
            "video_views_filtered":video_views_filtered,
            "odds_of_virality":odds_of_virality,
            "slope":slope,
            "intercept":intercept,
            "p_value":p_value,
            "next_video_views":next_video_views,
            "outlier_senitivity":outlier_sensitivity
            }
    return data

#The main function which calls all other functions
def model(user):

    #Default variables
    videos_num = 100 #Number of videos wanted
    videos_for_virality = 10 #Number of videos to check for virality
    num_days = 2 #Num of days to ignore

    #Defining list of various sensitivies and number of videos to check back.
    sensitivities = [0.1*i for i in range(1,11)]
    result_list = [10*i for i in range(1,11)]
    p_values=[]
    values=[]

    #Extracting the data using the tiktokapi
    video_views, video_times = extract_data(tiktokapi, user, videos_num)

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
    data = create_data(x, video_views, x_filtered, video_views_filtered, slope, intercept, p_value, next_video_views, odds_of_virality, outlier_sensitivity)

    #Printing data for internal use
    print_model(x, slope, intercept, video_views, x_filtered, video_views_filtered, user, odds_of_virality, next_video_views, p_value, result, outlier_sensitivity)

    #Returning the data
    return data

app = Flask(__name__)
api = Api(app)

class Data(Resource):
   def post(self):
       #Requesting a user from the client and returning the dataset
       postedData = request.get_json()
       user = postedData["user"]
       return model(user)

api.add_resource(Data, "/")

if __name__=="__main__":
    app.run(port=5003, debug=True)
