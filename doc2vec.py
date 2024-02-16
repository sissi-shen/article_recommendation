import sys
import re
import string
import os
import numpy as np
import codecs
import pickle

# From scikit learn that got words from:
# http://ir.dcs.gla.ac.uk/resources/linguistic_utils/stop_words
ENGLISH_STOP_WORDS = frozenset([
    "a", "about", "above", "across", "after", "afterwards", "again", "against",
    "all", "almost", "alone", "along", "already", "also", "although", "always",
    "am", "among", "amongst", "amoungst", "amount", "an", "and", "another",
    "any", "anyhow", "anyone", "anything", "anyway", "anywhere", "are",
    "around", "as", "at", "back", "be", "became", "because", "become",
    "becomes", "becoming", "been", "before", "beforehand", "behind", "being",
    "below", "beside", "besides", "between", "beyond", "bill", "both",
    "bottom", "but", "by", "call", "can", "cannot", "cant", "co", "con",
    "could", "couldnt", "cry", "de", "describe", "detail", "do", "done",
    "down", "due", "during", "each", "eg", "eight", "either", "eleven", "else",
    "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone",
    "everything", "everywhere", "except", "few", "fifteen", "fifty", "fill",
    "find", "fire", "first", "five", "for", "former", "formerly", "forty",
    "found", "four", "from", "front", "full", "further", "get", "give", "go",
    "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter",
    "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his",
    "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed",
    "interest", "into", "is", "it", "its", "itself", "keep", "last", "latter",
    "latterly", "least", "less", "ltd", "made", "many", "may", "me",
    "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly",
    "move", "much", "must", "my", "myself", "name", "namely", "neither",
    "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone",
    "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on",
    "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our",
    "ours", "ourselves", "out", "over", "own", "part", "per", "perhaps",
    "please", "put", "rather", "re", "same", "see", "seem", "seemed",
    "seeming", "seems", "serious", "several", "she", "should", "show", "side",
    "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone",
    "something", "sometime", "sometimes", "somewhere", "still", "such",
    "system", "take", "ten", "than", "that", "the", "their", "them",
    "themselves", "then", "thence", "there", "thereafter", "thereby",
    "therefore", "therein", "thereupon", "these", "they", "thick", "thin",
    "third", "this", "those", "though", "three", "through", "throughout",
    "thru", "thus", "to", "together", "too", "top", "toward", "towards",
    "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us",
    "very", "via", "was", "we", "well", "were", "what", "whatever", "when",
    "whence", "whenever", "where", "whereafter", "whereas", "whereby",
    "wherein", "whereupon", "wherever", "whether", "which", "while", "whither",
    "who", "whoever", "whole", "whom", "whose", "why", "will", "with",
    "within", "without", "would", "yet", "you", "your", "yours", "yourself",
    "yourselves"])


def load_glove(filename):
    """
    Read all lines from the indicated file and return a dictionary
    mapping word:vector where vectors are of numpy `array` type.
    GloVe file lines are of the form:

    the 0.418 0.24968 -0.41242 0.1217 ...

    So split each line on spaces into a list; the first element is the word
    and the remaining elements represent factor components. The length of the vector
    should not matter; read vectors of any length.

    ignore stopwords
    """
    glove_dict = {}
    
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split()
            word = parts[0]
            if word not in ENGLISH_STOP_WORDS:
                vector = np.array([float(v) for v in parts[1:]])
                glove_dict[word] = vector
    
    return glove_dict


def filelist(root):
    """Return a fully-qualified list of filenames under root directory"""
    allfiles = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            allfiles.append(os.path.join(path, name))
    return allfiles


def get_text(filename):
    """
    Load and return the text of a text file, assuming latin-1 encoding as that
    is what the BBC corpus uses.  Use codecs.open() function not open().
    """
    f = codecs.open(filename, encoding='latin-1', mode='r')
    s = f.read()
    f.close()
    return s


def words(text):
    """
    Given a string, return a list of words normalized as follows.
    
        1. Lowercase all words
        2. Use re.sub function and string.punctuation + '0-9\\r\\t\\n]'
            to replace all those char with a space character.
        3. Split on space to get word list.
        4. Ignore words < 3 char long.
        5. Remove English stop words
    Don't use Spacy.
    """
    text = text.lower()
    text = re.sub("[" + string.punctuation + '0-9\\r\\t\\n]', ' ', text)

    word_list = text.split()
    word_list = [word for word in word_list if len(word)>=3 and word not in ENGLISH_STOP_WORDS]
    
    return word_list


def split_title(text):
    """
    Given text returns title and the rest of the article.

    Split the test by "\n" and assume that the first element is the title
    """
    parts = text.split('\n', 1)

    title = parts[0].strip()
    article = parts[1].strip()

    return title, article


def load_articles(articles_dirname, gloves):
    """
    Load all .txt files under articles_dirname and return a table (list of lists/tuples)
    where each record is a list of:

      [filename, title, article-text-minus-title, wordvec-centroid-for-article-text]

    We use gloves parameter to compute the word vectors and centroid.

    The filename is fully-qualified name of the text file including
    the path to the root of the corpus passed in on the command line.

    When computing the vector for each document, use just the text, not the text and title.
    """
    article_table = []
    file_list = filelist(articles_dirname)

    for file in file_list:
        if file.endswith(".txt"):
            file_txt = get_text(file)
            title, article = split_title(file_txt)

            vector_centroid = doc2vec(article, gloves)

            record = [file, title, article, vector_centroid]
            article_table.append(record)

    return article_table


def doc2vec(text, gloves):
    """
    Return the word vector centroid for the text. Sum the word vectors
    for each word and then divide by the number of words. Ignore words
    not in gloves.
    """
    word_list = words(text)
    word_sum = 0
    word_in_gloves = 0
    for word in word_list:
        if word in gloves.keys():
            word_in_gloves += 1
            word_sum += gloves[word]
            vectors = [gloves.get(word)]

    vector_centroid = word_sum / word_in_gloves
    return vector_centroid


def distances(article, articles):
    """
    Compute the euclidean distance from article to every other article.

    Inputs:
        article = [filename, title, text-minus-title, wordvec-centroid]
        articles is a list of [filename, title, text-minus-title, wordvec-centroid]

    Output:
        list of (distance, a) for a in articles
        where a is a list [filename, title, text-minus-title, wordvec-centroid]
    """
    distance_list = []
    article_vector = article[3]
    for a in articles:
        a_vector = a[3]
        distance = np.linalg.norm(article_vector - a_vector)
        distance_list.append((distance, a))
    return distance_list


def recommended(article, articles, n):
    """ Return top n articles closest to article.

    Inputs:
        article: list [filename, title, text-minus-title, wordvec-centroid]
        articles: list of list [filename, title, text-minus-title, wordvec-centroid]

    Output:
         list of [topic, filename, title]
    """
    distance_list = sorted(distances(article, articles), key=lambda x: x[0])

    recommended_articles = []
    for i in range(n):
        filepath = distance_list[i+1][1][0]
        filename = filepath.split('/')[-1]
        title = distance_list[i+1][1][1]
        topic = filepath.split('/')[-2]
        info = [topic, filename, title]
        recommended_articles.append(info)

    return recommended_articles


def main():
    glove_filename = sys.argv[1]
    articles_dirname = sys.argv[2]

    gloves = load_glove(glove_filename)
    articles = load_articles(articles_dirname, gloves)

    # save a articles.pkl a list with the following information about articles
    # [[topic, filename, title, text], ...]
    articles_info = [[a[0].split('/')[-2], a[0].split('/')[-1], a[1], a[2]] for a in articles]
    with open('articles.pkl', 'wb') as articles_file:
        pickle.dump(articles_info, articles_file)

    # save in recommended.pkl a dictionary with top 5 recommendations for each article. 
    # given an article use (topic, filename) as the key
    # the recomendations are a list of [topic, filename, title] for the top 5 closest articles
    # you may want to also add the title and test of the current article
    rec = {}
    for a in articles:
        key = (a[0].split('/')[-2], a[0].split('/')[-1])
        top_5 = recommended(a, articles, 5)
        rec[key] = top_5

    with open('recommended.pkl', 'wb') as recommended_file:
        pickle.dump(rec, recommended_file)


if __name__ == '__main__':    
    main()


