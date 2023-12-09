## Description:
An OpenAI-compatible API script that takes RSS feeds and has the articles mentionned in it summarized

When invoked followed with the URL to RSS or Atom feeds, will parse the feed to grab a certain number of articles that are a certain number of seconds old, scrape the text of the associated link, send it to an OpenAI-compatible API with instructions to summarize it, and then, provided you configured SMTP server settings in your environmental variables, finally emails you the results.

Compatible and tested on Linux and Windows.

Detects and supports the DevTerm's printer to make wee thermal paper printouts of your summaries if you want.

Caution: Tested with Oobabooga's text-generation-webui, not tested with another OpenAI-compatible API, including OpenAI itself.

## Requirements:
Python 3
Libraries: requests, feedparser and BeautifulSoup4

## Installation:
git clone https://github.com/GuizzyQC/FeedSummarizer
pip install -r FeedSummarizer/requirements.txt

## Configuration:
The software is configured using environmental variables. You can either supply them to your command before launching it or save them in your command line shell's profile.

Here's what the environmental variables are and do:
OPENAI_API_BASE: **REQUIRED** Sets your API's endpoint. Defaults to "https://api.openai.com/v1". Note that I have never tested this with openai, it holds no interest for me. But in theory it should probably be compatible if you supply an API key.
OPENAI_API_KEY: Sets your API key.
OPENAI_API_ENFORCE_MODEL: Choose "y" or "n" to define whether you want the software to force the API endpoint to use another model than is currently running on it, useful for text-generation-webui which exposes multiple possible models. Defaults to "n".
OPENAI_API_SUMMARIZER: Sets the model used by your endpoint of you set y to OPENAI_API_ENFORCE_MODEL, useful for text-generation-webui which exposes multiple possible models.
OPENAI_API_PRESET: Sets the preset used by your endpoint, provided you are enforcing the model. Useful for text-generation-webui which exposes multiple possible presets. Defaults to "Divine Intellect"
OPENAI_API_SYSTEM: Sets the "system" prompt used in "instruct" mode. Defaults to a boring but multipurpose: "You are a helpful assistant, answer any request from the user."
OPENAI_API_INSTRUCTION: Sets the prompt to follow the article's scraped text, ideally an instruction to tell the LLM to summarize the text. Defaults to "Summarize this article".
FEEDSUMMARIZER_MAX_ARTICLES: Sets the maximum number of articles to fetch from each feed. Defaults to 20.
FEEDSUMMARIZER_TIME_LAPSE: Sets the time in seconds between now and the oldest article to fetch. Defaults to 86400, which is a day.
SMTP_SERVER: Sets the SMTP server to contact to send the email. It is assumed the server has to support SSL. I tested it on FastMail and it worked well. Without this, the script will just output the result to the shell.
SMTP_PORT: Sets the port for the SMTP connection. Defaults to 465.
SMTP_USER: Sets the username for SMTP authentication.
SMTP_PASSWORD: Sets the password for SMTP authentication.
SMTP_SENDER: Sets the sender email address for the summary.
SMTP_RECIPIENT: Sets the email address to send the summary too.
PYPROMPT_PRINTER: If you are the lucky owner of a DevTerm, setting "y" here will enable printouts on the thermal printer. Defaults to "n".

Setting variables in Bash can be done with the command:
``` bash
export OPENAI_API_MODEL=Nous-Capybara-34b.Q5_K_M-GGUF
```

And in Powershell with:
``` powershell
[System.Environment]::SetEnvironmentVariable('OPENAI_API_MODEL','Nous-Capybara-34b.Q5_K_M-GGUF')
```
You can set them permanently in \~/.bashrc for a Linux bash shell or $PROFILE on Windows.

## Usage:
python pyprompt.py https://news.ycombinator.com/rss

## Recommendation:
This script is really useful as a recurring daily task. I have it set in my crontab on linux with the environmental variables in the path.

For Linux this looks like this:

``` crontab
15 7 * * 1-5 OPENAI_API_BASE= OPENAI_API_KEY= OPENAI_API_ENFORCE_MODEL=y OPENAI_API_SUMMARIZER=Nous-Capybara-34b.Q5_K_M-GGUF OPENAI_API_SYSTEM="You are an expert summarizer. Your summaries are always accurate, complete and helpful." SMTP_SERVER= SMTP_PORT=465 SMTP_USER= SMTP_PASSWORD= SMTP_SENDER= SMTP_RECIPIENT= /usr/local/bin/python3.9 /home/USERNAME/summarizer/feedsummarizer.py "https://news.ycombinator.com/rss" > /var/log/feedsummarizer.log
```
Making sure of course that you do fill the variables, that the paths to your python interpreter is correct and the path to feedsummarizer.py is correct. This should start building a summary every weekday at 7:15 AM and email it to as each feed is read and parsed.