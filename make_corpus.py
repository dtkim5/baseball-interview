import numpy as np
import pandas as pd
import re
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from pathlib import Path
import Levenshtein
import wikipedia

def parse_interview(url, data):
  page = requests.get(url)
  soup = BeautifulSoup(page.text, 'html.parser')
  section = soup.find(attrs={'style':'padding: 10px;', 'valign':'top'})
  event = soup.find('h1').get_text()
  date = soup.find('h2').get_text()
  items = soup.find_all("h3")
  names = [item.get_text() for item in items]
  for p in soup.find_all(["strong", "i", "h1", "h2", "h3", "br", "a"]):
    p.decompose()
  paragraphs = section.find_all(string=True)
  output = ""
  for p in paragraphs:
    text = p.get_text()
    output = output + text
  data.append([output, event, date, names])

def parse_player(url, data):
  page = requests.get(url)
  soup = BeautifulSoup(page.text, 'html.parser')
  table = soup.find('table', attrs={'width':'100%', 'cellspacing':'0', 
	                  'cellpadding':'3', 'border':'0'})
  if table is None:
    return None
  links = table.find_all('a', href=True)
  for link in links:
    parse_interview(link['href'], data)

def parse_letter(url, data):
  page = requests.get(url)
  soup = BeautifulSoup(page.text, 'html.parser')
  table = soup.find('table', attrs={'width':'100%', 'cellspacing':'0', 
	                  'cellpadding':'3', 'border':'0'})
  if table is None:
    return None
  links = table.find_all('a', href=True)
  for link in tqdm(links):
    parse_player(link['href'], data)

def parse_sport(url):
  page = requests.get(url)
  soup = BeautifulSoup(page.text, 'html.parser')
  table = soup.find_all('table', attrs={'width':'100%', 'cellspacing':'0', 
	                  'cellpadding':'5', 'border':'0'})[0]
  links = table.find_all('a', href=True)
  data = []
  for link in links:
    parse_letter(link['href'], data)
  return data

def scrape(weblink, rewrite=False):
  file = Path("corpus_creation/summaries.csv")
  if not file.is_file() or rewrite:
    # make the summaries csv
    data = parse_sport(weblink)
    df = pd.DataFrame(data, columns=['text', 'event', 'date', 'names'])
    df.to_csv("corpus_creation/interviews_raw.csv", index=False)
    return df
  df = pd.read_csv("corpus_creation/interviews_raw.csv", converters={'names': pd.eval})
  return df

def chunk(row):
  text = row.iloc[0]
  text = re.sub(r"â€™", "\'", text)
  text = re.sub(r"Â", "", text)
  text = re.sub(r"Q\.", "999PLACEHOLDER999 Q.", text)
  QnA = re.split(r"999PLACEHOLDER999", text)[1:] # blocks of Questions and Answers
  return QnA

# helper function to fix OCR errors for and standardize interviewee names
def find_name(interviewee, names):
  interviewee_lower = interviewee.lower()
  closest_name = None
  min = 10000
  for name in names:
    dist = Levenshtein.distance(interviewee_lower, name.lower())
    if dist < min:
      min = dist
      closest_name = name
  return closest_name

# helper function to separate the questions and answers
# such that each row is a pair of questions and answers with the event, date, and interviewee attached

def separate(row, nationalities_dict):
  # input is a row
  interview = row.iloc[0]
  event = row.iloc[1]
  date = row.iloc[2]
  names = row.iloc[3]
  output = []
  for text in interview: # for each question and its following response(s)
    q_and_a = re.split(r"\n(?=[A-ZÀ-Ÿ ,.-]+:)", text)
    question = re.sub(r"Q\.", "", q_and_a[0]).strip()
    for answer in q_and_a[1:]: # go through the responses in case there are multiple responders
      interviewee = re.search(r"([A-ZÀ-Ÿ ,.-]+)(:)", answer)
      # use levenshtein distance to standardize the names
      name = find_name(interviewee.group(1), names)
      nationality = nationalities_dict[name]
      answer_noname = re.sub(interviewee.group(0), "", answer).strip()
      output.append([question, answer_noname, event, date, name, nationality])
  return output

def filter(data):
  raw_data = data.drop_duplicates(subset='text')

  mlb_data = raw_data[raw_data['event'].str.contains("MLB |NL |AL |WORLD SERIES|HOME RUN CHASE|MEDIA CONFERENCE", case=False, regex=True)]
  to_drop = mlb_data[mlb_data['event'].str.contains("NCAA|UNIVERSITY|COLLEGE|COLLEGIATE|STATE|MUNDIAL|ATLANTIC COAST|WINTER MEETINGS")].index
  mlb_data = mlb_data.drop(to_drop)
  return mlb_data

def get_events(data, rewrite=False):
  file = Path("corpus_creation/events.csv")
  if not file.is_file() or rewrite:
    events = pd.Series(pd.unique(data['event']))
    events.to_csv("corpus_creation/events.csv", header=False, index=False)
    return events
  events = pd.read_csv("corpus_creation/events.csv", header=None)
  return events[0]

def get_names(data, rewrite=False):
  file = Path("corpus_creation/interviewee_names.csv")
  if not file.is_file() or rewrite:
    names = pd.Series(data['names'].explode().unique())
    names.to_csv("corpus_creation/interviewee_names.csv", header=False, index=False)
    return names
  names = pd.read_csv("corpus_creation/interviewee_names.csv", header=None)
  return names[0]

def process(data, nationalities_dict):
  data['text'] = data.apply(chunk, axis=1)
  chunked = data[data['text'].map(len) > 0]

  separated = chunked.apply(separate, args=(nationalities_dict,), axis=1)
  separated_flattened = [x for xs in separated for x in xs]
  
  df = pd.DataFrame(separated_flattened, columns=['question', 'answer', 'event', 'date', 'name', 'nationality'])
  return df

def get_nat_info():
  nat_df = pd.read_csv("corpus_creation/nationality_info.csv") # need this file
  countries = nat_df.iloc[:,0].str.strip()
  adjectivals = nat_df.iloc[:,1].str.strip()
  nat_info = dict(zip(adjectivals, countries)) # maps the adjectival to the country
  return adjectivals, nat_info

def find_summary(name):
  name = re.sub(r"[\"\',]", "", name)
  results = wikipedia.search(name)
  for page in results:
    try:
      summary = wikipedia.summary(title=page, auto_suggest=False)
      if "baseball" in summary.lower():
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
      continue
  # print(f"\"baseball\" not found in any summary for {name}")
  return "None"

def get_summaries(names):
  sums = []
  for name in names:
    sums.append([name, find_summary(name)])
  sums_df = pd.DataFrame(sums, columns=["name", "summary"], dtype=str)
  return sums_df

def make_summaries(names, rewrite=False):
  file = Path("corpus_creation/summaries.csv")
  if not file.is_file() or rewrite:
    # make the summaries csv
    summaries = get_summaries(names)
    summaries.to_csv("corpus_creation/summaries.csv", index=False)

  summaries = pd.read_csv("corpus_creation/summaries.csv")

  summaries_dict = dict(zip(summaries['name'], summaries['summary']))
  return summaries_dict

def nationality(name, dict, adjectivals, nat_info):
  summary = dict[name]
  if not isinstance(summary, str):
    return None
  pattern = '(?:% s)' % '|'.join(adjectivals)

  # print(f"name: {name}\nsummary:{summary}\n")

  pos = summary.find(")")
  match = re.search(pattern, summary[pos:])
  if match is None:
    # print(f"nationality not found for {name}.\nSummary: {summary}")
    return None
  return nat_info[match.group(0)]

def get_nat_dict(names, summaries_dict, rewrite=False):
  file = Path("corpus_creation/player_nationalities.csv")
  if not file.is_file() or rewrite:
    adjectivals, nat_info = get_nat_info()
    nationalities = names.apply(nationality, args=(summaries_dict, adjectivals, nat_info))
    df = pd.DataFrame({'name'        : names,
                       'nationality' : nationalities})
    df.to_csv("corpus_creation/player_nationalities.csv", index=False)
    nationalities_dict = dict(zip(names, nationalities))
    return nationalities_dict
  
  player_nats = pd.read_csv("corpus_creation/player_nationalities.csv")
  players = player_nats.iloc[:,0].str.strip()
  nationalities = player_nats.iloc[:,1].str.strip()
  nationalities_dict = dict(zip(players, nationalities))

  return nationalities_dict

# rewrite flag decides whether to rewrite the csv or not
rw_flag = False

# putting it all together
weblink = "https://www.asapsports.com/showcat.php?id=2"
raw_data = scrape(weblink, rewrite=rw_flag)
mlb_data = filter(raw_data)

events = get_events(mlb_data, rewrite=rw_flag)
names = get_names(mlb_data, rewrite=rw_flag)

summaries_dict = make_summaries(names, rewrite=rw_flag)
nationalities_dict = get_nat_dict(names, summaries_dict, rewrite=rw_flag)

processed_mlb_data = process(mlb_data, nationalities_dict).dropna()
processed_mlb_data.to_csv("data/sportsQnA.csv", index=False)