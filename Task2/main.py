"""
Imports
"""
import json
import requests
from secretss import API_TOKEN

def create_survey_and_get_url():
    """
    Function for creating survey and url
    """
    with open("pytania.json", "r", encoding="utf-8") as file:
        survey_data = json.load(file)

    base_url = "https://api.surveymonkey.com/v3/surveys"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(base_url, headers=headers, json=survey_data, timeout=10)
    if response.status_code != 201:
        print("Failed to create survey:", response.json())
        return None, None

    survey_details = response.json()
    survey_id_local = survey_details["id"]
    print(f"Survey Created: {survey_details['title']}")

    link_response = requests.post(
        f"{base_url}/{survey_id_local}/collectors",
        headers=headers,
        timeout=10,
        json={"type": "weblink"}
    )

    if link_response.status_code != 201:
        print("Failed to generate weblink collector:", link_response.json())
        return survey_id_local, None

    collector_details = link_response.json()
    survey_link_local = collector_details.get("url", "No URL available")
    print("Weblink Collector Created")
    print(f"Survey Link: {survey_link_local}")
    return survey_id_local, survey_link_local


def send_survey_via_email(survey_id_param, survey_link_param):
    """
    Function sending email and checking if it was sent or not
    """
    if not survey_id_param or not survey_link_param:
        print("Survey ID or Survey Link is missing. Cannot send emails.")
        return

    base_url = "https://api.surveymonkey.com/v3/surveys"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    email_response = requests.post(
        f"{base_url}/{survey_id_param}/collectors",
        headers=headers,
        timeout=10,
        json={"type": "email"}
    )

    if email_response.status_code == 201:
        email_details = email_response.json()
        collector_id = email_details["id"]
        print(f"Email Collector Created with ID: {collector_id}")

        email_file = "emails.txt"
        try:
            with open(email_file, "r", encoding="utf-8") as file:
                email_addresses = [line.strip() for line in file.readlines() if line.strip()]

            recipients_payload = {
                "contacts": [
                    {"email": email} for email in email_addresses
                ]
            }

            recipients_response = requests.post(
                f"{base_url}/collectors/{collector_id}/messages",
                headers=headers,
                timeout=10,
                json={
                    "type": "invite",
                    "recipients": recipients_payload,
                    "subject": "You're Invited to Participate in a Survey",
                    "body": (
                        f"Hello,\n\n"
                        "You are invited to participate in our survey. "
                        "Please click the link below to access the survey:\n\n"
                        f"{survey_link_param}\n\n"
                        "Thank you!"
                    )
                }
            )

            if recipients_response.status_code == 201:
                print("Emails successfully sent through SurveyMonkey.")
            else:
                print("Failed to send emails through SurveyMonkey:", recipients_response.json())

        except FileNotFoundError:
            print(f"Email file '{email_file}' not found.")
    else:
        print("Failed to generate email collector:", email_response.json())


if __name__ == "__main__":
    created_survey_id, created_survey_link = create_survey_and_get_url()
    send_survey_via_email(created_survey_id, created_survey_link)
