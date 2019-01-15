import PyPDF2 

try:
    from urllib import urlretrieve as urlretrieve
except ImportError:
    from urllib.request import urlretrieve as urlretrieve    

import os

#import matplotlib as plt
import pylab as pl
import pandas as pd
import string


from numpy import array
from pickle import dump
from keras.preprocessing.text import Tokenizer
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Embedding


from random import randint
from pickle import load
from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences


# load doc into memory
def load_doc(filename):
    # open the file as read only
    file = open(filename, 'r')
    # read all text
    text = file.read()
    # close the file
    file.close()
    return text

def getText(file,start,end):
    print(start,end)
    data = pd.read_csv(file)
    print("Total articles: ",len(data))
    if len(data) < end:
        end = len(data)
    text = ' '.join(data.content.values[start:end])
    print("Sample articles: ",end-start)
    return text



# turn a doc into clean tokens
def clean_doc(doc):
    # replace '--' with a space ' '
    doc = doc.replace('--', ' ')
    # split into tokens by white space
    tokens = doc.split()
    # remove punctuation from each token
    table = str.maketrans('', '', string.punctuation)
    tokens = [w.translate(table) for w in tokens]
    # remove remaining tokens that are not alphabetic
    tokens = [word for word in tokens if word.isalpha()]
    # make lower case
    tokens = [word.lower() for word in tokens]
    return tokens

# organize into sequences of tokens
def getSequences(tokens):
    length = 50 + 1
    sequences = list()
    for i in range(length, len(tokens)):
        # select sequence of tokens
        seq = tokens[i-length:i]
        # convert into a line
        line = ' '.join(seq)
        # store
        sequences.append(line)
    print('Total Sequences: %d' % len(sequences))
    return sequences

def get_lines():
    doc = getText('crimeData.csv',0,5000)
    tokens = clean_doc(doc)
    #print(tokens[:5])
    print('Total Tokens: %d' % len(tokens))
    print('Unique Tokens: %d' % len(set(tokens))) 
    lines = getSequences(tokens)
    print('Sequences generated!')
    out_filename = 'csv1_sequences.txt'
    with open(out_filename, 'w') as f:
        for item in lines:
            f.write("%s\n" % item)
    return lines

def get_sequences():
    lines = get_lines()
    # integer encode sequences of words
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(lines)
    # save the tokenizer
    dump(tokenizer, open('tokenizer5k.pkl', 'wb'))
    print('Tokenizer saved!')
    sequences = tokenizer.texts_to_sequences(lines)
    # vocabulary size
    vocab_size = len(tokenizer.word_index) + 1
    print("Vocab SIze :",vocab_size)
    return sequences, vocab_size

def train_tokenizer():
    lines = get_lines()
    # integer encode sequences of words
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(lines)
    # save the tokenizer
    dump(tokenizer, open('tokenizer5k.pkl', 'wb'))
    print('Tokenizer saved!')
    #sequences = tokenizer.texts_to_sequences(lines)
    # vocabulary size
    #vocab_size = len(tokenizer.word_index) + 1
    #print("Vocab SIze :",vocab_size)
    return 

def get_sequence_tokenizer():
    lines = get_lines()
    # load the tokenizer
    tokenizer = load(open('tokenizer5k.pkl', 'rb'))
    sequences = tokenizer.texts_to_sequences(lines)
    # vocabulary size
    vocab_size = len(tokenizer.word_index) + 1
    print("Vocab SIze :",vocab_size)
    return sequences, vocab_size

def get_x_y():
    sequences,vocab_size = get_sequence_tokenizer()
    # separate into input and output
    sequences = array(sequences)
    X, y = sequences[:,:-1], sequences[:,-1]
    y = to_categorical(y, num_classes=vocab_size)
    return X,y, vocab_size

def get_sequence_tokenizer_lines(tokenizer,lines):
    sequences = tokenizer.texts_to_sequences(lines)
    return sequences


exists = os.path.isfile('tokenizer5k.pkl')
if not exists:
    train_tokenizer()



# load the tokenizer
tokenizer = load(open('tokenizer5k.pkl', 'rb'))
    
# vocabulary size
vocab_size = len(tokenizer.word_index) + 1
print("Vocab SIze :",vocab_size)

seq_length = 50

exists = os.path.isfile('model5k.h5')
if not exists:
    # define model
    model = Sequential()
    model.add(Embedding(vocab_size, 50, input_length=seq_length))
    model.add(LSTM(100, return_sequences=True))
    model.add(LSTM(100))
    model.add(Dense(100, activation='relu'))
    model.add(Dense(vocab_size, activation='softmax'))
    print(model.summary())
    # compile model
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
else:
    model = load_model('model5k.h5')


epochs = 50

for e in range(epochs):
    print('Epoch :',e)
    endData = True
    i=0
    while endData:
        print('Epoch :',e)
        start = i*1000
        end = (i+1)*1000
        lines = load_doc('csv1_sequences.txt').split('\n')
        if end >= len(lines):
            break
            end = len(lines)
            endData = False
        lines = lines[start:end]
        sequences = tokenizer.texts_to_sequences(lines)
        # separate into input and output
        sequences = array(sequences)
        X, y = sequences[:,:-1], sequences[:,-1]
        y = to_categorical(y, num_classes=vocab_size)
        # fit model
        model.fit(X, y, batch_size=128, epochs=1)
        print('Processed: ',end)
        # save the model to file
        model.save('model5k.h5')
        i += 1


# save the model to file
model.save('model5k.h5')

