import urllib3, requests, json, os,math
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, FloatField, IntegerField
from wtforms.validators import Required, Length, NumberRange

#url = 'https://ibm-watson-ml.mybluemix.net'
#username = 'a4f0f67f-279b-4fc3-8177-7c26ddb3d2d0'
#password = '12076bec-b267-407b-989d-d762ce069d0e'

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'pm-20' in vcap:
        creds = vcap['pm-20'][0]['credentials']
        username = creds['username']
        password = creds['password']
        url = creds['url']
scoring_endpoint = 'https://us-south.ml.cloud.ibm.com/v3/wml_instances/8db8a0ce-7ff1-4224-9186-eb410ef27f80/deployments/9beb64f0-0b47-463a-bde5-b46c1c5203ae/online'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretpassw0rd'
bootstrap = Bootstrap(app)
class TitanicForm(FlaskForm):
  pclass = RadioField('Passenger Class:', coerce=int, choices=[('1','First'),('2','Second'),('3','Third')])
  name = StringField('Name:')
  sex = RadioField('Gender:', coerce=str, choices=[('male','Male'),('female','Female')])
  age = RadioField('Age:', coerce=int, choices=[('0','0-5'),('1','6-11'),('2','12-17'),('3','18-39'),('4','40-64'),('5','65-79'),('6','>80')])
  ticket = StringField('Ticket:')
  fare = FloatField('Fare:')
  sibsp = IntegerField('Number of siblings/spouses:')
  parch = IntegerField('Number of parents/children:')
  embarked = RadioField('Embark Location:', coerce=str, choices=[('S','South Hampton'),('C','Cherbourg'),('Q','Queenstown')])
  submit = SubmitField('Submit')
@app.route('/', methods=['GET', 'POST'])
def index():
  form = TitanicForm()
  if form.is_submitted(): 
    sex = form.sex.data
    print (sex)
    form.sex.data = ''
    age = form.age.data
    print (age)
    form.age.data = ''
    name = form.name.data
    form.name.data = ''
    pclass = form.pclass.data
    form.pclass.data = ''
    ticket = form.ticket.data
    form.ticket.data = ''
    fare = form.fare.data
    fare = math.log10(fare)
    if (fare < 0) : fare = 0 
    elif (fare > 8): fare = 9 
    else: fare = int(fare) + 1
    form.fare.data = '' 
    sibsp = form.sibsp.data
    form.sibsp.data = ''
    parch = form.parch.data
    form.parch.data = ''   
    embarked = form.embarked.data
    form.embarked.data = ''    
    
    headers = urllib3.util.make_headers(basic_auth='{}:{}'.format(username, password))
    path = '{}/v3/identity/token'.format(url)
    response = requests.get(path, headers=headers)
    mltoken = json.loads(response.text).get('token')
    scoring_header = {'Content-Type': 'application/json', 'Authorization': 'Bearer' + mltoken}
    payload = {"fields": ["pclass","name","sex","sibsp","parch","ticket","embarked","survived_value","pclass_value","age_bin","log_fare_bin"], "values": [[pclass,name,sex,sibsp,parch,ticket,embarked," "," ",age,fare]]}
    scoring = requests.post(scoring_endpoint, json=payload, headers=scoring_header)

    scoringDICT = json.loads(scoring.text) 
    scoringList = scoringDICT['values'].pop()[11:13]
    print (scoringList)
    score = scoringList[1:].pop()
    probability_died = scoringList[0:1].pop()[0:1].pop()
    print (probability_died)
    probability_survived = scoringList[0:1].pop()[1:].pop()
    if (score == 1.0) :
      score_str = "survived"
      probability = probability_survived                                        
    else :
      score_str = "did not survive"
      probability = probability_died
      
    #probability = scoringList[6:7].pop()[0:1].pop()

    return render_template('score.html', form=form, scoring=score_str,probability=probability)
  return render_template('index.html', form=form)
port = os.getenv('PORT', '5000')
if __name__ == "__main__":
  app.run(host='0.0.0.0', port=int(port))
