from email.message import EmailMessage
from time import sleep
import spacy
import requests
from bs4 import BeautifulSoup
import smtplib

class NewsScrapingError(Exception):
    pass

def fetch_html(url):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            return response.text
        else:
            raise NewsScrapingError(f"Error: Unable to fetch page, status code {response.status_code}")
    except requests.RequestException as e:
        raise NewsScrapingError(e)

def scrape_latest_article_for_mention(html_content, keyword, cache):
    news_item = BeautifulSoup(html_content, 'html.parser').find('div', class_='sc-hRhbag kHbKLP news-item col-12 col-xl-4')
    if not news_item:
        raise NewsScrapingError("No latest news item found.")


    news_link = news_item.find('a', href=True)
    if not news_link or 'href' not in news_link.attrs:
        raise NewsScrapingError("No link found in news item.")

    link_text = "https://www.dw.com" + news_link.attrs['href']
    if link_text in cache:
        print("Already processed this article, skipping.")
        return

    cache[link_text] = False

    news_content = fetch_html(link_text)
    news_text = BeautifulSoup(news_content, 'html.parser').get_text().strip().lower()

    find_mention(news_text, keyword, link_text, cache)


def find_mention(news_text, keyword, link_text, cache):
    doc = nlp(news_text)
    keyword_doc = nlp(keyword)

    keyword_lemma = " ".join([token.lemma_ for token in keyword_doc])
    for token in doc:
        if token.lemma_ == keyword_lemma:
            cache[link_text] = True
            print(f"Found keyword '{keyword}' in article {link_text}")
            send_email("Keyword found", f"Found keyword '{keyword}' in article {link_text}")
            return

    cache[link_text] = False
    print(f"Did not find keyword '{keyword}' in article {link_text}")


def send_email(subject, body):
    email = EmailMessage()
    email["From"] = sender_email
    email["To"] = receiver_email
    email["Subject"] = subject
    email.set_content(body)

    smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
    smtp.starttls()
    smtp.login(sender_email, sender_password)
    smtp.sendmail(sender_email, receiver_email, email.as_string())
    smtp.quit()


nlp = spacy.load("en_core_web_sm")
sender_email = 'gleebus@outlook.com'
sender_password = 'Glbs1488!'
receiver_email = 'gleebus@outlook.com'
# Map containing links and status (true/false) if the mention has been found
cache = {}
main_page_content = fetch_html('https://www.dw.com/en/top-stories/s-9097')
while True:
    try:
        scrape_latest_article_for_mention(main_page_content, 'Election', cache)
        sleep(3)
    except NewsScrapingError as e:
        print(e)

