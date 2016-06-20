from junit_xml import TestSuite, TestCase

def parse_result(result):
    test_cases = []
    test_id = 0
    tc = None
    if "{{__" in result: # greentea control statemetns
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("{{"):
                line = line.strip("\{\}\r")
                line = line.split(';')
                if line[0] == "__testcase_start":
                    test_name = line[1]
                    if tc != None:
                        failed = 1
                        tc.add_failure_info('failed', tc.stdout)
                        test_cases.append(tc)
                    tc = TestCase(test_id, test_name, stdout='')
                    test_id += 1
                elif line[0] == "__testcase_finish":
                    success = int(line[2])
                    fail = int(line[3])
                    if fail and tc:
                        failed = 1
                        tc.add_failure_info('failed', tc.stdout)
                    test_cases.append(tc)
                    tc = None
                elif line[0] == "__testcase_summary":
                    if tc != None:
                        failed = 1
                        tc.add_failure_info('failed', tc.stdout)
                        test_cases.append(tc)
                    break
            elif tc is not None:
                tc.stdout += line + "\n"
    elif ">>>" in result: # utest control statements
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith(">>>"):
                line = line.strip(">.\r ")
                if "Test cases:" in line:
                    if tc != None:
                        failed = 1
                        tc.add_failure_info('failed', tc.stdout)
                        test_cases.append(tc)
                    break
                elif line.startswith("Running case"):
                    if tc != None:
                        failed = 1
                        tc.add_failure_info('failed', tc.stdout)
                        test_cases.append(tc)
                    test_name = line.split(" ")[-1].strip('\'')
                    tc = TestCase(test_id, test_name, stdout='')
                    test_id += 1
                elif line.endswith("failed"):
                    bits = line.split(' ')
                    success = int(bits[-4])
                    fail = int(bits[-2])
                    if fail and tc:
                        failed = 1
                        tc.add_failure_info('failed', tc.stdout)
                    test_cases.append(tc)
                    tc = None
            elif tc is not None:
                tc.stdout += line + "\n"
    return test_cases

if __name__ == '__main__':
    result = \
    """
    >>> Running 4 test cases...

    >>> Running case #1: 'manifest'...
    >>> 'manifest': 1 passed, 0 failed

    >>> Running case #2: 'test_manifest_fragment'...

    >>> Running case #3: 'test_firware_fragment'...
    >>> 'test_firware_fragment': 1 passed, 0 failed

    >>> Running case #4: 'test_keytable'...
    dummy output
    >>> 'test_keytable': 0 passed, 1 failed

    >>> Test cases: 4 passed, 0 failed

    """
    print TestSuite.to_xml_string([TestSuite("name", parse_result(result))])

    result = \
    """
    {{__testcase_count;4}}
    >>> Running 4 test cases...

    >>> Running case #1: 'simple_get_hash'...
    {{__testcase_start;simple_get_hash}}

    >>> Running case #2: 'simple_get_date'...
    {{__testcase_start;simple_get_date}}
    {{__testcase_finish;simple_get_date;1;0}}
    >>> 'simple_get_date': 1 passed, 0 failed

    >>> Running case #3: 'simple_get_fragment'...
    {{__testcase_start;simple_get_fragment}}
    {{__testcase_finish;simple_get_fragment;1;0}}
    >>> 'simple_get_fragment': 1 passed, 0 failed

    >>> Running case #4: 'Simple_get_file'...
    {{__testcase_start;Simple_get_file}}
    output
    output
    {{__testcase_finish;Simple_get_file;0;1}}
    >>> 'Simple_get_file': 1 passed, 0 failed

    >>> Test cases: 4 passed, 0 failed
    {{__testcase_summary;4;0}}
    {{end;success}}
    {{__exit;0}}

    """
    print TestSuite.to_xml_string([TestSuite("name", parse_result(result))])
