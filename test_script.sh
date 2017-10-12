#!/bin/bash

./capdet_server.py -vv &
./agent.py &

sleep(3)
./cli.py claim-host -i 1 -c 14
./cli.py schedule -i 1 -c 14 -s samples/sample_test.tf
