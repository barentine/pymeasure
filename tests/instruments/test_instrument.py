#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2021 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import pytest
from time import time
from pymeasure.adapters import FakeAdapter
from pymeasure.instruments.instrument import Instrument, FakeInstrument
from pymeasure.instruments.validators import strict_discrete_set, strict_range


def test_fake_instrument():
    fake = FakeInstrument()
    fake.write("Testing")
    assert fake.read() == "Testing"
    assert fake.read() == ""
    assert fake.values("5") == [5]


def test_control_doc():
    doc = """ X property """

    class Fake(Instrument):
        x = Instrument.control(
            "", "%d", doc
        )

    assert Fake.x.__doc__ == doc


def test_control_validator():
    class Fake(FakeInstrument):
        x = Instrument.control(
            "", "%d", "",
            validator=strict_discrete_set,
            values=range(10),
        )

    fake = Fake()
    fake.x = 5
    assert fake.read() == '5'
    fake.x = 5
    assert fake.x == 5
    with pytest.raises(ValueError) as e_info:
        fake.x = 20


def test_control_validator_map():
    class Fake(FakeInstrument):
        x = Instrument.control(
            "", "%d", "",
            validator=strict_discrete_set,
            values=[4, 5, 6, 7],
            map_values=True,
        )

    fake = Fake()
    fake.x = 5
    assert fake.read() == '1'
    fake.x = 5
    assert fake.x == 5
    with pytest.raises(ValueError) as e_info:
        fake.x = 20


def test_control_dict_map():
    class Fake(FakeInstrument):
        x = Instrument.control(
            "", "%d", "",
            validator=strict_discrete_set,
            values={5: 1, 10: 2, 20: 3},
            map_values=True,
        )

    fake = Fake()
    fake.x = 5
    assert fake.read() == '1'
    fake.x = 5
    assert fake.x == 5
    fake.x = 20
    assert fake.read() == '3'


def test_control_dict_str_map():
    class Fake(FakeInstrument):
        x = Instrument.control(
            "", "%d", "",
            validator=strict_discrete_set,
            values={'X': 1, 'Y': 2, 'Z': 3},
            map_values=True,
        )

    fake = Fake()
    fake.x = 'X'
    assert fake.read() == '1'
    fake.x = 'Y'
    assert fake.x == 'Y'
    fake.x = 'Z'
    assert fake.read() == '3'


def test_control_process():
    class Fake(FakeInstrument):
        x = Instrument.control(
            "", "%d", "",
            validator=strict_range,
            values=[5e-3, 120e-3],
            get_process=lambda v: v * 1e-3,
            set_process=lambda v: v * 1e3,
        )

    fake = Fake()
    fake.x = 10e-3
    assert fake.read() == '10'
    fake.x = 30e-3
    assert fake.x == 30e-3


def test_control_get_process():
    class Fake(FakeInstrument):
        x = Instrument.control(
            "", "JUNK%d", "",
            validator=strict_range,
            values=[0, 10],
            get_process=lambda v: int(v.replace('JUNK', '')),
        )

    fake = Fake()
    fake.x = 5
    assert fake.read() == 'JUNK5'
    fake.x = 5
    assert fake.x == 5


def test_control_preprocess_reply_property():
    # test setting preprocess_reply at property-level
    class Fake(FakeInstrument):
        x = Instrument.control(
            "", "JUNK%d",
            "",
            preprocess_reply=lambda v: v.replace('JUNK', ''),
            cast=int
        )

    fake = Fake()
    fake.x = 5
    assert fake.read() == 'JUNK5'
    # notice that read returns the full reply since preprocess_reply is only
    # called inside Adapter.values()
    fake.x = 5
    assert fake.x == 5
    fake.x = 5
    assert type(fake.x) == int


def test_control_preprocess_reply_adapter():
    # test setting preprocess_reply at Adapter-level
    class Fake(FakeInstrument):
        def __init__(self):
            super().__init__(preprocess_reply=lambda v: v.replace('JUNK', ''))

        x = Instrument.control(
            "", "JUNK%d", "",
            cast=int
        )

    fake = Fake()
    fake.x = 5
    assert fake.read() == 'JUNK5'
    # notice that read returns the full reply since preprocess_reply is only
    # called inside Adapter.values()
    fake.x = 5
    assert fake.x == 5


def test_measurement_dict_str_map():
    class Fake(FakeInstrument):
        x = Instrument.measurement(
            "", "",
            values={'X': 1, 'Y': 2, 'Z': 3},
            map_values=True,
        )

    fake = Fake()
    fake.write('1')
    assert fake.x == 'X'
    fake.write('2')
    assert fake.x == 'Y'
    fake.write('3')
    assert fake.x == 'Z'


def test_setting_process():
    class Fake(FakeInstrument):
        x = Instrument.setting(
            "OUT %d", "",
            set_process=lambda v: int(bool(v)),
        )

    fake = Fake()
    fake.x = False
    assert fake.read() == 'OUT 0'
    fake.x = 2
    assert fake.read() == 'OUT 1'


def test_control_multivalue():
    class Fake(FakeInstrument):
        x = Instrument.control(
            "", "%d,%d", "",
        )

    fake = Fake()
    fake.x = (5, 6)
    assert fake.read() == '5,6'


@pytest.mark.parametrize(
    'set_command, given, expected',
    [("%d", 5, 5),
     ("%d, %d", (5, 6), [5, 6]),  # input has to be a tuple, not a list
     ])
def test_fakeinstrument_control(set_command, given, expected):
    """FakeInstrument's custom simple control needs to process values correctly.
    """
    class Fake(FakeInstrument):
        x = FakeInstrument.control(
            "", set_command, "",
        )

    fake = Fake()
    fake.x = given
    assert fake.x == expected


def test_with_statement():
    """ Test the with-statement-behaviour of the instruments. """
    with FakeInstrument() as fake:
        # Check if fake is an instance of FakeInstrument
        assert isinstance(fake, FakeInstrument)

        # Check whether the shutdown function is already called
        assert fake.isShutdown == False

    # Check whether the shutdown function is called upon
    assert fake.isShutdown == True


def test_write_delay():
    """ Test whether all instrument writes correctly observe
    the write-delay"""
    delay = 0.2
    fake = FakeInstrument(write_delay=delay)

    # Patch the Adapter of the FakeInstrument to the binary_values method
    fake.adapter.binary_values = lambda c, h, d: c

    fake.write("command")
    t0 = time()

    fake.write("command")
    t1 = time()
    assert t1 - t0 >= delay

    fake.ask("command")
    t2 = time()
    assert t2 - t1 >= delay

    fake.values("command")
    t3 = time()
    assert t3 - t2 >= delay

    fake.binary_values("command")
    t4 = time()
    assert t4 - t3 >= delay
