import mimetypes
import os

import logging
from urllib.parse import urljoin, urlunparse

import re
from urllib.parse import urlparse
from urllib.request import urlopen, Request

xml_header = """<?xml version="1.0" encoding="UTF-8"?>"""

class Crawler():

	debug = False
	output = None
	output_file = None

	ignore_exts = (".docx", ".doc", ".mp4", ".jpg", ".jpeg", ".png", ".gif" ,".pdf")
	link_regex = re.compile(b'<a [^>]*href=[\'|"](.*?)[\'"][^>]*?>')
	image_regex = re.compile (b'<img [^>]*src=[\'|"](.*?)[\'"].*?>')

	response_code = {}
	nb_url = 1 # number of url's.

	domain = ""
	target_domain = ""
	scheme = ""
	tocrawl = set([])
	crawled = set([])

	def __init__(self, output=None, domain="", debug=False, images=False):

		self.output = output
		self.domain = domain
		self.debug = debug
		self.images = images

		if self.debug:
			log_level = logging.DEBUG
		else:
			log_level = logging.ERROR

		logging.basicConfig(level=log_level)

		self.tocrawl = set([self.format_link(domain)])

		try:
			url_parsed = urlparse(domain)
			self.target_domain = url_parsed.netloc
			self.scheme = url_parsed.scheme
		except:
			logging.error("Invalide domain")
			raise ("Invalid domain")

		if self.output:
			try:
				self.output_file = open(self.output, 'w')
			except:
				logging.error ("file not available.")
				exit(255)

	def run(self):
		print(xml_header, file=self.output_file)
		logging.info("Starting the crawling process")
		while len(self.tocrawl) != 0:
			self.__crawling()
		logging.info("Finished crawling all the links")

	def __crawling(self):
		crawler_user_agent = 'Sitemap crawler'
		crawling = self.tocrawl.pop()
		url = urlparse(crawling)
		self.crawled.add(crawling)
		if url.netloc != self.target_domain:
			print ("<url><loc>"+self.htmlspecialchars(url.geturl())+"</loc></url>", file=self.output_file)
		else:
			logging.info("Crawling #{}: {}".format(len(self.crawled), url.geturl()))
			request = Request(crawling, headers={"User-Agent":crawler_user_agent})

			# Ignore ressources listed in the ignore_exts
			# Its avoid dowloading file like pdf… etc
			if not url.path.endswith(self.ignore_exts):
				try:
					response = urlopen(request)
				except Exception as e:
					if hasattr(e,'code'):
						if e.code in self.response_code:
							self.response_code[e.code]+=1
						else:
							self.response_code[e.code]=1

					logging.debug ("{1} ==> {0}".format(e, crawling))
					return self.__continue_crawling()
			else:
				logging.debug("Ignore {0} content might be not parseable.".format(crawling))
				response = None

			# Read the response
			if response is not None:
				try:
					msg = response.read()
					if response.getcode() in self.response_code:
						self.response_code[response.getcode()]+=1
					else:
						self.response_code[response.getcode()]=1

					response.close()

				except Exception as e:
					logging.debug ("{1} ===> {0}".format(e, crawling))
					return None
			else:
				msg = "".encode( )

			image_list = "";
			if self.images:
				# Image search in the current page.
				images = self.image_regex.findall(msg)
				for image_link in list(set(images)):

					image_link = image_link.decode("utf-8", errors="ignore")
					# Ignore link starting with data:
					if image_link.startswith("data:"):
						continue

					# If path start with // get the current url scheme
					if image_link.startswith("//"):
						image_link = url.scheme + ":" + image_link
					# Append domain if not present
					elif not image_link.startswith(("http", "https")):
						if not image_link.startswith("/"):
							image_link = "/{0}".format(image_link)
						image_link = "{0}{1}".format(self.domain.strip("/"), image_link.replace("./", "/"))
					# Ignore other domain images
					image_link_parsed = urlparse(image_link)
					if image_link_parsed.netloc != self.target_domain:
						continue
					image_list = "{0}<image:image><image:loc>{1}</image:loc></image:image>".format(image_list, self.htmlspecialchars(image_link))

			print ("<url><loc>"+self.htmlspecialchars(url.geturl())+"</loc>" + image_list + "</url>", file=self.output_file)
			if self.output_file:
				self.output_file.flush()
			# Found links
			links = self.link_regex.findall(msg)
			for link in links:
				link = link.decode("utf-8", errors="ignore")
				link = self.format_link(link)
				logging.debug("Found : {0}".format(link))

				if link.startswith('/'):
					link = url.scheme + '://' + url[1] + link
				elif link.startswith('#'):
					link = url.scheme + '://' + url[1] + url[2] + link
				elif link.startswith(("mailto", "tel")):
					continue
				elif not link.startswith(('http', "https")):
					link = url.scheme + '://' + url[1] + '/' + link

				# Remove the anchor part if needed
				if "#" in link:
					link = link[:link.index('#')]

				# Parse the url to get domain and file extension
				parsed_link = urlparse(link)
				domain_link = parsed_link.netloc
				target_extension = os.path.splitext(parsed_link.path)[1][1:]

				if link in self.crawled:
					continue
				if link in self.tocrawl:
					continue
				# if domain_link != self.target_domain:
				# 	# print ("<url><loc>"+self.htmlspecialchars(link)+"</loc></url>", file=self.output_file)
				# 	continue
				if parsed_link.path in ["", "/"]:
					continue
				if "javascript" in link:
					continue
				if self.is_image(parsed_link.path):
					continue
				if parsed_link.path.startswith("data:"):
					continue

				# Count one more URL
				self.nb_url+=1
				self.tocrawl.add(link)

		return None

	def format_link(self, link):
		l = urlparse(link)
		l_res = list(l)
		l_res[2] = l_res[2].replace("./", "/")
		l_res[2] = l_res[2].replace("//", "/")
		return urlunparse(l_res)

	def is_image(self, path):
		 mt,me = mimetypes.guess_type(path)
		 return mt is not None and mt.startswith("image/")

	def __continue_crawling(self):
		if self.tocrawl:
			self.__crawling()

	def htmlspecialchars(self, text):
		return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
