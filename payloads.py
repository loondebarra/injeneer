import re
from bs4 import BeautifulSoup
import requests
import json

class Monkey:
    forms = []
    url = ''
    js_endpoints = []
    js_http_methods = []


    protocol = ''
    host = ''

    def __init__(self, url):
        self.url = url

        self.protocol = url.split("://")[0] + '://'
        self.host = url.split("://")[1].split("/")[0]

        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        self.forms = soup.find_all("form")
        self.inputs = soup.find_all("input")

        for form in self.forms:
            form_inputs = form.find_all("input")
            for form_input in form_inputs:
                if form_input in self.inputs:
                    self.inputs.remove(form_input)

        # extract js
        scripts = soup.find_all("script")
        js_code = "".join(script.string for script in scripts if script.string)

        # extract methods
        self.extract_js_endpoints_and_methods(js_code)

    def extract_js_endpoints_and_methods(self, js_code):
        pattern = r"""
            (fetch|axios\.(get|post)|\.ajax|\.get|\.post|XMLHttpRequest)\(.*?['\"](.*?)['\"]
            | # OR
            method:\s*['\"](GET|POST|PUT|DELETE)['\"]
        """
        matches = re.findall(pattern, js_code, re.IGNORECASE | re.VERBOSE)

        self.js_endpoints = []
        self.js_http_methods = []

        for match in matches:
            function, http_method, url, method_in_obj = match
            if function:
                method = 'GET' if 'get' in function.lower() else 'POST'
                self.js_endpoints.append(url)
                self.js_http_methods.append(http_method.upper() if http_method else method)
            elif method_in_obj:
                # update the last method if specified in an object (for 'fetch' or '.ajax')
                self.js_http_methods[-1] = method_in_obj

    def get_inputs(self):
        return self.inputs

    def get_forms(self):
        return self.forms
    
    def get_js_endpoints(self):
        return self.js_endpoints
    
    def get_js_http_methods(self):
        return self.js_http_methods
    
    def get_js_urls(self):
        return [(self.protocol + self.host + e) for e in self.js_endpoints]

    def inject_forms(self, custom_data):
        for form in self.forms:
            action_url = form.get("action")

            inputs = form.find_all("input")

            form_data = {}

            for input in inputs:
                input_name = input.get("name")
                input_value = input.get("value")
                form_data[input_name] = input_value

            form_data.update(custom_data)

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(self.protocol + self.host + action_url, data=json.dumps(form_data), headers=headers)

            return response.content

    def inject_fetch(self, custom_data):
        for (method, url) in zip(self.get_js_http_methods(), self.get_js_urls()):
            if method == 'GET':
                response = requests.get(url, params=custom_data)
            elif method == 'POST':
                headers = {
                    'Content-Type': 'application/json'
                }
                response = requests.post(url, data=json.dumps(custom_data), headers=headers)
            else:
                print(f"unhandled method: {method} for url: {url}")

            return response.content