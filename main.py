import os.path
import urllib.request
import urllib.parse
import json

short_a = '\u0B85'
independent_vowels = 'ஆஇஈஉஊஎஏஐஒஓஔ'

pulli = '\u0BCD'
combining_vowels = '\u0BBE\u0BBF\u0BC0\u0BC1\u0BC2\u0BC6\u0BC7\u0BC8\u0BCA\u0BCB\u0BCC'

to_combining = {}
from_combining = {}

for i, c in zip(independent_vowels, combining_vowels):
    to_combining[i] = c
    from_combining[c] = i

vallinam = 'கசடதபற'
mellinam = 'ஙஞணநமன'
idaiyinam = 'யரலவழள'

to_soft = {}
from_soft = {}

for hard, soft in zip(vallinam, mellinam):
    to_soft[hard] = soft
    from_soft[soft] = hard

tamil_consonants = vallinam + mellinam + idaiyinam
grantha_consonants = 'ஜஷஸஹஶ'

vowels = short_a + independent_vowels
consonants = tamil_consonants + grantha_consonants

y_vowels = 'இஈஎஏஐ'
v_vowels = 'அஆஉஊஎஏஒஓஔ'
invalid_start = 'ஙணழளறன'
invalid_end = vallinam + 'ஙஞநவ'
distance_prefixes = 'அஇஎ'

def expand_tamil(tam):
    phonemes = []
    for char in tam:
        if char == pulli:
            phonemes.pop()
        elif char in from_combining:
            phonemes.pop()
            phonemes.append(from_combining[char])
        else:
            phonemes.append(char)
            if char in consonants:
                phonemes.append(short_a)
    return phonemes

def rejoin_tamil(phs):
    tamil = []
    for phoneme in phs:
        if tamil and tamil[-1] == pulli:
            if phoneme == short_a:
                tamil.pop()
                continue
            elif phoneme in to_combining:
                tamil.pop()
                tamil.append(to_combining[phoneme])
                continue
        tamil.append(phoneme)
        if phoneme in consonants:
            tamil.append(pulli)
    return ''.join(tamil).strip()

def load_set(filename):
    if not os.path.isfile(filename):
        return None

    with open(filename) as json_file:
        return set(json.load(json_file))

fetch_string = 'https://dsal.uchicago.edu/cgi-bin/app/fabricius_query.py?format=json&searchhws=yes&qs='
fetched_words = {}
def fetch_with_prefix(prefix):
    if prefix in fetched_words:
        return

    filename = 'words/' + prefix + '.json'
    if words := load_set(filename):
        fetched_words[prefix] = words
        return

    print("Downloading list of '" + prefix + "' words...")
    address = fetch_string + urllib.parse.quote(prefix)
    with urllib.request.urlopen(address, timeout=10) as url:
        response = json.loads(url.read().split(b'\n')[1])

    words = set(map(lambda o: o['hw'], response))
    fetched_words[prefix] = words

    if not os.path.isdir('words'):
        os.mkdir('words')

    with open(filename, 'w') as json_file:
        json.dump(list(words), json_file, ensure_ascii=False, separators=(',', ':'))

def is_in_dictionary(word):
    if not word:
        return False

    first_letter = word[0]
    fetch_with_prefix(first_letter)
    return word in fetched_words[first_letter]

grammatical_suffixes = load_set('grammatical_suffixes.json')

def is_grammatical_suffix(word):
    return word in grammatical_suffixes

def find_ending_variations(word, next_letter):
    if not word:
        return []
    variations = [word]

    last_letter = word[-1]
    if last_letter == 'அ':
        variations.append(word + ['ம'])
        variations.append(word + ['ன'])
    elif last_letter == 'ஆ':
        variations.append(word[:-1] + ['அ', 'ன'])
    elif last_letter == 'ர':
        variations.append(word[:-1] + ['ன'])
    elif word[-3:] == ['ட', 'ட', 'உ'] or word[-3:] == ['ற', 'ற', 'உ']:
        variations.append(word[:-2] + ['உ'])
    elif word[-4:] == ['அ', 'த', 'த', 'உ']:
        variations.append(word[:-3] + ['ம'])

    if word[-3:] == ['இ', 'ய', 'அ']:
        variations.append(word[:-3] + ['உ', 'ம', 'ஐ'])
        variations.append(word[:-3] + ['உ'])
    elif last_letter in mellinam:
        if last_letter == 'ம':
            if len(word) > 2 and word[-2] == 'உ':
                variations.append(word + ['ஐ'])
        elif last_letter == next_letter or from_soft[last_letter] == next_letter:
            variations.append(word[:-1] + ['ம'])
            if len(word) > 2 and word[-2] == 'உ':
                variations.append(word[:-1] + ['ம', 'ஐ'])

    if next_letter:
        if next_letter in vallinam:
            if last_letter in vallinam:
                if last_letter == 'ட':
                    variations.append(word[:-1] + ['ள'])
                elif last_letter == 'ற':
                    variations.append(word[:-1] + ['ன'])
                    variations.append(word[:-1] + ['ல'])
                if last_letter == next_letter:
                    variations += find_ending_variations(word[:-1], next_letter)
            elif last_letter == 'ண':
                variations.append(word[:-1] + ['ள'])
            elif last_letter == 'ன':
                variations.append(word[:-1] + ['ல'])
        elif next_letter in mellinam:
            if last_letter == 'ண':
                variations.append(word[:-1] + ['ள'])
            elif last_letter == 'ன':
                variations.append(word[:-1] + ['ல'])
        elif next_letter in vowels and last_letter in consonants:
            variations += find_ending_variations(word + ['உ'], next_letter)

    return variations

def find_starting_variations(word, prev_letter):
    if not word:
        return []
    variations = [word]

    first_letter = word[0]
    if first_letter == 'இ' and len(word) >= 2 and (word[1] == 'ர' or word[1] == 'ல'):
        variations.append(word[1:])
    elif prev_letter:
        if first_letter == 'ய' and prev_letter in y_vowels:
            variations.append(word[1:])
        elif first_letter == 'வ' and prev_letter in v_vowels:
            variations.append(word[1:])
        elif first_letter == prev_letter:
            if first_letter in vallinam:
                if first_letter == 'ட':
                    variations.append(['த'] + word[1:])
                elif first_letter == 'ற':
                    variations.append(['த'] + word[1:])
            else:
                variations.append(word[1:])
                if first_letter in mellinam:
                    variations.append(['ந'] + word[1:])
        elif first_letter in vallinam and to_soft[first_letter] == prev_letter:
            variations.append(['த'] + word[1:])

    if first_letter in distance_prefixes and len(word) > 3:
        if word[1] in consonants and word[2] == word[1]:
            variations += find_starting_variations(word[2:], None)
            if word[1] == 'வ' and word[3] in vowels:
                variations += find_starting_variations(word[3:], None)
        elif word[1] == 'வ' and word[2] == 'ய' and word[3] in vowels:
            variations += find_starting_variations(word[2:], None)

    return variations

def is_invalid_start_of_split(word):
    if word and word[0] in consonants and (len(word) < 2 or word[1] in consonants):
        return True
    return False

def is_valid(word):
    if not word:
        return False
    if is_invalid_start_of_split(word):
        return False
    if word[0] in invalid_start:
        return False
    if word[-1] in consonants and word[-2] in consonants:
        return False
    if word[-1] in invalid_end:
        return False
    return True

def all_variations(word, prev_letter, next_letter):
    return [
        rejoin_tamil(starting)
        for starting in find_starting_variations(word, prev_letter)
        for ending in find_ending_variations(starting, next_letter)
        if is_valid(starting)
    ]

class Entry:
    def __init__(self, raw, word = None, is_grammatical = False):
        self.raw = raw
        self.word = word
        self.is_grammatical = is_grammatical

def split_word_reversed(word, prev_letter, next_letter):
    # If the word is empty, there are no parts
    if not word:
        return 0, 0, []

    # Default to returning the rest of the word raw if no match is found
    best_index = 0
    best_count = 1
    best_entries = [Entry(word)]

    # Try every possible prefix split, starting with the full word
    for i in range(len(word), 0, -1):
        # Make sure the rest of the word after the split is valid
        after_split = word[i:]
        if is_invalid_start_of_split(after_split):
            continue

        # Find all possible variations of the prefix that could appear in the dictionary
        before_split = word[:i]
        variations = all_variations(before_split, prev_letter, after_split[0] if after_split else next_letter)

        # Pick a prefix that was in the dictionary, if one exists
        matching_prefix = next(filter(is_grammatical_suffix, variations), None)
        is_grammatical = True

        # Otherwise, pick a prefix that was in the dictionary, if one exists
        if not matching_prefix:
            is_grammatical = False
            matching_prefix = next(filter(is_in_dictionary, variations), None)
            if not matching_prefix:
                continue

        # Try to split the rest of the word after this prefix
        index, count, entries = split_word_reversed(after_split, before_split[-1], next_letter)

        # If this is a less complete match, discard it
        index += len(before_split)
        if index < best_index:
            continue

        # Only increment the count if the suffix wasn't grammatical
        if not is_grammatical:
            count += 1

        # If this match requires more component words but is just as complete, discard it
        if index == best_index and count >= best_count:
            continue

        # Add this word to the reversed list of word parts
        entries.append(Entry(before_split, matching_prefix, is_grammatical))

        # This is the best result so far, so record it
        best_index = index
        best_count = count
        best_entries = entries

        # If it was a complete match and the suffix is entirely grammatical, then it cannot be improved
        if count == 0 and best_index == len(word):
            break

    # Return the best match that was found
    return best_index, best_count, best_entries

def split_word(word, prev_letter = None, next_letter = None):
    if prev_letter and prev_letter in consonants and prev_letter not in invalid_end:
        prev_letter = None
    _, _, entries = split_word_reversed(word, prev_letter, next_letter)
    entries.reverse()
    return entries

while line := input():
    vocab_list = set()
    words = list(map(expand_tamil, line.split()))
    for i in range(len(words)):
        prev_letter = None
        next_letter = None
        if i > 0:
            prev_letter = words[i - 1][-1]
        if i < len(words) - 1:
            next_letter = words[i + 1][0]
        first = True
        for entry in split_word(words[i], prev_letter, next_letter):
            if first:
                first = False
            else:
                print(' + ', end='')

            if not entry.word:
                print('(' + rejoin_tamil(entry.raw) + ')', end='')
                continue

            print(entry.word, end='')
            if not entry.is_grammatical:
                vocab_list.add(entry.word)
        print()
    print(vocab_list)
