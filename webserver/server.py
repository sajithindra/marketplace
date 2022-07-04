from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel


client = MongoClient('mongodb://localhost:27017/')
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/listservices')
async def listservices():
     return list(client.kriya.service.find({},{'_id':0}))

class Logindata (BaseModel):
    mob: str
    password : str
@app.post('/login')
async def login(login : Logindata):
    status= {}
    try :
        count = client.kriya.user.count_documents({'mob':login.mob,'password':login.password})
    except Exception as e:
        print(f'Error : {e}')
    
    if count ==1: status = {'status': "user"}
    elif count >1 : status= {'status':"More that one user with same credentials"}
    else : 
        try:
            count = client.kriya.sp.count_documents({'mob':login.mob})
        except Exception as e:
            print(f'Error : {e}')
        if count == 1: status = {'status':"sp"}
        elif count >1 : status= {'status':"More than one use with same credentials"}
        else : status= False

    return status
    

class Profile(BaseModel):
    mob:str

@app.post('/userprofile')
async def userprofile(profile : Profile):
    try:
       return dict(client.kriya.user.find_one({'mob': profile.mob},{'_id':0}))
    except Exception as e :
        print( f'Error : {e}')


@app.post('/spprofile')
async def spprofile(profile : Profile):
    try :
        return dict(client.kriya.sp.find_one({'mob':profile.mob},{'_id':0}))
    except Exception as e:
        print( f'Error : {e}')


class User(BaseModel):
    mob :str
    password : str
    name : str
    wallet : int = 0
@app.post('/adduser')
async def adduser(user : User):
    try:
        client.kriya.user.insert_one(dict(user))
        return True
    except Exception as e : 
        print(f'Error : {e}')
        return False

@app.post('/addsp')
async def addsp(sp:User):
    try:
        client.kriya.sp.insert_one(dict(sp))
        return True
    except Exception as e:
        print(f'Error : {e}')
        return False

class Service(BaseModel):
    servicename : str
    spmob : str
    charge :int = 0
    mode : str = 'perhour'


@app.post('/addservice')
async def addservice(service : Service):
    try: 
        client.kriya.service.insert_one(dict(service))
        return True
    except Exception as e :
        print(f'Error : {e}')
        return False

class Money(BaseModel):
    money : int = 0
    mob:str
@app.post('/addmoney')
async def addmoney(money: Money):
    try:
        wallet = dict(client.kriya.user.find_one({'mob': money.mob},{'_id':0,'wallet':1}))['wallet']
    except Exception as e:
        print(f'Error : {e}')
    wallet += money.money
    
    try:
        client.kriya.user.find_one_and_update({'mob': money.mob},{'wallet':wallet})
        return True
    except Exception as e:
        print(f'Error : {e}')
        return False
    
class Event (BaseModel):
    spmob: str
    usermob : str
    duration : int = 0
    servicename : str

@app.post('/scheduled')
async def scheduled(schedule : Event):
    try:
        client.kriya.scheduled.insert_one(dict(scheduled))
        return True
    except Exception as e :
        print(f'Error : {e}')
        return False

@app.post('/completed')
async def completed(completed : Event):
    try:
        charge = dict(client.kriya.service.find_one({'spmob':completed.spmob,'servicename':completed.servicename},{'_id':0,'charge':1}))['charge']
    except Exception as e:
        print( f' Error : {e}')
    
    cost = completed.duration*charge
    
    try:
        userwallet = dict(client.kriya.user.find_one({'mob':completed.usermob},{'wallet':1,'_id':0}))['wallet']
    except Exception as e:
        print(f'Error : {e}')
    
    userwallet -= cost

    try :
        client.kriya.user.find_one_and_update({'mob': completed.usermob},{'$set':{'wallet': userwallet}})
    except Exception as e:
        print( f'Error : {e}')
    
    try :
        spwallet=dict(client.kriya.sp.find_one({'mob': completed.spmob},{'_id':0,'wallet':1}))['wallet']
    except Exception as e:
        print(f'Error : {e}')

    spwallet += cost

    try:
        client.kriya.sp.find_one_and_update({'mob': completed.spmob},{'$set':{'wallet': spwallet}})
    except Exception as e:
        print(f'Error : {e}')
    
    return True