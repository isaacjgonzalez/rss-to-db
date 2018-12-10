#!/usr/bin/env python
# -*- coding: utf-8 -*-

from newspaper import Article
url = "https://espello.gal/2018/03/20/enfermidades-2-0/"
article = Article(url)
article.parse()
print(article.text)
print(article.top_image)
print(article.movies)
