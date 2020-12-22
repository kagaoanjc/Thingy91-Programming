#!/usr/bin/env python3
#
# Copyright (c) 2019 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-BSD-5-Clause-Nordic

import os
import os.path
import time
import argparse
import subprocess
import logging

from os import path
from tempfile import TemporaryDirectory, mkstemp
from pynrfjprog import HighLevel

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('modem_update')

def flash_modem_pkg(modem_zip, verify):
    start = time.time()
    with HighLevel.API(True) as api:
        snr = api.get_connected_probes()

        if len(snr) <= 0:
            print("Unable to detect connected JLink debugger")
            api.close()
            sys.exit(2)

        for s in snr:
            log.info("Establish board connection")
            log.info(f"Flashing '{modem_zip}' to board {s}")
            with HighLevel.IPCDFUProbe(api, s, HighLevel.CoProcessor.CP_MODEM) as probe:
                log.info(f"Programming '{modem_zip}'")
                probe.program(modem_zip)
                log.info("Programming complete")
                if verify:
                    log.info("Verifying")
                    probe.verify(modem_zip)
                    log.info("Verifying complete")
        api.close()
        log.info(f"Completed in {time.time() - start} seconds")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--firmware", help="path to modem firmware zip file", action="store", dest="firmware_path",  required=True)
    results = parser.parse_args()

    if not path.exists(results.firmware_path):
        print("Unable to find modem firmware at: " + results.firmware_path)
        sys.exit(1)

    log.info("Modem firmware upgrade")
    flash_modem_pkg(results.firmware_path, True)

if __name__ == '__main__':
    main()