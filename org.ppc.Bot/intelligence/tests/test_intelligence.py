
from botengine_pytest import BotEnginePyTest

from organization.organization import Organization
import utilities.utilities as utilities
from intelligence.intelligence import *

import unittest
from unittest.mock import MagicMock, patch

class TestIntelligence(unittest.TestCase):

    def test_intelligence_constructor(self):
        # Initial setup
        botengine = BotEnginePyTest({})
        organization_object = Organization(botengine, 0)

        mut = Intelligence(botengine, organization_object)
        
        assert mut is not None
        assert mut.intelligence_id is not None
        assert mut.parent == organization_object
    