FROM python:3.6.1-alpine
WORKDIR /home/sitemap-gen/
COPY main.py crawler.py /home/sitemap-gen/
ENTRYPOINT [ "python", "main.py" ]
