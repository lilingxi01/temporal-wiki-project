# Temporal Wiki Project

The objective of this project is to analyze and utilize the Wikipedia edit histories for future use in the natural language processing (NLP) field. Wikipedia has been built for a long time and nearly all long documents are built throughout a complicated editing histories. We believe that these informations could be helpful to optimize the NLP model for generating long documents. The main challenge of this project is how can we handle large size of Wikipedia's edit history which is larger than 5TB. Specifically, we are planing to use distributional processing systems such as Hadoop or Spark to make a parser. In addition, we are going to explore a way to efficiently construct a corpus to train machine learning models'.

## File Structure

- You should run `main.py` to run the parse locally. The root `__init__.py` is for package structure and may be used for CLI tool in the future.

## Naming Convension

The entire project is following the naming convention of Python (specifically [PEP 8](https://peps.python.org/pep-0008/)).