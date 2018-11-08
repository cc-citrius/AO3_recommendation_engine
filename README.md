This is a content-based recommendation engine for the website ArchiveOfOurOwn.org, aka AO3. AO3 is a fan-made website hosting millions of fanfictions. Right now it does not have an API, so all the data have to be scraped from html in order to form a database. After that an algorithm based on nearest neighbours will fetch entries from the data base that are closest to the user’s interest. Functions to plot a variety of statistics, or as Tumblr likes to call it, fandometrics, are also included so that users can explore their fandom of interest.
This repository contains 5 files.

Main.ipynb: For now this Jupyter Notebook serves as the user interface. First the user has to specify the fandom they would like to explore; this is done by providing the AO3’s search-by-tag page of any specified fandom/pairing, assuming the user knows AO3 well enough to navigate around the site. Next, information about fictions will be scraped from html stemmed from the webpage the user provided; a script utilising multi-threading process is called to speed up the process. This should take less than a minute; after that recommendations can be made when the user input any fiction of interest, provided that it is also on AO3. Additionally functions are provided at the end to show statistics of interest for the given fandom: percentage of fictions of different ratings and types, the most mentioned characters and the ratio of works that are never finished.

NN_weight_training.ipynb: This Jupyter Notebook trains the weight vector used in the nearest-neighbors algorithm. Numerical differentiation was coded for a gradient-descent algorithm. Sample recommendation lists are obtained from Tumblr, their AO3 archive found and scraped, and the weight vector was trained so that the sum of the similarity score between individual pairs of works in the list is minimized. Only one training data set is included in this notebook.

Popularity_Score.ipynb: This Jupyter Notebook describes how a popularity score is generated for each fiction.

ao3_functions.py: Includes all the functions called in Main.ipynb.
scraping_threading.py: Called by Main.ipynb. Html scraping with multi-processors.
