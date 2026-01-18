from flask import Blueprint , render_template , redirect , url_for , request, session

main = Blueprint('main' , __name__)


@main.route('/')
def main_page():
    return render_template('index.html') 

@main.route("/login" , methods=['GET','POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'Vipul' and password == '1234':
            # 1. Store the user's name in the session to remember them
            session['username'] = username
            
            # 2. Redirect to the new profile_page route
            return redirect(url_for('main.profile_page'))
        else:
            # If login fails, just show the login page again
            # (Later, you can add a flash() message here to show an error)
            return render_template('login.html')
    

# 3. Create a new route just for the profile page
@main.route('/profile')
def profile_page():
    # 4. Check if the user is logged in by looking in the session
    if 'username' in session:
        # 5. Get the username from the session
        username = session['username']
        # 6. Pass the username variable to the template
        return render_template('profile.html', username=username)
    else:
        # If no one is logged in, send them back to the login page
        return redirect(url_for('main.login_page'))