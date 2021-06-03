#!/usr/bin/env python3

import logging
import os.path
import sys

import boto3
import requests

# configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
LOG = logging.getLogger("disney")

# file to stop checking
STOP_NOTIFICATIONS_FILENAME = 'disabled'

# sns topic to notify
SNS_TOPIC_ARN = 'arn:aws:sns:us-west-2:550697800331:disneylandReservations'

# check the calendar for our desired dates
START_DATE = '2021-12-29'
URL = 'https://disneyland.disney.go.com/availability-calendar/api/calendar?segment=ticket&startDate=2021-12-01&endDate=2021-12-31'


def main():
    # exit if we've already been notified
    if os.path.exists(STOP_NOTIFICATIONS_FILENAME):
        LOG.debug('disabled')
        sys.exit()

    # check the calendar
    resp = requests.get(URL, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    })
    if resp.status_code != 200:
        LOG.exception('Error retrieving calendar')
        sys.exit(1)
    results = resp.json()
    found = any(map(lambda r: r.get('date', '') >= START_DATE, results))

    # exit if desired dates aren't available yet
    if not found:
        LOG.info('no available dates')
        sys.exit()

    try:
        sns = boto3.resource('sns')
        topic = sns.Topic(SNS_TOPIC_ARN)
        topic.publish(
            Subject='Disneyland Reservations - '.format(START_DATE),
            Message='Reservations for Disneyland are now available for {}!'.format(START_DATE),
        )
        LOG.info('notification sent')
        with open(STOP_NOTIFICATIONS_FILENAME, 'w') as fout:
            fout.write('')
        LOG.debug('notifications disabled')
    except Exception:
        LOG.exception('error sending notification')


if __name__ == '__main__':
    main()
