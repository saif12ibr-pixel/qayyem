"""The Arabic interface: complete, placeholder-safe, right-to-left."""
import ast
import pathlib
import re

import pytest
from jinja2 import Environment, nodes

from qayyem.grading.factory import SELECTABLE_PROVIDERS
from qayyem.i18n import COOKIE
from qayyem.translations_ar import AR

SOURCE = pathlib.Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"%\((\w+)\)s")


def interface_strings():
    """Every literal passed to _() in the templates and the Python code."""
    found = set()
    env = Environment()
    for path in (SOURCE / "templates").glob("*.html"):
        tree = env.parse(path.read_text(encoding="utf-8"))
        for call in tree.find_all(nodes.Call):
            if (isinstance(call.node, nodes.Name) and call.node.name == "_"
                    and call.args and isinstance(call.args[0], nodes.Const)):
                found.add(call.args[0].value)
    for path in list((SOURCE / "qayyem").rglob("*.py")) + [SOURCE / "app.py"]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for call in ast.walk(tree):
            if (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == "_" and call.args
                    and isinstance(call.args[0], ast.Constant)):
                found.add(call.args[0].value)
    # Shown through the |translate filter rather than _().
    for provider in SELECTABLE_PROVIDERS:
        found.update((provider["note"], provider["warning"]))
    return found


def test_every_interface_string_has_an_arabic_translation():
    missing = sorted(s for s in interface_strings() if s not in AR)
    assert not missing, "No Arabic for:\n" + "\n".join(missing)


@pytest.mark.parametrize("english", sorted(AR))
def test_translation_keeps_every_placeholder(english):
    assert sorted(PLACEHOLDER.findall(english)) == sorted(PLACEHOLDER.findall(AR[english]))


def test_english_is_the_default(client):
    page = client.get("/login")
    assert b'lang="en" dir="ltr"' in page.data
    assert b"Instructor sign in" in page.data


def test_switching_to_arabic_renders_right_to_left(client):
    response = client.get("/language/ar", headers={"Referer": "http://localhost/login"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    page = client.get("/login")
    html = page.data.decode("utf-8")
    assert 'lang="ar" dir="rtl"' in html
    assert "bootstrap.rtl.min.css" in html
    assert AR["Instructor sign in"] in html
    assert ">English<" in html  # the way back is named in its own language


def test_arabic_flash_messages(client, auth):
    client.set_cookie(COOKIE, "ar")
    response = auth.login(password="wrong-password")
    assert AR["Incorrect email or password."] in response.data.decode("utf-8")


def test_arabic_upload_error(client, auth):
    import io

    auth.login()
    client.set_cookie(COOKIE, "ar")
    response = client.post(
        "/upload",
        data={"file": (io.BytesIO(b"x"), "notes.doc"), "ideal_answer": "x",
              "max_score": "10"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "تُدعم ملفات" in response.data.decode("utf-8")


def test_language_switch_will_not_redirect_off_site(client):
    response = client.get("/language/ar", headers={"Referer": "https://evil.example/x"})
    assert "evil.example" not in response.headers["Location"]


def test_unknown_language_is_ignored(client):
    response = client.get("/language/xx")
    assert COOKIE not in response.headers.get("Set-Cookie", "")
