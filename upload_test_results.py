from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.attributes import NumberAttribute
from pynamodb.attributes import UTCDateTimeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
import sys
import os
import xml.etree.ElementTree as ET
import subprocess
import json
from bs4 import BeautifulSoup
import datetime
from glob import glob
from os import path

class WhenIndex(GlobalSecondaryIndex):

    class Meta:
        index_name = 'when-index'
        read_capacity_units = 2
        write_capacity_units = 1
        # All attributes are projected
        projection = AllProjection()

    when = UnicodeAttribute(hash_key=True)

class Build(Model):
    class Meta:
        table_name = 'BuildsTest'
        region = 'us-west-2'
        read_capacity_units = 1
        write_capacity_units = 1

    key = UnicodeAttribute(hash_key=True)
    branch = UnicodeAttribute()
    build = NumberAttribute()
    project = UnicodeAttribute()
    errors =  NumberAttribute()
    failures =  NumberAttribute()
    skip =  NumberAttribute()
    tests =  NumberAttribute()
    coverage_coverage = NumberAttribute()
    coverage_excluded = NumberAttribute()
    coverage_missing = NumberAttribute()
    coverage_statements = NumberAttribute()
    sub_module = UnicodeAttribute(null=True)
    when = UTCDateTimeAttribute(default=datetime.datetime.now())
    when_index = WhenIndex()

def get_test_details(filename,build):
    dom = ET.parse(open(filename, "r"))
    testsuiteNode = dom.getroot()
    build.tests = int(testsuiteNode.get('tests'))
    build.errors = int(testsuiteNode.get('errors'))
    build.failures = int(testsuiteNode.get('failures'))
    build.skip = 0

def add_details(build):
    build.branch = str(os.getenv("CIRCLE_BRANCH", ''))
    build.build = int(os.getenv("CIRCLE_BUILD_NUM", '0'))
    build.project = str(os.getenv("CIRCLE_PROJECT_REPONAME", ''))

    key = "%s-%d-%s" % ( build.branch, build.build ,build.project)
    if build.sub_module is not None:
        key = key+"-%s" % build.sub_module

    build.key = key

def add_coverate_details(build,coverage_file, module_name):
    print coverage_file
    with open(coverage_file, "r") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content)

    for coverFile in soup.findAll("td", {"class":"coverFile"}):
        if path.join(module_name,"source") in str(coverFile):
            coverBar = coverFile.findNext('td')
            coverBarOutline = coverBar.findNext('td')
            coverVal = coverBarOutline.findNext('td')
            coverLine = coverVal.findNext('td')

            percentage_coverage = float(coverVal.text.encode('utf-8').strip("\xc2\xa0%"))
            lines_covered, total_lines = [int(x) for x in coverLine.text.split("/")]
            break

    build.coverage_statements = total_lines
    build.coverage_missing = total_lines - lines_covered
    build.coverage_excluded = 0
    build.coverage_coverage = int(percentage_coverage)

if __name__ == "__main__":
    if not Build.exists():
        Build.create_table(wait=True)

    target = subprocess.check_output(["yt", "target"]).split("\n")[0].split(' ')[0]
    file_list = glob('build/' + target + '/test/*-test-*')
    module_name = path.basename(file_list[0]).split('-test-')[0]

    build = Build()
    build.sub_module = module_name

    reports_dir = os.getenv('CIRCLE_TEST_REPORTS', '')

    if reports_dir != '' and not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    report_fn = path.join(reports_dir, module_name+'_test_result_junit.xml')

    artifacts_dir = os.getenv('CIRCLE_ARTIFACTS', '')

    get_test_details(report_fn, build)
    add_details(build)
    add_coverate_details(build, os.path.join(artifacts_dir, 'html','index.html'), module_name)

    build.save()
