# Seasonal Recipe Finder

## About

This repository contains a GUI application for storing, managing and searching
recipes. The ingredients can be enriched with information about season and
origin so that recipes are filtered according to current seasonal conditions.

## Getting Started

Follow these instructions to get a copy of the project running in a virtual
environment on your local machine.

### Prerequisites

The application is written in Python. It is highly recommended using a virtual
environment (e.g. [virtualenv](https://docs.python.org/3/tutorial/venv.html))
to install additional packages while keeping them separated from your other
Python projects.

### Installation

To get started, clone this repository, set up a virtual environment (at
least Python 3.10) and install the dependencies by running `pip install -r
requirements.txt` from the root directory of this project.

## Usage

The application is launched via `python src/main.py`. Do not forget to activate
your virtual environment before.

In the main window, all available recipes can be filtered by name and
ingredients. The results will be sorted in descending order based on a
sustainability score that depends on season and origin of their ingredients.
On the right side, the preparation of the currently selected recipe is shown.
The quantities of the ingredients are automatically adapted to the desired
number of portions.

The control panel can be used to add new recipes and edit or delete existing
ones. In the underlying recipe window, ingredients can be managed in the same
way. Note that the ingredient names must be unique and each recipe must feature
at least two different ingredients.

## License

This project is published under the [Apache License 2.0](LICENSE.txt).
