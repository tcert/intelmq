# -*- coding: utf-8 -*-

import unittest
import mock

import intelmq.lib.bot
import intelmq.lib.bot as bot
import intelmq.lib.test as test
import intelmq.lib.utils as utils
from intelmq.lib.message import Event

RAW = """# ignore this
2015/06/04 13:37 +00,example.org,192.0.2.3,reverse.example.net,example description,report@example.org,0

2015/06/04_13:37 +00,example.org,192.0.2.3,reverse.example.net,example description,report@example.org,0
#ending line"""


EXAMPLE_REPORT = {"feed.url": "http://www.example.com/",
                  "time.observation": "2015-08-11T13:03:40+00:00",
                  "raw": utils.base64_encode(RAW),
                  "__type": "Report",
                  "feed.name": "Example"}
EXAMPLE_EVENT = {"feed.url": "http://www.example.com/",
                 "source.ip": "192.0.2.3",
                 "time.source": "2015-06-04T13:37:00+00:00",
                 "source.reverse_dns": "reverse.example.net",
                 "source.fqdn": "example.org",
                 "source.account": "report@example.org",
                 "time.observation": "2015-08-11T13:03:40+00:00",
                 "__type": "Event",
                 "classification.type": "malware",
                 "event_description.text": "example description",
                 "source.asn": 0,
                 "feed.name": "Example"}

EXPECTED_DUMP = '''# ignore this
2015/06/04_13:37 +00,example.org,192.0.2.3,reverse.example.net,example description,report@example.org,0
#ending line'''
EXAMPLE_EMPTY_REPORT = {"feed.url": "http://www.example.com/",
                        "__type": "Report",
                        "feed.name": "Example"}


class DummyParserBot(bot.ParserBot):
    """
    A dummy bot only for testing purpose.
    """

    def parse_line(self, line, report):
        if line.startswith('#'):
            self.logger.info('Lorem ipsum dolor sit amet.')
            self.tempdata.append(line)
        else:
            event = Event(report)
            line = line.split(',')
            event['time.source'] = line[0]
            event['source.fqdn'] = line[1]
            event['source.ip'] = line[2]
            event['source.reverse_dns'] = line[3]
            event['event_description.text'] = line[4]
            event['source.account'] = line[5]
            event['source.asn'] = line[6]
            event['classification.type'] = 'malware'
            yield event

    def recover_line(self, line):
        return '\n'.join([self.tempdata[0], line, self.tempdata[1]])


class TestDummyParserBot(test.BotTestCase, unittest.TestCase):
    """
    A TestCase for a DummyBot.
    """

    @classmethod
    def set_bot(cls):
        cls.bot_reference = DummyParserBot
        cls.default_input_message = EXAMPLE_REPORT
        cls.allowed_error_count = 1

    def dump_message(self, error_traceback, message=None):
        self.assertEqual(EXPECTED_DUMP, message)

    def run_bot(self):
        with mock.patch.object(intelmq.lib.bot.Bot, "_dump_message",
                               self.dump_message):
            super(TestDummyParserBot, self).run_bot()

    def test_log_test_line(self):
        """ Test if bot does log example message. """
        self.run_bot()
        self.assertRegexpMatchesLog("INFO - Lorem ipsum dolor sit amet.")

    def test_event(self):
        """ Test if correct Event has been produced. """
        self.run_bot()
        self.assertMessageEqual(0, EXAMPLE_EVENT)

    def test_missing_raw(self):
        """ Test if correct Event has been produced. """
        self.input_message = EXAMPLE_EMPTY_REPORT
        self.run_bot()
        self.assertAnyLoglineEqual(message='Report without raw field received. Possible '
                                           'bug or misconfiguration in previous bots.',
                                   levelname='WARNING')


if __name__ == '__main__':
    unittest.main()
