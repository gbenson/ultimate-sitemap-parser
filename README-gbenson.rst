Clone the repo::

  git clone https://github.com/gbenson/ultimate-sitemap-parser.git
  cd ultimate-sitemap-parser

Create a virtual environment::

  python3 -m venv venv
  . venv/bin/activate

Upgrade pip and setuptools::

  pip install --upgrade pip setuptools

Install in editable mode::

  pip install -e .[test]

Test it::

  pytest

Flex it::

  flex 'http://customer.com#@evil.com'
