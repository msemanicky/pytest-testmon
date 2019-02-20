import os
import pytest
import sqlite3


@pytest.fixture
def lib_py(testdir):
    return testdir.makepyfile(lib="""
        def multiply():
            return 2 * 4 / 0

        def call_multiply():
            multiply()
    """)


@pytest.fixture
def a_py(testdir):
    return testdir.makepyfile(test_a="""
        import lib

        def test_a():
            lib.call_multiply();
    """)


@pytest.fixture
def b_py(testdir):
    return testdir.makepyfile(test_b="""
        def test_b():
            assert False

        def test_pass():
            assert True
    """)


def test_plugin(testdir, lib_py, a_py, b_py):

    test_result = testdir.runpytest()
    # test if failed
    test_result.assert_outcomes(failed=2, passed=1)
    # test if result file was modified

    c = sqlite3.connect('.runtime_info').cursor()

    a_file = os.path.join(str(testdir.tmpdir), "test_a.py")
    b_file = os.path.join(str(testdir.tmpdir), "test_b.py")
    lib_file = os.path.join(str(testdir.tmpdir), "lib.py")

    # Exception Table
    c.execute("SELECT * FROM Exception")
    result = c.fetchall()

    # test the number of exceptions
    assert len(result) == 2

    # test the exception paths
    assert len([x for x in result if x[2] == lib_file]) == 1
    assert len([x for x in result if x[2] == b_file]) == 1

    # FileMark Table
    c.execute("SELECT * FROM FileMark")
    result = c.fetchall()

    # test the number of marks for each file
    assert len([x for x in result if x[3] == lib_file]) == 7
    assert len([x for x in result if x[3] == b_file]) == 2
    assert len([x for x in result if x[3] == a_file]) == 3

    # test the number of GutterLinks for file lib_file
    gutterMarks = [x for x in result if x[3] == lib_file and x[1] == "GutterLink"]
    assert len(gutterMarks) == 3

    # test the target paths for the gutterMarks above
    assert len([x for x in gutterMarks if x[9] == lib_file]) == 2
    assert len([x for x in gutterMarks if x[9] == a_file]) == 1

def test_remove(testdir):
    testdir.makepyfile(test_a="""
        def test_1():
            assert False
    """)

    testdir.runpytest()

    conn = sqlite3.connect('.runtime_info')
    c = conn.cursor()
    c.execute("SELECT count(*) as count FROM FileMark")
    result = c.fetchone()[0]
    assert result == 2

    testdir.makepyfile(test_a="""
        def test_1():
            assert True
    """)

    testdir.runpytest()

    c = conn.cursor()
    c.execute("SELECT count(*) as count FROM FileMark")
    result = c.fetchone()[0]
    assert result == 0



