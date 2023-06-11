# main.py can be thought of as the "server" of this app
# users connect to the server, then server handles requests and messages.
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
from string import ascii_uppercase
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "AaPL@#LAS!cs"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)  
        if code not in rooms:
            break
    return code
        
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        request.form.get

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)
        if join != False and not code:
            return render_template("home.html", error="Please enter a Room Code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(6)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")

    #users cannot go directly to /room url without taking proper steps
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    # messages var saves all the messages to prevent losing data on refresh
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

#"new_text" is user input. Defined in room.html under sendMessage func 
@socketio.on("new_text")
def message(data):
    #getting room user is in
    room = session.get("room")
    #if room not in rooms list, then exit
    if room not in rooms:
        return
    #generating content we want to send
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    #sending all content to everyone in the room
    send(content, to=room)
    #adding the message sent to message box
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

#"connect" is the name used by socketio to signify an
# attempted socket connection
@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    #prevent users connecting directly to socket w/o name and room
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({ "name": name, "message": "has entered the chat room"}, to=room )
    rooms[room]["members"] += 1
    print(f"{name} joined chat room {room}")

#"disconnect" socketio signify a socket disconnect 
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1

        #deleting the chat room if there are no members in it
        if rooms[room]["members"] <= 0:
            del rooms[room]

    # debugging info
    send({ "name": name, "message": "has left the chat room"}, to=room )
    print(f"{name} has left the chat room {room}")

if __name__ == "__main__":
    socketio.run(app)
