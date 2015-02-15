__author__ = "Aaron Huus"
__email__ = "huus@thehumangeo.com"


from random import choice
import sys
import json
import codecs
import glob
import wikipedia
import os.path
from BeautifulSoup import BeautifulSoup
import zipfile
import ntpath

fridge_words = ["service", "backend", "cache", "miss", "database", "op", "monitor", "data", "availability",
                "scalability", "not", "ready", "for", "app", "launch", "the", "in", "everything",
                "hit", "hack", "cloud", "a", "enterprise", "oriented", "system", "critical", "unicorn", "host", "latency",
                "with", "micro", "performance", "distributed", "need", "don't", "get", "high", "run", "like", "time",
                "over", "big", "mobile", "frontend", "responsive", "but", "always", "ironic","web", "still", "so", "boring",
                "open", "I'm", "framework", "it", "low", "yet", "you", "only", "what", "which", "out", "social", "network", "."]


def get_model(requested_order):
    if isinstance(requested_order, int):
        requested_order = str(requested_order)
    if os.path.isfile("models.json"):
        result = read_model_from_disk("models.json")
        return result["models"][requested_order]["model"]

    information = get_wikipedia_articles(fridge_words)
    #information = read_model_from_disk("wikipedida_articles.json")
    write_model_to_disk(information, "wiki_articles.txt")
    result = {
        "models" : {},
    }
    for order in range(1,6):
        word_count, model = generate_model(order, information)
        result["models"][order] = {}
        result["models"][order]["fragments"] = len(model.keys())
        result["models"][order]["model"] = model
        print "Generated model for order %s with %s fragments and %s examples" % (order, len(model.keys()), word_count)
        result["models"][order]["examples"] = word_count
    write_model_to_disk(result,"models.json")
    return result["models"][requested_order]["model"]

def generate_model(order, articles, model=None, word_count=0):

    for article in articles:
        for word in range(0,len(article) - order):
            fragment = strip_word(article[word])
            for j in range(1,order):
                fragment.extend(strip_word(article[word+j]))
            next_word = article[word + order]
            if not on_fridge(fragment, next_word):
                continue
            fragment = ' '.join(fragment)
            if fragment not in model:
                model[fragment] = {}
            if next_word not in model[fragment]:
                model[fragment][next_word] = 1
            else:
                model[fragment][next_word] += 1
            word_count += 1
    return word_count, model

def add_word_to_model()

def strip_word(word):
    return ["".join(c for c in word.strip().lower() if c not in ('!',',',';',':'))]

def on_fridge(fragment, next_word):
    _fridge_words = list(fridge_words)
    if fragment[0] == ".":
        return False
    for word in fragment:
        if word not in _fridge_words:
            return False
        _fridge_words.remove(word)
    if next_word not in _fridge_words:
        return False
    _fridge_words.remove(next_word)
    return True

def get_wikipedia_articles(search_words):
    articles = []
    for count, word in enumerate(search_words):
        results = wikipedia.search(word, results=75)
        for result in results:
            try:
                article = wikipedia.page(result)
            except:
                print "Skipping disambiguation page for %s ..." % result
                continue
            articles.append(article.content.replace("."," . ").split())
        print "Read %s articles about the term: \"%s\"" % (len(results), word)
        percent_complete = float((count+1)) / float(len(search_words)) * 100
        print "Completed %s terms: %f percent\n" % (count+1, percent_complete)
    return articles

def get_words_from_books(directory):
    books = []
    for book in glob.glob(directory):
        words = get_words_from_utf8_file(book)
        books.append(words)
    return books

def get_words_from_utf8_file(book_path):
    print book_path
    with codecs.open(book_path, encoding='utf-8') as book:
        BOM = codecs.BOM_UTF8.decode('utf8')
        words = []
        for line in book:
            print line
            words.extend(line.lstrip(BOM).split())
        print "Read %s" % os.path.basename(book_path)
    return words

def get_words_from_file(book_path):
    print book_path
    with codecs.open(book_path) as book:
        words = []
        for line in book:
            print line
            words.extend(line.split())
        print "Read %s" % os.path.basename(book_path)
    return words

def get_words_from_zip2(zip_path):
    base_path , filename = ntpath.split(zip_path)
    book_base = filename.split(".")[0]
    book_name = book_base + ".txt"
    download_path = "/Users/Aaron/Downloads/"
    book_path = download_path + book_name
    zfile = zipfile.ZipFile(zip_path)
    zfile.extractall(download_path)
    if not os.path.isfile(book_path):
        book_path = book_path.replace("_", "-")
        if not os.path.isfile(book_path):
            book_path = download_path + book_base.split("_")[0] + "/" + book_name
            if not os.path.isfile(book_path):
                book_path = download_path + book_base.split("_")[0] + "/" + book_name.replace("_","-")
    words = get_words_from_file(book_path)
    os.remove(book_path)
    return words

def get_words_from_zip(zip_path):
    words = []
    try:
        zfile = zipfile.ZipFile(zip_path)
    except:
        print "Error opening %s" % zip_path
    for finfo in zfile.infolist():
        try:
            book = zfile.open(finfo)
        except:
            print "Cannot open %s" % finfo.filename
            return []
        if finfo.filename.endswith('.txt'):
            for line in book:
                words.extend(line.replace("."," . ").split())
    return words

def update_model_from_gutenberg(iso_mount_point):
    book_count = 0
    for page_path in glob.glob(iso_mount_point + "/indexes/AUTHORS_*.HTML"):
        print "Reading all books from %s" % page_path
        books=[]
        with open(page_path, 'r') as page:
            data = page.read()
            soup = BeautifulSoup(data)
            book_links = soup.findAll('a')
            for book_link in book_links:
                if ("etext" in book_link['href']) and ("(English)" in book_link.parent.text):
                    base_path , filename = ntpath.split(page_path)
                    book_page_path = base_path + "/" + book_link['href']
                    with open(book_page_path, 'r') as book_page:
                        book_page_data = book_page.read()
                        soup2 = BeautifulSoup(book_page_data)
                        book_path = soup2.findAll('table')[1].findAll('td')[1].find('a')
                        book_zip_path = base_path + "/" + book_path['href']
                        if book_zip_path.endswith(".zip"):
                            words = get_words_from_zip(book_zip_path)
                        else:
                            continue
                        books.append(words)
                        book_count = book_count + 1
                        if book_count % 100 == 0:
                            print "Read %s books" % book_count
            update_model(books)

def generate_sentence(order, words_in_a_sentence, number_of_sentences, seed_original=None):
    model = get_model(order)
    for loop in range(0, number_of_sentences):
        sentence = []
        while len(sentence) < words_in_a_sentence:
            _fridge_words = list(fridge_words)
            if not seed_original:
                first_word = choice(fridge_words)
                while first_word == ".":
                    first_word = choice(fridge_words)
                seed = [first_word]
                for seed_number in range(1, order):
                    seed_word = get_next_word(get_model(1), seed[-1])
                    if seed_word and (seed_word in _fridge_words):
                        seed.append(seed_word)
                    else:
                        break
            else:
                seed = seed_original
            current_fragment = seed[0:order]
            for word in current_fragment:
                try:
                    _fridge_words.remove(word)
                except:
                    pass
            sentence = list(current_fragment)
            for i in range(0, words_in_a_sentence - order):
                next_word = get_next_word(model, current_fragment)
                if next_word and (next_word in _fridge_words):
                    sentence.append(next_word)
                    _fridge_words.remove(next_word)
                    current_fragment = list(sentence[order*-1:])
                else:
                    break
            #print ' '.join(sentence)
        print ' '.join(sentence)

def get_next_word(model, fragment):
    words = []
    if isinstance(fragment, list):
        fragment = ' '.join(fragment)

    if fragment not in model.keys():
        return None

    for word in model[fragment].keys():
        for count in range(0, model[fragment][word]):
            words.append(word)
    return choice(model[fragment].keys())

def update_model(information):
    print "Updating model ..."
    result = read_model_from_disk("models.json")
    for order in range(1,6):
        word_count, model = generate_model(order, information, get_model(order), result["models"][str(order)]["examples"])
        result["models"][str(order)]["fragments"] = len(model.keys())
        result["models"][str(order)]["model"] = model
        print "Updated model for order %s with %s fragments and %s examples" % (order, len(model.keys()), word_count)
        result["models"][str(order)]["examples"] = word_count
    write_model_to_disk(result,"models.json")

def write_model_to_disk(model, filename):
    with open(filename, 'wb') as f:
        json.dump(model, f)

def read_model_from_disk(filename):
    with open(filename, 'rb') as f:
        model = json.load(f)
    return model

if __name__ == "__main__":
    order = int(sys.argv[1])
    words_in_a_sentence = int(sys.argv[2])
    number_of_sentences = int(sys.argv[3])

    #information = get_words_from_books("books/*.txt")

    #search_words = ["computer science", "software engineering", "website", "internet", "software", "java", "python", "geography",
                    #"private network", "intranet", "scale", "delay", "tcp/ip", "facebook", "twitter"]
    #information = get_wikipedia_articles(search_words)

    update_model_from_gutenberg("/Volumes/PGDVD_2010_04_RC2")
    #generate_sentence(order, words_in_a_sentence, number_of_sentences)
