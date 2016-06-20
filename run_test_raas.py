import raas_client

def run_test_raas(binary, platform_name="K64F"):
    print "Running", binary
    print "On", platform_name

    client = raas_client.RaasClient(host="193.208.80.31", port=8007)

    try:
        k64f = client.allocate({"platform_name": [platform_name]})
        print "allocated", k64f.info()

        print "flashing...",
        k64f.flash(binary)
        print "flashed"

        serial_params = raas_client.SerialParameters(lineMode=True, baudrate=9600, bufferSize=256)
        print "opening connection to k64f"
        k64f.openConnection(parameters=serial_params)

        print "resetting...",
        k64f.reset()
        print "reset"

        data = "start"
        print "starting serial capture"
        serial_out = ""
        while(data != ""):
            data = k64f.readline(timeout=15)
            serial_out += data
            print "[DATA]", data.strip()

        k64f.closeConnection()
        k64f.release()
    finally:
        client.disconnect()

    return serial_out

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("binary", help="Path to binary")
    args = parser.parse_args()

    print run_test_raas(args.binary)
