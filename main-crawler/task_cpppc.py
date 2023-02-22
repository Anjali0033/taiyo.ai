from requests import Session
from lxml import html
import re
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import pandas_profiling
import pandas as pd


class CPPPCScraper:
    def __init__(self):
        self.session = Session()
        self.common_file_date = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        self.file = open(
            f"cpppc_{self.common_file_date}.csv",
            mode="w",
            newline="",
            encoding="utf-8",
        )
        self.row = csv.writer(self.file)
        self.row.writerow([
            "Rundatetime",
            "SiteAccessDate",
            "ArticleType",
            "ArticleName",
            "PostDate",
            "Editor",
            "View",
            "ArticleFrom",
            "ArticleDesc",
            "ArticleUrl",
            "ArticleImageUrl",
        ])
        self.matplot = {
            "PostYear": [],
            "ArticleView": [],
        }

    def create_profile_report(self):
        df = pd.read_csv(self.file.name, encoding='utf-8')
        profile = pandas_profiling.ProfileReport(df)
        profile.to_file(f"cpppc_report_{self.common_file_date}.html")

    def create_matplotlib(self):
        plt.plot(self.matplot['PostYear'], self.matplot['ArticleView'])

        # Add labels and title
        plt.xlabel('PostYear')
        plt.ylabel('ArticleView')
        plt.title('ArticleView over the PostYear')

        # Save the plot
        plt.savefig(f"article_views_{self.common_file_date}.png")

    def get_detail_page_info(self, url):
        tree = html.fromstring(self.session.get(url).text)

        def get_by_xpath(path): return ''.join(tree.xpath(path))

        editors_view = get_by_xpath('//div[@class="common-card detail-card"]//h1/following-sibling::p[contains(.,"EDITER")]/text()')
        article_type = get_by_xpath('//div[@class="component-menu-item component-menu-item-active"]/a/text()')
        article_date = get_by_xpath('//div[@class="common-card detail-card"]//h1/following-sibling::p[1]/text()')
        article_from = get_by_xpath(
            '//div[@class="common-card detail-card"]//h1/following-sibling::p[contains(.,"FROM")]/text()'
        ).split('：')[-1].strip()

        try:
            article_editor = (re.search(r'EDITOR：(.+?)\s', editors_view)).group(1)
        except:
            article_editor = 'N/A'

        try:
            article_view = (re.search(r'VIEW：(\d+)', editors_view)).group(1)
        except:
            article_view = 'N/A'

        return article_type, article_date, article_editor, article_view, article_from

    def scrape_list_page(self, url):
        tree = html.fromstring(self.session.get(url).text)

        for article in (tree.xpath('//ul[@class="new-content ppp-list"]//li')):

            def get_by_xpath(path): return ''.join(article.xpath(path))

            # list page data
            rundatetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            site_access_date = get_by_xpath('//div[@id="headerDate"]/text()')
            article_name = get_by_xpath('.//a[@class="content-title"]/text()')
            article_desc = get_by_xpath('.//div[@class="content-content"]/text()')
            article_url = 'https://www.cpppc.org{}'.format(get_by_xpath('.//a[@class="content-title"]/@href'))
            article_img = 'https://www.cpppc.org{}'.format(get_by_xpath('.//img//@src'))\

            # fetching detail page data
            article_type, article_date, article_editor, article_view, article_from = self.get_detail_page_info(article_url)

            # visualisation columns for graph
            self.matplot["PostYear"].append(article_date.split('-')[-1][:-1])
            self.matplot["ArticleView"].append(article_view)

            # write to csv handler
            self.row.writerow([
                rundatetime,
                site_access_date,
                article_type,
                article_name,
                article_date,
                article_editor,
                article_view,
                article_from,
                article_desc,
                article_url,
                article_img
            ])

        self.file.close()
        self.create_matplotlib()
        self.create_profile_report()


if __name__ == '__main__':
    scraper = CPPPCScraper()
    scraper.scrape_list_page('https://www.cpppc.org/en/PPPyd.jhtml')
