import kivy
kivy.require('1.10.0')

from glob import glob
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
import urllib2
import os
from BeautifulSoup import BeautifulSoup, NavigableString, Tag
from kivy.cache import Cache
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup

# adres strony, z ktorej beda pobierane obrazki
URL = "http://xkcd.com"
# katalog do zapisu obrazkow
DIR = "cache"


class PicturesApp(App):

    def __init__(self):
        App.__init__(self)
        self.layout = GridLayout(cols=1)
        self.picture = AsyncImage()
        self.soup = XKCD.load_soup(URL)

    def build(self):

        root = self.root
        self.layout = GridLayout(cols=1)
        self.button_layout = GridLayout(cols=1)
        self.title_label = Label(markup=True)
        self.title_label.size_hint = .1, .1
        self.layout.add_widget(self.title_label)

        self.layout.add_widget(self.picture)
        self.show_image("")

        btn1 = Button(text='Poprzedni')
        self.button_layout.add_widget(btn1)
        btn1.bind(on_press=lambda x: self.show_image_direction('prev'))

        btn2 = Button(text='Nastepny')
        self.button_layout.add_widget(btn2)
        btn2.bind(on_press=lambda x: self.show_image_direction('next'))

        btn3 = Button(text='Losowy')
        self.button_layout.add_widget(btn3)
        btn3.bind(on_press=lambda x: self.show_image_direction('random'))

        textinput = TextInput(multiline=False)
        textinput.hint_text = "Podaj numer obrazka i nacisnij enter"
        self.button_layout.add_widget(textinput)
        textinput.bind(on_text_validate=lambda x: self.show_image(textinput.text))
        self.layout.add_widget(self.button_layout)
        root.add_widget(self.layout)

    def show_image(self, number):
        """Funkcja odpowiedzialna za wyswietlenie obrazka w oknie."""
        Cache.remove('kv.image')
        Cache.remove('kv.texture')
        # pobranie obrazka

        url, title, number = XKCD.get_image(number)

        if url is not None:
            is_image, filename = "", ""
            # sprawdzenie czy obrazek ktory chcemy wyswietlic znajduje sie w katalogu
            for f in glob('cache/' + number + "_*.png"):
                is_image = 1
                filename = f
            # jezeli obrazek zostal znaleziony w katalogu jest wyswietlany
            if is_image == 1:
                image_path = filename
                print "ustawiam obrazek {}".format(image_path)
                self.picture.source = image_path
                self.picture.reload()
                self.layout.do_layout()
            else:
                # w przeciwnym wypadku pobieramy obrazek z sieci
                XKCD.save_image(url, number)
                image_path = 'cache/' + number + "_" + title + ".png"
                self.picture.source = url

            self.title_label.text = 'Numer obrazka: ' + number + ' Tytul: [b]' + title + '[/b]'
            # update aktualnej strony
            self.soup = XKCD.load_soup(URL + '/' + number)

    def show_image_direction(self, move):
        """Pobranie obrazka w zaleznosci od kliknietego przycisku {Nastepnny, Losowy, Poprzedni}."""

        image_url = XKCD.get_image_direction(self.soup, move)

        if image_url is None:
            return
        image_number = image_url.split('//')[1].split('/')[1]
        print image_url
        self.soup = XKCD.load_soup(image_url)
        # wyswietlenie obrazka
        self.show_image(image_number)


    def on_pause(self):
        return True




class XKCD:
    """Klasa odpowiedzialna za pobieranie danych ze strony xkcd.com.

    Zdecydowalem sie na uzycie metod statycznych, poniewaz chce traktowac klase jako biblioteke
    """

    def __init__(self):
        """Pusty konstruktor klasy."""

        pass

    @staticmethod
    def get_image_direction(soup, move):
        """Pobranie danych o obrazku w zaleznosci od kliknietego przycisku.

        Dane dla soup sa podawane na podstawie kodu HTML strony.
        """

        if move == 'prev':
            image_url = soup.find("a", {"href": True, "accesskey": "p"})["href"]
        elif move == 'next':
            image_url = soup.find("a", {"href": True, "accesskey": "n"})["href"]
        elif move == 'random':
            response = urllib2.urlopen("https://c.xkcd.com/random/comic/")
            image_url = response.geturl()

        if image_url == "#":
            return None
        if move == 'random':
            previous_image = image_url
        else:
            previous_image = URL + image_url
        return previous_image

    @staticmethod
    def save_image(url, number):
        """Funkcja, ktora pobiera obrazek do katalogu cache."""

        try:
            page = urllib2.urlopen(url)
        except urllib2.HTTPError:
            return None

        if not os.path.exists(DIR):
            os.makedirs(DIR)

        image_number = url.split('//')[1].split('/')[2]
        # zapisanie obrazka do katalogu
        with open(os.path.join(DIR, number + "_" + image_number), "wb") as f:
            f.write(page.read())
            f.close()
        print "Zapisuje plik o numerze: {} i tytule {}".format(number, image_number)

    @staticmethod
    def get_image(number):
        """Funkcja, ktora pobiera obrazek z danego adresu url."""

        soup = XKCD.load_soup(URL + '/' + number)
        if soup is not False:
            if isinstance(soup, BeautifulSoup):
                image_title = soup.find("div", {"id": "ctitle"})

                # wyszukiwanie numeru obrazka glownego
                for br in soup.findAll('br'):
                    next_br_tag = br.nextSibling
                    if not (next_br_tag and isinstance(next_br_tag, NavigableString)):
                        continue
                    next2_s = next_br_tag.nextSibling
                    if next2_s and isinstance(next2_s, Tag) and next2_s.name == 'br':
                        text = str(next_br_tag).strip()
                        if text:
                            image_number = next_br_tag.split('//')[1].split('/')[1]

                image_url = soup.find("img", {"src": True, "alt": True, "title": True})["src"]
                print image_url
                return 'http:' + image_url, image_title.text, image_number
        return None, None, None

    @staticmethod
    def load_soup(url):
        """Funkcja odpowiedzialna za przygotowanie danej strony do parsowania przez BeautyfoulSoup."""

        try:
            page = urllib2.urlopen(url)
        except urllib2.HTTPError as e:
            # W razie zapytania o strone ktora nie istnieje zwracany jest error 404
            print "Error"
            print e
            if e.code == 403:
                print "Sproboj pozniej"
            if e.code == 404:
                print "Blad 404"
                popup = Popup(title='Nie ma takiego obrazka',
                              content=Label(text='Nie ma takiego obrazka, sproboj ponownie'),
                              size_hint=(None, None), size=(400, 400))
                content = Button(text='Ok')
                content.bind(on_press=popup.dismiss)
                popup.open()

                return False
            return False
        # parsowanie bierzacej strony
        soup = BeautifulSoup(page.read())
        return soup


if __name__ == '__main__':
    PicturesApp().run()