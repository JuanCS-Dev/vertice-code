from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World'

def failing_function():
    # This will raise a ZeroDivisionError
    return 1 / 0

if __name__ == '__main__':
    # The following line will cause the app to crash on startup
    # failing_function() 
    app.run(debug=True)
