<h1>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://imagedelivery.net/Dr98IMl5gQ9tPkFM5JRcng/c693ab7a-14a9-4ac0-ed42-ae783dbc3700/HD">
  <img alt="Logo" width="170" src="https://imagedelivery.net/Dr98IMl5gQ9tPkFM5JRcng/10c71d08-c9a5-4fc1-c71f-d9566fbb3e00/HD">
</picture>
</h1>

**Main Code Repository**

[Go to documentation →](https://twiki.lingxi.li)

## Objective

The objective of this project is to analyze and utilize the Wikipedia edit histories for future use in the natural language processing (NLP) field. Wikipedia has been built for a long time and nearly all long documents are built throughout a complicated editing histories. We believe that these informations could be helpful to optimize the NLP model for generating long documents. The main challenge of this project is how can we handle large size of Wikipedia's edit history which is larger than 5TB. Specifically, we are planing to use distributional processing systems such as Hadoop or Spark to make a parser. In addition, we are going to explore a way to efficiently construct a corpus to train machine learning models'.

## File Structure

We are using Poetry to manage the dependencies. Each folder should be treated as a module except sample and output. You can check out Poetry's documentation [here](https://python-poetry.org/docs/) to learn more about how to use it.

### Existing Modules

- `ergodiff`
- `grimm`
- `twikidata`

## Code Formatting

We are using 4 spaces indentation and 120 characters per line. No linting is involved or required for now.

## Naming Convension

The entire project is following the naming convention of Python (specifically [PEP 8](https://peps.python.org/pep-0008/)).