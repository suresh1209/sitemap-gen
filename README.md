# Web-Crawler for sitemap generation

Script to create sitemap.xml of public links in the domain

## usage

	>>> python3 main.py --config config/config.json

***configure config/config.json to change the domain, enable/disable debug mode, enable/disable images parsing, set the path of output file***

## Docker usage

#### Building the Docker image:

  ```
  $ docker build -t sitemap-gen:latest .
  ```

#### Run with config file :

  ```
  $ docker run -it -v `pwd`:/home/sitemap-gen/ sitemap-gen --config config/config.json
  ```
