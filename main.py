from flask import Flask, request
from flask_restful import Api, Resource
from model import model

app = Flask(__name__)
api = Api(app)

class Data(Resource):
   def post(self):
       #Requesting a user from the client and returning the dataset
       postedData = request.get_json()
       user = postedData["user"]

       try:
           userinfo = model(user)
           return userinfo
       except KeyError:
           return "No such user"
       except:
           return "An error has occured"

api.add_resource(Data, "/")

if __name__=="__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
