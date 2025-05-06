Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

# baseball-interview
This repository contains a corpus consisting of ASAP Sports (https://www.asapsports.com/) interviews of Major League Baseball players with labels of the players' nationalities. Also included in this repository is the code for constructing this corpus, which should be easily modifiable for interviews of other sports represented on ASAP Sports. In this repository, we analyze this corpus for differences between the questions asked to Asian MLB players and questions asked to American MLB players.
## Necessary Modules and Files
This repository makes use of the following external modules:
- numpy
- pandas
- requests
- bs4
- tqdm
- Levenshtein
- wikipedia
The files used to construct the corpus are included in *corpus_creation/*. However, most of these files are only used as "checkpoints" such that the entire process of scraping, cleaning, labelling, etc. need not be repeated to reassemble the corpus. Only the file called *player_nationalities.csv* is **strictly necessary** for the construction of the corpus, as there is no code in the repository to obtain that information. Additionally, the leftover artifacts from the developmental process is included in *artifacts/*.
## Usage
The corpus is included in *data.zip*; the corpus creation files are included in *corpus_creation.zip*. To access them, simply unzip the files. The code for assembling the corpus can be executed via the Jupyter notebook *make_corpus.ipynb* or by running *make_corpus.py* in a terminal. The file *experiment.ipynb* can be run to execute the experiment using the corpus.