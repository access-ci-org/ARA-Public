from flask import Flask, render_template, request, send_file, redirect, jsonify
import json
import os
from datetime import datetime
from collections import defaultdict
from urllib.request import urlopen
from .models.rps import RPS
from .models.gui import GUI
from .models.researchField import ResearchFields
from .models.software import Software
from .models.rpInfo import RpInfo
from .models.gpu import GPU
from .models.rpGPU import RpGPU
from .logic.form_logging import log_form_data
from .logic.recommendation import get_recommendations
from .logic.reports import sanitize_and_process_reports, save_user_report
from .xdmod.get_xdmod_data import fetch_wait_time_by_resource

app = Flask(__name__, static_folder='static')

@app.route("/")
def recommender_page():

    rps = RPS.select()
    research_fields = ResearchFields.select().order_by(ResearchFields.field_name)
    guis = GUI.select()
    gpu_obj = RpGPU.select()
    gpus = defaultdict(list)
    for item in gpu_obj:
        gpus[item.gpu.gpu_name].append(item.gpu_memory)
    # create a sorted list of memory values with no duplicates
    gpus = {gpu: sorted(list(set(memory))) for gpu, memory in gpus.items()}

    return render_template("questions.html",
                           rps = rps,
                           research_fields = research_fields,
                           guis = guis,
                           gpus = gpus)

@app.route("/get_research_fields")
def get_research_fields():
    research_fields = ResearchFields.select().order_by(ResearchFields.field_name)
    return([field.field_name for field in research_fields])

@app.route("/get_software")
def get_software():
    softwares = Software.select().order_by(Software.software_name)
    softwares_and_versions = [f"{software.software_name}" for software in softwares]

    return softwares_and_versions

@app.route("/get_score", methods=['POST'])
def get_score():
    data = request.get_json()
    log_form_data(data)
    recommendations = get_recommendations(data)
    # 'reasons' is a set, convert it to a list before sending it to front-end
    for _, value in recommendations.items():
        value['reasons'] = list(value['reasons'])
    return json.dumps(recommendations, sort_keys=True)

@app.route("/get_xdmod_data", methods=['POST'])
def get_xdmod_data():
    try:
        wait_time = fetch_wait_time_by_resource()
        if not wait_time.empty:
            wait_times =  wait_time.set_index('Simplified Resource')['Wait Hours: Per Job'].round(2).to_dict()
            return json.dumps(wait_times)
    except Exception as e:
        print(e)
    return json.dumps({})

# get_info function pulls from the rpInfo database to get blurbs, links, and documentation links
@app.route("/get_info", methods=['POST'])
def get_info():
    info = RpInfo.select()
    blurbs_links = {
        "rp": [f"{info.rp.name}" for info in info],
        "blurb": [f"{info.blurb}" for info in info],
        "hyperlink": [f"{info.link}" for info in info],
        "documentation": [f"{info.documentation}" for info in info]
    }
    return blurbs_links


@app.route("/report-issue", methods=['POST'])
def process_feedback():
    # Grab Ajax Request
    user_feedback = request.get_json()

    if "userMessage" in user_feedback:
        feedback_report = sanitize_and_process_reports(
            user_feedback, report_type="feedback"
        )
        feedback_saved = save_user_report(feedback_report)

        if feedback_saved:
            return jsonify({"success": "Feedback processed successfully"})

        return ({"error": "Unable to save user feedback"}), 500

    return jsonify({"error": "Missing key userMessage."}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)