# -*- coding: cp1252 -*-
import spacy
import textacy.extract

# Load the large English NLP model
nlp = spacy.load('en_core_web_lg')

# The text we want to examine
text = """Sam is a good boy unlike other peers. he likes to play cricket. Sam was only three when he started to play cricket. He comes from Lahore which is one of the oldest towns in pakistan.
Pakistan has produced many great names in Cricket and Sam aspires to be one of them."""

file = open("testfile.txt", "r") 
text = file.read() 
#text = "My name is Khan."

key = "Umer"

# Parse the document with spaCy
doc = nlp(text)

for token in doc:
    print(token, token.pos_, token.tag_, token.dep_, token.head)
    print()

# 'doc' now contains a parsed version of text. We can use it to do anything we want!
# For example, this will print out all the named entities that were detected:
for entity in doc.ents:
    print(f"{entity.text} ({entity.label_})")

# Extract semi-structured statements
statements = textacy.extract.semistructured_statements(doc, key)

# Print the results
print("Here are the things I know about "+key+ " :")

for statement in statements:
    subject, verb, fact = statement
    print(f" - {fact}")

print("Here are the things I know "+key+ " did:")

for statement in statements:
    subject, verb, fact = statement
    print(f" - {verb}")

