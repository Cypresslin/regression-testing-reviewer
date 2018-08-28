from bs4 import BeautifulSoup
from urllib import request

def soup_generator(link):
    '''Function to turn target link into BeautifulSoup lxml'''
    page = request.urlopen(link).read()
    return BeautifulSoup(page, "lxml")


