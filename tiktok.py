from TikTokApi import TikTokApi
from TikTokApi.browser import set_async
import time
import matplotlib.pyplot as plt
from scipy import stats
from flask import Flask, jsonify

# RUN THIS PART ONLY WHEN FIRST RUNNNING THE PROGRAM

########################################## Acquiring the videos ############################################

#Setting the API
set_async()
api = TikTokApi()

#Acquiring the videos and arranging the view numbers in a list (reversing as the original order is newer first)
def extract_data(**kwargs):
    videos = api.byUsername(username=user, count=results)
    video_views = list([video['stats']['playCount'] for video in videos])
    video_times = list([video['createTime'] for video in videos])
    video_views.reverse()
    video_times.reverse()
    return [video_views, video_times]

########################################### Fitting the model ###############################################

#Defining a function to reject outliers and videos from last two days
def reject_outliers(**kwargs):

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

def fit_model(**kwargs):

    #Fitting the model to filtered data
    x=[i for i in range(len(video_views))]
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_filtered, video_views_filtered)
    next_video_views = int(slope*(len(video_views)) + intercept)
    
    #Bulding figure for inner use
    plt.plot(x, [slope*k + intercept for k in x], label = "Fitted model")
    plt.scatter(len(video_views),slope*(len(video_views)) + intercept, label = "Next video prediction")
    plt.scatter(x,video_views, label='Ignored data')
    plt.scatter(x_filtered,video_views_filtered, label='Fitted data')
    plt.title("Views vs Video: " + user)
    plt.xlabel('Video')
    plt.ylabel('Number of views')
    plt.legend()    
    
    #Printing data for inner use
    print("The odds to go viral are " + str(int(odds_of_virality*100)) + "%")
    if (next_video_views>0):
        print("The predicted views for the next video are " + str(next_video_views))
    else:
        print("The predicted views for the next video are below zero")
    print("the p value is: " + str(p_value) + " (above 0.05 is reccomended)")
    print(std_err)
    
    return [slope, intercept, p_value, next_video_views, x] 

def create_data(**kwargs):  
    data = {"x":x,
            "video_views":video_views,
            "x_filtered":x_filtered, 
            "video_views_filtered":video_views_filtered, 
            "odds_of_virality":odds_of_virality, 
            "slope":slope, 
            "intercept":intercept, 
            "p_value":p_value, 
            "next_video_views":next_video_views
            }
    return data

#Global variables for later use
prev_1=0
prev_2=0

########################################## USER INPUT ##################################################
#%% RUN THIS PART WHEN CHANGING INPUT

#USER INPUT VARIABLES
results = 10 #Number of videos wanted
user="ecruzn" #TikTok username
outlier_sensitivity = 0.1 #From 0.1 to 0.5
videos_for_virality = 10 #Number of videos to check for virality
num_days = 2 #Num of days to ignore


#This if statement checks wether the number of results or username has changed to avoid extracting data for no reason
if (prev_1!=results or prev_2!=user):
    video_views, video_times = extract_data(api = api, user = user, results = results)
x_filtered, video_views_filtered, odds_of_virality = reject_outliers(video_views = video_views, video_times = video_times, outlier_sensitivity = outlier_sensitivity, videos_for_virality = videos_for_virality, num_days = num_days)
slope, intercept, p_value, next_video_views, x = fit_model(x_filtered=x_filtered, video_views_filtered = video_views_filtered)
        
###################################### NEW IMPLEMENTATION STILL IN PROGRESS ##############################
# sensitivities = [0.1*i for i in range(1,11)]
# result_list = [10*i for i in range(1,5)]

# p_values=[]

# for result in result_list:
#     for outlier_sensitivity in sensitivities:
#         video_views = video_views[-result:]
#         video_times = video_times[-result:]
#         x_filtered, video_views_filtered, odds_of_virality = reject_outliers(video_views = video_views, video_times = video_times, outlier_sensitivity = outlier_sensitivity, videos_for_virality = videos_for_virality, num_days = num_days)
#         slope, intercept, p_value, next_video_views, x = fit_model(x_filtered=x_filtered, video_views_filtered = video_views_filtered)
#         p_values.append((p_value, result, outlier_sensitivity))
        
####################################################################################################

prev_1 = results
prev_2 = user

#%%
############################ Creating a data object and a flask endpoint ##################################

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    data = create_data(x = x, video_views = video_views, x_filtered = x_filtered, video_views_filtered = video_views_filtered, slope = slope, intercept = intercept, p_value = p_value, next_video_views = next_video_views)
    return jsonify(data)

if __name__=="__main__":
    app.run()