from cloudstackAPI import *
import unittest
import cloudstackTestClient
class cloudstackTestCase(unittest.case.TestCase):
    def __init__(self, args):
        unittest.case.TestCase.__init__(self, args)
        self.testClient = cloudstackTestClient.cloudstackTestClient()
