import datetime
from django.core.management.base import  BaseCommand

from .scrap import IndeedScrapper


class Command(BaseCommand):
    def handle(self, *args, **options):

        # todo add command line argument for keyword

        print("Starting scraping jobs", datetime.datetime.now())

        IndeedScrapper().scrap_jobs()

        print("Finished scrapping jobs", datetime.datetime.now())
