import re
import pytest
from main import findDefinition


class TestCsp:
    def test_simple(self):
        data = (
            ('AMA', 'American Medical Association', 'The AMA, the American Medical Association is an organization.'),
            ('RAM', 'Random Access Memory', 'Random Access Memory, or RAM (pronounced as ramm), is the physical hardware'),
            ('NASA', 'National Aeronautics and Space Administration', 'The National Aeronautics and Space Administration (NASA) is an independent agency of the executive branch'),
            ('ROS', 'Robot Operating System', 'ROS (Robot Operating System) provides libraries and tools to help software developers create robot applications.'),
            ('HPI', 'History of present illness', 'complaint. History of present illness (HPI): the chronological order of '),
        )
        for acronym, desc, text  in data:
            text = re.split(r'\W+', text)
            index = text.index(acronym)
            found = findDefinition(acronym, text, index)
            if found != desc:
                assert False, "Acronym full form not as expected {}: {}".format(desc, found)