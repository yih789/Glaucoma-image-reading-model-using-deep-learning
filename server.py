# -*- coding: utf-8 -*-
import sys
import os

from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, url_for, redirect
import cv2
import numpy as np

from pymongo import MongoClient
import datetime

app = Flask(__name__)

MODEL_PATH = 'models/VGG16_FF_Model.h5'

model = load_model(MODEL_PATH)
model._make_predict_function()


def model_predict(img_path, model):
	img = image.load_img(img_path,  target_size=(150, 150))

	x = image.img_to_array(img)

	x = np.expand_dims(x, axis=0)

	x /= 255.

	#x = preprocess_input(x)

	preds = model.predict(x)
	return preds

@app.route('/mongo', methods=['GET', 'POST'])
def mongoTest():
	client = MongoClient("localhost:27017")
	db = client.PatientDatabase
	collection = db.Glaucoma
	results = collection.find()
	client.close()
	return render_template('mongo.html', people=results)

@app.route('/selectPage', methods=['POST'])
def selec():
	client = MongoClient("localhost:27017")
	db = client.PatientDatabase
	collection = db.Glaucoma
	results = collection.find()
	client.close()
	return render_template('selectPage.html', people=results)

@app.route('/selectPageres', methods=['POST'])
def selectres():
	if request.method == 'POST':
		rrn = request.form['rnumber']

		client = MongoClient("localhost:27017")
		db = client.PatientDatabase
		collection = db.Glaucoma
		results = collection.find()
		info = list(collection.find({"RRN":rrn}, {"_id":False}))
		client.close()
		return render_template('selectPage.html', information=info, people=results)

'''
@app.route('/editPage', methods=['POST'])
def edit():
	client = MongoClient("localhost:27017")
	db = client.PatientDatabase
	collection = db.Glaucoma
	results = collection.find()
	client.close()
	return render_template('editPage.html', people=results)

@app.route('/editPageres', methods=['POST'])
def editres():
	if request.method == 'POST':
		rrn = request.form['rnumber']

		client = MongoClient("localhost:27017")
		db = client.PatientDatabase
		collection = db.Glaucoma
		results = collection.find()
		info = list(collection.find({"RRN":rrn}))
		client.close()
		return render_template('editPage.html', information=info, people=results)
'''

@app.route('/removePage', methods=['POST'])
def remove():
	client = MongoClient("localhost:27017")
	db = client.PatientDatabase
	collection = db.Glaucoma
	results = collection.find()
	client.close()
	return render_template('removePage.html', people=results)

@app.route('/removePageres', methods=['POST'])
def removeres():
	if request.method == 'POST':
		rrn = request.form['rnumber']
		date = request.form['date']

		client = MongoClient("localhost:27017")
		db = client.PatientDatabase
		collection = db.Glaucoma
		results = collection.find()
		collection.remove({"DATE":date}, {"RRN":rrn})
		client.close()
		return render_template('removePage.html', people=results)

@app.route('/loginForm', methods=['GET', 'POST'])
def login():
	return render_template('loginForm.html')

@app.route('/loginRes', methods=['GET', 'POST'])
def loginRes():
	if request.method == 'POST':

		userid = request.form['userID']
		userpw = request.form['userPassword']
		userpw = str(userpw)

		client = MongoClient("localhost:27017")
		db = client.UserDatabase
		collection = db.Users
		temp = list(collection.find({"ID":userid}, {"_id":False,"ID":True, "PASSWORD":True}))
		temp = str(temp)
		temp_i = temp.partition(userid)[1]
		temp_p = temp.partition(userpw)[1]
		client.close()
		if(userid==temp_i and userpw == temp_p):
			return render_template('index.html', user=userid)
		return render_template('loginForm.html', error="입력하신 정보는 없는 정보입니다. 다시 입력해주세요.")
		#"알 수 없는 정보입니다. 다시 입력해주세요."

@app.route('/registerForm', methods=['GET', 'POST'])
def register():
	return render_template('registerForm.html')

@app.route('/registerRes', methods=['GET', 'POST'])
def registerRes():
	if request.method == 'POST':

		userid = request.form['userID']
		useremail = request.form['userEmail']
		userpw = request.form['userPassword']


		client = MongoClient("localhost:27017")
		db = client.UserDatabase
		collection = db.Users
		collection.insert({"ID":userid, "EMAIL":useremail, "PASSWORD":userpw})
		client.close()
		return render_template('loginForm.html')

@app.route('/', methods=['GET'])
def home():
   return render_template('homePage.html')

@app.route('/predict')
def predict():
	return render_template('predict.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
	return render_template('index.html')

@app.route('/print', methods=['GET', 'POST'])
def upload():
	if request.method == 'POST':

		f = request.files['file']
		name = request.form['name']
		age = request.form['age']
		region = request.form['region']
		identyNum = request.form['identyNumber']

		basepath = os.path.dirname(__file__)
		file_path = os.path.join(
			basepath, 'uploads', secure_filename(f.filename))
		f.save(file_path)

		result = model_predict(file_path, model)
		result = round(float(result),2)
		score = result
		if result >= 0.5:
			result = result * 100
			comment1 = "위 환자는 정상일 확률이"
			text = ""
			if result == 0.5:
				text = "전문의를 만나 상담받는 것을 권장합니다."
		else :
			result = 100 - (result*100)
			comment1 = "위 환자는 녹내장일 확률이"
			text = "전문의를 만나 상담받는 것을 권장합니다."

		age = int(age)

		now = datetime.datetime.now()
		date = now.strftime('%Y-%m-%d')
		
		client = MongoClient("localhost:27017")
		db = client.PatientDatabase
		collection = db.Glaucoma
		'''
		if collection.find({"DATE":date}, {"RRN":identyNum}):
			collection.remove({"DATE":date}, {"RRN":identyNum})'''
		collection.insert({"DATE":date, "NAME":name, "AGE":age, "REGION":region, "RRN":identyNum, "RESULT":score, "IMG_PATH":file_path})
		client.close()
		
		return render_template('print.html', result=result, name=name, age=age, region=region, identy=identyNum, path=file_path, date=date, comment1=comment1, text=text)
	return None

if __name__ == '__main__':
	app.run(debug=True)













'''
		img_path = './dataset/test/data/'+imgfile

		img = cv2.imread(img_path)
		img = cv2.resize(img, (150, 150))
		img = np.array(img)
		img = img.reshape((1, 150, 150, 3))
		img = img / 255.

		result = model.predict(img)

		return render_template('index.html', result=result )
'''
		
'''
		img = image.load_img(img_path, target_size=(150, 150))
		img_tensor = image.img_to_array(img)
		img_tensor = np.expand_dims(img_tensor, axis=0)
		img_tensor /= 255.

		result = model.predict(img_tensor)
		
'''


			
		# 입력 받은 이미지 예측
		
		



	

	
