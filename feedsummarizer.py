# FeedSummarizer
# A script that takes a feed URL and a maximum number of articles and sends requests to an LLM engine to summarize each article
# By: GuizzyQC

import requests
import feedparser
import json
import os
import sys
import time
import smtplib, ssl
from bs4 import BeautifulSoup
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

now = time.time()
prettytime = time.strftime("%d %b %Y")
history = []
max_text_length = 7000

printer = "/tmp/DEVTERM_PRINTER_IN"

# Grab variables from environment and fill the default settings
default = dict()
default['url'] = os.environ.get("OPENAI_API_BASE") or "https://api.openai.com/v1"
default['api_key'] = os.environ.get("OPENAI_API_KEY") or ""
default['preset'] = os.environ.get("OPENAI_API_PRESET") or "Divine Intellect"
default['model'] = (os.environ.get("OPENAI_API_SUMMARIZER") or "n")
default['mode'] = "instruct"
default['system'] = os.environ.get("OPENAI_API_SYSTEM") or "You are an expert summarizer."
default['instruction'] = os.environ.get("OPENAI_API_INSTRUCTION") or "Summarize this article"
default['smtp'] = os.environ.get("SMTP_SERVER") or ""
default['port'] = os.environ.get("SMTP_PORT") or 465
default['username'] = os.environ.get("SMTP_USER") or ""
default['password'] = os.environ.get("SMTP_PASSWORD") or ""
default['sender'] = os.environ.get("SMTP_SENDER") or "no-reply@null.com"
default['recipient'] = os.environ.get("SMTP_RECIPIENT") or ""
default['maximum'] = os.environ.get("FEEDSUMMARIZER_MAX_ARTICLES") or 20
default['time_lapse'] = os.environ.get("FEEDSUMMARIZER_TIME_LAPSE") or 86400
default['printer_toggle'] = (os.environ.get("DEVTERM_PRINTER_TOGGLE") or "n").lower()

# SMTP connection object class
class SSLSMTP(smtplib.SMTP_SSL):
    def __init__(self, username, password, server, smtpport):
        super().__init__(server, port=smtpport)
        self.login(username, password)
    def send_message(self, *,
                     from_addr,
                     to_addrs,
                     msg,
                     subject,
                     attachments=None):
        msg_root = MIMEMultipart()
        msg_root['Subject'] = subject
        msg_root['From'] = from_addr
        msg_root['To'] = ', '.join(to_addrs)
        msg_alternative = MIMEMultipart('alternative')
        msg_root.attach(msg_alternative)
        msg_alternative.attach(MIMEText(msg))
        if attachments:
            for attachment in attachments:
                prt = MIMEBase('application', "octet-stream")
                prt.set_payload(open(attachment, "rb").read())
                encoders.encode_base64(prt)
                prt.add_header(
                    'Content-Disposition', 'attachment; filename="%s"'
                    % attachment.replace('"', ''))
                msg_root.attach(prt)
        self.sendmail(from_addr, to_addrs, msg_root.as_string())

# Article object class
class article:
    def __init__(self, entry, max_text_length):
        if hasattr(entry, 'title'):
            self.title = str(entry.title)
        else:
            self.title = "Unknown"
        if hasattr(entry, 'link'):
            self.url = str(entry.link)
        else:
            self.url = "NO LINK"
        if hasattr(entry, 'updated'):
            self.date = str(entry.updated)
        else:
            if hasattr(entry, 'published'):
                self.date = str(entry.published)
            else:
                self.date = str("Unknown")
        if hasattr(entry, 'author'):
            self.author = str(entry.author)
        else:
            self.author = "Unknown"
        output_result("Scraping content of " + str(self.url))
        self.text = get_page(self.url, max_text_length)
    def summarize(self, settings):
        if self.text != "The feed entry doesn't seem to have any URL. ":
            self.summary = generate_ai_response([], self.text, settings)
        else:
            self.summary = self.text
        return self.summary

def output_result(string, output_to_printer=False, echo=True):
    if echo:
        print(string)
    if output_to_printer:
        printer_command = "echo \"" + string + "\""
        os.system(printer_command + " > " + printer)

# Forces the model supplied to be loaded in the LLM engine if it's not
def enforce_model(settings):
    try:
        response = requests.get(settings['url'] + "/internal/model/info", headers=settings['headers'], timeout=15, verify=True)
        answer_json = response.json()
        if answer_json["model_name"] != settings['model']:
            output_result(">>> Please be patient, changing model to " + str(settings['model']))
            data = {
                'model_name': settings['model'],
                'settings': { "preset": settings['preset'], "custom_stopping_strings": '\"</s>\"' }
            }
            response = requests.post(settings['url'] + "/internal/model/load", headers=settings['headers'], json=data, timeout=60, verify=True)
    except Exception as e:
        output_result(f"Error setting model: {str(e)}")


# Send request to LLM engine API
def generate_ai_response(chat_history, prompt, settings):
    try:
        if settings['model'] != "n":
            enforce_model(settings)
        messages = []
        prompt = prompt + "\n\n" + settings['instruction']
        messages.append({"role": "system", "content": settings['system']})
        messages.append({"role": "user", "content": prompt})
        data = {
            'stream': False,
            'messages': messages,
            'max_tokens': 2000,
        }
        response = requests.post(settings['url'] + "/chat/completions", headers=settings['headers'], json=data, verify=True)
        assistant_message = response.json()['choices'][0]['message']['content']
        return(assistant_message)
    except Exception as e:
        output_result(f"Error generating response: {str(e)}")

# Create settings dictionary from default dictionary
def initialize_settings(default):
    def generate_headers(api_key):
        headers = {
            "Content-Type": "application/json",
        }
        headers['Authorization'] = f"Bearer " + api_key
        return headers
    settings = dict()
    settings['printer_toggle'] = False
    settings['url'] = str(default['url'])
    settings['api_key'] = str(default['api_key'])
    settings['headers'] = generate_headers(settings['api_key'])
    if str(default['model']) != "n":
        settings['model'] = str(default['model'])
    else:
        settings['model'] = "n"
    settings['mode'] = str(default['mode'])
    settings['system'] = str(default['system'])
    settings['preset'] = str(default['preset'])
    settings['instruction'] = str(default['instruction'])
    settings['smtp'] = str(default['smtp'])
    settings['port'] = int(default['port'])
    settings['username'] = str(default['username'])
    settings['password'] = str(default['password'])
    settings['sender'] = str(default['sender'])
    settings['recipient'] = str(default['recipient'])
    settings['maximum'] = int(default['maximum'])
    settings['time_lapse'] = int(default['time_lapse'])
    settings['printer_toggle'] = False
    if os.path.exists(printer):
        if str(default['printer_toggle']) == "y":
            settings['printer_toggle'] = True
    return settings

# Grabs all articles in the feed that are a day old at most, up to the maxmium from the command line argument, and creats a list of objects
def populate_articles(feed, maximum, time_lapse):
    i = 0
    articles = []
    for entry in feed.entries:
        if hasattr(entry, 'updated_parsed'):
            then = time.mktime(entry.updated_parsed)
        else:
            if hasattr(entry, 'published_parsed'):
                then = time.mktime(entry.published_parsed)
            else:
                then = now
        if (now - then) < time_lapse:
            if i < maximum:
                articles.append(article(entry, max_text_length))
            i = i + 1
    return articles

def get_page(url, max_text_length):
    def trim_to_x_words(prompt, limit):
        rev_rs = []
        words = prompt.split(" ")
        rev_words = reversed(words)
        for w in rev_words:
            rev_rs.append(w)
            limit -= 1
            if limit <= 0:
                break
        rs = reversed(rev_rs)
        return " ".join(rs)
        text = f"The web page at {url} doesn't have any useable content. Sorry. "
    if url == "NO LINK":
        return("The feed entry doesn't seem to have any URL. ")
    else:
        try:
            response = requests.get(url)
        except:
            return f"The page {url} could not be loaded"
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        if len(paragraphs) > 0:
            text = "\n".join(p.get_text() for p in paragraphs)
            text = f"Content of {url} : \n{trim_to_x_words(text, max_text_length)}[...]\n"
        else:
            text = f"The web page at {url} doesn't seem to have any readable content. "
            metas = soup.find_all("meta")
            for m in metas:
                if "content" in m.attrs:
                    try:
                        if (
                            "name" in m
                            and m["name"] == "page-topic"
                            or m["name"] == "description"
                        ):
                            if "content" in m and m["content"] != None:
                                text += f"It's {m['name']} is '{m['content']}'"
                    except:
                        pass
        return text

# Create a block of text with headers and text from the articles object, asks it to make a summary
def create_text(articles, settings):
    textarray = []
    for item in articles:
        textarray.append("Summarizing: " + item.title + "\n")
        textarray.append("By: " + item.author + "\n")
        textarray.append("Link : " + item.url + "\n")
        textarray.append("Date : " + item.date + "\n")
        output_result("Sending text of " + item.title + " to " + str(settings['url']))
        summary = item.summarize(settings)
        textarray.append(summary + "\n")
        textarray.append("\n#####\n\n")
    text = ''.join(textarray)
    text = text.replace("</s>", "")
    return text

# Grab variables from command line arguments and create settings dictionary from the default options
settings = initialize_settings(default)

if len(sys.argv)==1:
    output_result("Usage: python feedsummarizer.py \"URL of first feed to summarize\" \"URL of second feed to summarize\" [...]")

for arg in sys.argv[1:]:
    # Create objects from the articles in the feed, fill the summary in each object by interrogating the LLM and build a big block of text from this
    output_result("Grabbing feed " + str(arg))
    feed = feedparser.parse(arg)
    if hasattr(feed.feed, 'title'):
        feedtitle = str(feed.feed.title)
        output_result("Feed title: " + feedtitle)
    else:
        output_result("Feed has no title")
        if hasattr(feed.feed, 'link'):
            feedtitle = str(feed.feed.link)
            output_result("Using URL as substitute to feed title")
        else:
            feedtitle = "feed"
    output_result("Fetching up to " + str(settings['maximum']) + " articles from " + feedtitle)
    articles = populate_articles(feed, settings['maximum'], settings['time_lapse'])
    output_result("Sending scraped text to LLM")
    text = create_text(articles, settings)
    output_result(text, settings['printer_toggle'])

    # Send the block of text by email if the SMTP_SERVER variable was set
    if settings['smtp'] != "":
        with SSLSMTP(settings['username'], settings['password'], settings['smtp'], settings['port']) as server:
            server.send_message(from_addr=settings['sender'],
                                to_addrs=settings['recipient'],
                                msg=text,
                                subject="Summary of " + feedtitle + " for " + str(prettytime))
