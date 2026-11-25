"""Tests for the shared page layout: offline assets, navigation and sign-out."""
import re

from tests.test_auth import seed_assignment


def test_pages_load_no_assets_from_the_internet(client, auth):
    """The app must be fully styled without internet access (e.g. a demo room)."""
    html = client.get("/login").get_data(as_text=True)
    assert not re.search(r'(href|src)="https?://', html)

    client.get("/language/ar", headers={"Referer": "http://localhost/login"})
    html = client.get("/login").get_data(as_text=True)
    assert 'dir="rtl"' in html
    assert "vendor/fonts/plex-arabic.css" in html
    assert not re.search(r'(href|src)="https?://', html)
    client.get("/language/en", headers={"Referer": "http://localhost/login"})

    auth.login()
    html = client.get("/upload").get_data(as_text=True)
    assert not re.search(r'(href|src)="https?://', html)
    assert "vendor/bootstrap/bootstrap.bundle.min.js" in html


def test_vendored_assets_are_served(client):
    for path in ("vendor/bootstrap/bootstrap.min.css", "vendor/bootstrap/bootstrap.rtl.min.css",
                 "vendor/bootstrap/bootstrap.bundle.min.js", "vendor/fonts/plex-arabic.css",
                 "vendor/fonts/ibm-plex-sans-arabic-arabic-400-normal.woff2"):
        response = client.get("/static/" + path)
        assert response.status_code == 200, path
        response.close()


def test_menu_marks_the_current_page(client, auth):
    auth.login()
    html = client.get("/subjects/").get_data(as_text=True)
    current = re.findall(r'<a class="nav-link active"[^>]*aria-current="page"', html)
    assert len(current) == 1
    assert 'href="/subjects/"' in current[0]


def test_menu_collapses_on_small_screens(client, auth):
    auth.login()
    html = client.get("/upload").get_data(as_text=True)
    assert 'data-bs-target="#main-nav"' in html
    assert 'id="main-nav"' in html


def test_menu_sign_out_never_skips_the_undownloaded_warning(client, app, auth):
    """The menu button must not carry confirm=1, even with results pending."""
    seed_assignment(app)
    auth.login()
    html = client.get("/upload").get_data(as_text=True)
    nav = html.split("</nav>")[0]
    assert 'name="confirm"' not in nav
    assert "Sign out and delete" not in nav


def test_results_page_offers_deliberate_delete_when_results_pending(client, app, auth):
    seed_assignment(app)
    auth.login()
    main = client.get("/results/").get_data(as_text=True).split("</nav>")[1]
    assert 'name="confirm" value="1"' in main
    assert "Sign out and delete" in main


def test_results_page_has_no_delete_button_without_pending_results(client, app, auth):
    seed_assignment(app, status="failed")
    auth.login()
    main = client.get("/results/").get_data(as_text=True).split("</nav>")[1]
    assert "Sign out and delete" not in main
