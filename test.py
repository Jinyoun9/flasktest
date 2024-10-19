from flask import Flask, request, render_template
import pybamm
import numpy as np
import os
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Hello, World!"
