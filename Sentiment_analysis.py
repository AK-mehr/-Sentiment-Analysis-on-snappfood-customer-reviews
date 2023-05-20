#!/usr/bin/env python
# coding: utf-8

# In[1]:


from __future__ import unicode_literals
import re
import nltk
from nltk.corpus import stopwords
from hazm import *
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import math
from sklearn.feature_extraction.text import CountVectorizer
from collections import defaultdict
from cleantext import clean
import emoji


# In[2]:


comments = pd.read_csv('/home/ak/hazm-sample/snappfood.csv', sep='\t', on_bad_lines='skip', encoding='utf-8')
comments = comments.drop('Unnamed: 0', axis=1)
comments.dropna(inplace=True)
comments['label_id'] = comments['label_id'].astype(int)
comments.head(10)


# In[3]:


normalizer = Normalizer()
stemmer = Stemmer()
tagger = POSTagger(model='./resources/postagger.model')


def upper_repl(match):
    """ Convert mask-special tokens to real special tokens """
    return " [" + match.group(1).upper().replace('-', '_') + "] "


def convert_emoji_to_text(text, delimiters=('[', ']')):
    """ Convert emojis to something readable by the vocab and model """
    text = emoji.demojize(text, delimiters=delimiters)
    return text


def clean_html(raw_html):
    """ Remove all html tags """
    cleaner = re.compile('<.*?>')
    cleaned = re.sub(cleaner, '', raw_html)
    return cleaned


def clean_text(
        raw_text,
        fix_unicode=True,
        to_ascii=False,
        lower=True,
        no_line_breaks=True,
        no_urls=True,
        no_emails=True,
        no_phone_numbers=True,
        no_numbers=False,
        no_digits=False,
        no_currency_symbols=True,
        no_punct=False,
        replace_with_url="",
        replace_with_email="",
        replace_with_phone_number="",
        replace_with_number="",
        replace_with_digit="0",
        replace_with_currency_symbol=""):
    """ Preprocessing and normalization the text a the low level """
    cleaned = clean(
        raw_text,
        fix_unicode=fix_unicode,
        to_ascii=to_ascii,
        lower=lower,
        no_line_breaks=no_line_breaks,
        no_urls=no_urls,
        no_emails=no_emails,
        no_phone_numbers=no_phone_numbers,
        no_numbers=no_numbers,
        no_digits=no_digits,
        no_currency_symbols=no_currency_symbols,
        no_punct=no_punct,
        replace_with_url=replace_with_url,
        replace_with_email=replace_with_email,
        replace_with_phone_number=replace_with_phone_number,
        replace_with_number=replace_with_number,
        replace_with_digit=replace_with_digit,
        replace_with_currency_symbol=replace_with_currency_symbol
    )
    return cleaned


def cleaning(
        text,
        wikipedia=True,
        default_cleaning=True,
        normalize_cleaning=True,
        half_space_cleaning=True,
        html_cleaning=True,
        emoji_convert=False,
        username_cleaning=True,
        hashtag_cleaning=True,
        fix_unicode=True,
        to_ascii=False,
        lower=True,
        no_line_breaks=True,
        no_urls=True,
        no_emails=True,
        no_phone_numbers=True,
        no_numbers=False,
        no_digits=False,
        no_currency_symbols=True,
        no_punct=False,
        replace_with_url="",
        replace_with_email="",
        replace_with_phone_number="",
        replace_with_number="",
        replace_with_digit="0",
        replace_with_currency_symbol=""):
    """ A hierarchy of normalization and preprocessing """
    text = text.strip()
    
    if wikipedia:
        # If your data extracted from WikiPedia
        text = text.replace('_', ' ')
        text = text.replace('«', '').replace('»', '')
        text = text.replace('[[', '[').replace(']]', ']')
        text = text.replace('[ [ ', '[').replace(' ] ]', ']')
        text = text.replace(' [ [', ' [').replace('] ] ', '] ')
        text = text.replace(' [ [ ', ' [').replace(' ] ] ', '] ')
        text = text.replace(' . com', '.com').replace('. com', '.com')
        text = text.replace(' . net', '.net').replace('. net', '.net')
        text = text.replace(' . org', '.org').replace('. org', '.org')
        text = text.replace(' . io', '.io').replace('. io', '.io')
        text = text.replace(' . io', '.io').replace('. io', '.io')
        text = text.replace('ه ی', 'ه')
        text = text.replace('هٔ', 'ه')
        text = text.replace('أ', 'ا')

    if username_cleaning:
        text = re.sub(r"\@[\w.-_]+", " ", text)

    if hashtag_cleaning:
        text = text.replace('#', ' ')
        text = text.replace('_', ' ')

    if emoji_convert:
        text = emoji.emojize(text)
        text = convert_emoji_to_text(text)

    # regular cleaning
    if default_cleaning:
        text = clean_text(
            text,
            fix_unicode,
            to_ascii,
            lower,
            no_line_breaks,
            no_urls,
            no_emails,
            no_phone_numbers,
            no_numbers,
            no_digits,
            no_currency_symbols,
            no_punct,
            replace_with_url,
            replace_with_email,
            replace_with_phone_number,
            replace_with_number,
            replace_with_digit,
            replace_with_currency_symbol
        )

    # cleaning HTML
    if html_cleaning:
        text = clean_html(text)

    # normalizing
    if normalize_cleaning:
        text = normalizer.normalize(text)

    # removing weird patterns
    weird_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u'\U00010000-\U0010ffff'
        u"\u200d"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\u3030"
        u"\ufe0f"
        u"\u2069"
        u"\u2066"
        u"\u2013"
        u"\u2068"
        u"\u2067"
        "]+", flags=re.UNICODE)

    text = weird_pattern.sub(r'', text)

    # removing extra spaces, hashtags
    text = re.sub("#", "", text)
    # text = re.sub("\s+", " ", text)

    if emoji_convert:
        text = re.sub(r"\[(\w.+)\]", upper_repl, text)
        # text = re.sub("\s+", " ", text)

    if half_space_cleaning:
        text = text.replace('\u200c', ' ')
        # text = re.sub("\s+", " ", text)
    
    return text


def sent_tokenizer(text, cleaning_fn=None, return_status=False):
    text = cleaning_fn(text) if callable(cleaning_fn) else text
    _words = word_tokenize(text)
    words = tagger.tag(_words)
    items = list(filter(lambda w: (w[1][1] == 'V') and ((len(words) > (w[0] + 1)) and (words[w[0] + 1][0] in "!.?⸮؟")),
                        enumerate(words)))
    # items = list(filter(lambda w: (w[1][1] == 'V') and ((words[w[0] + 1][0] in "!.?⸮؟")), enumerate(words)))
    sid = list(sorted(map(lambda w: w[0] + 1, items)))
    sentences = []

    if not len(sid) > 0:
        if return_status:
            return False, [text]
        return [text]

    sid = list(sorted(list(set([0] + sid + [len(_words) - 1]))))
    for i in range(0, len(sid) - 1):
        if i == 0:
            start = 0
            end = sid[i + 1]
        else:
            start = sid[i]
            end = sid[i + 1]

        ss = _words[start: end]
        s = ' '.join(ss[:-1])
        s = s.replace('_', ' ').replace('_', ' ')
        s = s.replace(' . ', '.')
        s = s.replace('( ', ' (').replace(' )', ') ')
        s = s + ' ' + ss[-1].replace('_', ' ')
        s = re.sub('\s\s+', ' ', s)

        sentences.append(s)

    if return_status:
        return True, sentences

    return sentences


def sent_tokenizer_v2(text):
    words = tagger.tag(word_tokenize(text))

    items = list(filter(lambda w: (w[1][1] == 'V') and ((len(words) > (w[0] + 1)) and (words[w[0] + 1][0] in "!.?⸮؟")),
                        enumerate(words)))
    ids = list(map(lambda w: w[0] + 1, items))
    sentences = []

    for i in range(len(ids)):
        if i == 0:
            if ids[i] > 0:
                start = 0
                end = ids[i] + 1
        else:
            start = ids[i - 1] + 1
            end = ids[i] + 1

        ss = list(map(lambda w: w[0], words[start: end]))
        s = ' '.join(ss[:-1])
        s = s.replace('_', ' ').replace('_', ' ')
        s = s.replace(' . ', '.')
        s = s.replace('( ', ' (').replace(' )', ') ')
        # s = s + ' ' + ss[-1].replace('_', ' ')
        s = re.sub('\s\s+', ' ', s)
        sentences.append(s)

    return sentences
    
    
    
def preprocessing_text(string):
    # result = upper_repl(string)
    result = convert_emoji_to_text(string)
    result = clean_html(result)
    result = clean_text(result)
    result = cleaning(result)
    # result = sent_tokenizer(result)
    # result = sent_tokenizer_v2(result)
    return result



# In[4]:


comments['comment'] = comments['comment'].apply(lambda cw: preprocessing_text(cw))


# In[5]:


feedbacks = comments['comment'].values
sentiment = comments['label'].values
encoder = LabelEncoder()
encoded_labels = encoder.fit_transform(sentiment)

train_sentences, test_sentences, train_labels, test_labels = train_test_split(feedbacks, encoded_labels, stratify=encoded_labels)


# In[6]:


vec = CountVectorizer(max_features = 3000)
X = vec.fit_transform(train_sentences)
vocab = vec.get_feature_names_out()
X = X.toarray()

word_counts = {}
for l in range(2):
    word_counts[l] = defaultdict(lambda: 0)
for i in range(X.shape[0]):
    l = train_labels[i]
    for j in range(len(vocab)):
        word_counts[l][vocab[j]] += X[i][j]


# In[9]:


def laplace_smoothing(n_label_items, vocab, word_counts, word, text_label):
    a = word_counts[text_label][word] + 1
    b = n_label_items[text_label] + len(vocab)
    return math.log(a/b)

def group_by_label(x, y, labels):
    data = {}
    for l in labels:
        data[l] = x[np.where(y == l)]
    return data


def fit(x, y, labels):
    n_label_items = {}
    log_label_priors = {}
    n = len(x)
    grouped_data = group_by_label(x, y, labels)
    for l, data in grouped_data.items():
        n_label_items[l] = len(data)
        log_label_priors[l] = math.log(n_label_items[l] / n)
    return n_label_items, log_label_priors


def predict(n_label_items, vocab, word_counts, log_label_priors, labels, x):
    result = []
    for text in x:
        label_scores = {l: log_label_priors[l] for l in labels}
        words = set(word_tokenize(text))
        for word in words:
            if word not in vocab: continue
            for l in labels:
                log_w_given_l = laplace_smoothing(n_label_items, vocab, word_counts, word, l)
                label_scores[l] += log_w_given_l
        result.append(max(label_scores, key=label_scores.get))
    return result


# In[10]:


labels = [0,1]

n_label_items, log_label_priors = fit(train_sentences,train_labels,labels)
pred = predict(n_label_items, vocab, word_counts, log_label_priors, labels, test_sentences)
print("Accuracy of prediction on test set : ", accuracy_score(test_labels,pred))


# In[ ]:




