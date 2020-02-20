from unittest.mock import patch

from flask import g
import pytest

from scripts import __version__, server

# see the flask docs for an explanation of creating an example test client:
# https://flask.palletsprojects.com/en/1.1.x/testing/#the-testing-skeleton

# see also the docs on mocking the 'g' context object:
# https://flask.palletsprojects.com/en/1.1.x/testing/#faking-resources


@pytest.fixture
def client():
    # FIXME incomplete
    server.app.config['TESTING'] = True

    with server.app.test_client() as client, server.app.app_context():
            yield client


def test_index(client):
    # check home page
    rv = client.get('/')
    print(rv.data)
    assert 'version %s' % __version__ in rv.data.decode()
    assert b'<form action="/search" method="post">' in rv.data
    assert b'<input type="hidden" name="format" value="html"/>' in rv.data
    assert b'<input type="text" name="incipit"' in rv.data


@patch('scripts.server.SolrClient')
def test_get_solr(mocksolrclient, client):
    assert 'solr' not in g
    # should initialize solr client and store in app context global
    server.get_solr()
    assert 'solr' in g
    mocksolrclient.assert_called_with(server.SOLR_URL, server.SOLR_CORE)

    # if called again, should not re-initialize
    mocksolrclient.reset_mock()
    server.get_solr()
    mocksolrclient.assert_not_called()


