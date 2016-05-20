from junit_xml import TestSuite, TestCase
from collections import OrderedDict
from glob import glob
from os import path
import subprocess
import os

failed = 0

target = subprocess.check_output(["yt", "target"]).split("\n")[0].split(' ')[0]
file_list = glob('build/' + target + '/test/*-test-*')

test_suites = []
print file_list
for fn in file_list:
    if path.isfile(fn):
        try:
            result = subprocess.check_output([fn], stderr=subprocess.STDOUT)
        except Exception, e:
            failed = 1
            result = str(e.output)
        print result

        test_cases = []
        test_id = 0
        tc = None
        for line in result.split("\n"):
            # print line
            if line.startswith("{{"):
                line = line.strip("\{\}")
                line = line.split(';')
                if line[0] == "__testcase_start":
                    test_name = line[1]
                    tc = TestCase(test_id, test_name, stdout='')
                    test_id += 1
                elif line[0] == "__testcase_finish":
                    success = int(line[2])
                    fail = int(line[3])
                    if fail:
                        tc.add_failure_info('failed', tc.stdout)
                    test_cases.append(tc)
                    tc = None
                elif line[0] == "__testcase_summary":
                    break
            elif tc is not None:
                tc.stdout += line + "\n"

        ts = TestSuite(path.basename(fn), test_cases)
        test_suites.append(ts)

module_name = path.basename(file_list[0]).split('-test-')[0]
try:
    reports_dir = os.environ['CIRCLE_TEST_REPORTS']
except KeyError:
    reports_dir = ''

if reports_dir != '' and not os.path.exists(reports_dir):
    os.makedirs(reports_dir)
report_fn = path.join(reports_dir, module_name+'_test_result_junit.xml')

with open(report_fn, "w") as fd:
    TestSuite.to_file(fd, test_suites)

if failed:
    exit(1)