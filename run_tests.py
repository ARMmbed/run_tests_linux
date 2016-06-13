from junit_xml import TestSuite, TestCase
from collections import OrderedDict
from glob import glob
from os import path
import subprocess
import os
import argparse
import json

failed = 0

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--target",
    type=str, default="LINUX", help="The target platform")
args = parser.parse_args()

if args.target != "LINUX":
    from run_test_raas import run_test_raas

file_list = []
if args.target == "LINUX":
    target = subprocess.check_output(["yt", "target"]).split("\n")[0].split(' ')[0]
    file_list = glob('build/' + target + '/test/*-test-*')
elif args.target == "K64F":

    test_spec_fn = "test_spec.json"
    if not path.isfile(test_spec_fn):
        test_spec_fn = path.join(".build", "tests", "K64F", "GCC_ARM", "test_spec.json")

    with open(test_spec_fn, "r") as fd:
        parsed_json = json.load(fd)
        for _, test_bins in parsed_json["builds"]["K64F-GCC_ARM"]["tests"].iteritems():
            for test_bin in test_bins["binaries"]:
                test_bin_path = test_bin['path']
                if "/mbed-os/" not in test_bin_path:
                    file_list.append(test_bin_path)
else:
    print "Unsupported target", args.target
    exit(1)

test_suites = []
print file_list
for fn in file_list:
    if path.isfile(fn):
        if args.target == "LINUX":
            try:
                result = subprocess.check_output([fn], stderr=subprocess.STDOUT)
            except Exception, e:
                failed = 1
                result = str(e.output)
            print result
        elif args.target == "K64F":
            result = run_test_raas(fn, args.target)

        test_cases = []
        test_id = 0
        tc = None
        for line in result.split("\n"):
            # print line
            if line.startswith("{{"):
                line = line.strip("\{\}\r")
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

if args.target == "LINUX":
    module_name = path.basename(file_list[0]).split('-test-')[0]
elif args.target == "K64F":
    module_name = path.basename(file_list[0]).split('-TESTS-')[0]

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