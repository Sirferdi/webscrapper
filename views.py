import html
import os
import main
from flask import Blueprint, render_template, request, send_file

views = Blueprint(__name__, "views")

@views.route("/")
def home():
    with open('scrap_output.txt', 'r+') as f:
        f.truncate(0)
    return render_template("index.html")

@views.route('/scrap')
def scrap():
    with open('scrap_output.txt', 'r+') as f:
        f.truncate(0)
    site = request.args.get('site')
    max_courses = request.args.get('mc')
    max_days = request.args.get('mdo')
    return main.web_scrap(site, int(max_courses), int(max_days))

@views.route('/scrap-output')
def scrap_output():
    with open('scrap_output.txt', 'r', newline='') as f:
        return html.escape(f.read()).replace('\n', '<br>')
    
@views.route('/download-csv')
def download(): 
    return send_file('courses.csv', download_name='courses.csv', as_attachment=True)

@views.route('/hugo-barbosa-TnG2q8FtXsg.jpg')
def get_image():
    return send_file('hugo-barbosa-TnG2q8FtXsg.jpg', mimetype='image/jpg')

