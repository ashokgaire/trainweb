from flask import Flask
from flask import request, render_template, session 
import requests
import json
from datetime import timedelta
import datetime
import pandas as pd

app = Flask(__name__)
app.config.update(SECRET_KEY='33f20b8a')
app.permanent_session_lifetime = timedelta(days=100)


@app.route("/loc_id/<string:loc>", methods=["POST","GET"])
def loc_id(loc):

    # if no id
    if not session.get("id"):
        return render_template("accedi.html")

    # check all locids for current user
    id = session["id"] 
    access_token = session["access_token"]

    # if I just completed a wo
    if request.method == "POST" and request.form.get("wo_done"):
        wo_id = request.form.get("wo_done")


        url = "http://34.147.28.33:5000/api/v1/workorders/"+wo_id

        payload = json.dumps({
        "completed_status": True
        })
        headers = {
        'Authorization': 'Bearer '+ access_token,
        'Content-Type': 'application/json',
        'Cookie': 'token='+access_token,
        }

        response = requests.request("PUT", url, headers=headers, data=payload)

        
        
    if request.method == "POST" and request.form.get("titolo") and request.form.get("note"):

        titolo = request.form.get("titolo")
        note = request.form.get("note")

        url = "http://34.147.28.33:5000/api/v1/workorders"

        payload = json.dumps({
        "location_id": loc,
        "work_order_title": titolo,
        "work_order_notes": note,
        "completed_status": False,
        })

        headers = {
        'Authorization': 'Bearer '+ access_token,
        'Content-Type': 'application/json',
        'Cookie': 'token='+access_token,
        }

        requests.request("POST", url, headers=headers, data=payload)



    url_all_loc = 'http://34.147.28.33:5000/api/v1/location/userId/'+id

    headers = {
    'Authorization': 'Bearer '+ access_token,
    'Content-Type': 'application/json',
    'Cookie': 'token='+access_token,
    }

    response_loc = requests.request("GET", url_all_loc, headers=headers)

    locations = []
    ctss = []
    loc_ids = []

    for l in json.loads(response_loc.text)['data']:
        location_name = l['location_name']
        cts = l['createdAt']
        loc_id = l['_id']
        cts_formatted = datetime.datetime.strftime(pd.to_datetime(cts), "%d %b '%y")
        locations.append(location_name)
        ctss.append(cts_formatted)
        loc_ids.append(loc_id)

    # locations, ctss, loc_ids

    locs = pd.DataFrame({'locations': locations, 'ctss': ctss, 'loc_ids': loc_ids})

    loc_name = list(locs[locs['loc_ids'] == loc].locations)[0]

    # return wos
    url = "http://34.147.28.33:5000/api/v1/workorders/locationId/"+loc

    payload={}

    headers = {
    'Authorization': 'Bearer '+ access_token,
    'Content-Type': 'application/json',
    'Cookie': 'token='+access_token,
    }
    response_wo = requests.request("GET", url, headers=headers, data=payload)

    wo_ids = []
    wo_names = []
    wo_notes = []
    wo_stati = []
    wo_creations = []

    for l in json.loads(response_wo.text)['data']:
        wo_id = l['_id']
        wo_ids.append(wo_id)
        wo_name = l['work_order_title']
        wo_names.append(wo_name)
        wo_note = l['work_order_notes']
        wo_notes.append(wo_note)
        wo_status = l['completed_status']
        wo_stati.append(wo_status)
        wo_creation = l['createdAt']
        wo_creation_formatted = datetime.datetime.strftime(pd.to_datetime(wo_creation), "%d %b '%y")
        wo_creations.append(wo_creation_formatted)  
        
    wos = pd.DataFrame({'wo_ids': wo_ids, 'wo_names': wo_names,
                            'wo_notes': wo_notes, 'wo_stati': wo_stati,
                             'wo_creations': wo_creations})
    wos = wos[wos.wo_stati == False]
    wos = list(wos.transpose().to_dict().values())

    # take the components for the location

    url = "http://34.147.28.33:5000/api/v1/map/locationId/" + loc

    payload={}

    headers = {
    'Authorization': 'Bearer '+ access_token,
    'Content-Type': 'application/json',
    'Cookie': 'token='+access_token,
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    map_ids = json.loads(response.text)['data'] 
    map_ids

    comp_code = []
    comp_creation = []
    map_names = []


    for m in map_ids:
        
        map_id = m['_id']
        map_name = m['map_name']
        url = "http://34.147.28.33:5000/api/v1/components/mapId/" + map_id

        payload={}
        headers = {
        'Authorization': 'Bearer '+ access_token,
        'Cookie': 'token='+access_token,
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        for c in json.loads(response.text)['data']:
            comp_code.append(c['component_code'])
            comp_creation.append(datetime.datetime.strftime(pd.to_datetime(c['createdAt']), "%d %b '%y"))
            map_names.append(map_name)


    comps = list(pd.DataFrame({'comp_code': comp_code, 'comp_creation': comp_creation,
                    'map_names': map_names}).transpose().to_dict().values())

                    

    return render_template("work-orders.html", wos = wos, loc_name = loc_name, loc = loc, comps = comps)


    



@app.route('/signup')
def login():
    return render_template("signup.html")


# some lines omitted here

@app.route("/", methods=["POST","GET"])
def home():
    if request.method == "POST":

        # after adding new location
        if request.form.get("loc-title"):
            access_token = session["access_token"]
            url = "http://34.147.28.33:5000/api/v1/location/"

            payload = json.dumps({
            "user_id": session["id"],
            "location_name": request.form.get("loc-title")
            })

            headers = {
            'Authorization': 'Bearer '+ access_token,
            'Content-Type': 'application/json',
            'Cookie': 'token='+access_token,
            }
            response = requests.request("POST", url, headers=headers, data=payload)



        # signout
        if request.form.get("signout"):
            session.clear()
            return render_template("accedi.html", error = "signed out")

        # registration
        if request.form.get("nome") and request.form.get("cognome") and request.form.get("email") and request.form.get("password") :

            url = "http://34.147.28.33:5000/api/v1/auth/register"

            payload = json.dumps({
            "name": request.form.get("nome"),
            "surname": request.form.get("cognome"),
            "email": request.form.get("email"),
            "password": request.form.get("password")
            })
            headers = {
            'Content-Type': 'application/json',
            'Cookie': 'token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjYyNTg3YmViNGMwYTcyYWRhNThjMTUxNyIsImlhdCI6MTY0OTk2NjA1OSwiZXhwIjoxNjUyNTU4MDU5fQ.raMKAzRg-ODcpxc4AfQxwnnbba4sjsE_mHhdEjZYse8'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            access_token =   json.loads(response.text)['token']
            session["access_token"] = access_token


        # accessing
        if request.form.get("email") and request.form.get("password") and not request.form.get("nome"):
            email = request.form.get("email") # take the request the user made, access the form,
                                        # and store the field called `name` in a Python variable also called `name`
            password = request.form.get("password")

            url = "http://34.147.28.33:5000/api/v1/auth/login"

            payload = json.dumps({
            "email": email,
            "password": password
            })

            headers = {
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjYyNDk2ZDI1OWQwYzg5ZDIzNmM2ZWQ0OSIsImlhdCI6MTY0ODk3OTIzNywiZXhwIjoxNjUxNTcxMjM3fQ.F_pGUXr2ZVeO3AKoFbpL9EMqxW29EmhwtOF52XfxQ_k',
            'Content-Type': 'application/json',
            'Cookie': 'token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjYyNDk2ZDI1OWQwYzg5ZDIzNmM2ZWQ0OSIsImlhdCI6MTY0OTc3MTcwNywiZXhwIjoxNjUyMzYzNzA3fQ.8E0XUmKB2dyvjYUbZ2RA0EO1L26n4tYzRrQMxHiztQQ'
            }

            try:
                response_access = requests.request("POST", url, headers=headers, data=payload)

                if not json.loads(response_access.text)['success']:
                    return render_template("accedi.html", error='wrong credentials')

            except:
                return render_template("accedi.html", error='wrong credentials')


            access_token =   json.loads(response_access.text)['token']

            session.clear()

            session["access_token"] = access_token

        url = "http://34.147.28.33:5000/api/v1/auth/me/"

        headers = {
        'Authorization': 'Bearer '+ access_token,
        'Content-Type': 'application/json',
        'Cookie': 'token='+access_token,
        }

        response = requests.request("GET", url, headers=headers)

        id = json.loads(response.text)['data']['_id']
        name = json.loads(response.text)['data']['name']
        session["id"] = id
        session["name"] = name





    # if no id
    if not session.get("id"):
        return render_template("accedi.html", error='no id')





    id = session["id"] 
    access_token = session["access_token"]

    url_all_loc = 'http://34.147.28.33:5000/api/v1/location/userId/'+id

    headers = {
    'Authorization': 'Bearer '+ access_token,
    'Content-Type': 'application/json',
    'Cookie': 'token='+access_token,
    }

    try:

        response_loc = requests.request("GET", url_all_loc, headers=headers)


    # if not json.loads(response_loc.text)['success']:
    #     return render_template("accedi.html", error="couldn't add location")

        locations = []
        ctss = []
        loc_ids = []
        wo_count = []

        for l in json.loads(response_loc.text)['data']:
            location_name = l['location_name']
            cts = l['createdAt']
            loc_id = l['_id']
            cts_formatted = datetime.datetime.strftime(pd.to_datetime(cts), "%d %b '%y")
            locations.append(location_name)
            ctss.append(cts_formatted)
            loc_ids.append(loc_id)
            
            url = "http://34.147.28.33:5000/api/v1/workorders/locationId/"+loc_id

            payload={}

            headers = {
            'Authorization': 'Bearer '+ access_token,
            'Content-Type': 'application/json',
            'Cookie': 'token='+access_token,
            }
            response_wo = requests.request("GET", url, headers=headers, data=payload)

            wo_ids = []
            wo_names = []
            wo_notes = []
            wo_stati = []
            wo_creations = []

            for l in json.loads(response_wo.text)['data']:
                wo_id = l['_id']
                wo_ids.append(wo_id)
                wo_name = l['work_order_title']
                wo_names.append(wo_name)
                wo_note = l['work_order_notes']
                wo_notes.append(wo_note)
                wo_status = l['completed_status']
                wo_stati.append(wo_status)
                wo_creation = l['createdAt']
                wo_creation_formatted = datetime.datetime.strftime(pd.to_datetime(wo_creation), "%d %b '%y")
                wo_creations.append(wo_creation_formatted)  
                
            wos = pd.DataFrame({'wo_ids': wo_ids, 'wo_names': wo_names,
                                    'wo_notes': wo_notes, 'wo_stati': wo_stati,
                                    'wo_creations': wo_creations})

            wos = wos[wos.wo_stati == False]

            
            wo_count.append(len(wos))

        # locations, ctss, loc_ids

        locs = list(pd.DataFrame({'locations': locations, 'ctss': ctss, 'loc_ids': loc_ids, 'wo_count': wo_count}).transpose().to_dict().values())

        return render_template("index.html", name = session["name"] , locs = locs)

    except:
        return render_template("accedi.html", error="couldn't add location")

    # res.set_cookie('refresh_token', 'YOUR_REFRESH_TOKEN')






# @app.route('/')
# def hello_world():






@app.route("/add_location")
def add_location():
    # add location
    access_token = request.cookies.get('access_token')


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="8000", debug=True)
    session.permanent = True
