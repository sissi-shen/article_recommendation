# Launch with
#
# python app.py

from flask import Flask, render_template
import sys
import pickle

app = Flask(__name__)

@app.route("/")
def articles():
    """Show a list of article titles"""
    article_list = articles
    return render_template("articles.html", article_list = article_list)


@app.route("/article/<topic>/<filename>")
def article(topic, filename):
    """
    Show an article with relative path filename. Assumes the BBC structure of
    topic/filename.txt so our URLs follow that.
    """
    key = (topic, filename)
    rec_articles = recommended[key]

    for a in articles:
        if a[0] == topic and a[1] == filename:
            title = a[2]
            text = a[3].split('\n')
            break

    return render_template("article.html", title=title, text=text, rec_articles=rec_articles)


f = open('articles.pkl', 'rb')
articles = pickle.load(f)
f.close()

f = open('recommended.pkl', 'rb')
recommended = pickle.load(f)
f.close()


# you may need more code here or not


# for local debug
if __name__ == '__main__':
    app.run(debug=True)

