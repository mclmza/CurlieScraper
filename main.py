import time
import argparse
from bs4 import BeautifulSoup, NavigableString
from urllib3.util import Retry
from requests import Request, Session
from requests.adapters import HTTPAdapter
from stem import Signal
from stem.control import Controller
from multiprocessing.pool import Pool

CURLIE = 'https://curlie.org'
boosted = False

# Crea un nuovo oggetto Session, se in boosted setta i proxy TOR
def new_session():
    session = Session()
    if boosted:
        session.proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                                      'image/webp,image/apng,*/*;q=0.8',
                            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8', 'Upgrade-Insecure-Requests': '1',
                            'Connection': 'keep-alive'})
    retries = Retry(total=60, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# Manda un segnale al Controller finchè
def renew_connection(old_ip=''):
    while True:
        with Controller.from_port(port = 9051) as controller:
            controller.authenticate(password="password")
            controller.signal(Signal.NEWNYM)

        session = new_session()
        new_ip = session.get('https://api.ipify.org').text
        if new_ip != old_ip or old_ip == '':
            return session, new_ip

# Richiede una pagina e controlla se viene restituita correttamente
def get_page(url, session):
    retries = 120
    req = Request('GET', url)
    prepared_req = session.prepare_request(req)
    resp = session.send(prepared_req, timeout=12)
    if resp.text == '':
        while retries > 0:
            if boosted:
                session, old_ip = renew_connection()
            else:
                time.sleep(1)
            resp = session.send(prepared_req, timeout=12)
            if resp.text == '':
                retries -= 1
            else:
                return resp
        print('There has been a shadow ban from Curlie.org, change your IP or wait a couple of hours')
        exit(-1)
    else:
        return resp

# Raccoglie tutti le categorie in una pagina e si richiama per ognuna di esse
def get_nodes(link, session):
    resp = get_page(CURLIE + link, session)
    soup = BeautifulSoup(resp.text, 'html.parser')
    nodes = soup.select('#cat-list-content-main > .cat-item > a')
    if soup.select_one('.alphanumeric > .current') is None:
        nodes = nodes + soup.select('.alphanumeric > .links > a')
    for node in nodes:
        if len(node.findChildren()) > 0:
            node_name = ''.join([element for element in node.select_one('.browse-node') if
                                 isinstance(element, NavigableString)]).strip()
        else:
            node_name = node.text
        node_name = node_name.encode('ascii', 'ignore').decode('ascii')
        print('"' + node['href'] + '","' + link + '","' + node_name + '"')

        if link in node['href']:
            get_nodes(node['href'], session)

        if not boosted:
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--boosted', action='store_true')
    args = parser.parse_args()

    boosted = args.boosted

    if boosted:
        pool = Pool(16)
        session, old_ip = renew_connection('')
        old_ip = ''
    else:
        session = new_session()

    req = Request('GET', CURLIE)
    prepared_req = session.prepare_request(req)

    resp = session.send(prepared_req, timeout=12)

    soup = BeautifulSoup(resp.text, 'html.parser')

    print('id,parent_id,name')

    cats = soup.select('.top-cat > a')
    for cat in cats:
        print('"' + cat['href'] + '","","' + cat.text + '"')
        if boosted:
            session, old_ip = renew_connection(old_ip)
            pool.apply_async(get_nodes, args=[cat['href'], '- ', session])
        else:
            get_nodes(cat['href'], session)
            time.sleep(1)
    if boosted:
        pool.close()
        pool.join()




if __name__ == "__main__":
    main()