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
           return {"user_info":userinfo, "message":"succesful", "status_code":200}
       except KeyError:
           return {"message":"No such user", "status_code":404}
       except:
           return {"message":"The model has failed to fit", "status_code":500}

api.add_resource(Data, "/")

if __name__=="__main__":
    app.run(host='0.0.0.0', port=5000)
