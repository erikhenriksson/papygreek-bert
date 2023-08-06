import os

from flair.models import SequenceTagger
from flair.data import Sentence

os.chdir('tagger')
tagger = SequenceTagger.load('v4/best-model.pt')
os.chdir('..')

def tag(sentences):
    for item in sentences:
        sentence = Sentence(item, use_tokenizer=False)
        tagger.predict(sentence)
        yield sentence.to_dict()